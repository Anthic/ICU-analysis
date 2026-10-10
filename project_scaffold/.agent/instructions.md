# Agent Instructions — ICU Conformal Fairness Research Project

## Project Goal
Build a reproducible research pipeline for the paper:
"Group-Conditional Conformal Prediction for Equitable Uncertainty Quantification
in ICU Mortality Risk Prediction: A MIMIC-IV / eICU-CRD Study"

Research question: Does standard conformal prediction give equal coverage
across demographic subgroups (race, sex, age, insurance status) for ICU
mortality risk prediction? If not, can group-conditional (Mondrian) conformal
prediction fix it, and at what cost (interval width / efficiency)?

## Non-negotiable rules
1. NEVER modify files under `data/raw/`. Treat raw MIMIC-IV / eICU files as
   read-only source of truth. All transformations write to `data/processed/`.
2. Always split data into train / calibration / test BEFORE any model fitting.
   The calibration set must never be touched during model training, and the
   test set must never be touched until final evaluation. Leakage between
   these three sets invalidates the whole paper — treat this as a hard rule.
3. Every script must be runnable from the project root with a single command
   and must log (print or write to `outputs/results/`) what it did, how many
   rows it processed, and how long it took.
4. Every analysis that produces a number used in the paper must be
   reproducible: save the script, the random seed, and the output together.
5. Do not install packages outside `requirements.txt`. If a new package is
   needed, add it to `requirements.txt` with a pinned version and explain why
   in the commit/PR description.
6. Keep PHI-adjacent columns (subject_id, hadm_id, stay_id, dates) out of
   anything written to `outputs/` or `paper/` — only aggregated/statistical
   results leave the `data/` and `src/` boundary.

## Folder responsibilities (read this before creating any file)
- `data/raw/` — untouched MIMIC-IV (`hosp/`, `icu/`) and eICU source files.
- `data/processed/` — cleaned, merged, feature-engineered tables (parquet/csv).
- `src/data_processing/` — cohort building, feature engineering, missing data.
- `src/models/` — base ML model training (e.g., XGBoost mortality model).
- `src/conformal/` — split conformal, Mondrian/group-conditional conformal,
  coverage diagnostics.
- `src/evaluation/` — subgroup coverage audit, calibration, trade-off
  analysis, cross-institutional (MIMIC→eICU) comparisons.
- `notebooks/` — exploratory work only. Anything that produces a result used
  in the paper must be promoted to a script in `src/` before being trusted.
- `outputs/figures/`, `outputs/tables/`, `outputs/results/` — all generated
  artifacts, named with the phase number prefix (see workflow.md).
- `paper/` — manuscript drafts, references, proposal docs.

## How to work on a task
1. Read `.agent/workflow.md` and `.agent/decisions.md` (institutional memory & clinical rationale).
2. Check `data/processed/` and `outputs/results/` for existing outputs before
   recomputing anything expensive (chartevents-derived features especially).
3. Write or edit the relevant script under `src/<module>/`.
4. Run it, confirm it completes without errors, and save its output under
   `outputs/` with a clear filename (e.g. `phase4_subgroup_coverage.csv`).
5. Summarize what changed and what the numeric result was before moving on.

## Definition of done for this project
- Phase 1–3 (cohort, features, baseline model + standard conformal
  prediction) reproduce coverage close to the nominal target (e.g. ~90%)
  marginally, but may NOT hold within every subgroup — that gap is expected
  and is the paper's main finding, not a bug to "fix" by tuning.
- Phase 4 explicitly reports per-subgroup coverage with confidence intervals.
- Phase 5 (Mondrian conformal) must restore subgroup coverage close to
  nominal for every reported subgroup, or the shortfall must be explained.
- Phase 6 (eICU external validation) must report both MIMIC-IV (internal)
  and eICU (external) subgroup coverage side by side.
- Phase 7 must report the width/efficiency cost of the fairness correction.
