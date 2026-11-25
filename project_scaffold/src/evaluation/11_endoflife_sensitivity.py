"""
Phase 11 (Analysis 3): end-of-life / outcome-coding sensitivity and continuous-age coverage (MIMIC-IV only).
File: src/evaluation/11_endoflife_sensitivity.py

Concern: hospital discharge to hospice (and palliative-care coding) is coded as 'survival' (mortality = 0) although
these patients are expected to die soon, so age-related coverage patterns could reflect outcome coding / goals-of-care
rather than model behaviour. eICU has no hospice field, so this analysis is MIMIC-IV only.
Variants (same XGBoost predictors, same split procedure, own 50/25/25 split per variant and seed):
  V0_original        : y = in-hospital death                                   (reference)
  V1_death_or_hospice: y = death OR discharged to hospice                      (hospice treated as event)
  V2_excl_hospice    : hospice discharges removed, y = death
  V3_excl_hosp_or_pal: hospice discharges AND stays with a palliative-care diagnosis code (Z51.5 / V66.7) removed, y = death.
                       NOTE: palliative codes are assigned during/after the stay and are outcome-informative; this variant is
                       a bound, not a recommended analysis (it removes ~55% of deaths).
For each: pooled class-conditional conformal thresholds (alpha=0.10) from the calibration split; coverage on the test split by
age group (4 strata) and by 10-year age band (continuous-age view). Outputs per-seed rows and a summary.
Outputs: outputs/tables/phase11_endoflife_{rows,summary}{tag}.csv ; outputs/results/phase11_summary{tag}.json
Usage: python src/evaluation/11_endoflife_sensitivity.py --seeds 100 [--tag x]
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.conformal.utils import fit_class_conditional, prediction_sets  # noqa: E402


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


baseline = load("baseline", "src/models/03_train_baseline.py")
ext = load("extval", "src/evaluation/06_external_validation.py")
TABLES, RESULTS = ROOT / "outputs" / "tables", ROOT / "outputs" / "results"
BANDS = [(18, 29), (30, 39), (40, 49), (50, 59), (60, 69), (70, 79), (80, 200)]


def band(a):
    for lo, hi in BANDS:
        if lo <= a <= hi:
            return f"{lo}-{hi if hi < 200 else '91+'}"


def run(n_seeds, alpha, tag):
    t0 = time.time(); sfx = f"_{tag}" if tag else ""
    mimic = ext.read_table(ext.MIMIC_FEATURES)
    flags = pd.read_parquet(ROOT / "data" / "processed" / "mimic_endoflife_flags.parquet")[["stay_id", "hospice", "palliative_dx"]]
    mimic = mimic.merge(flags, on="stay_id", how="left", validate="one_to_one")
    assert mimic[["hospice", "palliative_dx"]].notna().all().all() and len(mimic) == 51838
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    mimic["band"] = mimic["anchor_age"].map(band)
    death, hos, pal = mimic["mortality"].astype(int).to_numpy(), mimic["hospice"].to_numpy(), mimic["palliative_dx"].to_numpy()
    variants = {"V0_original": (np.ones(len(mimic), bool), death),
                "V1_death_or_hospice": (np.ones(len(mimic), bool), np.maximum(death, hos)),
                "V2_excl_hospice": (hos == 0, death),
                "V3_excl_hosp_or_pal": ((hos == 0) & (pal == 0), death)}
    rows = []
    for seed in range(n_seeds):
        for vname, (keep, y_all) in variants.items():
            df = mimic[keep].reset_index(drop=True).copy(); y = y_all[keep]; df["mortality"] = y
            X = ext.encode(df, cols)
            tr, ca, te = baseline.split_indices(df, seed)
            model = baseline.fit_baseline(X.iloc[tr], y[tr], seed)
            p_cal, p_te = model.predict_proba(X.iloc[ca])[:, 1], model.predict_proba(X.iloc[te])[:, 1]
            q = fit_class_conditional(y[ca], p_cal, alpha); sets = prediction_sets(p_te, q)
            yt = y[te]; hit = np.where(yt == 1, sets[:, 1], sets[:, 0])
            for attr, g in (("All", np.array(["All"] * len(te))), ("age_group", df.iloc[te]["age_group"].astype(str).to_numpy()),
                            ("age_band", df.iloc[te]["band"].to_numpy())):
                for sg in np.unique(g):
                    m = g == sg; d, v = (yt == 1) & m, (yt == 0) & m
                    rows.append(dict(seed=seed, variant=vname, attr=attr, stratum=sg, n=int(m.sum()), n_deaths=int(d.sum()),
                                     prevalence=float(yt[m].mean()), cov_deaths=float(hit[d].mean()) if d.any() else np.nan,
                                     cov_surv=float(hit[v].mean()) if v.any() else np.nan))
        if (seed + 1) % 10 == 0:
            print(f"  seed {seed + 1}/{n_seeds} ({time.time() - t0:.0f}s)", flush=True)
    df = pd.DataFrame(rows); df.to_csv(TABLES / f"phase11_endoflife_rows{sfx}.csv", index=False)
    g = df.groupby(["variant", "attr", "stratum"])
    summ = g.agg(n=("n", "mean"), n_deaths=("n_deaths", "mean"), prevalence=("prevalence", "mean"),
                 cov_deaths=("cov_deaths", "mean"), sd_deaths=("cov_deaths", "std"),
                 cov_surv=("cov_surv", "mean"), sd_surv=("cov_surv", "std")).reset_index()
    summ.to_csv(TABLES / f"phase11_endoflife_summary{sfx}.csv", index=False)
    # paired contrasts vs V0 for the two age endpoints
    out = {}
    piv = df[df.attr == "age_group"].pivot_table(index=["seed", "stratum"], columns="variant", values=["cov_deaths", "cov_surv"])
    for vn in list(variants)[1:]:
        for stratum, col in (("18-49", "cov_deaths"), ("75+", "cov_surv")):
            d = (piv[col][vn] - piv[col]["V0_original"]).xs(stratum, level="stratum")
            out[f"{vn}__{stratum}__{col}__diff_vs_V0"] = dict(mean=float(d.mean()), sd=float(d.std()), p2_5=float(d.quantile(.025)), p97_5=float(d.quantile(.975)))
    (RESULTS / f"phase11_summary{sfx}.json").write_text(json.dumps(out, indent=1))
    pd.set_option("display.width", 220)
    print(summ[summ.attr != "age_band"].round(3).to_string(index=False)); print(json.dumps(out, indent=1)); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--alpha", type=float, default=0.10); ap.add_argument("--tag", default="")
    a = ap.parse_args(); run(a.seeds, a.alpha, a.tag)
