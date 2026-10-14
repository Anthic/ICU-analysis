"""Phase 4 subgroup coverage audit using the saved Phase 3 test predictions.

Patient identifiers are used only for an in-memory join to subgroup labels.
Only subgroup-level aggregates are written. Per-seed Wilson intervals describe
each test split; summaries across the overlapping random splits are descriptive
split-to-split variability, not confidence intervals for the population mean.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "outputs" / "results"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
FEATURES = ROOT / "data" / "processed" / "features.parquet"
GROUPS = ("race_group", "sex", "age_group", "age_quartile", "insurance_group")
RUNS = (("noflags", 0.10), ("noflags", 0.05))


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


def _records_for_run(variant: str, alpha: float, features: pd.DataFrame) -> list[dict]:
    tag = f"a{int(round(alpha * 100)):03d}"
    path = RESULTS / f"phase3_test_predictions_{variant}_{tag}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing Phase 3 predictions: {path}")

    # Read the identifier only to attach subgroup labels; never persist it.
    pred = pd.read_parquet(path, columns=[
        "stay_id", "seed", "y", "set_marginal_has0", "set_marginal_has1",
        "set_classcond_has0", "set_classcond_has1",
    ])
    pred["y"] = pred["y"].astype(int)
    joined = pred.merge(features, on="stay_id", how="left", validate="many_to_one")
    if joined[list(GROUPS)].isna().any().any():
        raise ValueError(f"Missing subgroup labels after joining {path.name}")

    records: list[dict] = []
    for seed, split in joined.groupby("seed", sort=True):
        y = split["y"].to_numpy()
        for method, c0, c1 in (
            ("marginal", "set_marginal_has0", "set_marginal_has1"),
            ("class_conditional_by_outcome", "set_classcond_has0", "set_classcond_has1"),
        ):
            has0 = split[c0].astype(bool).to_numpy()
            has1 = split[c1].astype(bool).to_numpy()
            true_label_covered = np.where(y == 1, has1, has0)
            set_size = has0.astype(np.int8) + has1.astype(np.int8)

            for attribute in GROUPS:
                # groupby sees only aggregate labels; no patient rows are emitted.
                for subgroup, positions in split.groupby(attribute, sort=True).indices.items():
                    ix = np.asarray(positions, dtype=int)
                    group_y = y[ix]
                    group_hit = true_label_covered[ix]
                    row = {
                        "variant": variant,
                        "alpha": alpha,
                        "seed": int(seed),
                        "method": method,
                        "attribute": attribute,
                        "subgroup": str(subgroup),
                        "n_test": int(ix.size),
                        "n_survivors": int((group_y == 0).sum()),
                        "n_deaths": int((group_y == 1).sum()),
                    }
                    row["coverage_overall"], row["coverage_overall_wilson_low"], row["coverage_overall_wilson_high"] = _rate_and_ci(group_hit)
                    for label, label_name in ((0, "survivors"), (1, "deaths")):
                        label_hit = group_hit[group_y == label]
                        rate, low, high = _rate_and_ci(label_hit)
                        row[f"coverage_{label_name}"] = rate
                        row[f"coverage_{label_name}_wilson_low"] = low
                        row[f"coverage_{label_name}_wilson_high"] = high
                    sizes = set_size[ix]
                    row["mean_set_size"] = float(sizes.mean())
                    row["share_empty"] = float((sizes == 0).mean())
                    row["share_singleton_0"] = float(((has0[ix]) & (~has1[ix])).mean())
                    row["share_singleton_1"] = float(((~has0[ix]) & (has1[ix])).mean())
                    row["share_both"] = float(((has0[ix]) & (has1[ix])).mean())
                    records.append(row)
    return records


def _summarize(per_seed: pd.DataFrame) -> pd.DataFrame:
    keys = ["variant", "alpha", "method", "attribute", "subgroup"]
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
        # These are averages of per-split Wilson bounds, not one pooled CI.
        for metric in (
            "coverage_overall", "coverage_deaths", "coverage_survivors",
        ):
            row[f"{metric}_mean_split_wilson_low"] = float(group[f"{metric}_wilson_low"].mean())
            row[f"{metric}_mean_split_wilson_high"] = float(group[f"{metric}_wilson_high"].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def _plot(summary: pd.DataFrame, path: Path) -> None:
    plot_data = summary[
        (summary["variant"] == "noflags")
        & (summary["alpha"] == 0.10)
        & (summary["method"].isin(["marginal", "class_conditional_by_outcome"]))
    ]
    fig, axes = plt.subplots(3, 2, figsize=(14, 12), constrained_layout=True)
    axes = axes.ravel()
    colors = {"marginal": "#B44D4D", "class_conditional_by_outcome": "#286C8E"}
    labels = {"marginal": "Standard marginal", "class_conditional_by_outcome": "Class-conditional by outcome"}
    for ax, attribute in zip(axes, GROUPS):
        part = plot_data[plot_data["attribute"] == attribute]
        groups = sorted(part["subgroup"].unique())
        x = np.arange(len(groups))
        offsets = {"marginal": -0.10, "class_conditional_by_outcome": 0.10}
        for method in offsets:
            vals = part[part["method"] == method].set_index("subgroup").reindex(groups)
            mean = vals["coverage_deaths_mean"].to_numpy()
            low = vals["coverage_deaths_split_p2_5"].to_numpy()
            high = vals["coverage_deaths_split_p97_5"].to_numpy()
            ax.errorbar(
                x + offsets[method], mean,
                yerr=np.vstack((mean - low, high - mean)),
                fmt="o", capsize=3, color=colors[method], label=labels[method],
            )
        ax.axhline(0.90, linestyle="--", color="#555555", linewidth=1, label="Nominal 90% (class-conditional)")
        ax.set_title(attribute.replace("_", " ").title())
        ax.set_xticks(x, groups, rotation=20, ha="right")
        ax.set_ylim(0, 1.02)
        ax.set_ylabel("Death-label coverage")
        ax.grid(axis="y", alpha=0.2)
    for ax in axes[len(GROUPS):]:
        ax.set_visible(False)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="outside lower center", ncol=3, frameon=False)
    fig.suptitle("Phase 4: Death coverage by subgroup (noflags, alpha=0.10)\nBars show 2.5th–97.5th percentiles across random splits, not confidence intervals")
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    for directory in (TABLES, FIGURES):
        directory.mkdir(parents=True, exist_ok=True)
    if not FEATURES.exists():
        raise FileNotFoundError(f"Missing subgroup metadata source: {FEATURES}")
    features = pd.read_parquet(FEATURES, columns=["stay_id", "anchor_age", "race_group", "sex", "age_group", "insurance_group"])
    # Keep the project's predefined clinical age bands and also meet the
    # workflow's age-quartile audit request. Cut points use the full cohort's
    # age distribution only to define descriptive groups, not model fitting.
    features["age_quartile"] = pd.qcut(
        features["anchor_age"], q=4, labels=["Q1", "Q2", "Q3", "Q4"]
    )
    features = features.drop(columns="anchor_age")
    if features["stay_id"].duplicated().any():
        raise ValueError("Subgroup metadata must have one row per stay_id")

    records = []
    for variant, alpha in RUNS:
        print(f"Auditing {variant}, alpha={alpha:.2f}", flush=True)
        records.extend(_records_for_run(variant, alpha, features))
    per_seed = pd.DataFrame.from_records(records)
    summary = _summarize(per_seed)
    per_seed_path = TABLES / "phase4_subgroup_coverage_per_seed.csv"
    summary_path = TABLES / "phase4_subgroup_coverage.csv"
    figure_path = FIGURES / "phase4_coverage_by_group.png"
    per_seed.to_csv(per_seed_path, index=False)
    summary.to_csv(summary_path, index=False)
    _plot(summary, figure_path)
    print(f"Saved {len(summary):,} aggregated subgroup rows and {len(per_seed):,} per-seed aggregate rows.")
    print(f"Aggregated table: {summary_path}")
    print(f"Per-seed table with Wilson intervals: {per_seed_path}")
    print(f"Figure: {figure_path}")
    print("Identifier check: only subgroup-level aggregate tables were written.")


if __name__ == "__main__":
    main()
