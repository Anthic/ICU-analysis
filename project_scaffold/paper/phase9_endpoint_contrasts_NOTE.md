# Phase 9 — P1/P2 as stratum-minus-overall contrasts, hospital-cluster bootstrap (100 seeds), 2026-11-23  [GENERATED — PENDING REVIEW]

Script `src/evaluation/09_endpoint_contrasts.py`; tables `outputs/tables/phase9_endpoint_contrasts_{main_100,harm_100}.csv`; `outputs/results/phase9_summary_{main_100,harm_100}.json`.
Responds to review issues: the absolute-coverage endpoints mixed the age effect with the overall transport shift; Wilson CIs ignored hospital clustering and reuse of the same patients across seeds.

## Definition
contrast(stratum, class) = coverage(stratum, class) minus coverage(all eICU patients, same class). Configurations: (transport) MIMIC-IV thresholds applied to all eICU patients; (recalibrated) class-conditional thresholds from an eICU calibration half, evaluated on the other half (patient split). Uncertainty: two-level bootstrap, 2000 draws, resampling the 207 hospitals and the 100 model seeds; percentile 95% CI; a Bonferroni CI over 8 contrasts (age stratum x class, per configuration) is also in the CSV. "Seed-only" intervals (hospitals fixed) are in the CSV to show how much clustering widens the uncertainty.
IMPORTANT STATUS: this contrast version was defined AFTER the absolute-coverage endpoint P1 failed in the primary model; it is a revised, post-hoc analysis (justified by the transport-shift confound), not the original pre-specified endpoint. Report it as such and keep the absolute-coverage results alongside. Revised replication rule used here: upper 95% bound < 0.

## Results (point estimate [95% cluster-bootstrap CI], percentage points)
| Config | Endpoint | Primary (66 predictors) | Harmonised (63 predictors) |
|---|---|---|---|
| Transport | P1: ages 18-49, death coverage minus overall | -1.9 [-3.4, -0.5] | -11.0 [-12.9, -9.3] |
| Transport | P2: ages 75+, survivor coverage minus overall | -8.6 [-9.3, -7.9] | -14.0 [-14.8, -13.2] |
| eICU-recalibrated | P1 | -1.8 [-3.5, -0.2] | -12.2 [-14.2, -10.3] |
| eICU-recalibrated | P2 | -5.6 [-6.1, -5.1] | -8.0 [-8.6, -7.4] |
Replicated by the upper-bound-below-0 rule in all eight cells. Caveats: (i) primary-model P1 is small (about -2 pp) and its Bonferroni-adjusted CI (8 contrasts) crosses zero (transport [-4.1, +0.1], recalibrated [-4.3, +0.4]); (ii) this is the same direction as in MIMIC (84% vs 90%) but a much smaller magnitude than in MIMIC; (iii) the harmonised model shows large effects (-11 to -12 pp), so the young-decedent gap is strongly model-dependent; (iv) P2 effects are large and clear in both models.

## Other strata (transport, contrast in pp; CI excludes 0 unless noted)
Primary: ages 18-49 survivors +6.5, 50-64 deaths -1.1 / survivors +3.6, 65-74 deaths -1.0 / survivors +0.7, 75+ deaths +1.6. Harmonised: 50-64 deaths -2.7, 65-74 about 0 (CI includes 0), 75+ deaths +4.1. The age ordering is monotone in both models.

## Clustering effect
Seed-only CIs are 0.1-0.3 pp wide; cluster CIs are 1-3 pp wide for death contrasts (primary 18-49: [-2.1, -1.6] seed-only vs [-3.4, -0.5] cluster). Ignoring clustering would have overstated precision by about 2 to 8.5x (about 5x for primary P1). Hospital resampling also reflects patient sampling within hospitals, but not model-training variation beyond the seed resampling.

## Reading for the paper
1. State the age pattern replicates in direction in eICU with cluster-aware CIs, with magnitude model-dependent: small (about -2 pp) in the primary model, large (-11 to -12 pp) in the harmonised model.
2. Do not call P1 "replicated" without saying that the absolute-coverage version failed in the primary model and the contrast version is a post-hoc revision with a small effect.
3. P2 is robust once the transport shift is removed (-8.6 / -14.0 pp).
