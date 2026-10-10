"""
Phase 1: Environment & Cohort Setup (Production & Publication Grade)
File: src/data_processing/01_build_cohort.py

Objective:
Extract clean, single-stay adult ICU cohort with outcomes (mortality)
and demographic protected attributes (Sex, Age Group, Race, Insurance).
Generates CONSORT exclusion flow with excluded counts for manuscript Figure 1.

Methodological Notes:
- Index ICU Stay: Only the first ICU stay per unique patient is retained.
- Observation Window: Stays < 24 hours are excluded to prevent survival/index bias.
- Race/Demographics: Recorded at admission level and extracted from the index admission.
- Other/Unknown Race: Heterogeneous composite group (Native American, Pacific Islander, 
  declined/unknown); reported transparently in fairness audits but not analyzed as a single cultural group.
"""

import os
import time
from pathlib import Path
import pandas as pd
import numpy as np

# -------------------------------------------------------------
# ১. পথ কনফিগারেশন (Configurable Paths)
# -------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_LOCAL = PROJECT_ROOT / "data" / "raw" / "mimic-iv"
PHYSIONET_PATH = Path(os.environ.get("MIMIC_PATH", r"D:\dataset\physionet.org\files\mimiciv\3.1"))

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "outputs" / "results"
OUTPUT_FILE = OUTPUT_DIR / "cohort.parquet"
EXCLUSION_FLOW_FILE = RESULTS_DIR / "phase1_exclusion_flow.csv"

def get_table_path(subfolder: str, filename: str) -> Path:
    """
    প্রথমে data/raw চেক করে, না পেলে সরাসরি physionet ফোল্ডার থেকে ফাইল লোড করে।
    """
    local_path = RAW_DATA_LOCAL / subfolder / filename
    physio_path = PHYSIONET_PATH / subfolder / filename
    
    if local_path.exists():
        return local_path
    elif physio_path.exists():
        return physio_path
    else:
        raise FileNotFoundError(f"ফাইল পাওয়া যায়নি: {local_path} অথবা {physio_path}")

# -------------------------------------------------------------
# ২. সাবগ্রুপ স্ট্যান্ডার্ডাইজেশন (Demographic Harmonization)
# -------------------------------------------------------------
def map_race(race_series: pd.Series) -> pd.Series:
    """
    MIMIC-IV-এর ৩০+ রেস টেক্সটকে স্ট্যান্ডার্ড ৫টি গ্রুপে ক্লাসিফাই করে।
    South American ও Brazilian কে Hispanic-এ অন্তর্ভুক্ত করা হয়েছে।
    ~is_hispanic দিয়ে White ও অন্যান্য গ্রুপের সাথে overlap প্রতিরোধ করা হয়েছে।
    """
    race_clean = race_series.str.upper().fillna("UNKNOWN")
    
    is_hispanic = race_clean.str.contains("HISPANIC|LATINO|SOUTH AMERICAN|BRAZILIAN", regex=True)
    is_black = race_clean.str.contains("BLACK|AFRICAN|CAPE VERDEAN|CARIBBEAN", regex=True) & (~is_hispanic)
    is_asian = race_clean.str.contains("ASIAN", regex=True) & (~is_hispanic)
    is_white = race_clean.str.contains("WHITE|PORTUGUESE", regex=True) & (~is_hispanic)
    
    conditions = [is_hispanic, is_black, is_asian, is_white]
    choices = ["Hispanic", "Black", "Asian", "White"]
    
    return np.select(conditions, choices, default="Other/Unknown")

def map_age_group(age_series: pd.Series) -> pd.Series:
    """
    বয়সকে ৪টি গ্রুপে ভাগ করে। ১৮ বছর বয়স যাতে অন্তর্ভুক্ত হয় সেজন্য bin শুরু ১৭ থেকে।
    (17, 49] -> ১৮ থেকে ৪৯ বছর।
    """
    bins = [17, 49, 64, 74, 150]
    labels = ["18-49", "50-64", "65-74", "75+"]
    return pd.cut(age_series, bins=bins, labels=labels, right=True)

