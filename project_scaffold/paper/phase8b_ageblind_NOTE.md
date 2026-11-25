# Phase 8b: age-blind model, calibration and coverage by age (MIMIC-IV, 100 seeds), 2026-11-25 [GENERATED — PENDING REVIEW]
Script `src/evaluation/08b_ageblind_calibration.py` (run in two chunks; merged to `outputs/tables/phase8b_ageblind_{rows,summary}_main_100.csv`). Replaces the earlier unsaved 10-seed check.
| Model | AUROC (all) | CITL 18-49 / 75+ | Death cov 18-49 / 75+ | Surv cov 18-49 / 75+ |
|---|---|---|---|---|
| with age | 0.8724 | +0.0013 / -0.0058 | 0.842 / 0.930 | 0.949 / 0.829 |
| age-blind | 0.8639 | +0.0254 / -0.0303 | 0.915 / 0.894 | 0.914 / 0.872 |
Gap metrics (two definitions): gap of seed-averaged coverage (Phase 8) 0.060/0.070 -> 0.015/0.027; per-seed max deviation averaged over seeds (includes noise) 0.064/0.071 -> 0.030/0.028 (placebo floor 0.026/0.009). Age-blind removes most but not all of the survivor-side gap (0.912 vs 0.872 residual 4 pp) and turns it into miscalibration by age.
