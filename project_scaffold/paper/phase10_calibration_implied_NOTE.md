# Phase 10 — calibration-implied coverage test + synthetic demonstration (100 seeds), 2026-11-23  [GENERATED — PENDING REVIEW]

Scripts: `src/evaluation/10_calibration_implied_coverage.py`, `src/evaluation/10b_synthetic_demo.py`. Tables: `outputs/tables/phase10_cells_{main_100,harm_100}.csv`, `phase10_fit_{main_100,harm_100}.csv`, `phase10_synthetic_demo.csv`; `outputs/results/phase10_summary_{main_100,harm_100}.json`.
Responds to review issue M3 (mechanism partly circular/ecological): converts the mechanism statement into a label-free quantitative prediction that can fail.

## Identity
Let the pooled class-conditional rule include the death label iff p >= t_d (t_d = 1 - q_1) and the survivor label iff p <= t_s (t_s = q_0); these are sensitivity and specificity of two risk thresholds. If scores are calibrated inside stratum g (P(y=1 | p, g) = p) then, using only the stratum's scores,
  coverage of deaths(g)    = sum_g p 1[p >= t_d] / sum_g p
  coverage of survivors(g) = sum_g (1-p) 1[p <= t_s] / sum_g (1-p).
So with pooled thresholds, group coverage gaps are fully determined by each group's score distribution (hence base-rate/score-level differences), with no appeal to within-group AUROC. When a stratum is miscalibrated the identity fails, so residuals diagnose miscalibration.

## Synthetic demonstration (exactly calibrated scores, n = 200,000, pooled thresholds from half the data)
| Scenario | Group | Prevalence | AUROC | Death cov obs / pred | Survivor cov obs / pred |
|---|---|---|---|---|---|
| A base-rate shift (same logit spread) | young / mid / old | 0.090 / 0.154 / 0.249 | 0.842 / 0.836 / 0.832 | 0.783 / 0.891 / 0.951 vs 0.790 / 0.891 / 0.951 | 0.961 / 0.907 / 0.815 vs 0.961 / 0.908 / 0.814 |
| B equal prevalence (0.10), different spread | narrow / wide | 0.098 / 0.101 | 0.749 / 0.883 | 0.900 / 0.906 vs 0.899 / 0.908 | 0.900 / 0.898 vs 0.900 / 0.898 |
| C identical groups | g1 / g2 | 0.153 / 0.156 | 0.836 / 0.836 | 0.900 / 0.897 vs 0.900 / 0.898 | 0.901 / 0.901 vs 0.901 / 0.900 |
| D miscalibrated groups (score shifted +0.6 / -0.6 on the logit scale) | young / old | 0.089 / 0.248 | 0.842 / 0.833 | 0.892 / 0.902 vs 0.881 / 0.918 | 0.902 / 0.901 vs 0.918 / 0.878 |
Reading: in A, a coverage gap of 17 pp between groups arises with practically equal AUROC (0.83-0.84), and the label-free identity reproduces it to within about 1 pp. In B, large AUROC differences (0.75 vs 0.88) with equal prevalence produced essentially no gap (0.900 vs 0.906), so in these settings the location (base rate) of the score distribution, not discrimination per se, drives the gap. This is one parameter choice, not a general theorem: the identity says the gap depends on the whole score distribution. C is a null check. D shows the identity breaking when within-group calibration fails, as intended.

