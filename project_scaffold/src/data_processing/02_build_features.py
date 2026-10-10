"""
Phase 2: Production Feature Engineering (Vitals & Labs Extraction)
File: src/data_processing/02_build_features.py

Objective:
Extract first-24h vital signs from chartevents and [-6h, +24h] laboratory tests
from labevents for the Phase 1 cohort. Handles neurological GCS triplets, intubation,
clinical plausibility range guards, informative missingness flags, cache invalidation
with configuration hashing, and generates demographic-stratified missingness reports.
Supports MAX_CHUNKS smoke testing mode.
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

# -------------------------------------------------------------
# ১. কনফিগারেশন ও পথ নির্ধারণ (Configuration & Paths)
# -------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_LOCAL = PROJECT_ROOT / "data" / "raw" / "mimic-iv"
PHYSIONET_PATH = Path(os.environ.get("MIMIC_PATH", r"D:\dataset\physionet.org\files\mimiciv\3.1"))

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "outputs" / "results"

COHORT_FILE = PROCESSED_DIR / "cohort.parquet"
OUTPUT_FEATURES_FILE = PROCESSED_DIR / "features.parquet"

# Checkpoint paths (Non-hidden)
CHECKPOINT_VITALS = PROCESSED_DIR / "checkpoint_vitals_extracted.parquet"
CHECKPOINT_LABS = PROCESSED_DIR / "checkpoint_labs_extracted.parquet"
CHECKPOINT_META = PROCESSED_DIR / "checkpoint_metadata.json"

# Missingness reports
REPORT_OVERALL = RESULTS_DIR / "phase2_missingness_overall.csv"
REPORT_RACE = RESULTS_DIR / "phase2_missingness_by_race.csv"
REPORT_INSURANCE = RESULTS_DIR / "phase2_missingness_by_insurance.csv"
REPORT_OUTLIERS = RESULTS_DIR / "phase2_outliers_report.csv"

# Time window named constants
LAB_WINDOW_HOURS_BEFORE = 6
WINDOW_HOURS_AFTER = 24

# Configuration Switch for Sensitivity Analysis
INCLUDE_MEASURED_FLAGS = True
CHUNK_SIZE = 2_000_000

# Smoke testing environment variable (None means full pipeline)
MAX_CHUNKS = int(os.environ["MAX_CHUNKS"]) if "MAX_CHUNKS" in os.environ and os.environ["MAX_CHUNKS"].strip() else None

def get_table_path(subfolder: str, filename: str) -> Path:
    local_path = RAW_DATA_LOCAL / subfolder / filename
    physio_path = PHYSIONET_PATH / subfolder / filename
    if local_path.exists():
        return local_path
    elif physio_path.exists():
        return physio_path
    else:
        raise FileNotFoundError(f"ফাইল পাওয়া যায়নি: {local_path} অথবা {physio_path}")

# -------------------------------------------------------------
# ২. আইটেম আইডি ম্যাপিং ও প্লাউসিবল রেঞ্জ (Item Definition & Ranges)
# -------------------------------------------------------------
VITALS_DEF = {
    "heart_rate": {
        "items": [220045],
        "keywords": ["heart rate"],
        "min": 20.0, "max": 300.0
    },
    "sbp": {
        "items": [220050, 220179],
        "keywords": ["systolic"],
        "min": 30.0, "max": 300.0
    },
    "dbp": {
        "items": [220051, 220180],
        "keywords": ["diastolic"],
        "min": 10.0, "max": 200.0
    },
    "map": {
        "items": [220052, 220181],
        "keywords": ["mean"],
        "min": 20.0, "max": 250.0
    },
    "resp_rate": {
        "items": [220210],
        "keywords": ["respiratory"],
        "min": 4.0, "max": 80.0
    },
    "spo2": {
        "items": [220277],
        "keywords": ["o2"],
        "min": 50.0, "max": 100.0
    },
    "temp_c": {
        "items": [223762],
        "keywords": ["celsius"],
        "min": 30.0, "max": 45.0
    },
    "temp_f": {
        "items": [223761],
        "keywords": ["fahrenheit"],
        "min": 86.0, "max": 113.0  # Converted to C before range filtering
    }
}

GCS_DEF = {
    220739: {"name": "gcs_eye", "keyword": "eye"},
    223900: {"name": "gcs_verbal", "keyword": "verbal"},
    223901: {"name": "gcs_motor", "keyword": "motor"},
}

LABS_DEF = {
    "lactate": {
        "items": [50813],
        "keywords": ["lactate"],
        "min": 0.1, "max": 30.0
    },
    "creatinine": {
        "items": [50912],
        "keywords": ["creatinine"],
        "min": 0.1, "max": 30.0
    },
    "wbc": {
        "items": [51301],
        "keywords": ["white blood cells"],
        "min": 0.1, "max": 200.0
    },
    "platelets": {
        "items": [51265],
        "keywords": ["platelet"],
        "min": 1.0, "max": 2000.0
    },
    "bun": {
        "items": [51006],
        "keywords": ["urea nitrogen"],
        "min": 1.0, "max": 250.0
    },
    "glucose": {
        "items": [50931, 50809],
        "keywords": ["glucose"],
        "min": 10.0, "max": 1500.0
    },
    "potassium": {
        "items": [50971, 50822],
        "keywords": ["potassium"],
        "min": 1.0, "max": 12.0
    },
    "sodium": {
        "items": [50983, 50824],
        "keywords": ["sodium"],
        "min": 90.0, "max": 200.0
    },
    "bicarbonate": {
        "items": [50882, 50803],
        "keywords": ["bicarbonate"],
        "min": 2.0, "max": 60.0
    }
}

# -------------------------------------------------------------
# ৩. আইটেম আইডি ভেরিফিকেশন (Item ID & Label Assertions)
# -------------------------------------------------------------
import sys
sys.stdout.reconfigure(encoding="utf-8")

def verify_item_definitions():
    print("\n[Step 1] Verifying Item IDs against d_items and d_labitems...")
    d_items_path = get_table_path("icu", "d_items.csv.gz")
    d_labitems_path = get_table_path("hosp", "d_labitems.csv.gz")

    df_ditems = pd.read_csv(d_items_path).set_index("itemid")["label"].to_dict()
    df_dlabs = pd.read_csv(d_labitems_path).set_index("itemid")["label"].to_dict()

    # Vitals check
    for feat, meta in VITALS_DEF.items():
        for itemid in meta["items"]:
            lbl = df_ditems.get(itemid, "")
            assert lbl, f"[ERROR] Vital Item ID {itemid} not found in d_items"
            assert any(kw in lbl.lower() for kw in meta["keywords"]), (
                f"[ERROR] Vital {itemid} label '{lbl}' does not contain expected keyword: {meta['keywords']}"
            )
            print(f"   [OK] Vital {itemid:6d} -> {lbl:40s} | Range: [{meta['min']} - {meta['max']}]")

    # GCS check
    for itemid, meta in GCS_DEF.items():
        lbl = df_ditems.get(itemid, "")
        assert lbl, f"[ERROR] GCS Item ID {itemid} not found in d_items"
        assert meta["keyword"] in lbl.lower(), f"[ERROR] GCS {itemid} label '{lbl}' missing keyword: {meta['keyword']}"
        print(f"   [OK] GCS   {itemid:6d} -> {lbl:40s}")

    # Labs check
    for feat, meta in LABS_DEF.items():
        for itemid in meta["items"]:
            lbl = df_dlabs.get(itemid, "")
            assert lbl, f"[ERROR] Lab Item ID {itemid} not found in d_labitems"
            assert any(kw in lbl.lower() for kw in meta["keywords"]), (
                f"[ERROR] Lab {itemid} label '{lbl}' does not contain expected keyword: {meta['keywords']}"
            )
            print(f"   [OK] Lab   {itemid:6d} -> {lbl:40s} | Range: [{meta['min']} - {meta['max']}]")

    print("   [OK] All item IDs and label assertions PASSED successfully!\n")

# -------------------------------------------------------------
# ৪. চেকপয়েন্ট ও ক্যাশ ভ্যালিডেশন (Config + Cohort Hashing)
# -------------------------------------------------------------
def get_cohort_hash(cohort_df: pd.DataFrame) -> str:
    h = hashlib.sha256()
    h.update(str(len(cohort_df)).encode("utf-8"))
    h.update(str(cohort_df["stay_id"].sum()).encode("utf-8"))
    config_str = json.dumps(
        [VITALS_DEF, GCS_DEF, LABS_DEF, LAB_WINDOW_HOURS_BEFORE, WINDOW_HOURS_AFTER],
        sort_keys=True,
        default=str
    )
    h.update(config_str.encode("utf-8"))
    return h.hexdigest()

def to_clean_serializable(obj):
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, dict):
        return {str(k): to_clean_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_clean_serializable(x) for x in obj]
    return obj

def check_cache_validity(cohort_df: pd.DataFrame) -> tuple[bool, bool, dict, dict]:
    current_hash = get_cohort_hash(cohort_df)
    vitals_valid = False
    labs_valid = False
    stored_vit_outliers = {}
    stored_lab_outliers = {}

    meta = {}
    if CHECKPOINT_META.exists():
        try:
            with open(CHECKPOINT_META, "r") as f:
                meta = json.load(f)
        except Exception:
            meta = {}

    # Validate vitals checkpoint (check parquet integrity & row count)
    if CHECKPOINT_VITALS.exists():
        try:
            df_v_chk = pd.read_parquet(CHECKPOINT_VITALS)
            if len(df_v_chk) == len(cohort_df):
                vitals_valid = True
                stored_vit_outliers = meta.get("vitals_outliers", {})
        except Exception:
            vitals_valid = False

    # Validate labs checkpoint
    if CHECKPOINT_LABS.exists():
        try:
            df_l_chk = pd.read_parquet(CHECKPOINT_LABS)
            if len(df_l_chk) == len(cohort_df):
                labs_valid = True
                stored_lab_outliers = meta.get("labs_outliers", {})
        except Exception:
            labs_valid = False

    return vitals_valid, labs_valid, stored_vit_outliers, stored_lab_outliers

def update_cache_metadata(cohort_df: pd.DataFrame, vitals_done=None, labs_done=None, vitals_outliers=None, labs_outliers=None):
    if MAX_CHUNKS is not None:
        return  # In smoke mode, do not write production cache metadata

    meta = {}
    if CHECKPOINT_META.exists():
        try:
            with open(CHECKPOINT_META, "r") as f:
                meta = json.load(f)
        except Exception:
            meta = {}
    
    meta["cohort_rows"] = int(len(cohort_df))
    meta["cohort_hash"] = str(get_cohort_hash(cohort_df))
    if vitals_done is not None:
        meta["vitals_done"] = bool(vitals_done)
    if labs_done is not None:
        meta["labs_done"] = bool(labs_done)
    if vitals_outliers is not None:
        meta["vitals_outliers"] = to_clean_serializable(vitals_outliers)
    if labs_outliers is not None:
        meta["labs_outliers"] = to_clean_serializable(labs_outliers)

    with open(CHECKPOINT_META, "w") as f:
        json.dump(meta, f, indent=2, default=to_clean_serializable)

# -------------------------------------------------------------
# ৫. ভাইটাল সাইন এক্সট্র্যাকশন (Chartevents Stream Processing)
# -------------------------------------------------------------
def extract_vitals(cohort_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    print("=" * 65)
    print(" [Step 2] Processing Vital Signs from chartevents.csv.gz")
    if MAX_CHUNKS is not None:
        print(f" *** SMOKE TEST ACTIVE: Stopping after {MAX_CHUNKS} chunks ***")
    print("=" * 65)

    valid_stay_ids = set(cohort_df["stay_id"])
    cohort_time_lookup = cohort_df.set_index("stay_id")["intime"].to_dict()

    # All item IDs for vitals + GCS
    target_vital_items = set()
    item_to_feat = {}
    for feat, meta in VITALS_DEF.items():
        for i in meta["items"]:
            target_vital_items.add(i)
            item_to_feat[i] = feat

    gcs_items = set(GCS_DEF.keys())
    all_target_items = target_vital_items.union(gcs_items)

    chartevents_path = get_table_path("icu", "chartevents.csv.gz")
    print(f"-> Reading from: {chartevents_path}")

    vitals_records = []
    gcs_records = []
    intubated_stays = set()
    ett_valuenum_series = []

    # Outlier counts: every vital EXCEPT temp_c/temp_f, plus a merged "temperature" key
    vital_feat_keys = [f for f in VITALS_DEF.keys() if f not in ["temp_c", "temp_f"]] + ["temperature"]
    outlier_counts = {f: {"total": 0, "clipped": 0} for f in vital_feat_keys}
    gcs_nan_counts = {i: {"total": 0, "nan": 0} for i in gcs_items}

    chunk_idx = 0
    start_t = time.time()

    for chunk in pd.read_csv(
        chartevents_path,
        chunksize=CHUNK_SIZE,
        usecols=["stay_id", "charttime", "itemid", "valuenum", "value"],
        dtype={"stay_id": "float64", "itemid": "int32", "valuenum": "float64", "value": "object"}
    ):
        chunk_idx += 1
        # 1. Cheap numeric integer & set filtering FIRST
        mask = chunk["itemid"].isin(all_target_items) & chunk["stay_id"].isin(valid_stay_ids)
        filtered = chunk[mask].copy()
        if filtered.empty:
            if MAX_CHUNKS is not None and chunk_idx >= MAX_CHUNKS:
                break
            continue

        # Type safety: cast stay_id to int64 and verify intime
        filtered["stay_id"] = filtered["stay_id"].astype("int64")
        filtered["intime"] = filtered["stay_id"].map(cohort_time_lookup)
        missing_intimes = filtered["intime"].isna().sum()
        assert missing_intimes == 0, f"[ERROR] Missing intime mapped in chartevents: {missing_intimes}"

        if chunk_idx == 1:
            print(f"   [Type Safety] Chunk 1: Cast stay_id to int64; verified {len(filtered):,} rows with 0 missing intimes.")

        # 2. Delayed Date Parsing on matching rows only
        filtered["charttime"] = pd.to_datetime(filtered["charttime"])
        
        # 3. 24h ICU Time Window: [intime, intime + 24h]
        time_mask = (filtered["charttime"] >= filtered["intime"]) & (
            filtered["charttime"] <= filtered["intime"] + pd.Timedelta(hours=WINDOW_HOURS_AFTER)
        )
        filtered = filtered[time_mask].copy()
        if filtered.empty:
            if MAX_CHUNKS is not None and chunk_idx >= MAX_CHUNKS:
                break
            continue

        # 4. Intubated flag detection from GCS Verbal text
        verbal_mask = filtered["itemid"] == 223900
        if verbal_mask.any():
            verbal_chunk = filtered[verbal_mask]
            has_ett = verbal_chunk["value"].astype(str).str.contains("ETT|TRACH|INTUBAT", case=False, na=False)
            if has_ett.any():
                intubated_stays.update(verbal_chunk.loc[has_ett, "stay_id"])
                ett_valuenum_series.append(verbal_chunk.loc[has_ett, "valuenum"])

        # 5. GCS component extraction & NaN tracking
        gcs_mask = filtered["itemid"].isin(gcs_items)
        if gcs_mask.any():
            gcs_chunk = filtered[gcs_mask]
            for gid in gcs_items:
                g_sub = gcs_chunk[gcs_chunk["itemid"] == gid]
                gcs_nan_counts[gid]["total"] += len(g_sub)
                gcs_nan_counts[gid]["nan"] += g_sub["valuenum"].isna().sum()
            gcs_records.append(gcs_chunk[["stay_id", "charttime", "itemid", "valuenum"]])

        # 6. Routine Vitals filtering & Plausible Ranges
        v_mask = filtered["itemid"].isin(target_vital_items) & filtered["valuenum"].notna()
        if v_mask.any():
            v_chunk = filtered[v_mask].copy()
            v_chunk["feature"] = v_chunk["itemid"].map(item_to_feat)
            
            # Convert F -> C before range filter
            f_mask = v_chunk["feature"] == "temp_f"
            if f_mask.any():
                v_chunk.loc[f_mask, "valuenum"] = (v_chunk.loc[f_mask, "valuenum"] - 32.0) * 5.0 / 9.0
                v_chunk.loc[f_mask, "feature"] = "temperature"

            t_mask = v_chunk["feature"] == "temp_c"
            if t_mask.any():
                v_chunk.loc[t_mask, "feature"] = "temperature"

            # Apply plausible range checks for non-temperature vitals
            for feat in [k for k in VITALS_DEF.keys() if k not in ["temp_c", "temp_f"]]:
                meta = VITALS_DEF[feat]
                f_sub = v_chunk["feature"] == feat
                if f_sub.any():
                    vals = v_chunk.loc[f_sub, "valuenum"]
                    outlier_counts[feat]["total"] += int(len(vals))
                    bad = (vals < meta["min"]) | (vals > meta["max"])
                    outlier_counts[feat]["clipped"] += int(bad.sum())
                    v_chunk.loc[f_sub & bad, "valuenum"] = np.nan

            # Apply plausible range check for temperature (30.0 - 45.0 C)
            temp_sub = v_chunk["feature"] == "temperature"
            if temp_sub.any():
                vals = v_chunk.loc[temp_sub, "valuenum"]
                outlier_counts["temperature"]["total"] += int(len(vals))
                bad = (vals < 30.0) | (vals > 45.0)
                outlier_counts["temperature"]["clipped"] += int(bad.sum())
                v_chunk.loc[temp_sub & bad, "valuenum"] = np.nan

            vitals_records.append(v_chunk.dropna(subset=["valuenum"])[["stay_id", "feature", "valuenum"]])

        if chunk_idx % 20 == 0:
            print(f"   Processed {chunk_idx * 2:,}M rows in chartevents... (Elapsed: {time.time() - start_t:.1f}s)")

        if MAX_CHUNKS is not None and chunk_idx >= MAX_CHUNKS:
            print(f"   [Smoke Test] Reached {MAX_CHUNKS} chunks in chartevents. Stopping extraction.")
            break

    print(f"   Finished scanning chartevents ({chunk_idx} chunks). Aggregating per stay_id...")

    # GCS Diagnostics
    print("\n[Diagnostics: GCS Verbal rows matching ETT/TRACH/INTUBAT]")
    if ett_valuenum_series:
        all_ett_vals = pd.concat(ett_valuenum_series)
        print("   valuenum value_counts for intubated verbal entries:")
        print(all_ett_vals.value_counts(dropna=False).to_string())
    else:
        print("   No intubated verbal entries found in processed chunks.")

    n_intubated = len(intubated_stays)
    pct_intubated = (n_intubated / len(valid_stay_ids)) * 100
    print(f"   Intubated stays flagged: {n_intubated:,} / {len(valid_stay_ids):,} ({pct_intubated:.2f}%)")
    # Note: intubated=1 only covers stays that have a verbal chart entry.

    # GCS NaN Summary
    print("\n[Diagnostics: GCS Component NaN Statistics in First 24h]")
    for gid, counts in gcs_nan_counts.items():
        name = GCS_DEF[gid]["name"]
        pct_nan = (counts["nan"] / counts["total"] * 100) if counts["total"] > 0 else 0
        print(f"   {name:12s} ({gid}): {counts['nan']:,} / {counts['total']:,} NaN ({pct_nan:.2f}%)")

    # Aggregate GCS Triplets
    df_gcs = pd.concat(gcs_records, ignore_index=True) if gcs_records else pd.DataFrame(columns=["stay_id", "charttime", "itemid", "valuenum"])
    if not df_gcs.empty:
        # Pivot by stay_id, charttime
        df_gcs_piv = df_gcs.pivot_table(
            index=["stay_id", "charttime"],
            columns="itemid",
            values="valuenum",
            aggfunc="first"
        )
        # Keep ONLY complete triplets
        complete_triplets = df_gcs_piv.dropna(subset=[220739, 223900, 223901]).copy()
        complete_triplets["gcs_total"] = (
            complete_triplets[220739] + complete_triplets[223900] + complete_triplets[223901]
        )
        gcs_agg = complete_triplets.groupby("stay_id")["gcs_total"].min().reset_index()
        gcs_agg.columns = ["stay_id", "gcs_min"]
    else:
        gcs_agg = pd.DataFrame(columns=["stay_id", "gcs_min"])

    # Aggregate Routine Vitals (min, max, mean)
    df_vit = pd.concat(vitals_records, ignore_index=True) if vitals_records else pd.DataFrame(columns=["stay_id", "feature", "valuenum"])
    if not df_vit.empty:
        vit_agg = df_vit.groupby(["stay_id", "feature"])["valuenum"].agg(
            min="min", max="max", mean="mean"
        ).unstack(level="feature")
        
        # Flatten multiindex columns: {feature}_min, {feature}_max, {feature}_mean
        vit_agg.columns = [f"{feat}_{stat}" for stat, feat in vit_agg.columns]
        vit_agg = vit_agg.reset_index()
    else:
        vit_agg = pd.DataFrame({"stay_id": list(valid_stay_ids)})

    # Combine vitals + GCS + Intubated flag
    vitals_final = pd.DataFrame({"stay_id": list(valid_stay_ids)})
    vitals_final = vitals_final.merge(vit_agg, on="stay_id", how="left")
    vitals_final = vitals_final.merge(gcs_agg, on="stay_id", how="left")
    vitals_final["intubated"] = vitals_final["stay_id"].isin(intubated_stays).astype(int)

    # Print percent of cohort with a non-null gcs_min
    non_null_gcs = vitals_final["gcs_min"].notna().sum()
    pct_gcs = (non_null_gcs / len(vitals_final)) * 100
    print(f"   [Diagnostics] Cohort with non-null gcs_min: {non_null_gcs:,} / {len(vitals_final):,} ({pct_gcs:.2f}%)")

    # Save Checkpoint (Skip in smoke mode)
    if MAX_CHUNKS is None:
        vitals_final.to_parquet(CHECKPOINT_VITALS, index=False)
        update_cache_metadata(cohort_df, vitals_done=True, vitals_outliers=outlier_counts)
        print(f"   [OK] Vitals checkpoint saved: {CHECKPOINT_VITALS} ({len(vitals_final):,} rows)")
    else:
        smoke_vit_path = PROCESSED_DIR / "checkpoint_vitals_smoke.parquet"
        vitals_final.to_parquet(smoke_vit_path, index=False)
        print(f"   [Smoke Test] Saved intermediate vitals to: {smoke_vit_path}")

    return vitals_final, outlier_counts

# -------------------------------------------------------------
# ৬. ল্যাব টেস্ট এক্সট্র্যাকশন (Labevents Stream Processing)
# -------------------------------------------------------------
def extract_labs(cohort_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    print("=" * 65)
    print(" [Step 3] Processing Laboratory Tests from labevents.csv.gz")
    if MAX_CHUNKS is not None:
        print(f" *** SMOKE TEST ACTIVE: Stopping after {MAX_CHUNKS} chunks ***")
    print("=" * 65)

    valid_sub_ids = set(cohort_df["subject_id"])
    cohort_lookup = cohort_df[["subject_id", "stay_id", "intime"]].copy()

    target_lab_items = set()
    item_to_lab = {}
    for feat, meta in LABS_DEF.items():
        for i in meta["items"]:
            target_lab_items.add(i)
            item_to_lab[i] = feat

    labevents_path = get_table_path("hosp", "labevents.csv.gz")
    print(f"-> Reading from: {labevents_path}")

    lab_records = []
    outlier_counts = {f: {"total": 0, "clipped": 0} for f in LABS_DEF.keys()}
    chunk_idx = 0
    start_t = time.time()

    for chunk in pd.read_csv(
        labevents_path,
        chunksize=CHUNK_SIZE,
        usecols=["subject_id", "charttime", "itemid", "valuenum"],
        dtype={"subject_id": "int64", "itemid": "int32", "valuenum": "float64"}
    ):
        chunk_idx += 1
        # 1. Filter subject_id and lab itemid FIRST
        mask = chunk["itemid"].isin(target_lab_items) & chunk["subject_id"].isin(valid_sub_ids)
        filtered = chunk[mask].copy()
        if filtered.empty:
            if MAX_CHUNKS is not None and chunk_idx >= MAX_CHUNKS:
                break
            continue

        # 2. Delayed Date Parsing
        filtered["charttime"] = pd.to_datetime(filtered["charttime"])

        # 3. Attach cohort stay_id and intime via fast DataFrame merge
        filtered = filtered.merge(cohort_lookup, on="subject_id", how="inner")

        # 4. Expanded Window: [intime - 6h, intime + 24h]
        time_mask = (filtered["charttime"] >= filtered["intime"] - pd.Timedelta(hours=LAB_WINDOW_HOURS_BEFORE)) & (
            filtered["charttime"] <= filtered["intime"] + pd.Timedelta(hours=WINDOW_HOURS_AFTER)
        )
        filtered = filtered[time_mask].copy()
        if filtered.empty:
            if MAX_CHUNKS is not None and chunk_idx >= MAX_CHUNKS:
                break
            continue

        # 5. Map itemid to lab feature name
        filtered["feature"] = filtered["itemid"].map(item_to_lab)

        # 6. Plausible Range check (Set out-of-range to NaN)
        for feat, meta in LABS_DEF.items():
            f_sub = filtered["feature"] == feat
            if f_sub.any():
                vals = filtered.loc[f_sub, "valuenum"]
                outlier_counts[feat]["total"] += int(len(vals))
                bad = (vals < meta["min"]) | (vals > meta["max"])
                outlier_counts[feat]["clipped"] += int(bad.sum())
                filtered.loc[f_sub & bad, "valuenum"] = np.nan

        lab_records.append(filtered.dropna(subset=["valuenum"])[["stay_id", "feature", "valuenum"]])

        if chunk_idx % 20 == 0:
            print(f"   Processed {chunk_idx * 2:,}M rows in labevents... (Elapsed: {time.time() - start_t:.1f}s)")

        if MAX_CHUNKS is not None and chunk_idx >= MAX_CHUNKS:
            print(f"   [Smoke Test] Reached {MAX_CHUNKS} chunks in labevents. Stopping extraction.")
            break

    print(f"   Finished scanning labevents ({chunk_idx} chunks). Aggregating per stay_id...")

    df_labs = pd.concat(lab_records, ignore_index=True) if lab_records else pd.DataFrame(columns=["stay_id", "feature", "valuenum"])
    if not df_labs.empty:
        labs_agg = df_labs.groupby(["stay_id", "feature"])["valuenum"].agg(
            min="min", max="max", mean="mean"
        ).unstack(level="feature")
        
        labs_agg.columns = [f"{feat}_{stat}" for stat, feat in labs_agg.columns]
        labs_agg = labs_agg.reset_index()
    else:
        labs_agg = pd.DataFrame({"stay_id": cohort_df["stay_id"]})

    # Save Checkpoint (Skip in smoke mode)
    if MAX_CHUNKS is None:
        labs_agg.to_parquet(CHECKPOINT_LABS, index=False)
        update_cache_metadata(cohort_df, labs_done=True, labs_outliers=outlier_counts)
        print(f"   [OK] Labs checkpoint saved: {CHECKPOINT_LABS} ({len(labs_agg):,} rows)")
    else:
        smoke_lab_path = PROCESSED_DIR / "checkpoint_labs_smoke.parquet"
        labs_agg.to_parquet(smoke_lab_path, index=False)
        print(f"   [Smoke Test] Saved intermediate labs to: {smoke_lab_path}")

    return labs_agg, outlier_counts

# -------------------------------------------------------------
# ৭. মিসিংনেস অডিট ও রিপোর্ট জেনারেটর (Stratified Missingness)
# -------------------------------------------------------------
def generate_missingness_reports(features_df: pd.DataFrame, outlier_stats: dict):
    print("=" * 65)
    print(" [Step 4] Generating Stratified Missingness & Quality Reports")
    print("=" * 65)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    suffix = "_smoke.csv" if MAX_CHUNKS is not None else ".csv"
    rep_overall = RESULTS_DIR / f"phase2_missingness_overall{suffix}"
    rep_race = RESULTS_DIR / f"phase2_missingness_by_race{suffix}"
    rep_ins = RESULTS_DIR / f"phase2_missingness_by_insurance{suffix}"
    rep_outliers = RESULTS_DIR / f"phase2_outliers_report{suffix}"

    # Exclude metadata columns from missingness percentage calculation
    meta_cols = [
        "subject_id", "hadm_id", "stay_id", "intime", "outtime", "los",
        "anchor_age", "age_group", "anchor_year_group", "sex",
        "race_group", "insurance_group", "mortality"
    ]
    feat_cols = [c for c in features_df.columns if c not in meta_cols and not c.endswith("_measured")]

    # 1. Overall Missingness
    overall_miss = features_df[feat_cols].isna().mean() * 100
    df_overall = pd.DataFrame({"feature": overall_miss.index, "missing_pct": overall_miss.values.round(2)})
    df_overall = df_overall.sort_values("missing_pct", ascending=False).reset_index(drop=True)
    df_overall.to_csv(rep_overall, index=False)
    print(f"   [OK] Overall missingness saved to: {rep_overall}")

    # 2. Stratified by Race Group
    race_miss = features_df.groupby("race_group")[feat_cols].apply(lambda g: g.isna().mean() * 100).T.round(2)
    race_miss.index.name = "feature"
    race_miss.reset_index().to_csv(rep_race, index=False)
    print(f"   [OK] Race-stratified missingness saved to: {rep_race}")

    # 3. Stratified by Insurance Group
    ins_miss = features_df.groupby("insurance_group")[feat_cols].apply(lambda g: g.isna().mean() * 100).T.round(2)
    ins_miss.index.name = "feature"
    ins_miss.reset_index().to_csv(rep_ins, index=False)
    print(f"   [OK] Insurance-stratified missingness saved to: {rep_ins}")

    # 4. Outliers Report
    outlier_rows = []
    for f, d in outlier_stats.items():
        pct = (d["clipped"] / d["total"] * 100) if d["total"] > 0 else 0
        outlier_rows.append({
            "feature": f,
            "total_measurements": d["total"],
            "outliers_clipped_to_nan": d["clipped"],
            "clipped_pct": round(pct, 3)
        })
    df_outliers = pd.DataFrame(outlier_rows).sort_values("clipped_pct", ascending=False)
    df_outliers.to_csv(rep_outliers, index=False)
    print(f"   [OK] Outliers audit report saved to: {rep_outliers}")

    return df_outliers

# -------------------------------------------------------------
# ৮. মূল পাইপলাইন এক্সিকিউশন (Main Pipeline)
# -------------------------------------------------------------
def build_features():
    total_start = time.time()
    print("=" * 65)
    print(" [Phase 2] Production Feature Engineering Pipeline")
    if MAX_CHUNKS is not None:
        print(f" *** SMOKE TEST MODE (MAX_CHUNKS={MAX_CHUNKS}) ***")
    print("=" * 65)

    # 1. Load Cohort
    assert COHORT_FILE.exists(), f"Phase 1 cohort not found at {COHORT_FILE}. Run 01_build_cohort.py first."
    cohort = pd.read_parquet(COHORT_FILE)
    print(f"-> Loaded Phase 1 cohort: {len(cohort):,} adult ICU patients.")

    # 2. Verify all item definitions & labels against dictionaries
    verify_item_definitions()

    # 3. Check Cache Validity (In smoke mode, always run fresh chunks)
    if MAX_CHUNKS is None:
        vitals_cached, labs_cached, stored_vit_outliers, stored_lab_outliers = check_cache_validity(cohort)
    else:
        vitals_cached, labs_cached = False, False
        stored_vit_outliers, stored_lab_outliers = {}, {}

    outlier_stats = {}

    # Extract Vitals
    if vitals_cached:
        print(f"-> Loading vitals from valid checkpoint: {CHECKPOINT_VITALS}")
        df_vitals = pd.read_parquet(CHECKPOINT_VITALS)
        outlier_stats.update(stored_vit_outliers)
    else:
        df_vitals, vit_outliers = extract_vitals(cohort)
        outlier_stats.update(vit_outliers)

    # Extract Labs
    if labs_cached:
        print(f"-> Loading labs from valid checkpoint: {CHECKPOINT_LABS}")
        df_labs = pd.read_parquet(CHECKPOINT_LABS)
        outlier_stats.update(stored_lab_outliers)
    else:
        df_labs, lab_outliers = extract_labs(cohort)
        outlier_stats.update(lab_outliers)

    # 4. Merge All Features with Cohort
    print("\n[Step 4] Merging all clinical features into single dataset...")
    features = cohort.merge(df_vitals, on="stay_id", how="left")
    features = features.merge(df_labs, on="stay_id", how="left")

    # 5. Add Informative Missingness Flags (*_measured)
    print(f"\n[Step 5] Adding informative missingness indicator flags (*_measured)...")
    for lab in LABS_DEF.keys():
        mean_col = f"{lab}_mean"
        flag_col = f"{lab}_measured"
        if mean_col in features.columns:
            features[flag_col] = features[mean_col].notna().astype(int)
        else:
            features[flag_col] = 0

    if not INCLUDE_MEASURED_FLAGS:
        print("   [Config Notice] INCLUDE_MEASURED_FLAGS is False. Dropping *_measured columns.")
        features = features.drop(columns=[f"{l}_measured" for l in LABS_DEF.keys()])

    # 6. Generate Missingness & Audit Reports
    df_outliers = generate_missingness_reports(features, outlier_stats)

    # 7. Final Sanity Checks & Assertions
    assert len(features) == len(cohort), f"Row count changed after feature merge: {len(features)} != {len(cohort)}"
    assert features["stay_id"].is_unique, "Duplicate stay_ids in final feature set"
    assert features["mortality"].notna().all(), "Missing outcomes detected"

    # 8. Save Final Features Parquet (or smoke parquet)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if MAX_CHUNKS is None:
        features.to_parquet(OUTPUT_FEATURES_FILE, index=False)
        target_out = OUTPUT_FEATURES_FILE
    else:
        smoke_out = PROCESSED_DIR / "features_smoke.parquet"
        features.to_parquet(smoke_out, index=False)
        target_out = smoke_out

    elapsed = time.time() - total_start
    print("=" * 65)
    print(f" [SUCCESS] Features saved successfully to:\n   {target_out}")
    print(f"   মোট সময়: {elapsed:.2f} সেকেন্ড ({elapsed / 60:.1f} মিনিট)")
    print(f"   চূড়ান্ত ফিচার টেবিল আকার: {features.shape[0]:,} সারি x {features.shape[1]} কলাম")
    print(f"   Mortality outcome rate: {features['mortality'].mean() * 100:.2f}%")
    print("=" * 65)

    if MAX_CHUNKS is not None:
        print("\n*** SMOKE TEST COMPLETE ***")
        print(f"Feature table shape: {features.shape}")
        # Print sample outlier rows
        print("\n[Outlier Summary (Smoke Mode)]")
        sample_outliers = df_outliers[df_outliers["feature"].isin(["temperature", "heart_rate", "lactate"])]
        print(sample_outliers.to_string(index=False))

    return features, df_outliers

if __name__ == "__main__":
    build_features()
