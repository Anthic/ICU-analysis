"""
Extract code-status chart events from MIMIC-IV chartevents (run ON THE USER'S PC; takes roughly 10-30 minutes, no network needed).
File: src/data_processing/11_extract_code_status.py
Keeps itemids 223758 (Code Status), 228687 (Code Status., MD progress note), 229784 (Code Status (Intubation)).
Input : <mimic>/icu/chartevents.csv.gz  (default: ../physionet.org/files/mimiciv/3.1/icu/chartevents.csv.gz relative to --mimic)
Output: data/processed/mimic_code_status_raw.csv.gz  (stay_id, charttime, itemid, value)
Usage : python src/data_processing/11_extract_code_status.py --chartevents "<MIMIC_PATH>/icu/chartevents.csv.gz"
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ITEMS = {223758, 228687, 229784}


def main(path, chunk):
    t0 = time.time(); parts = []; n = 0
    for i, df in enumerate(pd.read_csv(path, usecols=["stay_id", "charttime", "itemid", "value"], chunksize=chunk,
                                       dtype={"stay_id": "float64", "itemid": "int32", "value": "string", "charttime": "string"})):
        n += len(df); parts.append(df[df["itemid"].isin(ITEMS)])
        if (i + 1) % 5 == 0:
            print(f"  chunks {i + 1}, rows {n:,}, kept {sum(map(len, parts)):,}, {time.time() - t0:.0f}s", flush=True)
    out = pd.concat(parts, ignore_index=True)
    out["stay_id"] = out["stay_id"].astype("int64")
    dest = ROOT / "data" / "processed" / "mimic_code_status_raw.csv.gz"
    out.to_csv(dest, index=False); print(f"wrote {dest} ({len(out):,} rows) in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--chartevents", required=True); ap.add_argument("--chunk", type=int, default=5_000_000)
    a = ap.parse_args(); main(a.chartevents, a.chunk)
