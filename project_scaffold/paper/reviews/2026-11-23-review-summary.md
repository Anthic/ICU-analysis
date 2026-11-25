# Peer-review summary, 2026-11-23 (constructive + adversarial; full reports alongside)

Subject: ICU conformal fairness manuscript (master + results_draft + Phase 6-9 notes). Standards: TRIPOD+AI, STROBE. Reviewers read the markdown package only (no code, parquet or Tables 1-8); abstract-level literature; citation spot-checks partly from background knowledge (one by fetching Yang 2024).

## Verdicts
- Constructive: major revision before submission, good prognosis; Q1 acceptance about 5-10% as written (JAMIA), 20-30% (JAMIA) / 45-60% (JBI, AIIM, IJMI) after reframing and extra analyses.
- Adversarial: major revision, close to reject as written.

## Agreed Major Issues (both reviewers)
1. Class-conditional coverage with score 1 - p is sensitivity (deaths) and specificity (survivors) of two risk thresholds; the age gap is the known unequal-TPR/TNR effect of one threshold under unequal base rates, and Mondrian by age is group-specific thresholding (equalised-odds post-processing). Not stated; Hardt 2016, Chouldechova 2017, Kleinberg 2017, Pleiss 2017, Sadinle-Lei-Wasserman 2019, Vovk Mondrian work not cited.
2. "Equitable / vulnerable / fairness" framing not supported by an equity outcome; overclaiming text remains ("we prove", "mathematically guaranteed", "eliminating entirely", "5.94 pp below the nominal guarantee").
3. Mechanism section partly circular and ecological (coverage vs mean decedent score; 4 collinear age strata; overlapping strata; eICU-primary demographic correlation n.s.). "60-75% shrinkage" holds for MIMIC only (eICU: about 32% death, 52% survivor).
4. 40-calibration-death rule is not supported: hospital-specific thresholds never beat pooled; wrong estimand (variance vs bias trade-off, break-even about 0.09/delta^2); "84% infinite" is mathematical.
5. External-validation inference: endpoints not demonstrably pre-specified before results; P1 fails in the primary model (0.902), passes only in the harmonised model; P2 passes trivially because overall survivor coverage under transport is already low; seeds reuse patients; no hospital-cluster uncertainty; hospital-disjoint check is vacuous for pure-transport endpoints; recalibrated young-decedent coverage 0.884 is about 1 SE from nominal in the primary model.
6. Outcome/case-mix confounding (hospice/comfort care counted as survival, DNR, diagnosis mix, 24 h landmark) not examined.
7. Missing utility measures (P(death | set), absolute missed deaths, comparison with equalised-odds thresholds), single model class, single alpha, no placebo ablation, no temporal split.
8. Internal inconsistencies and stale text (Figure 3 caption ">82%"; "planned as Phase 6"; set-size bound -0.060/+0.058; tolerance <0.0005 vs 0.000000; CITL narrative vs Phase 8; calibration slope SD equals intercept mean; hospital-seed denominators; predictor counts 66/72/63).
9. Citation problems (Lei & Wasserman cited for Mondrian; Tibshirani 2019 for split CP; Lu 2022 for clinician efficiency fear; Yang 2024 "equity limitation" not verified) and TRIPOD+AI gaps (hyperparameters, early stopping, imbalance, sample size, predictor list).

## Items needing user decision (accept / reject / defer)
Each Major above. Suggested: accept 1-9; reframe as an audit of calibration-versus-coverage tension, transport and repair cost.

## Highest-value additions (ranked)
1. Re-express P1/P2 as stratum-minus-overall contrasts with hospital-cluster bootstrap CIs.
2. Calibration-implied coverage test (predict coverage from the group risk density under calibration) plus synthetic demonstration.
3. Hospice/comfort-care/case-mix sensitivity and continuous-age curves.
4. P(death | set), set-size equity, equalised-odds threshold baseline.
5. Temporal split, second model class, alpha sweep, placebo ablation.
