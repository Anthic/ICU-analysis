# Phase 6 + 7 — FINAL 100-seed results, 2026-11-22  [GENERATED — PENDING REVIEW BY AUTHOR]

100 seeds, alpha = 0.10, noflags XGBoost trained on MIMIC-IV. eICU: 95,558 patients, 8,885 deaths (9.30%), 207 hospitals (103 with >=100 pts and >=20 deaths). `main` = 66 predictors; `harm` = temperature, gcs_min, intubated removed (defined differently in eICU).
Files: `outputs/tables/phase6_*_{main_100,harm_100,main_100_hosp,harm_100_hosp}.csv`, `outputs/results/phase6_*`, `outputs/tables/phase7_*_{main_100,harm_100}.csv`, `outputs/results/phase7_summary_*`.
CIs: Wilson on mean per-seed counts (approximate; seeds reuse the same patients, so they are somewhat narrow). Seeds are not independent replications of new patients.

## 1. Pre-specified endpoints (ext_mimiccal_cc; replicated = Wilson upper bound < 0.90)
| | main | harm |
|---|---|---|
| P1 eICU death coverage, ages 18-49 | 0.902 [0.870, 0.926] -> NOT replicated | 0.819 [0.781, 0.852] -> replicated |
| P2 eICU survivor coverage, ages 75+ | 0.748 [0.741, 0.756] -> replicated | 0.677 [0.668, 0.685] -> replicated |
Hospital-disjoint eICU split gives the same numbers to the third decimal (P1 0.901/0.818; P2 0.748/0.677).
P2 is confounded with the overall survivor shortfall under transport (overall survivor coverage 0.835 main, 0.817 harm; death coverage 0.920/0.928): pure MIMIC->eICU transport over-covers decedents and under-covers survivors because the model over-predicts risk in eICU (CITL +0.042/+0.051; calibration slope 0.88/0.83; AUROC 0.834/0.810 vs MIMIC 0.873/0.847).

## 2. Age pattern after eICU recalibration (ext_eicucal_cc), death / survivor coverage
| Age | main | harm |
|---|---|---|
| 18-49 | 0.884 / 0.941 | 0.778 / 0.966 |
| 50-64 | 0.889 / 0.922 | 0.864 / 0.933 |
| 65-74 | 0.890 / 0.907 | 0.899 / 0.903 |
| 75+ | 0.919 / 0.844 | 0.950 / 0.820 |
Same direction as MIMIC internal (0.84/0.95 ... 0.93/0.83), also under hospital-disjoint splits (18-49 death 0.881 main, 0.776 harm). Young decedents and old survivors are under-covered in a second database; the gap is much stronger in the harmonised model than in `main`.

## 3. Mondrian (group x class) calibrated on eICU
Age strata: death and survivor coverage 0.898-0.903 in every stratum, both models, both split types. Confirms the by-construction repair in a second database.

## 4. Hospitals
SD of hospital death coverage under MIMIC thresholds: 0.045 (main) / 0.042 (harm) vs 0.039 expected from binomial noise alone: modest excess heterogeneity.

## 5. Mechanism (Phase 7; global class-conditional thresholds; ecological)
- Hospitals (n=103): death-coverage gap vs mean predicted risk among decedents Spearman 0.79 (main) / 0.70 (harm); vs hospital AUROC 0.42 / 0.43; prevalence 0.23 / 0.08. Joint OLS (standardised): +1 SD AUROC -> +0.021 / +0.027 death coverage, +1 SD prevalence -> +0.013; R2 0.22 / 0.30.
- Demographic strata (15 MIMIC, 11 eICU): prevalence tracks death-coverage gap (MIMIC 0.89 main / 0.79 harm; eICU 0.42 [n.s.] main / 0.83 harm). AUROC is NEGATIVELY associated (MIMIC -0.45 n.s. / -0.60; eICU -0.36 n.s. / -0.72): the young have the highest AUROC but low base risk, so their decedents score low.
- Interpretation: calibrated scores + group-specific base rates + one pooled threshold => unequal class-conditional coverage, independent of within-group discrimination. At site level better discrimination protects decedent coverage. Age, prevalence and AUROC are collinear across only 4 age strata: suggestive, not causal. In `main` the eICU demographic correlations are not significant, so the mechanism is solid in MIMIC and eICU-harm but weaker in eICU-main.

## 6. Small-stratum rule (hospital-specific vs global thresholds, death coverage, main; harm nearly identical)
| calibration deaths | hospital-seeds | infinite threshold | global mean abs dev | hospital-specific mean abs dev | hosp-specific share <0.80 |
|---|---|---|---|---|---|
| <10 | 3309 | 84% | 0.089 | 0.101 | 0.03 (full sets, mean cov 0.98) |
| 10-19 | 3898 | 0% | 0.075 | 0.086 | 0.10 |
| 20-39 | 3413 | 0% | 0.057 | 0.061 | 0.07 |
| 40-79 | 1941 | 0% | 0.046 | 0.047 | 0.04 |
| 80+ | 1383 | 0% | 0.030 | 0.032 | 0.01 |
Group-specific thresholds do not beat the pooled one in deviation from 0.90 at any size here; they only match it from ~40+ calibration deaths. Rule for the paper: use group x class calibration only with >= ~40 calibration deaths in the cell (hard floor ~20), else fall back to the pooled threshold and report set sizes. Note: this compares noise around 0.90 for hospitals as groups; for the age/race strata used in the paper (hundreds of deaths) Mondrian is by-construction valid.

## 7. What can go in the paper / what must be said
- Replicated: age gap direction in eICU; Mondrian repair; transport shift (survivor shortfall) under MIMIC thresholds.
- Not replicated: P1 in `main` (0.902). Must be reported as such, with the harmonised result as sensitivity analysis, not as a substitute.
- Not available in eICU: insurance. Race categories differ. eICU is 2014-15.
- Do not claim causality for the mechanism; present as an explanation consistent with calibration + base-rate heterogeneity, with the stratum count caveat.
