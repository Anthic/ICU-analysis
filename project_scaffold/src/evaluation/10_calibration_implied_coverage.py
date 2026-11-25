"""
Phase 10: calibration-implied coverage test of the mechanism (MIMIC-IV and eICU-CRD).
File: src/evaluation/10_calibration_implied_coverage.py

If scores are calibrated within a stratum g, the class-conditional coverage of the POOLED class-conditional rule is
determined by the stratum's score distribution alone (no labels):
    cov_deaths(g)    = sum_g p 1[p >= t_d] / sum_g p            (t_d = 1 - q_1)
    cov_survivors(g) = sum_g (1-p) 1[p <= t_s] / sum_g (1-p)    (t_s = q_0)
We compare these label-free predictions with observed coverage across strata (age, race, sex, insurance[MIMIC]) and
across hospitals (eICU), and report the share of the squared deviation from 0.90 that the prediction explains,
slope, RMSE and a binomial noise floor. Residuals indicate within-stratum miscalibration (the identity fails there).
  mimic_test : thresholds from MIMIC calibration split, strata of the MIMIC test split
  eicu_all   : class-conditional thresholds fit on ALL eICU (as in Phase 7); predictions with raw scores ('raw') and with
               scores logistic-recalibrated on eICU ('recal', in-sample; weights only, thresholds stay on the raw scale)
Outputs: outputs/tables/phase10_cells{tag}.csv ; phase10_fit{tag}.csv ; outputs/results/phase10_summary{tag}.json
Usage: python src/evaluation/10_calibration_implied_coverage.py --seeds 100 [--drop temperature gcs_min intubated --tag harm]
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.conformal.utils import fit_class_conditional  # noqa: E402


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


baseline = load("baseline", "src/models/03_train_baseline.py")
ext = load("extval", "src/evaluation/06_external_validation.py")
TABLES, RESULTS = ROOT / "outputs" / "tables", ROOT / "outputs" / "results"


def cell(y, p, w, t_d, t_s):
    d, v = y == 1, y == 0
    return dict(n=len(y), n_deaths=int(d.sum()), prevalence=float(y.mean()), mean_score=float(p.mean()),
                obs_d=float((p[d] >= t_d).mean()) if d.any() else np.nan, obs_s=float((p[v] <= t_s).mean()) if v.any() else np.nan,
                pred_d=float((w * (p >= t_d)).sum() / w.sum()), pred_s=float(((1 - w) * (p <= t_s)).sum() / (1 - w).sum()))


def recal_weights(y, p):
    z = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6))).reshape(-1, 1)
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(z, y)
    return lr.predict_proba(z)[:, 1]


def run(n_seeds, alpha, drop, tag):
    t0 = time.time(); sfx = f"_{tag}" if tag else ""
    mimic, eicu = ext.read_table(ext.MIMIC_FEATURES), ext.read_table(ext.EICU_FEATURES)
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    if drop:
        cols = [c for c in cols if not any(c.startswith(d) for d in drop)]
    Xm, Xe = ext.encode(mimic, cols), ext.encode(eicu, cols)
    ym, ye = mimic["mortality"].astype(int).to_numpy(), eicu["mortality"].astype(int).to_numpy()
    hosp = eicu["hospitalid"].to_numpy(); hc = pd.Series(hosp).value_counts()
    rows = []
    for seed in range(n_seeds):
        tr, ca, te = baseline.split_indices(mimic, seed)
        model = baseline.fit_baseline(Xm.iloc[tr], ym[tr], seed)
        p_cal, p_te = model.predict_proba(Xm.iloc[ca])[:, 1], model.predict_proba(Xm.iloc[te])[:, 1]
        pe = model.predict_proba(Xe)[:, 1]
        # --- MIMIC internal
        q = fit_class_conditional(ym[ca], p_cal, alpha); t_d, t_s = 1 - q[1], q[0]
        yt = ym[te]
        for a in ext.MIMIC_ATTRS:
            g = mimic.iloc[te][a].astype(str).to_numpy()
            for sg in np.unique(g):
                m = g == sg
                rows.append(dict(seed=seed, dataset="mimic_test", level="demographic", attr=a, stratum=sg, weights="raw", **cell(yt[m], p_te[m], p_te[m], t_d, t_s)))
        # --- eICU (thresholds fit on all eICU)
        qe = fit_class_conditional(ye, pe, alpha); t_d, t_s = 1 - qe[1], qe[0]
        w_rec = recal_weights(ye, pe)
        for wn, w in (("raw", pe), ("recal", w_rec)):
            for a in ext.EXT_ATTRS:
                g = eicu[a].astype(str).to_numpy()
                for sg in np.unique(g):
                    m = g == sg
                    rows.append(dict(seed=seed, dataset="eicu_all", level="demographic", attr=a, stratum=sg, weights=wn, **cell(ye[m], pe[m], w[m], t_d, t_s)))
            for hid, cnt in hc.items():
                m = hosp == hid
                if cnt >= ext.MIN_HOSPITAL_N and ye[m].sum() >= ext.MIN_HOSPITAL_DEATHS:
                    rows.append(dict(seed=seed, dataset="eicu_all", level="hospital", attr="hospital", stratum=str(hid), weights=wn, **cell(ye[m], pe[m], w[m], t_d, t_s)))
        if (seed + 1) % 20 == 0:
            print(f"  seed {seed + 1}/{n_seeds} ({time.time() - t0:.0f}s)")
    df = pd.DataFrame(rows)
    cells = df.groupby(["dataset", "level", "attr", "stratum", "weights"]).mean(numeric_only=True).drop(columns="seed").reset_index()
    cells.to_csv(TABLES / f"phase10_cells{sfx}.csv", index=False)

    fits = []
    for (ds, lv, wn), g in cells.groupby(["dataset", "level", "weights"]):
        for cls, obs, pred, nn in (("deaths", "obs_d", "pred_d", "n_deaths"), ("survivors", "obs_s", "pred_s", None)):
            d = g.dropna(subset=[obs, pred]); o, p_ = d[obs].values, d[pred].values
            nsz = d["n_deaths"].values if cls == "deaths" else (d["n"] - d["n_deaths"]).values
            gap_o, gap_p = o - (1 - alpha), p_ - (1 - alpha)
            sse_null = ((o - (1 - alpha)) ** 2).sum(); sse_pred = ((o - p_) ** 2).sum()
            noise = (0.09 / nsz).sum()                                        # expected sum of binomial noise variance
            sl = np.polyfit(gap_p, gap_o, 1)[0] if len(d) > 2 and gap_p.std() > 0 else np.nan
            fits.append(dict(dataset=ds, level=lv, weights=wn, class_=cls, n_cells=len(d), r2_vs_nominal=1 - sse_pred / sse_null,
                             slope_obs_on_pred=sl, spearman=float(spearmanr(gap_p, gap_o).statistic) if len(d) > 3 else np.nan,
                             rmse=float(np.sqrt(sse_pred / len(d))), rmse_noise_floor=float(np.sqrt(noise / len(d))),
                             rmse_nominal_baseline=float(np.sqrt(sse_null / len(d))), sd_obs_gap=float(gap_o.std())))
    fit = pd.DataFrame(fits); fit.to_csv(TABLES / f"phase10_fit{sfx}.csv", index=False)
    (RESULTS / f"phase10_summary{sfx}.json").write_text(fit.to_json(orient="records", indent=1))
    pd.set_option("display.width", 220)
    print(fit.round(3).to_string(index=False)); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=20); ap.add_argument("--alpha", type=float, default=0.10)
    ap.add_argument("--drop", nargs="*", default=None); ap.add_argument("--tag", default="")
    a = ap.parse_args(); run(a.seeds, a.alpha, a.drop, a.tag)
