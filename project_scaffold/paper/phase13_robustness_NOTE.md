# Phase 13 — robustness of the age coverage pattern: temporal split, second model, alpha sweep, placebo (MIMIC-IV), 2026-11-24  [GENERATED — PENDING REVIEW]

Script `src/evaluation/13_robustness.py` (`--part temporal|logistic|alpha|placebo`); tables `outputs/tables/phase13_{part}_{rows,summary}_*.csv`; gap summaries `outputs/results/phase13_{part}_gaps_*.json`. Responds to review issues: single model, single alpha, no temporal split, no placebo.
Metric: "max age gap" = per-seed largest absolute deviation of age-stratum coverage from 1 - alpha, averaged over seeds (this includes sampling noise, so it is larger than the gap of seed-averaged coverage used in Phase 8; compare variants only within this phase). Pooled = pooled class-conditional conformal; Mondrian = age x class.

## 1. Temporal split (train 2008-2013 [24,202], calibrate 2014-2016 [10,594], test 2017-2022 [17,042]; XGBoost, 20 training seeds on ONE fixed split)
Test AUROC 0.879, prevalence 11.4%. Pooled class-conditional coverage by age (death / survivor): 18-49 0.870 / 0.947; 50-64 0.884 / 0.923; 65-74 0.931 / 0.906; 75+ 0.935 / 0.827; overall 0.914 / 0.897. Max age gap 0.041 (deaths), 0.073 (survivors) - the same pattern as in random splits. For test years 2020-2022 only: 18-49 0.863 deaths, 75+ 0.823 survivors, overall survivor coverage 0.890.
Age Mondrian under the temporal shift: survivor coverage 0.894-0.903 by age (max gap 0.009) but death coverage 0.952 (18-49), 0.898, 0.912, 0.919 (max gap 0.052): the group-level guarantee is not restored for deaths in the youngest stratum when the calibration period precedes the test period (also higher mortality in 2020-2022, 12.8%).
Limitation: one temporal split; seed SDs reflect training randomness only; no patient bootstrap.

## 2. Second model class (L2 logistic regression with median imputation and standardisation; 100 random splits; AUROC 0.818)
Pooled coverage by age (death / survivor): 18-49 0.799 / 0.958; 50-64 0.859 / 0.933; 65-74 0.912 / 0.907; 75+ 0.947 / 0.817. Max age gap 0.102 / 0.083, larger than XGBoost (0.065 / 0.071 in the alpha run). Age Mondrian: coverage 0.899-0.903, max gap 0.039 / 0.013, mean set size 1.44 vs 1.41 pooled (18-49 1.32, 75+ 1.53). The pattern is not specific to gradient boosting; it is stronger for the less discriminative linear model.

## 3. Alpha sweep (XGBoost, 100 splits, pooled; death / survivor coverage in ages 18-49 and 75+)
| alpha | overall | 18-49 | 75+ | max age gap (deaths / survivors) | Mondrian max gap |
|---|---|---|---|---|---|
| 0.05 | 0.950 / 0.950 | 0.906 / 0.973 | 0.973 / 0.916 | 0.048 / 0.035 | 0.026 / 0.008 |
| 0.10 | 0.901 / 0.900 | 0.840 / 0.949 | 0.931 / 0.830 | 0.065 / 0.071 | 0.036 / 0.012 |
| 0.15 | 0.851 / 0.850 | 0.785 / 0.925 | 0.886 / 0.749 | 0.072 / 0.101 | 0.046 / 0.014 |
| 0.20 | 0.802 / 0.800 | 0.734 / 0.900 | 0.839 / 0.672 | 0.075 / 0.128 | 0.052 / 0.016 |
The direction is the same at every alpha; the survivor-side gap grows from 3.5 to 12.8 points as alpha increases (more patients fall below the survivor threshold in older strata), and set size drops from 1.43 to 1.02 labels.

## 4. Placebo tests (XGBoost, 100 splits, pooled; max age gap deaths / survivors)
- Full model 0.065 / 0.071.
- Permuted age labels (random groups of the same sizes; the null): 0.026 / 0.009; coverage 0.898-0.903 in every placebo group. This is the noise floor of the metric: the survivor-side age gap is about 8 times the null, the death-side gap about 2.5 times.
- Dropping one random non-age predictor (a different one each split): 0.065 / 0.071, i.e. no change.
- Dropping age (age-blind): 0.028 / 0.028, i.e. reduced to near the noise floor (death side 0.028 vs null 0.026). Note: in this within-phase metric the age-blind reduction is 57% (deaths) and 61% (survivors), consistent with the earlier 60-75% range but not larger; age-blind in eICU was weaker (Phase 8).
Hence the reduction is specific to removing age, not to removing any predictor.

## Reading for the paper
1. The age pattern (young decedents and elderly survivors under-covered with pooled thresholds) survives a temporal split, a different model class, every alpha tested (0.05-0.20), and is absent under permuted age labels; it is removed by dropping age but not by dropping a random predictor.
2. Under temporal shift the age Mondrian calibration does not fully restore coverage (young deaths 0.952), so the Mondrian group-level guarantee needs exchangeability between calibration and test periods.
3. Caveats: single temporal split; one non-boosting model; alpha sweep and placebo on one dataset (MIMIC-IV); the max-gap metric includes sampling noise, so use the placebo value as its floor.
