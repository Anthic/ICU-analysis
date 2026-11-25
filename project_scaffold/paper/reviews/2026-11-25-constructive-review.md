---
title: "Constructive peer review: Age-Related Coverage Differences of Class-Conditional and Group-Conditional Conformal Prediction for ICU Mortality"
reviewer: Peer Reviewer Subagent (constructive)
role: constructive
date: 2026-11-25
manuscript: research_writing/00_MANUSCRIPT_MASTER.md (MIMIC-IV v3.1 + eICU-CRD v2.0; with paper/*.md notes, outputs/*, src/*)
reporting_standard: TRIPOD+AI; STROBE
---

# Review Report (constructive, second pass on the current version)

Method: read the manuscript master, research_writing/09-12, paper/phase*_NOTE.md, paper/tables, all src/evaluation, src/conformal, src/models scripts, tests, and re-computed numbers from outputs/tables/*.csv, outputs/results/*.json and data/processed/*.parquet (read-only). This pass does not repeat the 2026-11-23 review; items it already raised and that are now fixed are not re-listed. Web access was unavailable, so the reference audit uses bibliographic knowledge only (flagged).

## Summary

This is a careful, unusually transparent empirical audit: a two-sided age pattern in pooled class-conditional conformal coverage (young decedents 84.1%, 75+ survivors 82.9%) is documented over 100 splits, probed externally (eICU, hospital clustering), by placebo, temporal, second-model, alpha, outcome-coding and age-blind analyses, and honestly framed as an audit rather than a method. All 25+ numbers I recomputed match the outputs. The remaining weaknesses are (i) the central hypotheses are partly tautological and the death-side half of the "explained by score distributions" claim is not supported by the project's own fits, (ii) the manuscript master is not a self-contained paper (Results/Discussion are pointers), (iii) a cluster of stale or wrong descriptors (predictor counts, feature list, "independent" check, 5-10x claim) and some residual overclaiming, and (iv) provenance gaps for a few reported numbers.

## Major Issues

**M1. "Age Mondrian = equalised-odds thresholds" is a mathematical identity, not an empirical finding (Sec 2.12, 3 line 164; src/evaluation/12_utility_equity.py lines 46-60).**
`eo_fit` takes the alpha-quantile of p among deaths and the (1-alpha)-quantile among survivors of the same calibration scores; Mondrian-by-age class-conditional includes label 1 iff 1-p <= (1-alpha) quantile of 1-p among deaths, i.e. p >= the alpha quantile among deaths. The two rules are the same up to the ceil((n+1)(1-alpha))/n correction. The reported 99.2% / 99.7% agreement therefore only measures the effect of the finite-sample correction. Falsification: this hypothesis cannot fail. Suggest stating it as a proposition with a three-line proof plus a unit test in tests/test_conformal.py, and reserving empirical language for what is actually informative (finite-sample/small-cell divergence, e.g. report agreement by calibration-cell size). Also say that the EO operating point (TPR=TNR=0.90) is a special case of Hardt-type post-processing, not the general method.

**M2. "Coverage differences are explained by score distributions" is true by definition for the descriptive part, and the non-trivial (calibration-identity) part is only half supported (Abstract line 24; Sec 2.10; outputs/tables/phase10_fit_main_100.csv).**
Class-conditional coverage is by construction a function of the within-group class-conditional score distribution. The informative claim is the label-free identity under within-stratum calibration. Your fits: survivor side R2 0.95 (MIMIC), 0.99 (eICU demographic, recalibrated), 0.92 (hospital). Death side: R2 -0.19 (MIMIC strata), -3.2 / -7.6 (eICU demographic, raw / recal), 0.50 / 0.37 (hospitals); RMSE 0.027 vs noise floor 0.025. Moreover, in outputs/results/phase7_summary_main_100.json the demographic-strata Spearman between mean decedent score and death-coverage gap is 0.004 (MIMIC, n=15) and 0.31 (eICU, n=11, p=0.36); only the 103 hospitals give 0.79. The abstract sentence "track subgroup score distributions (base rates), not demographic attributes as such" is therefore stronger than the evidence, and "not demographic attributes as such" is untestable for age (base rate is a function of age; only race/sex could separate the two, and they show no stable gap). Recommend: state the supported claim narrowly ("survivor-side coverage is predictable from scores under within-age calibration; death-side magnitudes are not, which points to within-stratum miscalibration and score-tail shape"), and test the tail/quantile mechanism directly (compare class-specific score quantiles at t_d, t_s across strata; this is the Gao 2026a prediction already listed in doc 09, Sec 7.3).

**M3. Several mechanism correlations rest on overlapping, non-independent strata and show a sign inconsistency that is not discussed (Sec 3 line 154; phase7_summary_*.json).**
The 15 MIMIC "strata" are four overlapping partitions of the same patients (p = 1e-5 for prevalence is not meaningful; effective n is about 4 for age). AUROC vs death-coverage gap is negative across demographic strata (-0.45 primary, p=0.09; -0.60 harmonised, p=0.018; eICU harmonised -0.72, p=0.013) but positive across hospitals (+0.42/+0.43). "Not explained by within-stratum AUROC" should become "AUROC shows opposite signs at the stratum and hospital levels, so it is not a consistent explanation". Report permutation or hospital-cluster p-values, or drop p-values.

**M4. Age-blind ablation: statement is not supported for eICU and one number has no reproducible source (Sec 3 line 156; paper/phase8_alternatives_NOTE.md line 18).**
"Shrank the age gap by roughly 60-75%" holds for MIMIC (death 0.060 to 0.015 = 75%; survivors 0.070 to 0.027 = 61%) but for eICU it is 32% (0.019 to 0.013) and 52% (0.056 to 0.027). The earlier review flagged this; the master text is unchanged. In addition, the age-blind CITL by age (+0.023, +0.007, -0.001, -0.030) and AUROC 0.874 to 0.866 come from an ad hoc "10-seed check" that is not produced by 08_alternatives_ablation.py or any output file. Add CITL/AUROC per age stratum to the Phase 8 script and rerun (100 seeds). Also note the ablation is consistent with, rather than a test of, the identity: removing age converts base-rate shifts into miscalibration (the paper's own "coverage parity is not calibration parity").

**M5. The manuscript master is not a self-contained paper.**
Sec 3 is "Key Numerical Highlights" with a pointer to results_draft.md; Sec 4 is a pointer plus a long limitations paragraph; there is no Discussion, no conclusion, no Table/Figure placement. results_draft.md still uses "deep, clinically concerning disparities", "visually proves", "eliminating the age disparity entirely", and Table 6 (script make_paper_tables.py line 279) still says "catastrophically", although the 2026-11-20 status line says these were removed. The abstract (line 21) still says "5.94 percentage points below the nominal guarantee"; pooled class-conditional CP gives no subgroup guarantee, so this wording is wrong in kind (the guarantee is marginal within class). Table 8 text uses "subgroup fairness", "vulnerable groups".

**M6. Replication logic: honest, but the headline is still more positive than the evidence.**
P1 failed under the pre-planned rule in the primary model (0.902, Wilson [0.870, 0.926]). The contrast rule (Sec 2.9) was defined after that failure; under it P1 passes (-1.9 pp [-3.4, -0.5]) but the Bonferroni interval over 8 contrasts crosses zero ([-4.1, +0.1]) and, because there are two configurations and two models, the true family is 32 contrasts. P2 passes mainly because overall survivor coverage under transport is already 0.835. The effect size for the primary model is about -2 pp versus -6 pp in MIMIC, and -11 pp in the harmonised model: the replication is "direction yes, magnitude model-dependent". The abstract mentions most of this; the Discussion needs to lead with it. Credit: doc 08_PHASE6_EICU_PLAN.md contains the pre-specified endpoints and rule, but git shows plan and 100-seed outputs were committed together (ff95d3c, 2026-11-22), so git cannot prove precedence. Deposit the plan with an external timestamp (OSF/Zenodo) now, with a statement of what was written before eICU was opened.

**M7. Stale or incorrect descriptors that affect TRIPOD+AI items and credibility.**
- Predictor count: manuscript Sec 2.6 and notes say 66 predictors (harmonised 63); the code (`predictor_columns`, outputs/results/phase3_baseline_metrics_noflags_a010.json: n_features 52) gives 52, and 47 after dropping temperature_{min,max,mean}, gcs_min, intubated. 66/63 do not occur anywhere in the code or JSON ("flags" variant = 61). "Three predictors" removed = five columns.
- Sec 2.2 lists hemoglobin and chloride; they are not in LABS (03_train_baseline.py lines 31-34) or features.parquet. GCS is `gcs_min` only, and `intubated` is derived from the GCS-verbal text containing ETT/TRACH/INTUBAT (02_build_features.py lines 378-384), not "invasive ventilation indicators"; in eICU it is the APACHE flag, so the 45% vs 18% gap is a definition gap, not only case-mix.
- Sec 2.5 (line 101) says independent_check.py "independently recomputed all metrics ... all published values". It reads the pipeline's own set-membership columns (so it cannot detect errors in thresholds, splits or leakage), covers 6 of 15 subgroups, 6 metrics, only Phases 3-5, and has a hard-coded Windows path (line 7). Please restate honestly ("re-aggregation check") or extend it to recompute quantiles from p_hat and y.
- Sec 3 line 159: "hospital-cluster intervals 5-10 times wider than seed-only". From phase9 CSVs the ratio is 2.1-8.5 (median about 5). Use "about 2-8 times".

## Minor Issues

1. Bootstrap CIs (reaggregate_phase4_audit.py lines 108-131) resample test patients after averaging each patient's hit over the roughly 25 splits in which they were in test, holding the 100 fitted models and calibration sets fixed. They omit calibration-set/model variance and so are likely too narrow (84.06% [81.43, 86.72]); the seed SD (3.0 pp) is a different quantity. Label them "test-patient bootstrap conditional on the fitted pipelines", or add a nested bootstrap (resample patients, then re-split once) for the headline.
2. 100 splits reuse the same 51,838 patients; seed SD and percentile ranges are split variability, not population uncertainty (said for eICU, should be said for MIMIC too; 04_subgroup_coverage.py docstring already does).
3. Splits are stratified on mortality x race (03_train_baseline.py line 63), which fixes race-by-outcome counts across splits and understates race-stratum variability; not on age. State this.
4. Table 7 / Sec 3 line 142: Black "-1.30 pp" is the difference of rounded values; unrounded 0.890749 - 0.903685 = -1.29 pp. Table 7 and Figure 2 panels A-C are hard-coded in make_paper_tables.py (lines 300-305) and generate_paper_master_figures.py (lines 233-235, 279-311); values I checked (CITL x1e-3, global/Mondrian death coverage) are correct but not reproducible from CSV. Table 1 (lines 35-52) is also a literal string; I verified all counts against features.parquet and phase1_exclusion_flow.csv.
5. Table 4 header still carries "[OLD TEXT, no longer used]" (make_paper_tables.py line 170); remove.
6. Sec 3 line 153 (SD 0.045 vs 0.039 expected) and line 157 (0.052 vs 0.043) are different analyses (pure transport with MIMIC thresholds vs thresholds fitted in-sample on all eICU, seed-averaged). Label them or reconcile.
7. Phase 10 "label-free" claim: the "recal" weights are a logistic recalibration fitted on all eICU outcomes (10_calibration_implied_coverage.py lines 46-49, 77), and eICU thresholds are fitted in-sample on the same data being evaluated. Say "uses two recalibration parameters estimated from labels".
8. Synthetic demonstration (10b_synthetic_demo.py): scenarios A, C, D are the law of iterated expectations in simulation; Scenario B (equal prevalence, different spread) shows essentially no gap (0.900 vs 0.906 deaths), which supports "base rate, not AUROC", a useful sentence to add.
9. Risk-bin Mondrian (Phase 8, 12) conditions on the score itself, so by design it forces inclusion of both labels near the overlap region and is bound to produce about 80% two-label sets; it is not a fair "no demographic attribute" repair. Add a cheaper demographic-free comparator (e.g. class-conditional on predicted-risk tercile only or a calibration-by-age-free reweighting) or reword as "the price of conditioning on the score".
10. Placebo "drop one random predictor" (13_robustness.py lines 97-103) drops a randomly chosen, usually low-importance, column; it cannot match the influence of age. Use an importance-matched drop (e.g. gcs_min, lactate_max) or age-residualised features.
11. Temporal split is one split, 20 seeds that vary only the XGBoost seed/early-stopping slice; the "SD" is not sampling variability. In the temporal split age-Mondrian worsens the death-side max gap (0.052 vs pooled 0.041, phase13_temporal_gaps_main.json); put this in the Abstract/Discussion because it bears on repair claims under shift.
12. Ten-year-band death coverage is not monotone (0.840, 0.865, 0.828, 0.880, 0.885, 0.907, 0.941; bands under 50 have SD 4-7 pp). "Roughly monotonic" is fine; add a smooth fit (e.g. isotonic/logistic in age) with CI.
13. 24-hour landmark: cohort requires ICU LOS >= 24 h (01_build_cohort.py line 121), excluding early deaths; the prediction time and its consequence for the intended-use population should be in Methods (TRIPOD+AI). Hospital-discharge to hospice coded as survival is addressed in 2.11; eICU lacks the field.
14. requirements.txt is unpinned and lists unused packages (mapie, crepes, lightgbm, statsmodels). Pin versions, record XGBoost/sklearn versions and n_jobs nondeterminism. Phases 9-14 outputs/scripts are not in git (last commit 2026-11-22).
15. tests/test_conformal.py covers the utilities but not the split disjointness/leakage assertions, the Mondrian-equals-EO property, or Phase 6 label alignment. Add them; they are cheap and answer a likely reviewer request.
16. Wilson intervals in Phase 6 use mean counts across seeds (Sec 2.6 acknowledges); keep them only as descriptive and make the cluster bootstrap the primary interval in the text.

## Editorial

- Status banner (line 1) is five nested "earlier status" notes; replace with one dated line before submission.
- Introduction line 34 is a single 190-word paragraph mixing prior work and gap; split, and cut "recent benchmark studies ... include a Mondrian conformal predictor" (cites Yang 2024 only).
- Intro line 36: "clinicians often fear an efficiency penalty" is unsupported; cite or rephrase as a design question.
- Sec 2.5 title "Multi-Attribute Fairness Audit": the paper itself argues coverage parity is not fairness; use "subgroup coverage audit".
- Target-venue line (JAMIA / Lancet Digital Health) is inconsistent with the number of exploratory analyses; consider JAMIA Open, J Biomed Inform, Artif Intell Med, or IJMI (as doc 02 suggests).
- Sec 2 is 14 subsections; move 2.7-2.14 to a "Secondary analyses" block and the rest to Supplement, with a one-page analysis map (question, data, estimand, label: pre-planned / post hoc / exploratory).
- Mixed terms: "death/decedent", "stratum/group/subgroup", "Mondrian marginal" vs "group-conditional"; fix once in a terminology box.

## Methodological Assessment (TRIPOD+AI / STROBE)

Strengths: cohort flow numbers verified; all splits disjoint (asserted in split_indices); early-stopping slice drawn from the training part; no eICU data used for MIMIC training; consistent seeds across phases (0-99); conformal quantile implementation and Mondrian infinite-threshold rule are correct and match Sec 2.4; coverage and set-size reporting by class; hospital clustering; negative-control placebo; multiple robustness checks; honest status labelling.

Gaps (most are already in 10_REPORTING_CHECKLIST; additions in bold):
- TRIPOD+AI: hyperparameter table, early stopping and selection of 0.05/0.8/depth 4 ("fixed before results" is claimed in code comment; say so in Methods with date); **prediction time point and intended use of the sets (decision the set would support)**; **predictor count/definitions (M7)**; sample size / events per variable (5,522 events, 52 predictors); missing-data table (lactate 28% MIMIC vs 64% eICU, temperature 3% vs 89%); fairness/subgroup definitions and rationale for age cut points (18-49/50-64/65-74/75+ chosen before results? say); code/data availability and unpinned environment; registration statement; PPI; funding; ethics.
- **Model updating/transport**: the primary model is never retrained on eICU; state this explicitly as intended (it is a transport evaluation).
- STROBE: flow diagram figure (numbers exist), eICU column in Table 1, bias section for race coding (eICU "ethnicity" mapped by RACE_MAP) and Other/Unknown (18.8%; heterogeneous), clustering by hospital in MIMIC (single centre), exploratory vs confirmatory split of analyses, missing outcome handling (hospice), sensitivity to 24 h landmark.
- Multiplicity: 15 strata x classes x methods with unadjusted intervals; label all race/insurance results exploratory and put the age result as the single pre-highlighted finding (already partly done: "age was highlighted after inspecting results" - a rare and good disclosure; keep it).

## Falsification Test

Hypothesis A: pooled class-conditional CP has age-dependent coverage explained by score distributions.
| Prediction (what would falsify) | Result | Verdict |
|---|---|---|
| Age gradient absent out of sample (P1/P2, pre-planned absolute rule) | P1 primary 0.902 [0.870, 0.926] fails; harmonised 0.819 passes; P2 passes in both (confounded by transport shift) | Partly falsified on the pre-planned rule; direction replicates |
| Gradient absent after removing transport shift (contrast rule, post hoc) | -1.9 pp primary (Bonferroni crosses 0), -11.0 harmonised; P2 -8.6 / -14.0 | Supported, small and model-dependent |
| Permuted age labels also give a gap | max gap 0.026 / 0.009 vs 0.065 / 0.071 | Not falsified (good) |
| Dropping a random predictor reproduces the gap shrinkage | 0.065 / 0.071 unchanged; dropping age 0.028 / 0.028 | Not falsified; placebo weak (minor 10) |
| Pattern disappears under other outcome coding / model / alpha / time | persists; logistic gap larger (0.102); Mondrian worse death-side under temporal shift | Not falsified |
| Label-free identity predicts group coverage | survivors R2 0.95-0.99; deaths R2 -0.19 to -7.6 (demographic), 0.37-0.50 (hospital) | Survivor side supported; death-side magnitude falsified, ordering retained (Spearman 0.75-0.97) |
| Gap tracks decedent score level across demographic strata | Spearman 0.004 (MIMIC), 0.31 (eICU primary, n.s.) | Not supported at stratum level; hospital level 0.79 |

The manuscript reports these results fairly (Sec 3 lines 150, 159-160, 166) but does not present them as pre-stated criteria; add a table like the above with the criteria written as "would falsify if", dated, and keep the abstract's mechanism sentence within the supported rows.

Hypothesis B: age Mondrian equals equalised-odds thresholds. Not falsifiable (identity, M1); only the finite-sample difference is empirical (99.2% / 99.7% identical sets).

## Cited Evidence Audit (spot checks of five references)

Web access unavailable in this session (search and fetch blocked), so these are judgments from bibliographic knowledge and the manuscript's own notes; verify against the full texts.

| # | Reference / claim in manuscript | Check | Status |
|---|---|---|---|
| [3] Guo et al. 2017, ICML 1321-1330, for "point probabilities from modern ML frequently lack calibration" (Intro line 30) | Paper is about neural networks; the model here is gradient-boosted trees, and your own calibration slope is 1.00. Footnote at line 204 already concedes this | Weak support; cite tree-model calibration work or soften |
| [8] Lei et al. 2018, JASA, for split conformal validity (Intro line 32) | Regression-focused; split conformal for classification is in Vovk/Angelopoulos-Bates [5,6]; the exchangeability statement is correct | Acceptable, better with [6] |
| [11] Cauchois, Gupta, Duchi 2021, JMLR, for "marginal methods favour easy examples" (line 34) | The paper studies validated multiclass/multilabel sets and conditional validity; plausible but not the canonical statement of this point | Acceptable; Barber et al. [9] fits better |
| [12] Yang et al. 2024, JMIR e50369: "Mondrian conformal predictor for sepsis mortality with eICU external validation" | Matches the cited record (title, MIMIC-IV to eICU); doc 09 says marginal sets, no subgroup audit; the manuscript line 34 "include a Mondrian conformal predictor" should be checked against the full text | To verify in full text |
| [14] Toccaceli & Gammerman 2019, Mach Learn 108:489-510, cited for Mondrian conformal giving "coverage guarantees within predefined sub-populations" (line 36) | The paper is about combining inductive Mondrian predictors; supports Mondrian validity, not the clinical sub-population claim. Vovk 2013 [13] is the better anchor | Acceptable with [13] |

Not re-checked: [1] Rajkomar 2018, [17] PhysioNet (also flagged by the authors). Doc 09/11 2026 preprints are abstract-level only; read full texts of Gao 2026a, Zhong 2026, Yu 2026, You 2026 before writing the positioning paragraph.

## Suggestions to Strengthen Argument, Structure, Novelty

1. Position as a mechanism-and-cost audit with one clear thesis: "In ICU mortality, pooled class-conditional CP is valid on average, but class-conditional coverage equals sensitivity and specificity at two thresholds, so age differences are the familiar unequal TPR/TNR under unequal base rates; the practical questions are transport, small-cell stability and the cost of the repair." Put the equalised-odds equivalence in the first paragraph of Methods, not in the Discussion; this removes M1 and pre-empts the "known result" objection.
2. Lead the Results with three figures: (a) pooled age pattern with test-patient and cluster intervals (Fig 1), (b) transport vs recalibration vs Mondrian in eICU with contrasts (Fig 4 variants), (c) cost: P(death | {survive}) 0.9% vs 3.2%, set size gap about 0.2 not reduced (Phase 12). Phase 12 is the most clinically novel piece (the repair equalises sensitivity, not predictive value); promote it from "exploratory" bullet to a main result.
3. Make the novelty claim about the combination (clinical instance, replicated direction, transport vs heterogeneity separation, cost accounting) and keep doc 09 section 5 "claims we should not make" as an explicit sentence in Discussion.
4. Add the direct test of the pooled-threshold theory (quantile gaps of class-specific scores by age vs observed coverage gaps) and a finer-stratum check (age x sex, age x race, flagged unstable cells), already recommended in doc 09; both are cheap with existing predictions.
5. Choose primary and secondary outcomes in the abstract: primary = age pattern (pre-highlighted post hoc, said so); everything else secondary. Report the primary effect as a stratum-minus-overall contrast with a cluster CI alongside the absolute value.
6. Report one decision-relevant table: absolute missed deaths per 1,000 by age under pooled vs Mondrian, and a simple net-benefit sentence at a stated threshold; this answers "so what" without a full decision-curve analysis.
7. Housekeeping before submission: fix M7 numbers; regenerate Tables 1, 7 and Figure 2 from CSV; pin environment; commit phases 9-14; add external timestamp for the plan; run a final "numbers audit" script that parses the manuscript for every quoted figure and checks it against outputs (a lightweight version of what I did manually: 25+ numbers all matched).

## Numbers verified against outputs (all matched unless noted)

AUROC 0.8726 (SD 0.0042), AUPRC 0.5023, Brier 0.0706, marginal coverage 90.02% / deaths 23.52% / survivors 97.94%, class-conditional deaths 90.14%, mean set size 1.257, singleton 74.3% (phase3 JSON); age 18-49 death coverage 84.06% [81.43, 86.72], 75+ survivors 82.94%, observed vs predicted risk by age (Figure 1 legend), 14 cohort counts in Table 1 (features.parquet), 29,092 / 13,528 exclusions; Mondrian age-class death 90.42%, +6.36 pp paired (Table 4/5), Mondrian marginal 11.77-39.79% (age) and 11.77-43.94% (15 strata; Fig 3 "about 12-44%"), set-size change -0.060 to +0.058, singleton 62-87%; Asian/Hispanic about 39 deaths and 78-100% range; eICU 95,558 / 8,885 / 9.30% / 207 / 103 hospitals; eICU AUROC 0.834 (0.810), slope 0.88 (0.83), CITL +0.042 (+0.051); transport 0.920 / 0.835 (0.928 / 0.817); P1 0.902 [0.870, 0.926] and 0.819 [0.781, 0.852]; P2 0.748 and 0.677; recalibrated and Mondrian eICU age rows; hospital SD 0.045 vs 0.039; Phase 9 contrasts and Bonferroni intervals; Phase 12 99.2% / 99.7%, P(death | {survive}) 0.9-3.2%, {die}-only 32-47%; Phase 11 hospice 1,209 (2.3%; 0.8-3.9%) and variant coverages; Phase 13 alpha, logistic, temporal, placebo gaps; small-stratum 84% infinite; temperature 89%/3%, GCS 12.6/9.8, intubated 18%/45%. Discrepancies: predictor counts 66/63 (code: 52/47); "60-75%" (MIMIC only); "5-10x" (2-8.5x); Black -1.30 (unrounded -1.29).

## Overall recommendation

Constructive verdict: major revision before submission, good prognosis. The evidence base is strong and honestly reported; the work needed is mostly reframing (M1-M3), correcting stale text and provenance (M4, M7), and turning the pointer-style master into a complete paper (M5). With these done and the claims kept at the supported level, the paper is a credible methods-meets-clinical audit for a specialty informatics venue.
