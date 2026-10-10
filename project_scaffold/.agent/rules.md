# Coding Rules

## Language & libraries
- Python 3.10+, pandas, numpy, scikit-learn, xgboost.
- Conformal prediction: prefer `mapie` or `crepes`; if a needed method isn't
  available in either, implement it manually in `src/conformal/` with a
  docstring citing the paper/algorithm it follows.
- Use `pyarrow`/parquet for all intermediate data, not CSV, once past
  Phase 1 raw ingestion (faster, preserves dtypes).

## Style
- One script = one phase step (see workflow.md numbering). No notebook-only
  results feed into the paper.
- Every script takes no required CLI args for the default run (sensible
  defaults), but accepts `--sample N` for quick smoke-testing on a subset.
- Set and log `random_state=42` (or project-wide seed) everywhere a split or
  stochastic model is used.
- Print a short summary block at the end of every script: rows in, rows out,
  key metric(s), path(s) written.

## Statistics / ML correctness checks (ask before skipping any of these)
- Train / calibration / test sets must be disjoint at the patient level
  (subject_id), not just the stay level, to avoid leakage from repeat ICU
  admissions of the same patient.
- Report coverage with a confidence interval (e.g. Wilson score interval),
  not just a point estimate — subgroup sample sizes can be small.
- Before claiming a coverage gap is fixed in Phase 5, confirm it on a held-
  out test set never used for Mondrian calibration, not the calibration set
  itself.
- Any accuracy/AUROC number reported in the paper must come from the test
  set only.

## Data hygiene
- Never print or log raw PHI-adjacent values (dates, free text, exact ages
  over 89, subject_id) to stdout in shared logs — aggregate first.
- Document every exclusion criterion applied to the cohort with the row
  count before/after, saved to `outputs/results/phase1_exclusion_flow.csv`
  (a CONSORT-style flow is expected in the paper).
