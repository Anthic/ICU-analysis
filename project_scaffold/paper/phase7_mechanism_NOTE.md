# Phase 7 (mechanism + small-stratum stability) — first pass, 2026-11-22  [GENERATED — PENDING REVIEW]

20 seeds, alpha = 0.10, global class-conditional thresholds, noflags model. Exploratory; not for the paper until the final run.
`main` = 66 predictors; `harm` = temperature, gcs_min, intubated removed.
Script: `src/evaluation/07_mechanism_analysis.py`. Tables: `outputs/tables/phase7_*_{main,harm}.csv`, `outputs/results/phase7_summary_{main,harm}.json`.
Thresholds: MIMIC = MIMIC calibration split -> MIMIC test. eICU = class-conditional thresholds fit on ALL eICU (target-domain marginal threshold; so remaining gaps are heterogeneity, not transport shift).

## A. What explains the stratum coverage gap?
**Demographic strata (15 in MIMIC, 11 in eICU; ecological, small n).**
- The age gradient is the whole story: 18-49 -> 75+ death coverage 0.85 -> 0.93 (MIMIC), 0.88 -> 0.92 (eICU main), 0.78 -> 0.95 (eICU harm); survivor coverage 0.95 -> 0.83 / 0.94 -> 0.85 / 0.97 -> 0.82. Race and sex strata stay within about 0.89-0.92 (except small MIMIC strata with wide uncertainty).
- Stratum prevalence tracks death-coverage gap (Spearman 0.85 MIMIC, 0.54 eICU main [p=0.09], 0.85 eICU harm). Within-stratum AUROC does NOT explain it in the expected direction: Spearman -0.30 (n.s.) / -0.38 (n.s.) in main, -0.58 / -0.64 in harm (negative = higher AUROC goes with LOWER death coverage). Reason: young patients have the HIGHEST AUROC but low baseline risk, so their decedents have low scores (mean predicted risk among deaths 0.31 young vs 0.38 old in eICU harm) while their survivors have very low scores.
- Mechanism that fits: the score distribution is calibrated to a group-specific base rate while one pooled threshold is used. Low-base-rate groups: decedents sit lower on the score scale -> excluded from the "death" prediction set more often; survivors are very safe. High-base-rate groups: the reverse (survivors' scores are high -> survivor coverage drops). So the problem is baseline-risk heterogeneity combined with pooled class-conditional thresholds, not worse discrimination in the affected group.
- CAUTION: with 4 age strata, prevalence, AUROC and age are collinear; this is suggestive, not causal. Do not write "AUROC does not matter".

**Hospitals (eICU, 103 sites with >=100 patients and >=20 deaths; more informative, n=103).**
- Death-coverage gap correlates with hospital-level mean predicted risk among decedents (Spearman 0.78 main, 0.69 harm; p < 1e-14) and with hospital AUROC (0.42 / 0.45; p < 1e-5); prevalence adds little (0.23 main, 0.06 harm).
- Joint OLS (standardised, 103 hospitals): +1 SD hospital AUROC -> +0.021 (main) / +0.028 (harm) death coverage (SE 0.004-0.005); +1 SD prevalence -> +0.012. R2 = 0.21 / 0.31. SD of the hospital gap is 0.051. So at site level, better discrimination protects decedent coverage, which is the opposite sign from the demographic-strata picture. Both effects can be true: coverage follows where decedents sit on the score scale, and that depends on discrimination AND base rate.
- Corrects my earlier hint in the Phase 6 note: "gap larger when AUROC lower" was a model-level contrast (main vs harm); within demographic strata AUROC is not the driver.

## B. Small-stratum stability (hospital-specific class-conditional thresholds vs global eICU thresholds; patient split)
Per seed x hospital, test deaths >= 5 and survivors >= 20; calibration deaths binned. Death coverage, `main`:
| calibration deaths | hospital-seeds | share with infinite threshold | global mean abs dev | hospital-specific mean abs dev | hospital-specific share <0.80 | hospital-specific mean cov |
|---|---|---|---|---|---|---|
| <10 | 673 | 0.86 | 0.087 | 0.103 | 0.03 | 0.984 (trivially full sets) |
| 10-19 | 773 | 0 | 0.073 | 0.083 | 0.09 | 0.927 |
| 20-39 | 686 | 0 | 0.058 | 0.063 | 0.09 | 0.913 |
| 40-79 | 388 | 0 | 0.046 | 0.045 | 0.04 | 0.908 |
| 80+ | 279 | 0 | 0.030 | 0.034 | 0.01 | 0.905 |
`harm` is almost identical.
Reading: group-specific thresholds do not beat the global threshold in deviation from 0.90 until a group has roughly 40+ calibration deaths; below ~20 deaths the death threshold is infinite or wildly noisy (coverage reached only by returning uninformative full sets, ~0.98). Proposed working rule (to be re-checked on the 100-seed run and MIMIC subgroups): only use group-by-class calibration when the group has >= ~40 calibration deaths (>= ~20 as the absolute floor); otherwise fall back to the pooled threshold and report set size.
Note: the table compares deviation from 0.90 in hospital-seeds; hospital-seed rows are not independent across seeds.

## Implications for the paper
1. The age gap is explained by calibrated base-rate differences meeting a pooled threshold; this is a testable, general mechanism and a better contribution than "we found a gap".
2. Site-level heterogeneity in eICU is partly explained by site AUROC and decedent score level.
3. The Mondrian fix needs a minimum-stratum rule; the 20-seed data support about 40 deaths.

## Limits
Ecological correlations on few strata; collinearity of age/prevalence/AUROC; 20 seeds on the same patients; eICU feature definitions differ (see Phase 6 note); not yet run on hospital-disjoint splits.
