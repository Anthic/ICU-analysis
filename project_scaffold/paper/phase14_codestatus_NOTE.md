# Phase 14 — code-status (DNR/DNI/CMO) sensitivity, MIMIC-IV, 100 seeds, 2026-11-25  [GENERATED — PENDING REVIEW]
Scripts: `src/data_processing/11_extract_code_status.py` (extraction done with zcat|grep on chartevents because a Python background job was killed by the shell; same itemids 223758, 228687, 229784; 86,858 rows, 41,891 stays), `src/evaluation/14_code_status_sensitivity.py` (100 seeds in 3 chunks with `--start`, merged). Outputs: `outputs/tables/phase14_codestatus_{rows,summary}_main_100.csv`, `outputs/results/phase14_summary_main_100.json`. Chunk files `*__s0/__s1/__s2.csv` and `*__test.csv` are intermediates (could not be deleted).
Flags use only entries charted in the first 24 h after ICU admission. Documented limitation in first 24 h: 1,377 stays (comfort measures only 55; DNR/DNI 1,340) in the 51,838... profile table (seed 0 flags file) — about 2.7% of stays; rises with age (0.5% at 18-49, 6.4% at 75+); mortality among limited stays 27-48%.
## Result (mean over 100 seeds, class-conditional pooled, alpha 0.10)
| Variant | 18-49 death cov | 75+ survivor cov | 75+ death cov | 18-49 survivor cov |
|---|---|---|---|---|
| V0 original | 0.842 | 0.829 | 0.930 | 0.949 |
| V4 excl. CMO (24h) | 0.841 | 0.829 | 0.932 | 0.950 |
| V5 excl. any limitation (24h) | 0.847 | 0.831 | 0.931 | 0.948 |
Seed SD about 0.03 (young deaths), 0.01 (75+ survivors).
## Reading
Excluding stays with documented comfort-measures-only or DNR/DNI in the first 24 h changed young-decedent death coverage by at most +0.5 pp and old-survivor coverage by at most +0.2 pp, well inside seed SD. The age pattern is therefore not driven by early documented treatment limitation.
## Limits
- Only the first 24 h are used; later orders (a common route to death with limitation) are not captured, so this is a partial test of the end-of-life explanation.
- Code-status charting is incomplete (fewer than 3% of stays carry a limitation entry), so many true limitation cases remain in the data.
- eICU not examined. Excluding stays changes the cohort (V5 removes 2.4% of stays).
