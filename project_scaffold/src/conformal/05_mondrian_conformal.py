"""Phase 5: Mondrian (Group-Conditional) Conformal Prediction.

Fits group-conditional and group-by-class-conditional conformal prediction quantiles
on the calibration split for single protected attributes (race, sex, age, insurance)
and intersectional pairs (race x sex, race x insurance, age x sex).
Evaluates empirical coverage, set size, and Wilson score intervals exclusively on
the held-out test split across 100 seeds.

Outputs:
  outputs/results/phase5_mondrian_intervals.parquet
  outputs/tables/phase5_subgroup_coverage_corrected.csv
  outputs/tables/phase5_subgroup_coverage_corrected_per_seed.csv
  outputs/figures/phase5_mondrian_coverage_by_group.png
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.conformal.utils import (
    fit_mondrian_class_conditional,
    fit_mondrian_marginal,
    prediction_sets_mondrian,
)

# Load baseline split and training utilities
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "03_train_baseline.py"
spec = importlib.util.spec_from_file_location("phase3_baseline", MODEL_PATH)
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
FEATURES_PATH = baseline.FEATURES_PATH
fit_baseline = baseline.fit_baseline
predictor_columns = baseline.predictor_columns
split_indices = baseline.split_indices

RESULTS_DIR = PROJECT_ROOT / "outputs" / "results"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"

AUDIT_ATTRIBUTES = ("race_group", "sex", "age_group", "insurance_group")
INTERSECTION_PAIRS = (
    ("race_group", "sex", "race_sex"),
    ("race_group", "insurance_group", "race_insurance"),
    ("age_group", "sex", "age_sex"),
)


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Return a two-sided 95% Wilson score interval, or NaNs for no cases."""
    if total <= 0:
        return float("nan"), float("nan")
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return float(center - half), float(center + half)


def _rate_and_ci(hit: np.ndarray) -> tuple[float, float, float]:
    n = int(hit.size)
    successes = int(hit.sum())
    low, high = wilson(successes, n)
    return (successes / n if n else float("nan"), low, high)