## Real data (mean over 100 seeds; strata cells: age, race, sex, insurance [MIMIC]; 103 eICU hospitals)
Fit measures per class: R2 vs nominal = 1 - SSE(obs - pred) / SSE(obs - 0.90), the share of the squared deviation from 0.90 explained by the label-free prediction; slope of observed gap on predicted gap; Spearman; RMSE against a binomial noise floor.
Survivor coverage (specificity side):
| Data | Cells | R2 (primary / harmonised) | Slope |
|---|---|---|---|
| MIMIC test, 15 strata | 15 | 0.953 / 0.954 | 0.97 / 1.03 |
| eICU demographics, raw scores | 11 | 0.17 / 0.45 | 1.23 / 1.28 |
| eICU demographics, eICU-recalibrated scores | 11 | 0.988 / 0.994 | 1.04 / 1.05 |
| eICU 103 hospitals, raw | 103 | 0.61 / 0.46 | 1.27 / 1.33 |
| eICU 103 hospitals, recalibrated | 103 | 0.917 / 0.930 | 1.05 / 1.06 |
Death coverage (sensitivity side):
| Data | Cells | R2 (primary / harmonised) | Slope | Spearman |
|---|---|---|---|---|
| MIMIC test, 15 strata | 15 | -0.19 / -0.46 | 0.76 / 0.64 | 0.85 / 0.75 |
| eICU demographics, raw | 11 | -3.2 / 0.985 | 0.36 / 0.92 | 0.78 / 0.97 |
| eICU 103 hospitals, raw | 103 | 0.50 / 0.41 | 0.98 / 0.99 | 0.74 / 0.59 |
Age strata, observed vs predicted (primary model): MIMIC death coverage 18-49 0.840 vs 0.810, 50-64 0.871 vs 0.847, 65-74 0.907 vs 0.865, 75+ 0.931 vs 0.922; survivor 0.949 vs 0.951, 0.925 vs 0.926, 0.911 vs 0.908, 0.830 vs 0.831. eICU harmonised death coverage 0.777 vs 0.768, 0.865 vs 0.855, 0.899 vs 0.899, 0.950 vs 0.955.

## Interpretation
1. Survivor-side gaps are almost entirely explained by the stratum's score distribution under the calibration identity (R2 0.95-0.99 in MIMIC and in eICU after recalibration, 0.92-0.93 across hospitals). With raw eICU scores the fit is much worse, as expected: eICU risk is over-predicted (CITL about +0.04 to +0.05, Phase 6), so the "calibrated" premise fails; recalibrating the weights restores it. This is the intended falsification test: when calibration fails, the prediction fails.
2. The death side is only partly explained. The ordering and direction are predicted well (Spearman 0.75-0.97 in demographic strata) but magnitudes are less accurate: in MIMIC the predicted death coverage is 2-4 pp below observed in all three age strata under 75 (same sign in each, 0.4-0.9 pp above in 75+), but the RMSE (0.027) is about the binomial noise floor (0.025) and the nominal-0.90 baseline (0.024), so R2 is negative and the deviations cannot be separated from sampling noise; in eICU-primary the young stratum is mispredicted (0.825 vs 0.882). Recalibrating the weights improved survivor predictions but worsened death predictions in eICU demographic strata (R2 -3.2 to -7.6 primary; 0.985 to 0.69 harmonised), so one logistic recalibration does not fix tail calibration. Death coverage depends on the low-score tail where decedents in low-risk groups lie, and small calibration errors at very low probabilities matter there. At hospital level, the prediction error (RMSE 0.037-0.045) is near the binomial noise floor (0.043), so the test cannot resolve more.
3. The prediction needs no AUROC and no labels beyond the calibration premise; what it shows is that, if scores are calibrated, pooled thresholds must produce the observed pattern. It does not by itself explain why the score distributions differ between age groups (the age-blind ablation in Phase 8 speaks to that).

## Limits and honest status
- A consistency test of calibration plus pooled thresholds, not a causal analysis; the premise is calibration within each stratum, which holds approximately for survivors and less so in the low-score tail.
- The eICU test uses thresholds fitted on all eICU patients (in-sample for the marginal threshold) and in-sample logistic recalibration for the weights; the hospital test is subject to binomial noise (20-320 deaths per hospital).
- Synthetic scenario B is a single parameter configuration.
- The eICU raw-score fit failing is a result about transport miscalibration, not evidence against the identity.
- Do not write "explains the gap" for death coverage in the paper; write "explains the survivor-side gap and the direction and ordering of the death-side gap".
