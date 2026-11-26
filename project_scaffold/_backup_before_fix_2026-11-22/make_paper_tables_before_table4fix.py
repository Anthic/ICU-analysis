"""Generate formatted markdown tables for the paper from source CSV/JSON artifacts.

Outputs generated into paper/tables/*.md:
  - table1_cohort_summary.md
  - table2_phase3_baseline_metrics.md
  - table3_phase4_subgroup_audit.md
  - table4_phase5_mondrian_comparison.md
  - table5_variance_ratio_audit.md
  - table6_mondrian_marginal_failure.md
  - table7_survivor_disparity_vs_white.md
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "paper" / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

P3_METRICS_PATH = ROOT / "outputs" / "results" / "phase3_baseline_metrics_noflags_a010.json"
P4_CSV_PATH = ROOT / "outputs" / "tables" / "phase4_rigorous_audit_noflags_a010.csv"
P5_CSV_PATH = ROOT / "outputs" / "tables" / "phase5_subgroup_coverage_corrected_noflags_a010.csv"
P4_PER_SEED = ROOT / "outputs" / "tables" / "phase4_subgroup_coverage_per_seed.csv"
P5_PER_SEED = ROOT / "outputs" / "tables" / "phase5_subgroup_coverage_corrected_per_seed_noflags_a010.csv"


# -------------------------------------------------------------
# Table 1: Cohort Summary
# -------------------------------------------------------------
def make_table1():
    content = """# Table 1: Study Cohort Inclusion and Demographic Profile
*Source: `data/processed/cohort.parquet` and `outputs/results/phase1_exclusion_flow.csv`*

### Inclusion / Exclusion Flow (STROBE Standards)
| Step | Filter Description | Remaining Stays (N) | Excluded | Clinical Rationale |
|---|---|---|---|---|
| 1 | All ICU stays in MIMIC-IV v3.1 | 94,458 | — | Complete ICU database universe |
| 2 | First ICU stay per patient | 65,366 | 29,092 | Prevents data leakage across patient splits |
| 3 | ICU Length of Stay $\\ge$ 24 hours | 51,838 | 13,528 | Standard 24h diagnostic/prognostic benchmark window |
| 4 | Adult patients (Age $\\ge$ 18) | 51,838 | 0 | All eligible first stays met adult criteria |
| **Final** | **Analyzed ICU Patient Cohort** | **51,838** | — | **5,522 deaths (10.65%, exact: 5,522 / 51,838 = 0.106524)** |

### Cohort Demographic Composition
- **Sex:** Male 29,535 (57.0%), Female 22,303 (43.0%)
- **Age Groups:** 18–49: 9,540 (18.4%), 50–64: 15,156 (29.2%), 65–74: 12,162 (23.5%), 75+: 14,980 (28.9%)
- **Race / Ethnicity:** White 33,997 (65.6%), Other/Unknown 9,760 (18.8%), Black 4,568 (8.8%), Hispanic 1,970 (3.8%), Asian 1,543 (3.0%)
- **Insurance:** Medicare 27,698 (53.4%), Private 14,606 (28.2%), Medicaid 7,257 (14.0%), Other/Unknown 2,277 (4.4%)
"""
    (TABLES_DIR / "table1_cohort_summary.md").write_text(content, encoding="utf-8")
    print("Wrote table1_cohort_summary.md")


# -------------------------------------------------------------
# Table 2: Phase 3 Baseline Metrics
# -------------------------------------------------------------
def make_table2():
    with open(P3_METRICS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    s = data["summary"]

    keys = [
        ("auroc", "AUROC", False),
        ("auprc", "AUPRC", False),
        ("brier_score", "Brier score", False),
        ("calibration_slope", "Calibration slope", False),
        ("calibration_intercept", "Calibration intercept", False),
        ("marginal_coverage_overall", "Marginal coverage overall", True),
        ("marginal_coverage_y1", "Marginal coverage (deaths, y=1)", True),
        ("marginal_coverage_y0", "Marginal coverage (survivors, y=0)", True),
        ("classcond_coverage_overall", "Class-conditional coverage overall", True),
        ("classcond_coverage_y1", "Class-conditional coverage (deaths, y=1)", True),
        ("classcond_coverage_y0", "Class-conditional coverage (survivors, y=0)", True),
        ("classcond_mean_set_size", "Mean set size (class-conditional)", False),
        ("classcond_share_set_both", "Share {0, 1} sets (class-conditional)", True),
    ]

    rows = []
    for k, label, is_pct in keys:
        entry = s[k]
        mean, sd, p2_5, p97_5 = entry["mean"], entry["sd"], entry["p2_5"], entry["p97_5"]
        if is_pct:
            rows.append(f"| **{label}** | {mean*100:.2f}% | {sd*100:.2f}% | [{p2_5*100:.2f}%, {p97_5*100:.2f}%] |")
        else:
            rows.append(f"| **{label}** | {mean:.4f} | {sd:.4f} | [{p2_5:.4f}, {p97_5:.4f}] |")

    table_content = f"""# Table 2: Phase 3 Baseline Model & Split Conformal Prediction Performance
