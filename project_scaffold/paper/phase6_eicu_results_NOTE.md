# Phase 6 (eICU-CRD) — first-pass results, 2026-11-22  [GENERATED — PENDING REVIEW]

20 seeds, patient-level eICU 50/50 split, alpha = 0.10, noflags model. Exploration run (not the final 100-seed run).
eICU cohort: 95,558 patients, 8,885 deaths (9.30 %), 207 hospitals. Insurance is not available in eICU.
Source: `outputs/tables/phase6_mimic_vs_eicu_coverage_{main,harm}.csv`, `outputs/results/phase6_model_performance_{main,harm}.csv`, `phase6_summary_{main,harm}.json`.
`main` = same 66 predictors as Phase 3. `harm` = harmonised sensitivity model: temperature, gcs_min and intubated removed (they are defined/measured differently in eICU: temperature 89 % missing vs 3 % in MIMIC; GCS mean 12.6 vs 9.8; intubated 18 % vs 45 %).
CIs are Wilson intervals computed on mean per-seed counts (approximate; seeds reuse the same patients).

## 1. Model transport
| | MIMIC test | eICU (main) | eICU (harm) |
|---|---|---|---|
| AUROC | 0.873 | 0.834 | 0.810 |
| Calibration slope | 1.01 | 0.88 | 0.84 |
| CITL (mean pred - prevalence) | -0.003 | +0.041 | +0.051 |

## 2. Overall coverage (death / survivor)
| Config | main | harm |
|---|---|---|
| internal MIMIC, class-conditional | 0.902 / 0.901 | 0.901 / 0.900 |
| eICU, MIMIC thresholds (pure transport) | 0.917 / 0.838 | 0.926 / 0.817 |
| eICU, eICU-recalibrated class-conditional | 0.901 / 0.900 | 0.899 / 0.900 |

Pure transport leaves survivors under-covered (risk over-prediction in eICU); eICU recalibration restores overall coverage.

## 3. Pre-specified endpoints (config ext_mimiccal_cc)
- P1 (ages 18-49 death coverage): main 0.900 (not below 90 %); harm 0.818 [0.780, 0.851].  -> NOT replicated in `main`; replicated in `harm`.
- P2 (ages 75+ survivor coverage): main 0.753 (Wilson upper 0.761); harm 0.678.  -> replicated in both, but confounded by the overall survivor shortfall under transport.

## 4. Age pattern after eICU recalibration (ext_eicucal_cc), death / survivor coverage
| Age | MIMIC internal (main) | eICU main | eICU harm |
|---|---|---|---|
| 18-49 | 0.841 / 0.949 | 0.883 / 0.942 | 0.781 / 0.965 |
| 50-64 | 0.872 / 0.925 | 0.889 / 0.922 | 0.862 / 0.932 |
| 65-74 | 0.907 / 0.911 | 0.889 / 0.905 | 0.895 / 0.902 |
| 75+ | 0.931 / 0.829 | 0.919 / 0.845 | 0.951 / 0.821 |
(MIMIC internal values: Phase 4 CSV; eICU: this run.) The direction replicates in every column: young decedents under-covered, old survivors under-covered. In `main` the individual eICU death-coverage CIs for 18-49/50-64/65-74 include 0.90 or sit just under it; in `harm` 18-49 and 50-64 are clearly below 0.90.

## 5. Mondrian class-conditional calibrated on eICU (ext_eicucal_mondrian_cc, main)
All age, race and sex strata have mean death and survivor coverage 0.89-0.91 (Asian/Hispanic wide CIs, ~84/176 deaths per test half). Confirms the by-construction repair in a second database.

## 6. Hospitals (MIMIC thresholds, 103 hospitals with >=100 patients and >=20 deaths)
SD of hospital-level death coverage 0.046 (main) / 0.044 (harm) vs 0.039 expected from binomial noise alone: modest excess site heterogeneity.

## 7. Caveats to carry into the paper
- Main-model comparison is affected by definitional differences in GCS/intubation/temperature; the harmonised model is the cleaner replication test and also shows the gap is larger when discrimination is lower (AUROC 0.81 vs 0.83).
- This is a 20-seed exploratory run; the final 100-seed run (and `--split hospital`) is still to do.
- Random 50/50 eICU split shares hospitals between calibration and test halves; `--split hospital` is the stricter test.
- eICU outcome/race coding and 2014-2015 era differ from MIMIC.
