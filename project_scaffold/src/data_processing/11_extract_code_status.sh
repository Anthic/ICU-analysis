#!/usr/bin/env bash
# Fast extraction of code-status chartevents rows (items 223758, 228687; 229784 returns no rows).
# This is the command that produced data/processed/mimic_code_status_raw.csv.gz.
# Usage: bash 11_extract_code_status.sh <MIMIC_PATH>/icu/chartevents.csv.gz out.csv.gz
set -euo pipefail
IN="$1"; OUT="$2"
{ zcat "$IN" | head -1
  zcat "$IN" | grep -E ',(223758|228687|229784),'; } | gzip > "$OUT"