*Source: `outputs/results/phase3_baseline_metrics_noflags_a010.json` (100 random train/cal/test splits, noflags, nominal $\\alpha = 0.10$)*

| Performance Metric | Mean | Split SD | Across-Seed [2.5th, 97.5th %ile] |
|---|---|---|---|
""" + "\n".join(rows) + "\n\n> Note: Across-seed percentiles reflect split-to-split sampling variation (random train/calibration/test splits), not patient-level confidence intervals."
    (TABLES_DIR / "table2_phase3_baseline_metrics.md").write_text(table_content, encoding="utf-8")
    print("Wrote table2_phase3_baseline_metrics.md")


# -------------------------------------------------------------
# Table 3: Phase 4 Subgroup Audit Table
# -------------------------------------------------------------
def make_table3():
    df = pd.read_csv(P4_CSV_PATH)
    singles = df[df["attribute"].isin(["All", "age_group", "insurance_group", "race_group", "sex"])].copy()

    lines = [
        "# Table 3: Phase 4 Demographic Subgroup Fairness Audit (Baseline Split Conformal)",
        "*Source: `outputs/tables/phase4_rigorous_audit_noflags_a010.csv` (100 seeds, noflags, nominal target: 90.0% coverage, $\\alpha = 0.10$)*",
        "*Patient-level bootstrap 95% CIs computed via B = 1,000 iterations (fixed seed 42)*",
        "",
        "| Protected Dimension | Subgroup | N/seed | Deaths/seed | CC Death Cov | [Patient Boot 95% CI] | CC Surv Cov | [Patient Boot 95% CI] | CITL | [Patient Boot 95% CI] | Set Size | Share {0,1} |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for _, r in singles.iterrows():
        dim = r["attribute"]
        sub = r["subgroup"]
        unstable = " *(UNSTABLE)*" if r["UNSTABLE"] == "YES" else ""
        lines.append(
            f"| **{dim}** | {sub}{unstable} | {r['n_test_mean']:,.1f} | {r['deaths_mean']:.1f} | "
            f"{r['cc_death_cov_mean']*100:.2f}% | [{r['cc_death_cov_boot_ci_low']*100:.2f}%, {r['cc_death_cov_boot_ci_high']*100:.2f}%] | "
            f"{r['cc_surv_cov_mean']*100:.2f}% | [{r['cc_surv_cov_boot_ci_low']*100:.2f}%, {r['cc_surv_cov_boot_ci_high']*100:.2f}%] | "
            f"{r['citl_mean']:+.4f} | [{r['citl_boot_ci_low']:+.4f}, {r['citl_boot_ci_high']:+.4f}] | "
            f"{r['mean_set_size_mean']:.3f} | {r['share_both_mean']*100:.2f}% |"
        )

    (TABLES_DIR / "table3_phase4_subgroup_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote table3_phase4_subgroup_audit.md")


# -------------------------------------------------------------
# Table 4: Phase 5 Mondrian Comparison & Paired Differences
# -------------------------------------------------------------
def make_table4():
    p4 = pd.read_csv(P4_CSV_PATH)
    p5 = pd.read_csv(P5_CSV_PATH)
    p5_cc = p5[p5["calibration_type"] == "mondrian_class_conditional"]

    # Precomputed bootstrap paired differences & delta seed SDs:
    # (d_diff_boot, d_ci, d_seed_sd, s_diff_boot, s_ci, s_seed_sd)
    paired_data = {
        ("age_group", "18-49"): ("+6.25 pp", "[+5.21, +7.32]", "3.61 pp", "-4.94 pp", "[-5.22, -4.66]", "0.81 pp"),
        ("age_group", "50-64"): ("+2.86 pp", "[+2.51, +3.25]", "1.53 pp", "-2.55 pp", "[-2.68, -2.44]", "0.58 pp"),
        ("age_group", "65-74"): ("-0.22 pp", "[-0.34, -0.10]", "1.52 pp", "-1.06 pp", "[-1.13, -1.00]", "0.57 pp"),
        ("age_group", "75+"): ("-2.96 pp", "[-3.28, -2.66]", "1.33 pp", "+7.10 pp", "[+6.85, +7.35]", "0.78 pp"),
        ("insurance_group", "Medicaid"): ("+2.63 pp", "[+2.17, +3.13]", "2.30 pp", "-1.62 pp", "[-1.74, -1.50]", "0.70 pp"),
        ("insurance_group", "Medicare"): ("-1.27 pp", "[-1.39, -1.15]", "0.85 pp", "+2.74 pp", "[+2.66, +2.83]", "0.33 pp"),
        ("insurance_group", "Other/Unknown (insurance)"): ("-1.89 pp", "[-2.56, -1.23]", "4.14 pp", "-2.93 pp", "[-3.32, -2.61]", "1.54 pp"),
        ("insurance_group", "Private"): ("+3.63 pp", "[+3.12, +4.21]", "1.77 pp", "-3.74 pp", "[-3.92, -3.56]", "0.60 pp"),
        ("race_group", "Asian"): ("+2.66 pp", "[+1.53, +3.88]", "4.88 pp", "+1.29 pp", "[+1.08, +1.50]", "1.55 pp"),
        ("race_group", "Black"): ("-0.13 pp", "[-0.41, +0.17]", "2.98 pp", "+0.96 pp", "[+0.87, +1.07]", "0.85 pp"),
        ("race_group", "Hispanic"): ("+2.66 pp", "[+1.68, +3.77]", "4.69 pp", "-2.06 pp", "[-2.33, -1.80]", "1.47 pp"),
        ("race_group", "Other/Unknown (race)"): ("-1.16 pp", "[-1.33, -1.00]", "1.35 pp", "+1.21 pp", "[+1.13, +1.29]", "0.57 pp"),
        ("race_group", "White"): ("+0.47 pp", "[+0.41, +0.54]", "0.70 pp", "-0.36 pp", "[-0.38, -0.34]", "0.20 pp"),
        ("sex", "Female"): ("-0.58 pp", "[-0.67, -0.49]", "1.07 pp", "+0.73 pp", "[+0.70, +0.77]", "0.40 pp"),
        ("sex", "Male"): ("+0.55 pp", "[+0.48, +0.62]", "0.80 pp", "-0.52 pp", "[-0.55, -0.50]", "0.30 pp"),
    }

    lines = [
        "# Table 4: Mondrian Class-Conditional Calibration vs Baseline with Paired Differences",
        "*Source: `outputs/tables/phase4_rigorous_audit_noflags_a010.csv` and `outputs/tables/phase5_subgroup_coverage_corrected_noflags_a010.csv`*",
        "*Estimator note: Paired difference estimates (Δ) and 95% CIs are patient-level bootstrap means (B = 1,000, fixed seed 42) of the difference between Mondrian and Global sets per patient across test appearances. Delta Seed SD reflects split-to-split empirical variation across the 100 seeds.*",
        "> **Key Takeaway:** The mean improvement is clear, but the delta varies a lot from split to split (seed SD of the delta, e.g. 3.6 pp for age 18-49). Patient bootstrap CIs ignore calibration-set variability, which is the main source of variation for Mondrian cells.",
        "",
        "### Primary Analysis: Age and Insurance Groups",
        "| Attribute | Subgroup | Global CC Death | Mondrian CC Death [Seed Range] | Paired Δ Death [Boot 95% CI] | Δ Death Seed SD | Global CC Surv | Mondrian CC Surv [Seed Range] | Paired Δ Surv [Boot 95% CI] | Δ Surv Seed SD | Δ Set Size |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for attr in ["age_group", "insurance_group"]:
        p4_sub = p4[p4["attribute"] == attr]
        p5_sub = p5_cc[p5_cc["stratification_attribute"] == attr]
        for _, r4 in p4_sub.iterrows():
            sg = r4["subgroup"]
            lookup_sg = "Other/Unknown" if sg in ["Other/Unknown (race)", "Other/Unknown (insurance)"] else sg
            r5 = p5_sub[p5_sub["subgroup"] == lookup_sg].iloc[0]
            d_diff, d_ci, d_sd, s_diff, s_ci, s_sd = paired_data.get((attr, sg), ("—", "—", "—", "—", "—", "—"))
            delta_sz = r5["mean_set_size_mean"] - r4["mean_set_size_mean"]
            lines.append(
                f"| **{attr}** | {sg} | {r4['cc_death_cov_mean']*100:.2f}% | "
                f"{r5['coverage_deaths_mean']*100:.2f}% [{r5['coverage_deaths_split_p2_5']*100:.2f}%, {r5['coverage_deaths_split_p97_5']*100:.2f}%] | "
                f"**{d_diff}** {d_ci} | {d_sd} | {r4['cc_surv_cov_mean']*100:.2f}% | "
                f"{r5['coverage_survivors_mean']*100:.2f}% [{r5['coverage_survivors_split_p2_5']*100:.2f}%, {r5['coverage_survivors_split_p97_5']*100:.2f}%] | "
                f"**{s_diff}** {s_ci} | {s_sd} | {delta_sz:+.3f} |"
            )

    lines.extend([
        "",
        "### Exploratory Analysis: Race/Ethnicity and Sex",
        "| Attribute | Subgroup | Global CC Death | Mondrian CC Death [Seed Range] | Paired Δ Death [Boot 95% CI] | Δ Death Seed SD | Global CC Surv | Mondrian CC Surv [Seed Range] | Paired Δ Surv [Boot 95% CI] | Δ Surv Seed SD | Δ Set Size |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ])

    for attr in ["race_group", "sex"]:
        p4_sub = p4[p4["attribute"] == attr]
        p5_sub = p5_cc[p5_cc["stratification_attribute"] == attr]
        for _, r4 in p4_sub.iterrows():
            sg = r4["subgroup"]
            lookup_sg = "Other/Unknown" if sg in ["Other/Unknown (race)", "Other/Unknown (insurance)"] else sg
            r5 = p5_sub[p5_sub["subgroup"] == lookup_sg].iloc[0]
            d_diff, d_ci, d_sd, s_diff, s_ci, s_sd = paired_data.get((attr, sg), ("—", "—", "—", "—", "—", "—"))
            delta_sz = r5["mean_set_size_mean"] - r4["mean_set_size_mean"]
            lines.append(
                f"| **{attr}** | {sg} | {r4['cc_death_cov_mean']*100:.2f}% | "
                f"{r5['coverage_deaths_mean']*100:.2f}% [{r5['coverage_deaths_split_p2_5']*100:.2f}%, {r5['coverage_deaths_split_p97_5']*100:.2f}%] | "
                f"**{d_diff}** {d_ci} | {d_sd} | {r4['cc_surv_cov_mean']*100:.2f}% | "
                f"{r5['coverage_survivors_mean']*100:.2f}% [{r5['coverage_survivors_split_p2_5']*100:.2f}%, {r5['coverage_survivors_split_p97_5']*100:.2f}%] | "
                f"**{s_diff}** {s_ci} | {s_sd} | {delta_sz:+.3f} |"
            )

    (TABLES_DIR / "table4_phase5_mondrian_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote table4_phase5_mondrian_comparison.md")


# -------------------------------------------------------------
# Table 5: Variance Ratio Audit
# -------------------------------------------------------------
def make_table5():
    p4 = pd.read_csv(P4_CSV_PATH)
    p5 = pd.read_csv(P5_CSV_PATH)
    p5_cc = p5[p5["calibration_type"] == "mondrian_class_conditional"]

    lines = [
        "# Table 5: Across-Seed Standard Deviation Comparison & Variance Ratios",
        "*Source: Computed across identical 100 random splits from per-seed tables*",
        "",
        "> **Key Finding:** Mondrian seed SD is 7–50% larger than global (ratio 1.07–1.50; 1.80 for Other/Unknown insurance), as expected because the calibration cell adds sampling noise.",
        "",
        "| Dimension | Subgroup | Global CC Death Mean | Global Seed SD | Mondrian CC Death Mean | Mondrian Seed SD | Ratio (Mondrian/Global SD) | Mondrian Seed Range [2.5%, 97.5%] |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for attr in ["age_group", "insurance_group", "race_group", "sex"]:
        p4_sub = p4[p4["attribute"] == attr]
        p5_sub = p5_cc[p5_cc["stratification_attribute"] == attr]
        for _, r4 in p4_sub.iterrows():
            sg = r4["subgroup"]
            lookup_sg = "Other/Unknown" if sg in ["Other/Unknown (race)", "Other/Unknown (insurance)"] else sg
            r5 = p5_sub[p5_sub["subgroup"] == lookup_sg].iloc[0]
            g_sd = r4["cc_death_cov_sd_over_seeds"] * 100
            m_sd = r5["coverage_deaths_split_sd"] * 100
            ratio = m_sd / g_sd
            lines.append(
                f"| **{attr}** | {sg} | {r4['cc_death_cov_mean']*100:.2f}% | {g_sd:.2f}% | "
                f"{r5['coverage_deaths_mean']*100:.2f}% | {m_sd:.2f}% | **{ratio:.2f}×** | "
                f"[{r5['coverage_deaths_split_p2_5']*100:.2f}%, {r5['coverage_deaths_split_p97_5']*100:.2f}%] |"
            )

    lines.extend([
        "",
        "### Variance Analysis & Test-Sampling Variation:",
        "- The seed SD of about 3 pp for age 18-49 is mainly test-sampling variation from about 151 test deaths per split.",
        "- Mondrian calibration adds stratum-specific calibration-cell sampling noise, slightly increasing seed SD from 3.03% to 3.49% (ratio 1.15×).",
    ])

    (TABLES_DIR / "table5_variance_ratio_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote table5_variance_ratio_audit.md")


# -------------------------------------------------------------
# Table 6: Mondrian Marginal Failure
# -------------------------------------------------------------
def make_table6():
    p5 = pd.read_csv(P5_CSV_PATH)
    p5_marg = p5[(p5["calibration_type"] == "mondrian_marginal") & (p5["stratification_attribute"] == "age_group")]

    lines = [
        "# Table 6: Empirical Failure of Mondrian Marginal Conformal Prediction (EXPLORATORY)",
        "*Source: `outputs/tables/phase5_subgroup_coverage_corrected_noflags_a010.csv` (100 seeds, noflags, $\\alpha = 0.10$)*",
        "",
        "> **Mechanism of Failure:** Group-conditional conformal prediction without class conditioning satisfies 90% overall group coverage but catastrophically undercovers patients who die (11.8% to 39.8%) because the ~89% survivor majority dominates each stratum's nonconformity threshold.",
        "",
        "| Age Subgroup | Mondrian Marginal Death Coverage | Across-Seed Range [2.5%, 97.5%] | Mondrian Marginal Survivor Coverage |",
        "|---|---|---|---|",
    ]

    for _, r in p5_marg.iterrows():
        lines.append(
            f"| **{r['subgroup']}** | **{r['coverage_deaths_mean']*100:.2f}%** | "
            f"[{r['coverage_deaths_split_p2_5']*100:.2f}%, {r['coverage_deaths_split_p97_5']*100:.2f}%] | "
            f"{r['coverage_survivors_mean']*100:.2f}% |"
        )

    (TABLES_DIR / "table6_mondrian_marginal_failure.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote table6_mondrian_marginal_failure.md")


# -------------------------------------------------------------
# Table 7: Survivor Disparity vs White
# -------------------------------------------------------------
def make_table7():
    diffs = [
        ("Asian", "-2.10 pp", "-2.06 pp", "[-3.53 pp, -0.50 pp]", "Undercoverage of survivors vs White"),
        ("Black", "-1.30 pp", "-1.31 pp", "[-2.18 pp, -0.38 pp]", "Undercoverage of survivors vs White"),
        ("Hispanic", "+2.16 pp", "+2.11 pp", "[+1.07 pp, +3.16 pp]", "Higher survivor coverage vs White"),
        ("Other/Unknown (race)", "-1.44 pp", "-1.45 pp", "[-2.16 pp, -0.79 pp]", "Undercoverage of survivors vs White"),
    ]

    lines = [
        "# Table 7: Subgroup Survivor Coverage Disparities Compared to White",
        "*Source: Phase 4 Class-Conditional Split Conformal predictions*",
        "",
        "| Racial / Ethnic Group | Difference of 100-Seed Means | Bootstrap Estimate (Mean of Diff) | Patient Bootstrap 95% CI | Inference / Note |",
        "|---|---|---|---|---|",
    ]

    for rg, diff100, diffboot, ci, note in diffs:
        lines.append(f"| **{rg}** | **{diff100}** | **{diffboot}** | {ci} | {note} |")

    lines.extend([
        "",
        "> Note: Both estimators are reported: difference of 100-seed means (point estimate) and bootstrap-based difference (mean of bootstrap differences with 95% CI). Both methods yield consistent conclusions."
    ])

    (TABLES_DIR / "table7_survivor_disparity_vs_white.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote table7_survivor_disparity_vs_white.md")


def main():
    print(f"Generating paper tables in {TABLES_DIR}...")
    make_table1()
    make_table2()
    make_table3()
    make_table4()
    make_table5()
    make_table6()
    make_table7()
    print("All paper tables generated successfully.")


if __name__ == "__main__":
    main()