def run_phase5(
    n_seeds: int = 100,
    alpha: float = 0.10,
    variant: str = "noflags",
    sample_n: int | None = None,
) -> None:
    started = time.time()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    alpha_tag = f"a{int(round(alpha * 100)):03d}"
    print(f"=== Starting Phase 5: Mondrian Conformal Prediction ===")
    print(f"Variant: {variant}, Alpha: {alpha} ({alpha_tag}), Seeds: {n_seeds}")

    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing required input features: {FEATURES_PATH}")

    df = pd.read_parquet(FEATURES_PATH)
    if sample_n is not None and sample_n < len(df):
        print(f"Sampling {sample_n:,} rows for smoke testing...")
        df = df.sample(n=sample_n, random_state=42).reset_index(drop=True)

    # Precompute intersection columns
    for a1, a2, pair_name in INTERSECTION_PAIRS:
        df[pair_name] = df[a1].astype(str) + " & " + df[a2].astype(str)

    all_mondrian_attrs = list(AUDIT_ATTRIBUTES) + [pair[2] for pair in INTERSECTION_PAIRS]

    use_flags = (variant == "flags")
    drop_lactate = (variant == "nolactate")
    cols = predictor_columns(df, use_measured_flags=use_flags, drop_lactate=drop_lactate)
    y = df["mortality"].astype(int).to_numpy()

    X = df[cols].copy()
    X["sex"] = X["sex"].map({"Male": 1, "Female": 0})
    if X["sex"].isna().any():
        raise ValueError("sex must contain only Male/Female for encoding")

    all_test_predictions: list[pd.DataFrame] = []
    per_seed_records: list[dict] = []

    for seed in range(n_seeds):
        t0 = time.time()
        train_ix, cal_ix, test_ix = split_indices(df, seed)

        model = fit_baseline(X.iloc[train_ix], y[train_ix], seed)
        p_cal = model.predict_proba(X.iloc[cal_ix])[:, 1]
        p_test = model.predict_proba(X.iloc[test_ix])[:, 1]

        y_cal, y_test = y[cal_ix], y[test_ix]
        test_stay_ids = df.iloc[test_ix]["stay_id"].to_numpy()

        pred_dict = {
            "seed": seed,
            "stay_id": test_stay_ids,
            "y": y_test,
            "p_hat": p_test,
        }

        # Fit and evaluate Mondrian for each attribute
        for attr in all_mondrian_attrs:
            cal_groups = df.iloc[cal_ix][attr].to_numpy()
            test_groups = df.iloc[test_ix][attr].to_numpy()

            # 1. Mondrian Class-Conditional (Primary Repair Mechanism)
            q_cc = fit_mondrian_class_conditional(y_cal, p_cal, cal_groups, alpha=alpha)
            sets_cc = prediction_sets_mondrian(p_test, test_groups, q_cc)
            pred_dict[f"mondrian_cc_{attr}_has0"] = sets_cc[:, 0]
            pred_dict[f"mondrian_cc_{attr}_has1"] = sets_cc[:, 1]

            # 2. Mondrian Marginal
            q_marg = fit_mondrian_marginal(y_cal, p_cal, cal_groups, alpha=alpha)
            sets_marg = prediction_sets_mondrian(p_test, test_groups, q_marg)
            pred_dict[f"mondrian_marg_{attr}_has0"] = sets_marg[:, 0]
            pred_dict[f"mondrian_marg_{attr}_has1"] = sets_marg[:, 1]

            # Audit coverage on test set for each subgroup in attr
            for method_name, sets in (
                (f"mondrian_class_conditional", sets_cc),
                (f"mondrian_marginal", sets_marg),
            ):
                has0 = sets[:, 0]
                has1 = sets[:, 1]
                true_label_covered = np.where(y_test == 1, has1, has0)
                set_size = has0.astype(np.int8) + has1.astype(np.int8)

                for subgroup in np.unique(test_groups):
                    mask = (test_groups == subgroup)
                    ix_sub = np.where(mask)[0]
                    sub_y = y_test[mask]
                    sub_hit = true_label_covered[mask]

                    cov_all, ci_low, ci_high = _rate_and_ci(sub_hit)
                    cov_surv, s_low, s_high = _rate_and_ci(sub_hit[sub_y == 0])
                    cov_death, d_low, d_high = _rate_and_ci(sub_hit[sub_y == 1])

                    sub_sizes = set_size[mask]
                    row = {
                        "variant": variant,
                        "alpha": alpha,
                        "seed": seed,
                        "calibration_type": method_name,
                        "stratification_attribute": attr,
                        "subgroup": str(subgroup),
                        "n_test": int(mask.sum()),
                        "n_survivors": int((sub_y == 0).sum()),
                        "n_deaths": int((sub_y == 1).sum()),
                        "coverage_overall": cov_all,
                        "coverage_overall_wilson_low": ci_low,
                        "coverage_overall_wilson_high": ci_high,
                        "coverage_survivors": cov_surv,
                        "coverage_survivors_wilson_low": s_low,
                        "coverage_survivors_wilson_high": s_high,
                        "coverage_deaths": cov_death,
                        "coverage_deaths_wilson_low": d_low,
                        "coverage_deaths_wilson_high": d_high,
                        "mean_set_size": float(sub_sizes.mean()),
                        "share_empty": float((sub_sizes == 0).mean()),
                        "share_singleton_0": float(((has0[mask]) & (~has1[mask])).mean()),
                        "share_singleton_1": float(((~has0[mask]) & (has1[mask])).mean()),
                        "share_both": float(((has0[mask]) & (has1[mask])).mean()),
                    }
                    per_seed_records.append(row)

        all_test_predictions.append(pd.DataFrame(pred_dict))
        if (seed + 1) % 10 == 0 or seed == 0 or (seed + 1) == n_seeds:
            elapsed = time.time() - t0
            print(f"Seed {seed + 1}/{n_seeds} completed in {elapsed:.1f}s", flush=True)

    print("Concatenating test predictions and compiling audit...")
    test_pred_df = pd.concat(all_test_predictions, ignore_index=True)
    per_seed_df = pd.DataFrame(per_seed_records)

    # Save test predictions parquet
    out_parquet = RESULTS_DIR / f"phase5_mondrian_intervals_{variant}_{alpha_tag}.parquet"
    test_pred_df.to_parquet(out_parquet, index=False)
    print(f"Saved Mondrian test intervals: {out_parquet} ({len(test_pred_df):,} rows)")

    # Save per-seed audit CSV
    out_per_seed = TABLES_DIR / f"phase5_subgroup_coverage_corrected_per_seed_{variant}_{alpha_tag}.csv"
    per_seed_df.to_csv(out_per_seed, index=False)

    # Summarize across seeds
    summary_df = _summarize(per_seed_df)
    out_summary = TABLES_DIR / f"phase5_subgroup_coverage_corrected_{variant}_{alpha_tag}.csv"
    summary_df.to_csv(out_summary, index=False)
    # Also save canonical default file if noflags and a010
    if variant == "noflags" and alpha == 0.10:
        canonical_summary = TABLES_DIR / "phase5_subgroup_coverage_corrected.csv"
        canonical_intervals = RESULTS_DIR / "phase5_mondrian_intervals.parquet"
        summary_df.to_csv(canonical_summary, index=False)
        test_pred_df.to_parquet(canonical_intervals, index=False)

    print(f"Saved aggregated audit summary: {out_summary}")

    # Generate comparison plot
    fig_path = FIGURES_DIR / f"phase5_mondrian_coverage_by_group_{variant}_{alpha_tag}.png"
    _plot_mondrian_comparison(summary_df, fig_path, alpha=alpha)
    print(f"Saved visualization: {fig_path}")

    total_time = time.time() - started
    print(f"\n=== Phase 5 Complete in {total_time:.1f}s ===")
    print(f"Total test rows processed: {len(test_pred_df):,}")
    print(f"Summary rows: {len(summary_df):,}")


