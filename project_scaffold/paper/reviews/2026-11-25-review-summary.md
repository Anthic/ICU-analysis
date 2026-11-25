# Collated review summary, 2026-11-25 (constructive + adversarial, code access)
Verdict from both reviewers: MAJOR REVISION, good prognosis. Number audit: about 54 numbers checked, 2 mismatches (predictor counts; "hospital-disjoint third decimal").

## Major issues (merged, need decision: accept / reject / defer)
| ID | Issue | Source | Proposed action |
|---|---|---|---|
| R1 | Predictor count wrong: text says 66/63, code/JSON give 52/47; Sec 2.2 lists hemoglobin, chloride not in feature set; `intubated` is a GCS-verbal airway proxy, not ventilation | both | Fix text, rename variable in prose |
| R2 | Mechanism = identity; fits survivors (R2 0.95-0.99) but fails deaths (R2 -0.19 MIMIC, -3.2/-7.6 eICU); eICU death values and raw/recalibrated mix in Fig 4 not reported; abstract overclaims | both | Report all values, tone down "explains", fix Fig 4 |
| R3 | Age mechanism rests on 4 collinear strata (effective n ~4); AUROC-gap sign flips strata vs hospitals; alternative explanations (case-mix, treatment limitation) untested | both | Add limitation + discuss; no new test |
| R4 | Replication: P1 failed pre-planned rule in primary model (0.902); contrast rule set afterwards; Bonferroni interval crosses 0; multiplicity family ~32; plan and outputs share one git commit | both | State openly as post hoc/exploratory; deposit plan with external timestamp |
| R5 | Mondrian "repair" true by construction; temporal split over-covers young deaths (0.952) and death-side max gap worse (0.052 vs 0.041), absent from abstract | adversarial | Put in abstract + limitations |
| R6 | Novelty incremental: Mondrian = EO thresholds (99.2/99.7% identical); missing refs Sadinle 2019, Gibbs 2023, Jung 2023, Zhou-Sesia 2024, clinical fair-CP; Discussion comparison unwritten | both | Reframe as proposition + proof + test; add refs; write comparison |
| R7 | EO equivalence mislabelled (two one-sided rules, not Hardt's single predictor) and inexact (interpolated quantile vs conformal order statistic) | both | Reword; add unit test |
| R8 | Uncertainty: seed SD mostly test-sampling noise; patient bootstrap ignores model/calibration variance; eICU Wilson CIs ignore clustering; "5-10x wider" is really 2.1-8.5x; "third decimal" claim false for recalibrated | both | Correct statements |
| R9 | Max-gap metric noise floor (0.026/0.009); two versions of same quantity (Phase 8 vs 13) ; age-blind shrinkage 60-75% only MIMIC (eICU 32%/52%); age-blind CITL numbers from an unsaved 10-seed check | both | Floor-correct, harmonise, save script/output |
| R10 | End-of-life: code-status section pending; paired-difference SD 4-5 pp so "size not direction" unsupported; LOS>=24h selection not discussed | adversarial | Run code-status or mark as limitation; reword |
| R11 | Manuscript not self-contained (Results/Discussion are pointers); residual overclaims ("below the nominal guarantee", "catastrophically", "visually proves", "eliminating entirely") | both | Write Results+Discussion; purge wording |
| R12 | Reproducibility: independent_check covers 6/15 groups and re-aggregates same files; hard-coded Windows path; Fig 2 values hard-coded; Phase 3 vs 6 reruns not bit-identical; requirements unpinned; Phases 9-14 not in git; no tests for leakage or Mondrian=EO | both | Fix in code pass |

Code review: no test-set threshold fitting found in the conformal pipeline; test-set fitting only in diagnostic recalibration and eICU thresholds (fitted on all eICU data).
Reference notes: [3] is a neural-network paper used for a premise contradicted by own XGBoost (slope 1.00); `01_LITERATURE_SEARCH_AND_COMPARISON.md` has wrong Romano title and mis-describes Yang 2024.
