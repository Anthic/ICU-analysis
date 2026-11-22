"""
Phase 7: Mechanism + small-stratum stability analysis (exploratory; MIMIC-IV -> eICU-CRD).
File: src/evaluation/07_mechanism_analysis.py

Question A (mechanism): is a stratum's class-conditional coverage gap explained by how well the model
separates deaths from survivors INSIDE that stratum (within-stratum AUROC), rather than by group
identity itself?  Global class-conditional thresholds are used, so any gap is heterogeneity, not shift:
    mimic_test : thresholds from MIMIC calibration split, evaluated on MIMIC test split
    eicu_all   : thresholds fit on ALL eICU (target-domain, in-sample for the marginal threshold only)
Strata: age, race, sex, insurance (MIMIC only), hospital (eICU only, >=100 pts and >=20 deaths).

Question B (stability): when is group-specific (Mondrian) calibration safe?  Using hospitals as groups
in eICU (patient-level 50/50 split), compare hospital-specific class-conditional thresholds against the
global eICU-calibration thresholds, binned by the number of deaths in the hospital's calibration part.

Outputs: outputs/tables/phase7_stratum_stats{tag}.csv (per seed x dataset x stratum)
         outputs/tables/phase7_mechanism_summary{tag}.csv, phase7_stability{tag}.csv
         outputs/results/phase7_summary{tag}.json
Usage:  python src/evaluation/07_mechanism_analysis.py --seeds 20 [--drop temperature gcs_min intubated --tag harm]
"""
from __future__ import annotations

import argparse, importlib.util, json, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.conformal.utils import fit_class_conditional, prediction_sets  # noqa: E402


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


baseline = load("baseline", "src/models/03_train_baseline.py")
ext = load("extval", "src/evaluation/06_external_validation.py")
TABLES, RESULTS = ROOT / "outputs" / "tables", ROOT / "outputs" / "results"


def stratum_stats(y, p, hit, mask):
    yy, pp, hh = y[mask], p[mask], hit[mask]
    d, v = yy == 1, yy == 0
    auc = roc_auc_score(yy, pp) if d.sum() >= 5 and v.sum() >= 5 else np.nan
    return dict(n=int(mask.sum()), n_deaths=int(d.sum()), prevalence=float(d.mean()), auroc=float(auc),
                mean_p_deaths=float(pp[d].mean()) if d.any() else np.nan,
                mean_p_surv=float(pp[v].mean()) if v.any() else np.nan,
                cov_deaths=float(hh[d].mean()) if d.any() else np.nan,
                cov_surv=float(hh[v].mean()) if v.any() else np.nan)


def hit_of(y, sets):
    return np.where(y == 1, sets[:, 1], sets[:, 0])


