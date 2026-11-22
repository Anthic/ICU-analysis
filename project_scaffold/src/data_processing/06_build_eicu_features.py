"""
Phase 6a: Build the eICU-CRD external cohort + features (mirrors Phase 1/2 definitions).
File: src/data_processing/06_build_eicu_features.py

Input  (data/raw/eicu/, or env EICU_PATH):
    patient.csv.gz, vitalPeriodic.csv.gz, vitalAperiodic.csv.gz, lab.csv.gz,
    nurseCharting.csv.gz, apacheApsVar.csv.gz       (eICU-CRD v2.0, PhysioNet credentialed)
Output:
    data/processed/eicu_features.parquet            one row per patient, same feature names as MIMIC features.parquet
    outputs/results/phase6_eicu_exclusion_flow.csv  CONSORT-style flow
    outputs/results/phase6_eicu_missingness.csv     % missing per feature

Cohort definition (kept as close to MIMIC Phase 1 as eICU allows):
    1. all unit stays
    2. first ICU stay per patient (uniquepid; ordered by hospitaldischargeyear,
       patienthealthsystemstayid, unitvisitnumber -- eICU only gives discharge YEAR, so the
       order across hospitalisations of one patient is approximate)
    3. ICU length of stay >= 24 h (unitdischargeoffset >= 1440 min)
    4. age >= 18 ('> 89' coded as 90)
    5. known hospital outcome (Alive / Expired) and sex (Male / Female)
Outcome: in-hospital mortality (hospitaldischargestatus == 'Expired').
Windows (minutes from unit admission = offset 0): vitals [0, 1440]; labs [-360, 1440].

Known, documented differences from MIMIC-IV (state them in the paper's Methods/Limitations):
    * eICU has NO insurance field -> insurance results cannot be validated externally.
    * Vitals: eICU periodic (5-min) + aperiodic tables; SBP/DBP/MAP combine invasive and
      non-invasive like the MIMIC item sets.
    * GCS: eICU nurse-charted 'GCS Total' (min over window); fallback = APACHE first-day
      eyes+motor+verbal when all three are valid.  MIMIC used complete charted triplets.
    * intubated: APACHE 'intubated' flag (first day), not charted verbal text as in MIMIC.
    * eICU covers 2014-2015, 208 hospitals; hospitalid is the cluster for site analyses.

Usage:
    python src/data_processing/06_build_eicu_features.py            # full run
    python src/data_processing/06_build_eicu_features.py --sample 2000   # smoke test
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EICU_DIR = Path(os.environ.get("EICU_PATH", PROJECT_ROOT / "data" / "raw" / "eicu"))
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "outputs" / "results"
OUT_FEATURES = PROCESSED_DIR / "eicu_features.parquet"
OUT_FLOW = RESULTS_DIR / "phase6_eicu_exclusion_flow.csv"
OUT_MISSING = RESULTS_DIR / "phase6_eicu_missingness.csv"

CHUNK = 2_000_000
VITAL_END_MIN = 24 * 60
LAB_START_MIN = -6 * 60

# Plausible ranges: identical to MIMIC Phase 2 (02_build_features.py)
RANGES = {
    "heart_rate": (20, 300), "sbp": (30, 300), "dbp": (10, 200), "map": (20, 250),
    "resp_rate": (4, 80), "spo2": (50, 100), "temperature": (30.0, 45.0),
    "lactate": (0.1, 30), "creatinine": (0.1, 30), "wbc": (0.1, 200), "platelets": (1, 2000),
    "bun": (1, 250), "glucose": (10, 1500), "potassium": (1, 12), "sodium": (90, 200),
    "bicarbonate": (2, 60),
}
VITALS = ("heart_rate", "sbp", "dbp", "map", "resp_rate", "spo2", "temperature")
LABS = ("lactate", "creatinine", "wbc", "platelets", "bun", "glucose",
        "potassium", "sodium", "bicarbonate")

PERIODIC_MAP = {"heartrate": "heart_rate", "respiration": "resp_rate", "sao2": "spo2",
                "temperature": "temperature", "systemicsystolic": "sbp",
                "systemicdiastolic": "dbp", "systemicmean": "map"}
APERIODIC_MAP = {"noninvasivesystolic": "sbp", "noninvasivediastolic": "dbp",
                 "noninvasivemean": "map"}
LAB_MAP = {"lactate": "lactate", "creatinine": "creatinine", "wbc x 1000": "wbc",
           "platelets x 1000": "platelets", "bun": "bun", "glucose": "glucose",
           "potassium": "potassium", "sodium": "sodium", "bicarbonate": "bicarbonate"}

RACE_MAP = {"caucasian": "White", "african american": "Black", "hispanic": "Hispanic",
            "asian": "Asian", "native american": "Other/Unknown", "other/unknown": "Other/Unknown"}


def find_file(stem: str) -> Path:
    """Case-insensitive lookup of <stem>.csv.gz, then <stem>.csv, anywhere under EICU_DIR.
    Handles the layout where an extracted file sits in a folder of the same name
    (e.g. patient.csv/patient.csv).  Only real files are returned, never folders."""
    if not EICU_DIR.exists():
        raise FileNotFoundError(f"eICU folder not found: {EICU_DIR}  (set EICU_PATH or place files there)")
    files = [p for p in EICU_DIR.rglob("*") if p.is_file()]
    for name in (f"{stem}.csv.gz", f"{stem}.csv"):
        hits = sorted((p for p in files if p.name.lower() == name.lower()), key=lambda p: len(p.parts))
        if hits:
            return hits[0]
    raise FileNotFoundError(f"{stem}.csv(.gz) not found under {EICU_DIR}")


def read_chunks(path: Path, usecols: list[str], max_chunks: int | None):
    """Yield chunks with lower-cased column names (eICU headers are lower-case already)."""
    reader = pd.read_csv(path, usecols=lambda c: c.lower() in usecols, chunksize=CHUNK, low_memory=False)
    for i, ch in enumerate(reader):
        if max_chunks is not None and i >= max_chunks:
            break
        ch.columns = [c.lower() for c in ch.columns]
        yield ch


def map_age_group(age: pd.Series) -> pd.Series:
    return pd.cut(age, bins=[17, 49, 64, 74, 150], labels=["18-49", "50-64", "65-74", "75+"], right=True)


def parse_age(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    out = pd.to_numeric(s.str.replace(r"^>\s*89$", "90", regex=True), errors="coerce")
    return out


def build_cohort(sample: int | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = ["patientunitstayid", "patienthealthsystemstayid", "uniquepid", "hospitalid", "gender", "age",
            "ethnicity", "hospitaldischargeyear", "hospitaldischargestatus", "unitvisitnumber",
            "unitdischargeoffset"]
    pat = pd.read_csv(find_file("patient"), usecols=lambda c: c.lower() in cols)
    pat.columns = [c.lower() for c in pat.columns]
    flow = [("All eICU unit stays", len(pat))]

    pat = pat.sort_values(["hospitaldischargeyear", "patienthealthsystemstayid", "unitvisitnumber"])
    pat = pat.drop_duplicates("uniquepid", keep="first")
    flow.append(("First ICU stay per patient", len(pat)))

    pat = pat[pat["unitdischargeoffset"] >= VITAL_END_MIN]
    flow.append(("ICU LOS >= 24h", len(pat)))

    pat["anchor_age"] = parse_age(pat["age"])
    pat = pat[pat["anchor_age"] >= 18]
    flow.append(("Adult with valid age (>= 18)", len(pat)))

    pat = pat[pat["hospitaldischargestatus"].isin(["Alive", "Expired"]) & pat["gender"].isin(["Male", "Female"])]
    flow.append(("Known outcome and sex", len(pat)))

    if sample is not None and sample < len(pat):
        pat = pat.sample(n=sample, random_state=42)
        flow.append((f"Smoke-test subsample", len(pat)))

    pat["sex"] = pat["gender"]
    pat["mortality"] = (pat["hospitaldischargestatus"] == "Expired").astype(int)
    pat["race_group"] = pat["ethnicity"].astype(str).str.strip().str.lower().map(RACE_MAP).fillna("Other/Unknown")
    pat["age_group"] = map_age_group(pat["anchor_age"]).astype(str)
    pat["stay_id"] = pat["patientunitstayid"]
    pat["subject_id"] = pat["uniquepid"]
    keep = ["stay_id", "subject_id", "patientunitstayid", "hospitalid", "hospitaldischargeyear",
            "anchor_age", "sex", "age_group", "race_group", "mortality"]
    return pat[keep].reset_index(drop=True), pd.DataFrame(flow, columns=["step", "n"])


def _partial_agg(df_long: pd.DataFrame) -> pd.DataFrame:
    g = df_long.groupby(["patientunitstayid", "feature"])["value"]
    return g.agg(["min", "max", "sum", "count"]).reset_index()


def _combine(parts: list[pd.DataFrame]) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame(columns=["patientunitstayid"])
    p = pd.concat(parts, ignore_index=True)
    g = p.groupby(["patientunitstayid", "feature"]).agg(
        min=("min", "min"), max=("max", "max"), sum=("sum", "sum"), count=("count", "sum")).reset_index()
    g["mean"] = g["sum"] / g["count"]
    wide = g.pivot(index="patientunitstayid", columns="feature", values=["min", "max", "mean"])
    wide.columns = [f"{feat}_{stat}" for stat, feat in wide.columns]
    return wide.reset_index()


def _clip(df: pd.DataFrame) -> pd.DataFrame:
    lo = df["feature"].map(lambda f: RANGES[f][0])
    hi = df["feature"].map(lambda f: RANGES[f][1])
    return df[(df["value"] >= lo) & (df["value"] <= hi)]


def extract_vitals(ids: set, max_chunks: int | None) -> pd.DataFrame:
    parts = []
    for fname, mapping in (("vitalPeriodic", PERIODIC_MAP), ("vitalAperiodic", APERIODIC_MAP)):
        cols = ["patientunitstayid", "observationoffset"] + list(mapping)
        for ch in read_chunks(find_file(fname), cols, max_chunks):
            ch = ch[ch["patientunitstayid"].isin(ids) & ch["observationoffset"].between(0, VITAL_END_MIN)]
            if ch.empty:
                continue
            long = ch.melt(id_vars="patientunitstayid", value_vars=list(mapping), var_name="feature", value_name="value")
            long["feature"] = long["feature"].map(mapping)
            long = _clip(long.dropna(subset=["value"]))
            if not long.empty:
                parts.append(_partial_agg(long))
    return _combine(parts)


def extract_labs(ids: set, max_chunks: int | None) -> pd.DataFrame:
    parts = []
    cols = ["patientunitstayid", "labresultoffset", "labname", "labresult"]
    for ch in read_chunks(find_file("lab"), cols, max_chunks):
        ch["labname"] = ch["labname"].astype(str).str.strip().str.lower()
        ch = ch[ch["patientunitstayid"].isin(ids) & ch["labname"].isin(LAB_MAP)
                & ch["labresultoffset"].between(LAB_START_MIN, VITAL_END_MIN)]
        if ch.empty:
            continue
        long = pd.DataFrame({"patientunitstayid": ch["patientunitstayid"],
                             "feature": ch["labname"].map(LAB_MAP),
                             "value": pd.to_numeric(ch["labresult"], errors="coerce")}).dropna()
        long = _clip(long)
        if not long.empty:
            parts.append(_partial_agg(long))
    return _combine(parts)


def extract_gcs_and_intubation(ids: set, max_chunks: int | None) -> pd.DataFrame:
    # nurse-charted GCS Total (min within window)
    gcs_parts = []
    cols = ["patientunitstayid", "nursingchartoffset", "nursingchartcelltypevalname", "nursingchartvalue"]
    for ch in read_chunks(find_file("nurseCharting"), cols, max_chunks):
        ch = ch[ch["patientunitstayid"].isin(ids) & ch["nursingchartoffset"].between(0, VITAL_END_MIN)]
        ch = ch[ch["nursingchartcelltypevalname"].astype(str).str.strip().str.lower() == "gcs total"]
        if ch.empty:
            continue
        v = pd.to_numeric(ch["nursingchartvalue"], errors="coerce")
        d = pd.DataFrame({"patientunitstayid": ch["patientunitstayid"], "v": v}).dropna()
        d = d[d["v"].between(3, 15)]
        if not d.empty:
            gcs_parts.append(d.groupby("patientunitstayid")["v"].min().reset_index())
    gcs = (pd.concat(gcs_parts).groupby("patientunitstayid")["v"].min().rename("gcs_min").reset_index()
           if gcs_parts else pd.DataFrame(columns=["patientunitstayid", "gcs_min"]))

    aps = pd.read_csv(find_file("apacheApsVar"), usecols=lambda c: c.lower() in
                      ["patientunitstayid", "intubated", "eyes", "motor", "verbal"])
    aps.columns = [c.lower() for c in aps.columns]
    aps = aps[aps["patientunitstayid"].isin(ids)].drop_duplicates("patientunitstayid")
    ok = (aps[["eyes", "motor", "verbal"]] >= 1).all(axis=1)
    aps["gcs_aps"] = np.where(ok, aps["eyes"] + aps["motor"] + aps["verbal"], np.nan)
    aps["intubated"] = (aps["intubated"] == 1).astype(int)

    out = aps[["patientunitstayid", "intubated", "gcs_aps"]].merge(gcs, on="patientunitstayid", how="outer")
    out["gcs_min"] = out["gcs_min"].fillna(out["gcs_aps"])
    return out[["patientunitstayid", "gcs_min", "intubated"]]


def cached(name: str, fn, use_cache: bool) -> pd.DataFrame:
    """Run fn() once and keep the result as CSV (no pyarrow needed) so a crash later does not lose hours of work."""
    path = PROCESSED_DIR / f"eicu_checkpoint_{name}.csv.gz"
    if use_cache and path.exists():
        print(f"[6a] resuming {name} from checkpoint {path.name}")
        return pd.read_csv(path)
    out = fn()
    if use_cache:
        out.to_csv(path, index=False)
    return out


def build(sample: int | None, max_chunks: int | None) -> None:
    t0 = time.time()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    use_cache = sample is None and max_chunks is None
    cohort, flow = build_cohort(sample)
    ids = set(cohort["patientunitstayid"])
    print(f"[6a] cohort built: {len(cohort):,} patients, {cohort['mortality'].mean():.2%} mortality")

    vit = cached("vitals", lambda: extract_vitals(ids, max_chunks), use_cache)
    print("[6a] vitals extracted")
    lab = cached("labs", lambda: extract_labs(ids, max_chunks), use_cache)
    print("[6a] labs extracted")
    gcs = cached("gcs", lambda: extract_gcs_and_intubation(ids, max_chunks), use_cache)
    print("[6a] GCS / intubation extracted")

    df = cohort.merge(vit, on="patientunitstayid", how="left")
    df = df.merge(lab, on="patientunitstayid", how="left")
    df = df.merge(gcs, on="patientunitstayid", how="left")
    df["intubated"] = df["intubated"].fillna(0).astype(int)

    # make sure every expected predictor exists (all-NaN if absent), same names as MIMIC
    expected = [f"{n}_{s}" for n in VITALS + LABS for s in ("min", "max", "mean")] + ["gcs_min"]
    for c in expected:
        if c not in df.columns:
            df[c] = np.nan

    miss = (df[expected].isna().mean() * 100).round(2).rename("pct_missing").reset_index()
    miss.columns = ["feature", "pct_missing"]
    sfx = "_smoke" if (sample is not None or max_chunks is not None) else ""   # never overwrite real outputs with a test run
    out_feat = OUT_FEATURES.with_name(OUT_FEATURES.stem + sfx + ".parquet")
    out_flow = OUT_FLOW.with_name(OUT_FLOW.stem + sfx + ".csv")
    out_miss = OUT_MISSING.with_name(OUT_MISSING.stem + sfx + ".csv")
    miss.to_csv(out_miss, index=False)
    flow.to_csv(out_flow, index=False)
    try:
        df.to_parquet(out_feat, index=False)
    except Exception as exc:  # e.g. pyarrow DLL blocked by Windows Application Control
        out_feat = out_feat.with_name(out_feat.stem + ".csv.gz")
        df.to_csv(out_feat, index=False)
        print(f"[6a] WARNING parquet unavailable ({type(exc).__name__}); saved CSV instead: {out_feat.name}")

    print("\n=== Phase 6a summary (aggregates only) ===")
    print(flow.to_string(index=False))
    print(f"rows out: {len(df):,} | mortality: {df['mortality'].mean():.2%} | hospitals: {df['hospitalid'].nunique()}")
    print("race:", df["race_group"].value_counts().to_dict())
    print("age:", df["age_group"].value_counts().to_dict())
    print("features with >50% missing:", miss.loc[miss.pct_missing > 50, "feature"].tolist())
    print(f"written: {out_feat.name}, {out_flow.name}, {out_miss.name} | {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=None, help="subsample N patients (smoke test)")
    ap.add_argument("--max-chunks", type=int, default=None, help="limit chunks per big table (smoke test)")
    a = ap.parse_args()
    build(a.sample, a.max_chunks)
