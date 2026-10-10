# Workflow — Phase by Phase

Each phase below maps to a folder and an expected output file. Work phases
in order; do not start Phase N+1 until Phase N's output file exists and has
been sanity-checked (row counts, no NaNs where not expected, outcome rate
looks clinically plausible, e.g. ICU mortality roughly 10–15%).

## Phase 1 — Environment + Cohort Setup
- Location: `src/data_processing/01_build_cohort.py`
- Input: `data/raw/mimic-iv/hosp/*.csv.gz`, `data/raw/mimic-iv/icu/*.csv.gz`
- Output: `data/processed/cohort.parquet`
- Logic: adult patients, ICU stay >= 24h, Sepsis-3 cohort (or all-cause ICU
  admission as a sensitivity cohort), one row per ICU stay, with outcome
  (in-hospital mortality), demographics (age, sex, race/ethnicity,
  insurance), and admission/ICU timestamps.

## Phase 2 — Feature Engineering
- Location: `src/data_processing/02_build_features.py`
- Input: `data/processed/cohort.parquet`, `data/raw/mimic-iv/icu/chartevents.csv.gz`
- Output: `data/processed/features.parquet`
- Logic: first-24h vitals (HR, BP, temp, RR, SpO2) and labs (lactate,
  creatinine, WBC, etc.), aggregated (min/max/mean) per ICU stay. Handle
  missingness explicitly (document % missing per feature before imputing).

## Phase 3 — Baseline Model + Standard Conformal Prediction
- Location: `src/models/03_train_baseline.py`, `src/conformal/03b_split_conformal.py`
- Output: `outputs/results/phase3_baseline_metrics.json`,
  `outputs/results/phase3_conformal_intervals.parquet`
- Logic: train/calibration/test split (e.g. 60/20/20), XGBoost classifier,
  then split conformal prediction on the calibration set to get per-patient
  prediction sets/intervals at a chosen nominal level (e.g. 90%).

## Phase 4 — Subgroup Coverage Audit (core contribution #1)
- Location: `src/evaluation/04_subgroup_coverage.py`
- Output: `outputs/tables/phase4_subgroup_coverage.csv`,
  `outputs/figures/phase4_coverage_by_group.png`
- Logic: empirical coverage of the Phase 3 intervals, broken down by race/
  ethnicity, sex, age-quartile, insurance status. Report coverage with
  binomial confidence intervals per subgroup.

## Phase 5 — Mondrian / Group-Conditional Conformal Prediction (core
contribution #2)
- Location: `src/conformal/05_mondrian_conformal.py`
- Output: `outputs/results/phase5_mondrian_intervals.parquet`,
  `outputs/tables/phase5_subgroup_coverage_corrected.csv`
- Logic: stratify calibration by subgroup (single and multi-attribute),
  recompute intervals, re-run the Phase 4 audit on the corrected intervals.

## Phase 6 — External Validation (eICU)
- Location: `src/evaluation/06_external_validation.py`
- Output: `outputs/tables/phase6_mimic_vs_eicu_coverage.csv`
- Logic: apply the MIMIC-IV-trained model + conformal calibration to eICU,
  compare internal vs external coverage overall and per subgroup. Include
  per-hospital-site breakdown where eICU site ID is available.

## Phase 7 — Trade-off Analysis + Write-up
- Location: `src/evaluation/07_tradeoff_analysis.py`, `paper/`
- Output: `outputs/figures/phase7_width_vs_fairness.png`,
  `paper/results_draft.md`
- Logic: quantify interval width / set size increase from Phase 3 → Phase 5
  per subgroup; draft Results and Discussion sections referencing the exact
  files above.

## When asked to "continue the research"
Default to the next incomplete phase in this list, in order. If asked to
redo a phase, archive the previous output file (append `_v1`, `_v2`, …)
rather than overwriting it, so earlier results used in the proposal/paper
are never silently lost.
