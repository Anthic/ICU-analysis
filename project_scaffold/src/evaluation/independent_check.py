"""Independent recomputation check from scratch without using shared audit code."""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"d:\dataset\icu_conformal_fairness_project (1)\project_scaffold")
P3_PATH = ROOT / "outputs" / "results" / "phase3_test_predictions_noflags_a010.parquet"
P5_PATH = ROOT / "outputs" / "results" / "phase5_mondrian_intervals_noflags_a010.parquet"
FEAT_PATH = ROOT / "data" / "processed" / "features.parquet"

P4_CSV = ROOT / "outputs" / "tables" / "phase4_rigorous_audit_noflags_a010.csv"
P5_CSV = ROOT / "outputs" / "tables" / "phase5_subgroup_coverage_corrected_noflags_a010.csv"

# Load raw parquets
print("Loading parquets...")
p3 = pd.read_parquet(P3_PATH, columns=["seed", "stay_id", "y", "p_hat", "set_classcond_has0", "set_classcond_has1"])
p5 = pd.read_parquet(P5_PATH, columns=[
    "seed", "stay_id",
    "mondrian_cc_age_group_has0", "mondrian_cc_age_group_has1",
    "mondrian_cc_insurance_group_has0", "mondrian_cc_insurance_group_has1",
    "mondrian_cc_race_group_has0", "mondrian_cc_race_group_has1",
])
feat = pd.read_parquet(FEAT_PATH, columns=["stay_id", "age_group", "insurance_group", "race_group"])
feat["race_group"] = feat["race_group"].replace({"Other/Unknown": "Other/Unknown (race)"})
feat["insurance_group"] = feat["insurance_group"].replace({"Other/Unknown": "Other/Unknown (insurance)"})

df = p3.merge(p5, on=["seed", "stay_id"]).merge(feat, on="stay_id")

# Target groups
targets = [
    ("age_group", "18-49", "mondrian_cc_age_group"),
    ("age_group", "75+", "mondrian_cc_age_group"),
    ("insurance_group", "Medicare", "mondrian_cc_insurance_group"),
    ("insurance_group", "Private", "mondrian_cc_insurance_group"),
    ("race_group", "Hispanic", "mondrian_cc_race_group"),
    ("race_group", "Other/Unknown (race)", "mondrian_cc_race_group"),
]

# Read CSV ground truths
p4_csv_df = pd.read_csv(P4_CSV)
p5_csv_df = pd.read_csv(P5_CSV)
p5_cc_csv = p5_csv_df[p5_csv_df["calibration_type"] == "mondrian_class_conditional"]

all_passed = True
print(f"{'Group':<25} | {'Metric':<20} | {'Recomputed':<10} | {'CSV Value':<10} | {'Diff':<10} | {'Status'}")
print("-" * 90)

for attr, grp_val, mond_col in targets:
    sub_df = df[df[attr] == grp_val]
    
    # Compute per-seed metrics
    per_seed = []
    for s, sdf in sub_df.groupby("seed"):
        y_s = sdf["y"].to_numpy()
        p_s = sdf["p_hat"].to_numpy()
        
        deaths = (y_s == 1)
        surv = (y_s == 0)
        
        c0 = sdf["set_classcond_has0"].to_numpy()
        c1 = sdf["set_classcond_has1"].to_numpy()
        
        m0 = sdf[f"{mond_col}_has0"].to_numpy()
        m1 = sdf[f"{mond_col}_has1"].to_numpy()
        
        cc_death_cov = c1[deaths].mean() if deaths.any() else np.nan
        cc_surv_cov = c0[surv].mean() if surv.any() else np.nan
        
        m_death_cov = m1[deaths].mean() if deaths.any() else np.nan
        m_surv_cov = m0[surv].mean() if surv.any() else np.nan
        
        set_sz = (c0.astype(int) + c1.astype(int)).mean()
        citl = p_s.mean() - y_s.mean()
        
        per_seed.append({
            "cc_death_cov": cc_death_cov,
            "cc_surv_cov": cc_surv_cov,
            "m_death_cov": m_death_cov,
            "m_surv_cov": m_surv_cov,
            "set_size": set_sz,
            "citl": citl,
        })
        
    ps_df = pd.DataFrame(per_seed)
    recomp = {
        "cc_death_cov": ps_df["cc_death_cov"].mean(),
        "cc_surv_cov": ps_df["cc_surv_cov"].mean(),
        "m_death_cov": ps_df["m_death_cov"].mean(),
        "m_surv_cov": ps_df["m_surv_cov"].mean(),
        "set_size": ps_df["set_size"].mean(),
        "citl": ps_df["citl"].mean(),
    }
    
    # Retrieve CSV values
    r4 = p4_csv_df[(p4_csv_df["attribute"] == attr) & (p4_csv_df["subgroup"] == grp_val)].iloc[0]
    
    lookup_p5_sg = "Other/Unknown" if grp_val in ["Other/Unknown (race)", "Other/Unknown (insurance)"] else grp_val
    r5 = p5_cc_csv[(p5_cc_csv["stratification_attribute"] == attr) & (p5_cc_csv["subgroup"] == lookup_p5_sg)].iloc[0]
    
    csv_vals = {
        "cc_death_cov": r4["cc_death_cov_mean"],
        "cc_surv_cov": r4["cc_surv_cov_mean"],
        "m_death_cov": r5["coverage_deaths_mean"],
        "m_surv_cov": r5["coverage_survivors_mean"],
        "set_size": r4["mean_set_size_mean"],
        "citl": r4["citl_mean"],
    }
    
    for metric_name in ["cc_death_cov", "cc_surv_cov", "m_death_cov", "m_surv_cov", "set_size", "citl"]:
        val_recomp = recomp[metric_name]
        val_csv = csv_vals[metric_name]
        diff = abs(val_recomp - val_csv)
        status = "PASS" if diff < 0.0005 else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"{grp_val:<25} | {metric_name:<20} | {val_recomp:10.6f} | {val_csv:10.6f} | {diff:10.6f} | {status}")

print("-" * 90)
if all_passed:
    print("FINAL RESULT: PASS (All differences are below 0.0005)")
else:
    print("FINAL RESULT: FAIL (One or more differences exceed 0.0005)")