def run(n_seeds, alpha, drop, tag):
    t0 = time.time()
    sfx = f"_{tag}" if tag else ""
    mimic, eicu = ext.read_table(ext.MIMIC_FEATURES), ext.read_table(ext.EICU_FEATURES)
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    if drop:
        cols = [c for c in cols if not any(c.startswith(d) for d in drop)]
    Xm, Xe = ext.encode(mimic, cols), ext.encode(eicu, cols)
    ym, ye = mimic["mortality"].astype(int).to_numpy(), eicu["mortality"].astype(int).to_numpy()
    hosp = eicu["hospitalid"].to_numpy()
    hosp_ok = pd.Series(hosp).value_counts()
    rows, stab = [], []

    for seed in range(n_seeds):
        tr, ca, te = baseline.split_indices(mimic, seed)
        model = baseline.fit_baseline(Xm.iloc[tr], ym[tr], seed)
        p_cal, p_te = model.predict_proba(Xm.iloc[ca])[:, 1], model.predict_proba(Xm.iloc[te])[:, 1]
        p_e = model.predict_proba(Xe)[:, 1]

        # ---- A1: MIMIC internal ----
        q = fit_class_conditional(ym[ca], p_cal, alpha)
        h = hit_of(ym[te], prediction_sets(p_te, q))
        base = dict(seed=seed, dataset="mimic_test")
        rows.append({**base, "attr": "All", "stratum": "All", **stratum_stats(ym[te], p_te, h, np.ones(len(te), bool))})
        for a in ext.MIMIC_ATTRS:
            g = mimic.iloc[te][a].astype(str).to_numpy()
            for sg in np.unique(g):
                rows.append({**base, "attr": a, "stratum": sg, **stratum_stats(ym[te], p_te, h, g == sg)})

        # ---- A2: eICU, target-domain global thresholds ----
        qe = fit_class_conditional(ye, p_e, alpha)
        he = hit_of(ye, prediction_sets(p_e, qe))
        base = dict(seed=seed, dataset="eicu_all")
        rows.append({**base, "attr": "All", "stratum": "All", **stratum_stats(ye, p_e, he, np.ones(len(ye), bool))})
        for a in ext.EXT_ATTRS:
            g = eicu[a].astype(str).to_numpy()
            for sg in np.unique(g):
                rows.append({**base, "attr": a, "stratum": sg, **stratum_stats(ye, p_e, he, g == sg)})
        for hid, cnt in hosp_ok.items():
            m = hosp == hid
            if cnt >= ext.MIN_HOSPITAL_N and ye[m].sum() >= ext.MIN_HOSPITAL_DEATHS:
                rows.append({**base, "attr": "hospital", "stratum": str(hid), **stratum_stats(ye, p_e, he, m)})

        # ---- B: hospital-specific vs global thresholds, by calibration deaths ----
        e_cal, e_te = ext.split_eicu(eicu, seed, "patient")
        q_glob = fit_class_conditional(ye[e_cal], p_e[e_cal], alpha)
        hg = hit_of(ye[e_te], prediction_sets(p_e[e_te], q_glob))
        hc, ht = hosp[e_cal], hosp[e_te]
        for hid in np.unique(hosp):
            mc, mt = hc == hid, ht == hid
            ytc, ytt = ye[e_cal][mc], ye[e_te][mt]
            if (ytt == 1).sum() < 5 or (ytt == 0).sum() < 20:
                continue
            ph = p_e[e_cal][mc]
            qh = fit_class_conditional(ytc, ph, alpha) if len(ytc) and (ytc == 1).any() and (ytc == 0).any() else np.array([np.inf, np.inf])
            hm = hit_of(ytt, prediction_sets(p_e[e_te][mt], qh))
            d, v = ytt == 1, ytt == 0
            stab.append(dict(seed=seed, hospitalid=hid, cal_deaths=int((ytc == 1).sum()), cal_surv=int((ytc == 0).sum()),
                             test_deaths=int(d.sum()), inf_death_q=bool(np.isinf(qh[1])),
                             global_cov_deaths=float(hg[mt][d].mean()), hosp_cov_deaths=float(hm[d].mean()),
                             global_cov_surv=float(hg[mt][v].mean()), hosp_cov_surv=float(hm[v].mean())))
        print(f"  seed {seed + 1}/{n_seeds} ({time.time() - t0:.0f}s)")

    ps = pd.DataFrame(rows)
    ps.to_csv(TABLES / f"phase7_stratum_stats{sfx}.csv", index=False)
    st = pd.DataFrame(stab)
    st.to_csv(TABLES / f"phase7_stability_per_seed{sfx}.csv", index=False)

    # ---- mechanism summary: stratum-level (mean over seeds), then correlation ----
    s = ps[ps.attr != "All"].groupby(["dataset", "attr", "stratum"]).mean(numeric_only=True).reset_index()
    s["gap_deaths"] = s.cov_deaths - (1 - alpha)
    s["gap_surv"] = s.cov_surv - (1 - alpha)
    s["gap_min"] = s[["gap_deaths", "gap_surv"]].min(axis=1)
    all_ref = ps[ps.attr == "All"].groupby("dataset")["auroc"].mean().to_dict()
    s["auroc_minus_overall"] = s.apply(lambda r: r.auroc - all_ref[r.dataset], axis=1)
    s.to_csv(TABLES / f"phase7_mechanism_summary{sfx}.csv", index=False)

    def corr(df, x, y):
        d = df[[x, y]].dropna()
        if len(d) < 4:
            return None
        r = spearmanr(d[x], d[y])
        return dict(n=int(len(d)), spearman=float(r.statistic), p=float(r.pvalue))

    out = {"n_seeds": n_seeds, "alpha": alpha, "dropped": drop or [], "corr": {}}
    for ds in ("mimic_test", "eicu_all"):
        d = s[s.dataset == ds]
        dh = d[d.attr == "hospital"]
        dg = d[d.attr != "hospital"]
        out["corr"][ds] = {
            "demographic_strata: AUROC vs death-coverage gap": corr(dg, "auroc", "gap_deaths"),
            "demographic_strata: prevalence vs death-coverage gap": corr(dg, "prevalence", "gap_deaths"),
            "demographic_strata: mean_p_deaths vs death-coverage gap": corr(dg, "mean_p_deaths", "gap_deaths"),
            "hospital: AUROC vs death-coverage gap": corr(dh, "auroc", "gap_deaths"),
            "hospital: prevalence vs death-coverage gap": corr(dh, "prevalence", "gap_deaths"),
            "hospital: mean_p_deaths vs death-coverage gap": corr(dh, "mean_p_deaths", "gap_deaths"),
        }
        out["corr"][ds] = {k: v for k, v in out["corr"][ds].items() if v is not None}

    # ---- stability summary ----
    if len(st):
        st["cal_deaths_bin"] = pd.cut(st.cal_deaths, [-1, 9, 19, 39, 79, 10**6], labels=["<10", "10-19", "20-39", "40-79", "80+"])
        for c in ("global", "hosp"):
            st[f"{c}_dev_deaths"] = (st[f"{c}_cov_deaths"] - (1 - alpha)).abs()
        rows_b = []
        for b, d in st.groupby("cal_deaths_bin", observed=True):
            rows_b.append(dict(cal_deaths_bin=str(b), n_hosp_seed=len(d), share_inf_threshold=float(d.inf_death_q.mean()),
                               global_mean_abs_dev=float(d.global_dev_deaths.mean()), hosp_mean_abs_dev=float(d.hosp_dev_deaths.mean()),
                               global_share_below_80=float((d.global_cov_deaths < .8).mean()),
                               hosp_share_below_80=float((d.hosp_cov_deaths < .8).mean()),
                               hosp_mean_cov=float(d.hosp_cov_deaths.mean()), global_mean_cov=float(d.global_cov_deaths.mean())))
        stb = pd.DataFrame(rows_b)
        stb.to_csv(TABLES / f"phase7_stability{sfx}.csv", index=False)
        out["stability"] = rows_b
    (RESULTS / f"phase7_summary{sfx}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--alpha", type=float, default=0.10)
    ap.add_argument("--drop", nargs="*", default=None)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    run(a.seeds, a.alpha, a.drop, a.tag)