def map_insurance(insurance_series: pd.Series) -> pd.Series:
    """
    Private insurance-কে স্বতন্ত্র গ্রুপ হিসেবে রেখে ৪টি ক্যাটাগরি করা হয়েছে।
    """
    ins_clean = insurance_series.str.title().fillna("Other")
    conditions = [
        ins_clean.str.contains("Medicare"),
        ins_clean.str.contains("Medicaid"),
        ins_clean.str.contains("Private"),
    ]
    choices = ["Medicare", "Medicaid", "Private"]
    return np.select(conditions, choices, default="Other/Unknown")

# -------------------------------------------------------------
# ৩. মূল কোহোর্ট পাইপলাইন (Main Pipeline)
# -------------------------------------------------------------
def build_cohort():
    start_time = time.time()
    print("=" * 65)
    print(" [Phase 1] Production ICU Cohort Construction Pipeline")
    print("=" * 65)
    
    # ৩.১. আইসিইউ স্টে ডেটা লোড
    icustays_path = get_table_path("icu", "icustays.csv.gz")
    print(f"-> Reading ICU stays from: {icustays_path}")
    df_icu = pd.read_csv(
        icustays_path,
        usecols=["subject_id", "hadm_id", "stay_id", "intime", "outtime", "los"],
        parse_dates=["intime", "outtime"]
    )
    n_all_stays = len(df_icu)
    print(f"   ১. সর্বমোট আইসিইউ স্টে (All ICU stays): {n_all_stays:,}")

    # ৩.২. ফিল্টার ১: প্রতিটি রোগীর শুধুমাত্র প্রথম আইসিইউ স্টে (Index Stay)
    df_icu = df_icu.sort_values(["subject_id", "intime"]).drop_duplicates(
        subset=["subject_id"], keep="first"
    )
    n_first_stays = len(df_icu)
    print(f"   ২. প্রতি রোগীর প্রথম আইসিইউ স্টে (First stay per patient): {n_first_stays:,}")

    # ৩.৩. ফিল্টার ২: আইসিইউতে অবস্থান কমপক্ষে ২৪ ঘণ্টা (los >= 1.0 দিন)
    df_icu = df_icu[df_icu["los"] >= 1.0].copy()
    n_los_ge_24h = len(df_icu)
    print(f"   ৩. আইসিইউ অবস্থান >= ২৪ ঘণ্টা (ICU LOS >= 24h): {n_los_ge_24h:,} (বাদ: {n_first_stays - n_los_ge_24h:,})")

    # ৩.৪. পেশেন্ট ডেমোগ্রাফিক্স লোড
    patients_path = get_table_path("hosp", "patients.csv.gz")
    print(f"-> Reading Patients from: {patients_path}")
    df_patients = pd.read_csv(
        patients_path,
        usecols=["subject_id", "gender", "anchor_age", "anchor_year_group"]
    )
    
    # আইসিইউ স্টে-এর সাথে মার্জ
    df_merged = df_icu.merge(df_patients, on="subject_id", how="inner")

    # ৩.৫. ফিল্টার ৩: প্রাপ্তবয়স্ক রোগী (Age >= 18)
    df_merged = df_merged[df_merged["anchor_age"] >= 18].copy()
    n_adults = len(df_merged)
    print(f"   ৪. প্রাপ্তবয়স্ক রোগী (Adults Age >= 18): {n_adults:,}")

    # ৩.৬. অ্যাডমিশন তথ্য ও আউটকাম লোড
    admissions_path = get_table_path("hosp", "admissions.csv.gz")
    print(f"-> Reading Admissions from: {admissions_path}")
    df_admissions = pd.read_csv(
        admissions_path,
        usecols=["hadm_id", "race", "insurance", "hospital_expire_flag"]
    )
    
    cohort = df_merged.merge(df_admissions, on="hadm_id", how="inner")
    n_final = len(cohort)
    print(f"   ৫. সম্পূর্ণ অ্যাডমিশন রেকর্ডসহ চূড়ান্ত কোহোর্ট: {n_final:,}")

    # ৩.৭. সুরক্ষা অ্যাসারশন (Safety & Integrity Assertions)
    assert n_final == n_adults, f"[INTEGRITY ERROR] Admissions merge changed row count: {n_final} != {n_adults}"
    assert cohort["subject_id"].is_unique and cohort["stay_id"].is_unique, "[INTEGRITY ERROR] Duplicate patients/stays detected"
    print("   [✓] Integrity Check Passed: No dropped rows, perfect 1-to-1 unique cohort.")

    # ৩.৮. কলাম ম্যাপিং
    cohort["race_group"] = map_race(cohort["race"])
    cohort["age_group"] = map_age_group(cohort["anchor_age"])
    cohort["insurance_group"] = map_insurance(cohort["insurance"])
    cohort["sex"] = cohort["gender"].map({"M": "Male", "F": "Female"}).fillna("Unknown")
    cohort["mortality"] = cohort["hospital_expire_flag"].astype(int)

    # ৩.৯. কঠোর কুয়ালিটি চেক (NaN Assertion Guard)
    check_cols = ["age_group", "race_group", "sex", "insurance_group", "mortality", "anchor_year_group"]
    for col in check_cols:
        assert cohort[col].notna().all(), f"[CRITICAL ERROR] NaN detected in column: {col}"
    print("   [✓] Assertion Passed: কোনো প্রটেক্টেড অ্যাট্রিবিউট বা আউটকামে কোনো NaN নেই!")

    # প্রয়োজনীয় কলামগুলো সাজানো
    final_cols = [
        "subject_id", "hadm_id", "stay_id",
        "intime", "outtime", "los",
        "anchor_age", "age_group", "anchor_year_group",
        "sex", "race_group", "insurance_group",
        "mortality"
    ]
    cohort = cohort[final_cols].reset_index(drop=True)

    # ৩.১০. ফাইল সেভ (Parquet ও Exclusion Flow CSV)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Parquet সেভ
    cohort.to_parquet(OUTPUT_FILE, index=False)
    
    # CONSORT Flow CSV সেভ (with 'excluded' column)
    flow_data = [
        ("All ICU stays in MIMIC-IV", n_all_stays),
        ("First ICU stay per patient", n_first_stays),
        ("ICU LOS >= 24h", n_los_ge_24h),
        ("Adult patients (Age >= 18)", n_adults),
        ("Final analyzed cohort", n_final)
    ]
    flow_df = pd.DataFrame(flow_data, columns=["step", "n"])
    flow_df["excluded"] = (flow_df["n"].shift(1) - flow_df["n"]).fillna(0).astype(int)
    flow_df.to_csv(EXCLUSION_FLOW_FILE, index=False)
    
    elapsed = time.time() - start_time
    print("=" * 65)
    print(f" [SUCCESS] Cohort saved successfully to:\n   {OUTPUT_FILE}")
    print(f" [SUCCESS] CONSORT flow diagram saved to:\n   {EXCLUSION_FLOW_FILE}")
    print(f"   মোট সময়: {elapsed:.2f} সেকেন্ড")
    print(f"   চূড়ান্ত কোহোর্ট সাইজ: {len(cohort):,} জন রোগী")
    print(f"   ইন-হসপিটাল মর্টালিটি রেট: {cohort['mortality'].mean() * 100:.2f}%")
    print("=" * 65)

    # ৩.১১. ডেমোগ্রাফিক ডিস্ট্রিবিউশন প্রদর্শন
    print("\n[Sanity Check: সাবগ্রুপ বন্টন ও স্যাম্পল সাইজ]")
    for attr in ["sex", "age_group", "race_group", "insurance_group", "anchor_year_group"]:
        print(f"\n--- {attr} ---")
        counts = cohort[attr].value_counts()
        pcts = cohort[attr].value_counts(normalize=True).round(3) * 100
        summary_df = pd.DataFrame({"N": counts, "Percentage (%)": pcts})
        print(summary_df)

if __name__ == "__main__":
    build_cohort()
