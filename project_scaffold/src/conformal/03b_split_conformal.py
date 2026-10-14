"""Phase 3 train, calibrate, evaluate and save standard split-conformal results."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import logit
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.linear_model import LogisticRegression

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.conformal.utils import fit_class_conditional, fit_marginal, prediction_sets

# Numeric-leading filename is retained per phase convention; load by path.
import importlib.util
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "03_train_baseline.py"
spec = importlib.util.spec_from_file_location("phase3_baseline", MODEL_PATH)
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
FEATURES_PATH = baseline.FEATURES_PATH
fit_baseline = baseline.fit_baseline
predictor_columns = baseline.predictor_columns
split_indices = baseline.split_indices

RESULTS_DIR = PROJECT_ROOT / "outputs" / "results"
ALPHA = float(os.environ.get("ALPHA", "0.10"))
N_SEEDS = int(os.environ.get("N_SEEDS", "100"))
ALPHA_TAG = f"a{int(round(ALPHA * 100)):03d}"
VARIANTS = tuple(v.strip() for v in os.environ.get(
    "VARIANTS", "flags,noflags,nolactate"
).split(",") if v.strip())


def conformal_metrics(y, sets, prefix):
    n = len(y)
    sizes = sets.sum(axis=1)
    out = {
        f"{prefix}_coverage_overall": sets[np.arange(n), y].mean(),
        f"{prefix}_coverage_y1": sets[y == 1, 1].mean(),
        f"{prefix}_coverage_y0": sets[y == 0, 0].mean(),
        f"{prefix}_mean_set_size": sizes.mean(),
        f"{prefix}_share_set_0": (sets[:, 0] & ~sets[:, 1]).mean(),
        f"{prefix}_share_set_1": (~sets[:, 0] & sets[:, 1]).mean(),
        f"{prefix}_share_set_both": (sets[:, 0] & sets[:, 1]).mean(),
        f"{prefix}_share_set_empty": (~sets.any(axis=1)).mean(),
    }
    return out


def evaluate_seed(df, seed, use_flags, drop_lactate=False):
    train_ix, cal_ix, test_ix = split_indices(df, seed)
    cols = predictor_columns(df, use_flags, drop_lactate=drop_lactate)
    X = df[cols].copy()
    if set(cols) & baseline.FORBIDDEN:
        raise AssertionError("Forbidden columns are in X")
    X["sex"] = X["sex"].map({"Male": 1, "Female": 0})
    if X["sex"].isna().any():
        raise ValueError("sex must contain only Male/Female for the configured encoding")
    y = df["mortality"].astype(int).to_numpy()
    model = fit_baseline(X.iloc[train_ix], y[train_ix], seed)
    p_cal = model.predict_proba(X.iloc[cal_ix])[:, 1]
    p_test = model.predict_proba(X.iloc[test_ix])[:, 1]
    y_cal, y_test = y[cal_ix], y[test_ix]
    q_marginal = fit_marginal(y_cal, p_cal, ALPHA)
    q_class = fit_class_conditional(y_cal, p_cal, ALPHA)
    set_marginal = prediction_sets(p_test, q_marginal)
    set_classcond = prediction_sets(p_test, q_class)
    p_safe = np.clip(p_test, 1e-8, 1 - 1e-8)
    # Logistic calibration model: y ~ intercept + logit(p_hat).
    calibration = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    calibration.fit(logit(p_safe).reshape(-1, 1), y_test)
    metrics = {
        "seed": seed,
        "best_iteration": int(model.best_iteration),
        "auroc": roc_auc_score(y_test, p_test),
        "auprc": average_precision_score(y_test, p_test),
        "brier_score": brier_score_loss(y_test, p_test),
        "calibration_slope": float(calibration.coef_[0, 0]),
        "calibration_intercept": float(calibration.intercept_[0]),
        "marginal_qhat": q_marginal,
        "classcond_qhat_0": q_class[0],
        "classcond_qhat_1": q_class[1],
    }
    metrics.update(conformal_metrics(y_test, set_marginal, "marginal"))
    metrics.update(conformal_metrics(y_test, set_classcond, "classcond"))
    predictions = pd.DataFrame({
        "seed": seed,
        "stay_id": df.iloc[test_ix]["stay_id"].to_numpy(),
        "y": y_test,
        "p_hat": p_test,
        "set_marginal_has0": set_marginal[:, 0],
        "set_marginal_has1": set_marginal[:, 1],
        "set_classcond_has0": set_classcond[:, 0],
        "set_classcond_has1": set_classcond[:, 1],
    })
    importance = None
    if seed == 0 or (use_flags and seed < 10):
        gain_by_name = model.get_booster().get_score(importance_type="gain")
        importance = pd.DataFrame({
            "seed": seed,
            "feature": cols,
            "gain": [float(gain_by_name.get(name, 0.0)) for name in cols],
        }).sort_values("gain", ascending=False, kind="stable")
    return metrics, predictions, importance


def summarize(rows):
    frame = pd.DataFrame(rows)
    result = {}
    for column in frame.columns:
        if column == "seed":
            continue
        values = frame[column].astype(float)
        result[column] = {
            "mean": float(values.mean()),
            "sd": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
            "p2_5": float(values.quantile(0.025)),
            "p97_5": float(values.quantile(0.975)),
        }
    return result


def write_measured_flag_sanity(df):
    """Summarize flag prevalence only; never include patient-level rows/IDs."""
    measured_cols = [c for c in df.columns if c.endswith("_measured")]
    if not measured_cols:
        raise ValueError("No *_measured columns found for the sanity check")
    report = pd.DataFrame({
        "feature": measured_cols,
        "mean": [float(df[c].mean()) for c in measured_cols],
    })
    path = RESULTS_DIR / f"phase3_measured_flag_sanity_{ALPHA_TAG}.csv"
    report.to_csv(path, index=False)
    return path


def run():
    if N_SEEDS < 1:
        raise ValueError("N_SEEDS must be positive")
    if not 0 < ALPHA < 1:
        raise ValueError("ALPHA must be between 0 and 1")
    allowed_variants = {"flags", "noflags", "nolactate"}
    if not VARIANTS or set(VARIANTS) - allowed_variants:
        raise ValueError(f"VARIANTS must be a comma-separated subset of {sorted(allowed_variants)}")
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing required input: {FEATURES_PATH}")
    df = pd.read_parquet(FEATURES_PATH)
    if len(df) != 51838:
        raise AssertionError(f"Expected 51,838 cohort rows, found {len(df):,}")
    if not df["subject_id"].is_unique:
        raise AssertionError("subject_id must be unique")
    print(f"Loaded {len(df):,} rows from {FEATURES_PATH}")
    print(f"N_SEEDS={N_SEEDS}, alpha={ALPHA}, alpha_tag={ALPHA_TAG}, split=50/25/25")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if "flags" in VARIANTS:
        sanity_path = write_measured_flag_sanity(df)
        print(f"Wrote measured-flag prevalence sanity report: {sanity_path}")

    variant_config = {
        "flags": (True, False),
        "noflags": (False, False),
        "nolactate": (False, True),
    }
    for suffix in VARIANTS:
        use_flags, drop_lactate = variant_config[suffix]
        cols = predictor_columns(df, use_flags, drop_lactate=drop_lactate)
        print(f"\nVariant _{suffix}: {len(cols)} predictors")
        print("Predictors: " + ", ".join(cols))
        per_seed, preds = [], []
        seed0_importance = None
        flags_seed_importance = []
        started = time.time()
        for seed in range(N_SEEDS):
            seed_start = time.time()
            metrics, prediction, importance = evaluate_seed(
                df, seed, use_flags, drop_lactate=drop_lactate
            )
            per_seed.append(metrics)
            preds.append(prediction)
            if seed == 0:
                seed0_importance = importance
            if use_flags and seed < 10:
                flags_seed_importance.append(importance)
            print(f"Seed {seed + 1}/{N_SEEDS} (seed={seed}) complete in {time.time()-seed_start:.1f}s; best_iteration={metrics['best_iteration']}; AUROC={metrics['auroc']:.4f}, marginal coverage={metrics['marginal_coverage_overall']:.4f}, class-conditional coverage={metrics['classcond_coverage_overall']:.4f}", flush=True)
        per_seed_df = pd.DataFrame(per_seed)
        summary = summarize(per_seed)
        max_rounds = baseline.MODEL_CONFIG["n_estimators"]
        capped = [row["seed"] for row in per_seed if row["best_iteration"] + 1 >= max_rounds]
        if capped:
            print(f"WARNING: seed(s) {capped} reached n_estimators={max_rounds} for _{suffix}.", flush=True)
        out_json = RESULTS_DIR / f"phase3_baseline_metrics_{suffix}_{ALPHA_TAG}.json"
        out_csv = RESULTS_DIR / f"phase3_per_seed_summary_{suffix}_{ALPHA_TAG}.csv"
        out_parquet = RESULTS_DIR / f"phase3_test_predictions_{suffix}_{ALPHA_TAG}.parquet"
        out_importance = RESULTS_DIR / f"phase3_feature_importance_{suffix}_{ALPHA_TAG}.csv"
        out_flags_10 = RESULTS_DIR / f"phase3_feature_importance_flags_seeds0-9_{ALPHA_TAG}.csv"
        out_flag_check = RESULTS_DIR / f"phase3_measured_flag_gain_sanity_{ALPHA_TAG}.csv"
        with out_json.open("w", encoding="utf-8") as f:
            json.dump({
                "metadata": {
                    "task": "Phase 3 Baseline XGBoost + Split Conformal Prediction",
                    "suffix": suffix,
                    "n_seeds": N_SEEDS,
                    "alpha": ALPHA,
                    "alpha_tag": ALPHA_TAG,
                    "n_cohort": len(df),
                    "split_ratios": "50% Train / 25% Calibration / 25% Test",
                    "n_features": len(cols),
                    "features_used": cols,
                    "elapsed_seconds": time.time() - started,
                },
                "summary": summary,
                "per_seed_metrics": per_seed,
            }, f, indent=2)
        per_seed_df.to_csv(out_csv, index=False)
        pd.concat(preds, ignore_index=True).to_parquet(out_parquet, index=False)
        if seed0_importance is None:
            raise AssertionError("seed 0 feature importance was not captured")
        seed0_importance.drop(columns="seed", errors="ignore").to_csv(out_importance, index=False)
        if use_flags:
            if len(flags_seed_importance) != min(10, N_SEEDS):
                raise AssertionError("Missing one or more flags feature-importance seeds")
            flags_importance_df = pd.concat(flags_seed_importance, ignore_index=True)
            flags_importance_df.to_csv(out_flags_10, index=False)
            measured = flags_importance_df[
                flags_importance_df["feature"].str.endswith("_measured")
            ]
            flag_check_rows = []
            for seed, group in measured.groupby("seed", sort=True):
                positive = group[group["gain"] > 0]
                flag_check_rows.append({
                    "seed": int(seed),
                    "measured_flags_with_nonzero_gain": int(len(positive)),
                    "total_measured_flag_gain": float(group["gain"].sum()),
                    "nonzero_measured_flags": ",".join(positive["feature"].tolist()),
                })
            flag_check_df = pd.DataFrame(flag_check_rows)
            flag_check_df.to_csv(out_flag_check, index=False)
            nonzero_seeds = flag_check_df.loc[
                flag_check_df["measured_flags_with_nonzero_gain"] > 0, "seed"
            ].tolist()
            if nonzero_seeds:
                print(f"WARNING: measured flags have nonzero gain in seed(s) {nonzero_seeds}.", flush=True)
            else:
                print(f"Measured-flag sanity check: zero gain across seeds {flag_check_df['seed'].tolist()}.", flush=True)
        print(f"Variant _{suffix} finished in {time.time()-started:.1f}s")
        print(f"Wrote: {out_json}\nWrote: {out_csv}\nWrote seed 0 feature importance: {out_importance}")
        if use_flags:
            print(f"Wrote flags feature importance for seeds 0-9: {out_flags_10}")
            print(f"Wrote measured-flag sanity report: {out_flag_check}")
        print(f"Wrote patient-level predictions (gitignored): {out_parquet}")


if __name__ == "__main__":
    run()

