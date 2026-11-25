# Phase 12 — P(death | set), set-size equity and equalised-odds threshold baseline (100 seeds), 2026-11-24  [GENERATED — PENDING REVIEW]

Script `src/evaluation/12_utility_equity.py`; table `outputs/tables/phase12_utility_main_100.csv` (all strata, both datasets); `outputs/results/phase12_summary_main_100.json`.
Responds to review issues: no utility measures beyond coverage and set size; no equalised-odds threshold baseline. Primary model (66 predictors), alpha = 0.10, MIMIC internal (cal to test) and eICU (eICU-cal half to test half).

## Methods in brief
Per age stratum: set composition ({survive} only, {die} only, both, empty), mean set size, P(death | set) for each set type, and the share of deaths that received a {survive}-only set (missed-death share). Methods: pooled class-conditional conformal (cc_global); age x class Mondrian; equalised-odds baseline (age-specific risk thresholds giving sensitivity = specificity = 0.90 by plain empirical quantiles, no finite-sample correction); 10-bin risk Mondrian.

## 1. Mondrian by age is the equalised-odds post-processing rule
The equalised-odds thresholds and the age x class Mondrian conformal sets are identical for 99.2% of MIMIC test patients and 99.7% of eICU test patients (remaining differences come from the conformal finite-sample rank). So the "Mondrian repair" is group-specific thresholding to equal sensitivity and specificity; the paper must say this and cite Hardt et al. 2016 (verification of the reference still pending).

## 2. MIMIC-IV results by age (mean of 100 seeds)
| Method | Age | Set size | Singleton share | P(death given {survive}-only) | P(death given {die}-only) | Missed-death share |
|---|---|---|---|---|---|---|
| Pooled | 18-49 | 1.146 | 85.4% | 1.3% | 42.3% | 16.0% |
| Pooled | 50-64 | 1.223 | 77.7% | 1.7% | 43.0% | 12.9% |
| Pooled | 65-74 | 1.262 | 73.8% | 1.6% | 44.0% | 9.3% |
| Pooled | 75+ | 1.354 | 64.6% | 2.6% | 40.2% | 6.9% |
| Age Mondrian | 18-49 | 1.175 | 82.5% | 0.9% | 32.3% | 9.5% |
| Age Mondrian | 50-64 | 1.248 | 75.3% | 1.4% | 38.6% | 9.9% |
| Age Mondrian | 65-74 | 1.244 | 75.5% | 1.7% | 42.3% | 9.6% |
| Age Mondrian | 75+ | 1.376 | 62.4% | 3.2% | 47.0% | 9.8% |
| 10-bin risk Mondrian | 18-49 / 75+ | 1.835 / 1.769 | about 17-23% | 8.4% / 14.1% | 16.8% / 25.5% | 8.7% / 10.1% |
eICU (age Mondrian, 18-49 to 75+): set size 1.263 to 1.466; P(death given {survive}-only) 0.8% to 3.3%; P(death given {die}-only) 25.7% to 38.4%; pooled set size 1.264 to 1.443.

## 3. What this shows
1. Equalising death coverage equalises the missed-death share (about 10% in every age stratum, versus 16% for the youngest and 7% for the oldest under pooled calibration) but does not equalise predictive values. Behind a confident-survivor call the death rate is 0.9% in ages 18-49 and 3.2% in ages 75+; the confident-death call is right 32% of the time in the young and 47% in the old. Compared with pooled calibration, Mondrian lowers residual risk behind {survive}-only sets in the young (1.3% to 0.9%) and raises it in the old (2.6% to 3.2%), and makes the death call less precise in the young (42% to 32%). This is the expected trade-off when base rates differ and sensitivity and specificity are equalised (cf. Chouldechova 2017, Kleinberg et al. 2017; references pending verification).
2. Set-size inequity: older patients receive larger sets (MIMIC 1.15 to 1.35 pooled, 1.18 to 1.38 Mondrian; singleton share 85% to 65% pooled, 83% to 62% Mondrian). Mondrian changes this little; the gap in set size across age (about 0.2 labels) is as large as the coverage repair it buys. Age Mondrian slightly increases set size in three of the four strata (not in 65-74).
3. Race, sex and insurance differences in set size are small (race within 0.04 labels in MIMIC under both methods; sex 0.02; insurance 1.18-1.32, largely reflecting age mix) and P(death given {survive}-only) is 1.1-2.6% across race groups.
4. Risk-bin Mondrian gives near-equal set size across age (1.77-1.84) but only about 7-12% of patients receive a confident-survivor set, whose death rate is 8-14%, so it is not an attractive clinical rule; its equity comes from making sets uninformative.

## Limits
Singleton and set-size figures depend on alpha = 0.10, one model class and one split design; residual-risk figures are small-count in young strata (151 deaths per test split, so P(death given {survive}-only) of 0.9% rests on about 14 deaths); no decision-curve or net-benefit analysis was done; no clinician-defined thresholds. eICU values are for recalibrated eICU thresholds.