def _summarize(per_seed: pd.DataFrame) -> pd.DataFrame:
    keys = ["variant", "alpha", "calibration_type", "stratification_attribute", "subgroup"]
    metric_cols = [
        "coverage_overall", "coverage_deaths", "coverage_survivors",
        "mean_set_size", "share_empty", "share_singleton_0",
        "share_singleton_1", "share_both",
    ]
    rows = []
    for key, group in per_seed.groupby(keys, sort=True, dropna=False):
        row = dict(zip(keys, key))
        row.update({
            "n_seeds": int(group["seed"].nunique()),
            "n_test_mean": float(group["n_test"].mean()),
            "n_test_min": int(group["n_test"].min()),
            "n_test_max": int(group["n_test"].max()),
            "n_deaths_mean": float(group["n_deaths"].mean()),
            "n_survivors_mean": float(group["n_survivors"].mean()),
        })
        for metric in metric_cols:
            vals = group[metric].dropna()
            row[f"{metric}_mean"] = float(vals.mean())
            row[f"{metric}_split_sd"] = float(vals.std(ddof=1)) if len(vals) > 1 else 0.0
            row[f"{metric}_split_p2_5"] = float(vals.quantile(0.025))
            row[f"{metric}_split_p97_5"] = float(vals.quantile(0.975))
        for metric in ("coverage_overall", "coverage_deaths", "coverage_survivors"):
            row[f"{metric}_mean_split_wilson_low"] = float(group[f"{metric}_wilson_low"].mean())
            row[f"{metric}_mean_split_wilson_high"] = float(group[f"{metric}_wilson_high"].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def _plot_mondrian_comparison(summary: pd.DataFrame, path: Path, alpha: float = 0.10) -> None:
    """Plot empirical death coverage across single protected groups under Mondrian correction."""
    target_cov = 1.0 - alpha
    single_attrs = AUDIT_ATTRIBUTES
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    axes = axes.ravel()

    # Compare Mondrian Class-Conditional vs Mondrian Marginal
    plot_df = summary[
        (summary["stratification_attribute"].isin(single_attrs))
        & (summary["stratification_attribute"] == summary["stratification_attribute"])
    ]

    for ax, attr in zip(axes, single_attrs):
        part = plot_df[plot_df["stratification_attribute"] == attr]
        groups = sorted(part["subgroup"].unique())
        x = np.arange(len(groups))

        methods = [
            ("mondrian_marginal", "Mondrian Marginal", "#B44D4D", -0.12),
            ("mondrian_class_conditional", "Mondrian Class-Cond", "#2A9D8F", 0.12),
        ]
        for m_key, m_label, color, offset in methods:
            m_part = part[part["calibration_type"] == m_key].set_index("subgroup").reindex(groups)
            means = m_part["coverage_deaths_mean"].to_numpy()
            lows = m_part["coverage_deaths_split_p2_5"].to_numpy()
            highs = m_part["coverage_deaths_split_p97_5"].to_numpy()
            ax.errorbar(
                x + offset, means,
                yerr=np.vstack((means - lows, highs - means)),
                fmt="o", capsize=3, color=color, label=m_label,
            )

        ax.axhline(target_cov, linestyle="--", color="#333333", linewidth=1.2, label=f"Nominal {int(target_cov*100)}%")
        ax.set_title(attr.replace("_", " ").title(), fontsize=12, fontweight="bold")
        ax.set_xticks(x, groups, rotation=20, ha="right")
        ax.set_ylim(0, 1.02)
        ax.set_ylabel("Death-label coverage (y=1)")
        ax.grid(axis="y", alpha=0.25)

    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="lower center", bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=True)
    fig.suptitle(
        f"Phase 5: Subgroup Death Coverage with Mondrian Conformal Prediction (alpha={alpha:.2f})\n"
        f"Bars show 2.5th–97.5th percentiles across 100 splits on held-out test data",
        fontsize=14,
        fontweight="bold",
    )
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Phase 5 Mondrian Conformal Prediction")
    parser.add_argument("--seeds", type=int, default=int(os.environ.get("N_SEEDS", "100")), help="Number of split seeds (default 100)")
    parser.add_argument("--alpha", type=float, default=float(os.environ.get("ALPHA", "0.10")), help="Nominal error rate (default 0.10)")
    parser.add_argument("--variant", type=str, default=os.environ.get("VARIANT", "noflags"), choices=["noflags", "flags", "nolactate"])
    parser.add_argument("--sample", type=int, default=None, help="Sample size for fast smoke testing")
    args = parser.parse_args()

    run_phase5(n_seeds=args.seeds, alpha=args.alpha, variant=args.variant, sample_n=args.sample)


if __name__ == "__main__":
    main()
