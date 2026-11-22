# Phase 8 — risk-bin baseline and age-blind ablation (100 seeds), 2026-11-22  [GENERATED — PENDING REVIEW]

Script `src/evaluation/08_alternatives_ablation.py`; tables `outputs/tables/phase8_alternatives_main_100.csv`; `outputs/results/phase8_summary_main_100.json`.
Primary 66-predictor model (age-blind = anchor_age removed). alpha = 0.10, 100 seeds, MIMIC internal (cal -> test) and eICU (eICU-cal half -> eICU-test half, patient split). Seeds reuse the same patients; seed SD omitted here.
Variants: cc_global (class-conditional, pooled), mondrian_age (age x class), riskbin5 / riskbin10 (predicted-risk-bin x class, quantile bins from the calibration set; no demographic attribute used).

## A. Risk-bin Mondrian (works without demographic attributes) vs age Mondrian
Max absolute deviation from 0.90 over the four age strata (death / survivor coverage), and mean set size:
| dataset | cc_global | mondrian_age | riskbin5 | riskbin10 |
|---|---|---|---|---|
| MIMIC | 0.060 / 0.070, size 1.256 | 0.005 / 0.001, size 1.271 | 0.006 / 0.023, size 1.732 | 0.013 / 0.016, size 1.795 |
| eICU | 0.019 / 0.056, size 1.352 | 0.003 / 0.001, size 1.362 | 0.007 / 0.012, size 1.717 | 0.006 / 0.006, size 1.770 |
Singleton share: 0.74 (cc_global), 0.73 (age Mondrian), 0.21-0.27 (risk-bin) in MIMIC.
Reading: calibrating by predicted-risk bin x class largely closes the age gap without using age (useful when the attribute is unavailable or should not be used), but costs about +0.5 labels per patient (singleton share falls from ~74% to ~21-27%). Age x class Mondrian reaches a smaller gap at almost no set-size cost (+0.015 in MIMIC), so the attribute-based fix is far more efficient. Use of a risk-bin alternative must therefore be reported with its set-size cost.

## B. Age-blind ablation (age removed from predictors), pooled class-conditional thresholds
Max absolute age-stratum deviation from 0.90 (death / survivor): MIMIC 0.060 / 0.070 with age -> 0.015 / 0.027 age-blind; eICU 0.019 / 0.056 -> 0.013 / 0.027. The age gap shrinks by roughly 60-75% when the age feature is removed; the residual is mainly 75+ survivors (0.873 MIMIC, 0.879 eICU).
Cost and caveat (10-seed check, MIMIC test): overall AUROC 0.874 -> 0.866; calibration-in-the-large by age with age removed: 18-49 +0.023, 50-64 +0.007, 65-74 -0.001, 75+ -0.030 (with age: about 0 in all strata); AUROC 75+ 0.829 -> 0.819.
Reading: a large part of the age coverage gap arises because the model itself uses age to shift scores by base rate; removing age equalises coverage but makes risk estimates miscalibrated by age (over-prediction in the young, under-prediction in the old). Coverage parity is therefore not calibration parity; do not recommend dropping age.

## Implications
1. Strengthens the mechanism claim with an intervention-type ablation: removing the base-rate-carrying feature shrinks the gap (supports that the gap follows base-rate-shifted scores under a pooled threshold, not within-group discrimination). Still not a formal causal proof: age also correlates with physiology.
2. Answers the likely reviewer request for a risk-conditioned baseline (cf. the 2026 missingness-aware Mondrian preprint, which found risk-based calibration gives smaller gaps): here it equalises coverage but is much less efficient than attribute-based Mondrian.
3. Reporting: show both coverage and calibration-by-group when discussing age-blind models.
