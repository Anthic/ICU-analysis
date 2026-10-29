"""Rigorous Phase 4 Re-aggregation and Patient-Level Bootstrap Audit.

Computes:
  - Exact split-level statistics (Mean, SD, across-seed 2.5th-97.5th percentiles)
  - Patient-level bootstrap 95% Confidence Intervals (B=1000, random_state=42)
  - Subgroup metrics: Class-conditional death coverage, survivor coverage, overall coverage,
    mean set size, share of {0,1}, AUROC, CITL, observed mortality, mean predicted risk.
  - Distinguishes 'Other/Unknown (race)' and 'Other/Unknown (insurance)'
  - Intersectional pairs: ONLY race_group x sex and age_group x insurance_group
  - UNSTABLE flag for any group with mean deaths < 50 per seed.

Output:
  outputs/tables/phase4_rigorous_audit_noflags_a010.csv
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
PREDS_PATH = ROOT / "outputs" / "results" / "phase3_test_predictions_noflags_a010.parquet"
FEATURES_PATH = ROOT / "data" / "processed" / "features.parquet"
OUT_CSV = ROOT / "outputs" / "tables" / "phase4_rigorous_audit_noflags_a010.csv"

B_BOOTSTRAP = 1000
BOOT_SEED = 42


def run_audit():
    print(f"Loading predictions: {PREDS_PATH}")
    preds = pd.read_parquet(PREDS_PATH)
    features = pd.read_parquet(
        FEATURES_PATH,
        columns=["stay_id", "race_group", "sex", "age_group", "insurance_group"]
    )
    df = preds.merge(features, on="stay_id", how="left", validate="many_to_one")

    # Disambiguate duplicate labels
    df["race_group"] = df["race_group"].replace({"Other/Unknown": "Other/Unknown (race)"})
    df["insurance_group"] = df["insurance_group"].replace({"Other/Unknown": "Other/Unknown (insurance)"})

    # Create approved intersectional pairs ONLY
    df["race_sex"] = df["race_group"].astype(str) + " & " + df["sex"].astype(str)
    df["age_insurance"] = df["age_group"].astype(str) + " & " + df["insurance_group"].astype(str)

    attributes = [
        ("race_group", "Single"),
        ("sex", "Single"),
        ("age_group", "Single"),
        ("insurance_group", "Single"),
        ("race_sex", "Pair (race x sex)"),
        ("age_insurance", "Pair (age x insurance)"),
    ]

    # Precompute coverage flags
    y = df["y"].to_numpy().astype(int)
    has0_marg = df["set_marginal_has0"].to_numpy().astype(bool)
    has1_marg = df["set_marginal_has1"].to_numpy().astype(bool)
    has0_cc = df["set_classcond_has0"].to_numpy().astype(bool)
    has1_cc = df["set_classcond_has1"].to_numpy().astype(bool)

    df["hit_marg"] = np.where(y == 1, has1_marg, has0_marg)
    df["hit_cc"] = np.where(y == 1, has1_cc, has0_cc)
    df["size_cc"] = has0_cc.astype(np.int8) + has1_cc.astype(np.int8)
    df["both_cc"] = (has0_cc & has1_cc).astype(np.int8)

    rng = np.random.default_rng(BOOT_SEED)
    results = []

    # First add the "All" row
    all_groups = [("All", "All", df)]
    for attr, attr_type in attributes:
        for grp_val, grp_df in df.groupby(attr, sort=True):
            all_groups.append((attr, grp_val, grp_df))

    print(f"Total subgroups/cells to process: {len(all_groups)}")

    for attr, subgroup, grp in all_groups:
        n_seeds = grp["seed"].nunique()
        # Per-seed counts and rates
        seed_stats = []
        for s, s_df in grp.groupby("seed"):
            s_y = s_df["y"].to_numpy()
            s_p = s_df["p_hat"].to_numpy()
            s_deaths = (s_y == 1).sum()
            s_surv = (s_y == 0).sum()
            s_n = len(s_y)

            s_marg_death_cov = s_df.loc[s_y == 1, "hit_marg"].mean() if s_deaths > 0 else np.nan
            s_cc_death_cov = s_df.loc[s_y == 1, "hit_cc"].mean() if s_deaths > 0 else np.nan
            s_cc_surv_cov = s_df.loc[s_y == 0, "hit_cc"].mean() if s_surv > 0 else np.nan
            s_overall_cov = s_df["hit_cc"].mean()
            s_size = s_df["size_cc"].mean()
            s_both = s_df["both_cc"].mean()

            # AUROC per seed
            if s_deaths > 0 and s_surv > 0:
                s_auc = roc_auc_score(s_y, s_p)
            else:
                s_auc = np.nan

            s_citl = s_p.mean() - s_y.mean()

            seed_stats.append({
                "n": s_n,
                "n_deaths": s_deaths,
                "n_surv": s_surv,
                "obs_mort": s_y.mean(),
                "mean_p": s_p.mean(),
                "citl": s_citl,
                "auroc": s_auc,
                "marg_death_cov": s_marg_death_cov,
                "cc_death_cov": s_cc_death_cov,
                "cc_surv_cov": s_cc_surv_cov,
                "overall_cov": s_overall_cov,
                "mean_size": s_size,
                "share_both": s_both,
            })

        sdf = pd.DataFrame(seed_stats)
        mean_deaths = float(sdf["n_deaths"].mean())
        unstable = "YES" if mean_deaths < 50.0 else "NO"

        # Patient-level Bootstrap (B=1000) using unique patient stays in this group
        # Each patient stay_id in test has average observed performance
        pt_summary = grp.groupby("stay_id").agg({
            "y": "first",
            "p_hat": "mean",
            "hit_marg": "mean",
            "hit_cc": "mean",
            "size_cc": "mean",
            "both_cc": "mean",
        })
        n_pts = len(pt_summary)
        pt_y = pt_summary["y"].to_numpy().astype(int)
        pt_p = pt_summary["p_hat"].to_numpy()
        pt_hit_marg = pt_summary["hit_marg"].to_numpy()
        pt_hit_cc = pt_summary["hit_cc"].to_numpy()
        pt_size = pt_summary["size_cc"].to_numpy()
        pt_both = pt_summary["both_cc"].to_numpy()

        boot_marg_death, boot_cc_death, boot_cc_surv = [], [], []
        boot_cov, boot_size, boot_both = [], [], []
        boot_citl, boot_auc = [], []

        for b in range(B_BOOTSTRAP):
            b_ix = rng.integers(0, n_pts, size=n_pts)
            b_y = pt_y[b_ix]
            b_p = pt_p[b_ix]
            b_deaths = (b_y == 1)
            b_surv = (b_y == 0)

            if b_deaths.any():
                boot_marg_death.append(float(pt_hit_marg[b_ix][b_deaths].mean()))
                boot_cc_death.append(float(pt_hit_cc[b_ix][b_deaths].mean()))
            if b_surv.any():
                boot_cc_surv.append(float(pt_hit_cc[b_ix][b_surv].mean()))

            boot_cov.append(float(pt_hit_cc[b_ix].mean()))
            boot_size.append(float(pt_size[b_ix].mean()))
            boot_both.append(float(pt_both[b_ix].mean()))
            boot_citl.append(float(b_p.mean() - b_y.mean()))

            if b_deaths.any() and b_surv.any():
                try:
                    boot_auc.append(float(roc_auc_score(b_y, b_p)))
                except Exception:
                    pass

        def get_boot_ci(arr):
            if len(arr) == 0:
                return np.nan, np.nan
            return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))

        b_marg_d_low, b_marg_d_high = get_boot_ci(boot_marg_death)
        b_cc_d_low, b_cc_d_high = get_boot_ci(boot_cc_death)
        b_cc_s_low, b_cc_s_high = get_boot_ci(boot_cc_surv)
        b_cov_low, b_cov_high = get_boot_ci(boot_cov)
        b_size_low, b_size_high = get_boot_ci(boot_size)
        b_both_low, b_both_high = get_boot_ci(boot_both)
        b_citl_low, b_citl_high = get_boot_ci(boot_citl)
        b_auc_low, b_auc_high = get_boot_ci(boot_auc)

        row = {
            "attribute": attr,
            "subgroup": subgroup,
            "n_test_mean": float(sdf["n"].mean()),
            "deaths_mean": mean_deaths,
            "survivors_mean": float(sdf["n_surv"].mean()),
            "UNSTABLE": unstable,
            "observed_mortality": float(sdf["obs_mort"].mean()),
            "mean_p_hat": float(sdf["mean_p"].mean()),
            
            # CITL
            "citl_mean": float(sdf["citl"].mean()),
            "citl_sd_over_seeds": float(sdf["citl"].std(ddof=1)),
            "citl_split_p2_5": float(sdf["citl"].quantile(0.025)),
            "citl_split_p97_5": float(sdf["citl"].quantile(0.975)),
            "citl_boot_ci_low": b_citl_low,
            "citl_boot_ci_high": b_citl_high,

            # AUROC
            "auroc_mean": float(sdf["auroc"].mean()),
            "auroc_sd_over_seeds": float(sdf["auroc"].std(ddof=1)),
            "auroc_split_p2_5": float(sdf["auroc"].quantile(0.025)),
            "auroc_split_p97_5": float(sdf["auroc"].quantile(0.975)),
            "auroc_boot_ci_low": b_auc_low,
            "auroc_boot_ci_high": b_auc_high,

            # Marginal death coverage
            "marginal_death_cov_mean": float(sdf["marg_death_cov"].mean()),
            "marginal_death_cov_sd_over_seeds": float(sdf["marg_death_cov"].std(ddof=1)),
            "marginal_death_cov_split_p2_5": float(sdf["marg_death_cov"].quantile(0.025)),
            "marginal_death_cov_split_p97_5": float(sdf["marg_death_cov"].quantile(0.975)),
            "marginal_death_cov_boot_ci_low": b_marg_d_low,
            "marginal_death_cov_boot_ci_high": b_marg_d_high,

            # Class-conditional death coverage
            "cc_death_cov_mean": float(sdf["cc_death_cov"].mean()),
            "cc_death_cov_sd_over_seeds": float(sdf["cc_death_cov"].std(ddof=1)),
            "cc_death_cov_split_p2_5": float(sdf["cc_death_cov"].quantile(0.025)),
            "cc_death_cov_split_p97_5": float(sdf["cc_death_cov"].quantile(0.975)),
            "cc_death_cov_boot_ci_low": b_cc_d_low,
            "cc_death_cov_boot_ci_high": b_cc_d_high,

            # Class-conditional survivor coverage
            "cc_surv_cov_mean": float(sdf["cc_surv_cov"].mean()),
            "cc_surv_cov_sd_over_seeds": float(sdf["cc_surv_cov"].std(ddof=1)),
            "cc_surv_cov_split_p2_5": float(sdf["cc_surv_cov"].quantile(0.025)),
            "cc_surv_cov_split_p97_5": float(sdf["cc_surv_cov"].quantile(0.975)),
            "cc_surv_cov_boot_ci_low": b_cc_s_low,
            "cc_surv_cov_boot_ci_high": b_cc_s_high,

            # Overall coverage
            "overall_cov_mean": float(sdf["overall_cov"].mean()),
            "overall_cov_sd_over_seeds": float(sdf["overall_cov"].std(ddof=1)),
            "overall_cov_split_p2_5": float(sdf["overall_cov"].quantile(0.025)),
            "overall_cov_split_p97_5": float(sdf["overall_cov"].quantile(0.975)),
            "overall_cov_boot_ci_low": b_cov_low,
            "overall_cov_boot_ci_high": b_cov_high,

            # Set size
            "mean_set_size_mean": float(sdf["mean_size"].mean()),
            "mean_set_size_sd_over_seeds": float(sdf["mean_size"].std(ddof=1)),
            "mean_set_size_split_p2_5": float(sdf["mean_size"].quantile(0.025)),
            "mean_set_size_split_p97_5": float(sdf["mean_size"].quantile(0.975)),
            "mean_set_size_boot_ci_low": b_size_low,
            "mean_set_size_boot_ci_high": b_size_high,

            # Share of {0, 1}
            "share_both_mean": float(sdf["share_both"].mean()),
            "share_both_sd_over_seeds": float(sdf["share_both"].std(ddof=1)),
            "share_both_split_p2_5": float(sdf["share_both"].quantile(0.025)),
            "share_both_split_p97_5": float(sdf["share_both"].quantile(0.975)),
            "share_both_boot_ci_low": b_both_low,
            "share_both_boot_ci_high": b_both_high,
        }
        results.append(row)
        print(f"Processed: {attr} - {subgroup} (Deaths: {mean_deaths:.1f}, UNSTABLE: {unstable})")

    res_df = pd.DataFrame(results)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(OUT_CSV, index=False)
    print(f"\nSaved rigorous audit table: {OUT_CSV} ({len(res_df)} rows)")


if __name__ == "__main__":
    run_audit()
