"""
Phase 6b: External validation of subgroup conformal coverage (MIMIC-IV -> eICU-CRD).
File: src/evaluation/06_external_validation.py

Per seed:  train XGBoost on the MIMIC-IV train split (same split/model as Phase 3), calibrate on the
MIMIC-IV calibration split, then evaluate on eICU.  eICU patients are also split (patient-level, or
hospital-disjoint) into an eICU-calibration half and an eICU-test half so that target-domain
recalibration can be compared with pure transport on the SAME eICU test patients.

Configurations (all evaluated on the eICU test half unless noted):
    internal_mimic_cc            MIMIC test, global class-conditional (reference, = Phase 4)
    internal_mimic_mondrian_cc   MIMIC test, group x class thresholds (reference, = Phase 5)
    ext_mimiccal_cc              eICU test, thresholds from MIMIC calibration (pure transport)
    ext_mimiccal_mondrian_cc     eICU test, group x class thresholds from MIMIC calibration
    ext_eicucal_cc               eICU test, global class-conditional thresholds from eICU calibration half
    ext_eicucal_mondrian_cc      eICU test, group x class thresholds from eICU calibration half
    ext_mimiccal_cc_alleicu      ALL eICU patients, MIMIC thresholds (used for the per-hospital table)

Attributes audited externally: age_group, race_group, sex  (eICU has NO insurance variable).

PRE-SPECIFIED PRIMARY ENDPOINTS (see research_writing/08_PHASE6_EICU_PLAN.md):
    P1  eICU death coverage, ages 18-49, config ext_mimiccal_cc
    P2  eICU survivor coverage, ages 75+, config ext_mimiccal_cc
    Everything else is secondary/exploratory.

Outputs (outputs/tables, outputs/results):
    phase6_mimic_vs_eicu_coverage_per_seed.csv
    phase6_mimic_vs_eicu_coverage.csv            (aggregated over seeds; main table)
    phase6_hospital_coverage.csv
    phase6_model_performance.csv
    phase6_summary.json

Usage:
    python src/evaluation/06_external_validation.py                 # 20 seeds, patient split
    python src/evaluation/06_external_validation.py --seeds 100     # final run
    python src/evaluation/06_external_validation.py --split hospital
    python src/evaluation/06_external_validation.py --seeds 2 --eicu-path <file>   # smoke test
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.conformal.utils import (  # noqa: E402
    fit_class_conditional,
    fit_mondrian_class_conditional,
    prediction_sets,
    prediction_sets_mondrian,
)

spec = importlib.util.spec_from_file_location("phase3_baseline", PROJECT_ROOT / "src" / "models" / "03_train_baseline.py")
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)

TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
RESULTS_DIR = PROJECT_ROOT / "outputs" / "results"
MIMIC_FEATURES = baseline.FEATURES_PATH
EICU_FEATURES = PROJECT_ROOT / "data" / "processed" / "eicu_features.parquet"

EXT_ATTRS = ("age_group", "race_group", "sex")
MIMIC_ATTRS = ("age_group", "race_group", "sex", "insurance_group")
MIN_HOSPITAL_DEATHS = 20
MIN_HOSPITAL_N = 100


def wilson(k: float, n: float, z: float = 1.959963984540054):
    if n <= 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(c - h), float(c + h)


def read_table(path: Path) -> pd.DataFrame:
    """Read parquet; if pyarrow is unavailable/blocked, fall back to the CSV twin (.csv.gz, or .csv for MIMIC)."""
    try:
        if path.exists():
            return pd.read_parquet(path)
    except Exception as exc:
        print(f"parquet read failed ({type(exc).__name__}); trying CSV twin")
    for alt in (path.with_name(path.stem + ".csv.gz"), path.with_suffix(".csv")):
        if alt.exists():
            print(f"reading {alt.name}")
            return pd.read_csv(alt)
    raise FileNotFoundError(path)


def encode(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    X = df[cols].copy()
    X["sex"] = X["sex"].map({"Male": 1, "Female": 0})
    if X["sex"].isna().any():
        raise ValueError("sex must be Male/Female")
    return X


def metrics(y, sets, mask) -> dict:
    yy = y[mask]
    s = sets[mask]
    hit = np.where(yy == 1, s[:, 1], s[:, 0])
    size = s.sum(1)
    d, v = yy == 1, yy == 0
    return dict(
        n=int(mask.sum()), n_deaths=int(d.sum()), n_survivors=int(v.sum()),
        coverage_overall=float(hit.mean()) if len(hit) else np.nan,
        coverage_deaths=float(hit[d].mean()) if d.any() else np.nan,
        coverage_survivors=float(hit[v].mean()) if v.any() else np.nan,
        mean_set_size=float(size.mean()) if len(size) else np.nan,
        share_singleton=float((size == 1).mean()) if len(size) else np.nan,
        share_both=float((size == 2).mean()) if len(size) else np.nan,
    )


def audit(rows: list, base: dict, y, sets, groups: dict[str, np.ndarray]) -> None:
    rows.append({**base, "attr": "All", "subgroup": "All", **metrics(y, sets, np.ones(len(y), bool))})
    for attr, g in groups.items():
        for sg in np.unique(g):
            rows.append({**base, "attr": attr, "subgroup": str(sg), **metrics(y, sets, g == sg)})


def calib_stats(y, p) -> dict:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    lg = np.log(p / (1 - p)).reshape(-1, 1)
    lr = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000).fit(lg, y)
    return dict(auroc=float(roc_auc_score(y, p)), brier=float(brier_score_loss(y, p)),
                cal_slope=float(lr.coef_[0, 0]), cal_intercept=float(lr.intercept_[0]),
                citl=float(p.mean() - y.mean()), mean_pred=float(p.mean()), prevalence=float(y.mean()))


def split_eicu(eicu: pd.DataFrame, seed: int, mode: str):
    ix = np.arange(len(eicu))
    y = eicu["mortality"].to_numpy()
    if mode == "hospital":
        gss = GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=seed)
        cal, test = next(gss.split(ix, y, groups=eicu["hospitalid"].to_numpy()))
        return cal, test
    strata = eicu["mortality"].astype(str) + "_" + eicu["race_group"].astype(str)
    vc = strata.value_counts()
    strata = strata.where(strata.map(vc) >= 4, eicu["mortality"].astype(str))
    return train_test_split(ix, test_size=0.5, random_state=seed, stratify=strata)


def run(n_seeds: int, split_mode: str, alpha: float, eicu_path: Path, sample: int | None,
        drop: list[str] | None = None, tag: str = "") -> None:
    t0 = time.time()
    sfx = f"_{tag}" if tag else ""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if not eicu_path.exists() and not eicu_path.with_name(eicu_path.stem + ".csv.gz").exists():
        raise FileNotFoundError(f"Run src/data_processing/06_build_eicu_features.py first: {eicu_path}")

    mimic = read_table(MIMIC_FEATURES)
    eicu = read_table(eicu_path)
    if sample is not None and sample < len(eicu):
        eicu = eicu.sample(n=sample, random_state=42).reset_index(drop=True)
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    if drop:
        cols = [c for c in cols if not any(c.startswith(d) for d in drop)]
        print(f"dropping features with prefixes {drop}; {len(cols)} predictors remain")
    missing = [c for c in cols if c not in eicu.columns]
    if missing:
        raise ValueError(f"eICU features missing predictors: {missing}")
    Xm, Xe = encode(mimic, cols), encode(eicu, cols)
    ym, ye = mimic["mortality"].astype(int).to_numpy(), eicu["mortality"].astype(int).to_numpy()
    eicu_groups = {a: eicu[a].astype(str).to_numpy() for a in EXT_ATTRS}

    rows: list[dict] = []
    hosp_rows: list[pd.DataFrame] = []
    perf_rows: list[dict] = []

    for seed in range(n_seeds):
        ts = time.time()
        tr, ca, te = baseline.split_indices(mimic, seed)
        model = baseline.fit_baseline(Xm.iloc[tr], ym[tr], seed)
        p_cal = model.predict_proba(Xm.iloc[ca])[:, 1]
        p_te = model.predict_proba(Xm.iloc[te])[:, 1]
        p_e = model.predict_proba(Xe)[:, 1]
        y_cal, y_te = ym[ca], ym[te]

        perf_rows.append({"seed": seed, "dataset": "mimic_test", **calib_stats(y_te, p_te)})
        perf_rows.append({"seed": seed, "dataset": "eicu_all", **calib_stats(ye, p_e)})

        # ---- reference: internal MIMIC ----------------------------------------------------
        q_cc = fit_class_conditional(y_cal, p_cal, alpha)
        m_groups_te = {a: mimic.iloc[te][a].astype(str).to_numpy() for a in MIMIC_ATTRS}
        base = {"split_mode": split_mode, "seed": seed}
        audit(rows, {**base, "config": "internal_mimic_cc"}, y_te, prediction_sets(p_te, q_cc), m_groups_te)
        m_groups_cal = {a: mimic.iloc[ca][a].astype(str).to_numpy() for a in MIMIC_ATTRS}
        # Mondrian internal, evaluated per attribute (one attribute at a time, like Phase 5)
        for a in MIMIC_ATTRS:
            qd = fit_mondrian_class_conditional(y_cal, p_cal, m_groups_cal[a], alpha)
            sets = prediction_sets_mondrian(p_te, m_groups_te[a], qd)
            audit(rows, {**base, "config": "internal_mimic_mondrian_cc"}, y_te, sets, {a: m_groups_te[a]})

        # ---- external, pure transport (all eICU, for hospital table) ----------------------
        sets_all = prediction_sets(p_e, q_cc)
        audit(rows, {**base, "config": "ext_mimiccal_cc_alleicu"}, ye, sets_all, eicu_groups)
        hit = np.where(ye == 1, sets_all[:, 1], sets_all[:, 0])
        h = pd.DataFrame({"hospitalid": eicu["hospitalid"].to_numpy(), "y": ye, "hit": hit})
        agg = h.groupby("hospitalid").apply(lambda d: pd.Series({
            "n": len(d), "n_deaths": int((d.y == 1).sum()),
            "cov_deaths": d.loc[d.y == 1, "hit"].mean() if (d.y == 1).any() else np.nan,
            "cov_survivors": d.loc[d.y == 0, "hit"].mean() if (d.y == 0).any() else np.nan}), include_groups=False
        ).reset_index()
        agg["seed"] = seed
        hosp_rows.append(agg)

        # ---- external with eICU calibration / test halves ---------------------------------
        e_cal, e_te = split_eicu(eicu, seed, split_mode)
        ye_cal, ye_te = ye[e_cal], ye[e_te]
        if (ye_cal == 1).sum() < 5 or (ye_te == 1).sum() < 5:
            print(f"  seed {seed}: too few deaths in an eICU half; skipping external configs")
            continue
        pe_cal, pe_te = p_e[e_cal], p_e[e_te]
        g_te = {a: eicu_groups[a][e_te] for a in EXT_ATTRS}
        g_cal = {a: eicu_groups[a][e_cal] for a in EXT_ATTRS}

        audit(rows, {**base, "config": "ext_mimiccal_cc"}, ye_te, prediction_sets(pe_te, q_cc), g_te)
        q_e = fit_class_conditional(ye_cal, pe_cal, alpha)
        audit(rows, {**base, "config": "ext_eicucal_cc"}, ye_te, prediction_sets(pe_te, q_e), g_te)
        for a in EXT_ATTRS:
            q_m_mimic = fit_mondrian_class_conditional(y_cal, p_cal, m_groups_cal[a], alpha)
            audit(rows, {**base, "config": "ext_mimiccal_mondrian_cc"}, ye_te,
                  prediction_sets_mondrian(pe_te, g_te[a], q_m_mimic), {a: g_te[a]})
            q_m_e = fit_mondrian_class_conditional(ye_cal, pe_cal, g_cal[a], alpha)
            audit(rows, {**base, "config": "ext_eicucal_mondrian_cc"}, ye_te,
                  prediction_sets_mondrian(pe_te, g_te[a], q_m_e), {a: g_te[a]})
        print(f"  seed {seed + 1}/{n_seeds} done ({time.time() - ts:.0f}s)")

    per_seed = pd.DataFrame(rows)
    per_seed.to_csv(TABLES_DIR / f"phase6_mimic_vs_eicu_coverage_per_seed{sfx}.csv", index=False)

    # ---- aggregate over seeds -------------------------------------------------------------
    keys = ["split_mode", "config", "attr", "subgroup"]
    agg = per_seed.groupby(keys).agg(
        seeds=("seed", "nunique"), n_mean=("n", "mean"), deaths_mean=("n_deaths", "mean"),
        survivors_mean=("n_survivors", "mean"),
        cov_deaths_mean=("coverage_deaths", "mean"), cov_deaths_sd=("coverage_deaths", "std"),
        cov_deaths_p025=("coverage_deaths", lambda s: s.quantile(.025)),
        cov_deaths_p975=("coverage_deaths", lambda s: s.quantile(.975)),
        cov_surv_mean=("coverage_survivors", "mean"), cov_surv_sd=("coverage_survivors", "std"),
        cov_surv_p025=("coverage_survivors", lambda s: s.quantile(.025)),
        cov_surv_p975=("coverage_survivors", lambda s: s.quantile(.975)),
        cov_overall_mean=("coverage_overall", "mean"), set_size_mean=("mean_set_size", "mean"),
        singleton_mean=("share_singleton", "mean")).reset_index()
    lo_hi = [wilson(r.cov_deaths_mean * r.deaths_mean, r.deaths_mean) for r in agg.itertuples()]
    agg["cov_deaths_wilson_low"] = [x[0] for x in lo_hi]
    agg["cov_deaths_wilson_high"] = [x[1] for x in lo_hi]
    lo_hi = [wilson(r.cov_surv_mean * r.survivors_mean, r.survivors_mean) for r in agg.itertuples()]
    agg["cov_surv_wilson_low"] = [x[0] for x in lo_hi]
    agg["cov_surv_wilson_high"] = [x[1] for x in lo_hi]
    agg["UNSTABLE_lt50_deaths"] = agg["deaths_mean"] < 50
    agg.to_csv(TABLES_DIR / f"phase6_mimic_vs_eicu_coverage{sfx}.csv", index=False)

    # ---- hospital-level dispersion --------------------------------------------------------
    hosp = pd.concat(hosp_rows, ignore_index=True)
    hh = hosp.groupby("hospitalid").agg(n=("n", "first"), n_deaths=("n_deaths", "first"),
                                        cov_deaths=("cov_deaths", "mean"),
                                        cov_survivors=("cov_survivors", "mean")).reset_index()
    hh = hh[(hh.n >= MIN_HOSPITAL_N) & (hh.n_deaths >= MIN_HOSPITAL_DEATHS)]
    hh["expected_sd_binomial"] = np.sqrt(0.9 * 0.1 / hh["n_deaths"])
    hh["z_vs_nominal"] = (hh["cov_deaths"] - 0.90) / hh["expected_sd_binomial"]
    hh.to_csv(TABLES_DIR / f"phase6_hospital_coverage{sfx}.csv", index=False)

    pd.DataFrame(perf_rows).to_csv(RESULTS_DIR / f"phase6_model_performance{sfx}.csv", index=False)

    # ---- summary + pre-specified endpoints -------------------------------------------------
    def pick(cfg, attr, sg):
        r = agg[(agg.config == cfg) & (agg.attr == attr) & (agg.subgroup == sg)]
        return r.iloc[0] if len(r) else None

    p1, p2 = pick("ext_mimiccal_cc", "age_group", "18-49"), pick("ext_mimiccal_cc", "age_group", "75+")
    summary = {
        "n_seeds": n_seeds, "split_mode": split_mode, "alpha": alpha,
        "n_eicu_patients": int(len(eicu)), "eicu_mortality": float(ye.mean()),
        "n_hospitals": int(eicu["hospitalid"].nunique()),
        "P1_eicu_18_49_death_coverage": None if p1 is None else float(p1.cov_deaths_mean),
        "P2_eicu_75plus_survivor_coverage": None if p2 is None else float(p2.cov_surv_mean),
        "hospitals_in_table": int(len(hh)),
        "hospital_death_coverage_sd": float(hh.cov_deaths.std()) if len(hh) > 1 else None,
        "hospital_expected_sd_binomial_median": float(hh.expected_sd_binomial.median()) if len(hh) else None,
    }
    (RESULTS_DIR / f"phase6_summary{sfx}.json").write_text(json.dumps(summary, indent=2))

    print("\n=== Phase 6b summary ===")
    print(json.dumps(summary, indent=2))
    print(f"written to {TABLES_DIR} and {RESULTS_DIR} | {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--split", choices=["patient", "hospital"], default="patient")
    ap.add_argument("--alpha", type=float, default=0.10)
    ap.add_argument("--eicu-path", type=Path, default=EICU_FEATURES)
    ap.add_argument("--sample", type=int, default=None, help="subsample eICU rows (smoke test)")
    ap.add_argument("--drop", nargs="*", default=None, help="drop predictors whose name starts with these prefixes (harmonised-feature sensitivity analysis)")
    ap.add_argument("--tag", default="", help="suffix for output files")
    a = ap.parse_args()
    np.random.seed(42)
    run(a.seeds, a.split, a.alpha, a.eicu_path, a.sample, a.drop, a.tag)
