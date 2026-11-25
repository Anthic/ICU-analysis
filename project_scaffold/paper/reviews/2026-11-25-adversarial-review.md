---
title: "Adversarial peer review: Age-Related Coverage Differences of Class-Conditional and Group-Conditional Conformal Prediction for ICU Mortality"
reviewer: Reviewer 2 (adversarial)
role: adversarial
date: 2026-11-25
manuscript: research_writing/00_MANUSCRIPT_MASTER.md (version with Sections 2.9-2.14 and Phase 9/10 bullets)
reporting_standard: TRIPOD+AI, STROBE
---

# Summary
The manuscript shows that pooled class-conditional split conformal prediction (alpha = 0.10) on an XGBoost ICU-mortality model gives unequal death/survivor coverage across age strata in MIMIC-IV (young decedents 84.1%, 75+ survivors 82.9%), and that age x class Mondrian calibration restores ~90% in every stratum at small set-size cost; an eICU-CRD validation, mechanism analyses and robustness checks are added. Numerically the work is careful and most numbers reproduce from the CSV/JSON files (31 checked, see audit). The problem is the inferential layer. The central "finding" is a mathematical consequence of calibrated scores with group-specific base rates under a pooled threshold; the "repair" is true by construction and is (by the authors' own Phase 12) 99% identical to group-specific thresholding; the headline young-decedent result failed its own pre-planned external endpoint in the primary model; and the paper is still a hybrid of a manuscript and pointers to notes (Results/Discussion are "refer to results_draft.md", Section 2.14 is a placeholder, Methods predictor counts contradict the code).

# Major Issues

**M1. The core finding is an expected consequence, and the "mechanism" is a tautology that fails quantitatively on the death side.**
Class-conditional coverage of a pooled rule is the sensitivity/specificity of two risk thresholds in each stratum (Section 2.10). With calibrated scores and different base rates, coverage differs. The Phase 10 "calibration-implied test" is an algebraic identity (E[p 1(p>=t)]/E[p]), not a test of a mechanism. Where it can fail (death side), it does: MIMIC death R2 vs nominal = -0.19; eICU demographic strata death R2 = -3.2 (raw) and -7.6 (recalibrated) (`phase10_fit_main_100.csv`). The manuscript text reports only "negative" for MIMIC and omits the eICU values. Predicted MIMIC death coverage is 0.810/0.848/0.865/0.922 vs observed 0.840/0.871/0.907/0.931 (age strata): the identity under-predicts by 1-4 pp in every stratum, i.e. within-stratum scores are not calibrated for decedents, exactly the population of interest. "Explains" / "supporting that the gap arises because..." should be removed for deaths. Figure 4 additionally uses recalibrated eICU scores for the survivor panel (where it helps, R2 0.99) and raw scores for the death panel (where recalibration worsens R2 from -3.2 to -7.6): panel-specific choice of the better weights is selective presentation.

**M2. Age mechanism rests on n = 4 strata; age, prevalence and AUROC are collinear.** Spearman 0.89/0.79 across 4 age strata (or 15 overlapping strata where the same patients appear in age, race, sex and insurance cells) are not independent observations. The age-blind ablation is the only interventional evidence, but removing age also changes the model's calibration by age (CITL +0.023 / -0.030) and does not separate age from correlated physiology (acknowledged). Alternative explanations are untested: young decedents are plausibly a different case-mix (overdose, trauma, anoxic injury, sudden arrest) whose first-24h physiology is uninformative; elderly survivors are enriched for treatment limitation/palliative trajectories. No diagnosis/admission-type stratification is done. The mechanism claim in the abstract ("track subgroup score distributions (base rates), not demographic attributes as such") is not identifiable from the analyses.

**M3. The headline young-decedent deficit did not replicate on its own endpoint in the primary model, and the replication rule was changed post hoc.**
P1 (primary model) = 0.902 [0.870, 0.926]: not replicated. After eICU recalibration young death coverage is 0.884 (-1.6 pp from 0.90; -1.8 pp vs overall, hospital-cluster CI [-3.5, -0.2]; Bonferroni-adjusted [-4.3, +0.4] crosses zero). The replacement criterion ("upper bound < 0", Section 2.9) was defined after P1 failed; with the original rule the result is negative, with the new rule it is borderline and fails multiplicity control. The deficit is large only in the harmonised model (AUROC 0.81, 3 predictors dropped, i.e. a weaker model), and that model was introduced as a sensitivity analysis, not a pre-specified one. Abstract and conclusions ("the age pattern persisted") describe direction only; the magnitude shrinks from -6 pp (MIMIC) to -2 pp (eICU primary). Within MIMIC, the age finding is explicitly post hoc ("highlighted after inspecting results") out of 15 strata x 2 classes (+ 42 intersectional cells) with no multiplicity control.

**M3b. The Mondrian "repair" is not demonstrated under realistic shift and is guaranteed by construction elsewhere.**
In MIMIC internal and eICU-recalibrated analyses nominal coverage is a theorem under exchangeability, so 90.4% is a unit test, not evidence. The only non-exchangeable test (temporal split, `phase13_temporal_summary_main.csv`) shows age Mondrian OVER-covers young decedents (0.952) and has a larger max death-side gap than the pooled rule (0.052 vs 0.041 in 2017-2022; 0.056 vs 0.050 in 2020-2022). This is buried in one clause of Section 3 and absent from the abstract/conclusion, which say the repair "restored nominal coverage in every age stratum". The temporal analysis is a single split with 20 training seeds, so its SDs reflect only training randomness. The eICU transport analysis (Mondrian thresholds from MIMIC) is also not reported in the text, although coded (`ext_mimiccal_mondrian_cc`).

**M4. Novelty is incremental, and the paper's own Phase 12 shows it.** Age x class Mondrian and an equalised-odds-type threshold baseline give identical sets for 99.2% (MIMIC) / 99.7% (eICU) of patients; so the contribution reduces to "group-specific thresholds equalise group-specific TPR/TNR", which is Hardt et al. 2016 and the Mondrian/class-conditional machinery of Vovk (2003, 2005) and Romano et al. 2020 applied to age strata. Missing from the reference list and from the positioning: Sadinle-Lei-Wasserman 2019 (class-conditional sets), Gibbs-Cherian-Candes 2023 (conditional guarantees over group classes), Jung et al. 2023 (multivalid/multigroup CP), Liu et al. 2022 / Wang et al. 2023 (fair CP), Zhou-Sesia 2024 (equalised coverage for adaptively selected groups), and the 2025-26 clinical conformal-fairness preprints (the Discussion itself says the comparison "remains to be written; do not claim priority", and the user-facing brief mentions Tasar 2025, which I could not verify and which is not cited). A Discussion that has not been written cannot support a novelty claim; the abstract's "we evaluated whether..." framing is acceptable but the Introduction's "to resolve these open challenges... comprehensive audit" is not.

**M5. The equalised-odds equivalence is imprecise as stated.** (i) Hardt's equalised odds equalises TPR and FPR of ONE predictor. Mondrian-by-class equalises the TPR of the rule "die in set" (death coverage) and the TNR of a different rule "survive in set" (survivor coverage); the FPR of the "die in set" rule (share of survivors with p >= t_d) is not equalised, and the "EO baseline" in `12_utility_equity.py` is a two-threshold (reject-option) rule, not Hardt's EO. (ii) Equivalence is not exact: `np.quantile` (linear interpolation, rank ~ alpha(n-1)) vs the order statistic ceil((n+1)(1-alpha)) differ by about one rank (up to ~1/n_cell in coverage), and the EO rule carries no finite-sample guarantee, which is precisely what conformal adds; the 0.8%/0.3% disagreement is this effect. The claim "i.e. the Mondrian repair is group-specific thresholding" is fine; labelling it EO and then reporting (Section 4) that EO "cannot coincide with equal predictive values" is a known impossibility result and tells us nothing new.

**M6. Uncertainty quantification mixes incompatible notions and understates it in places.**
(a) 100 random 50/25/25 splits of the same 51,838 patients: each patient is in test ~25 times; seed SD (3.0 pp for young deaths) is dominated by test-sampling noise of ~151 deaths (binomial SD 3.0 pp), not by an independent replicate distribution; it is not a CI for the population. The manuscript says so for eICU but reports "split-level 2.5-97.5 percentile +0.30 to +14.58" and bootstrap CIs side by side in the abstract. (b) The patient bootstrap (`reaggregate_phase4_audit.py`) resamples patients' seed-averaged hit indicators; model refitting and threshold re-estimation are not inside the bootstrap, and averaging hits over ~25 splits removes the Bernoulli variability from threshold randomness. The resulting SE (~1.3 pp) is about half the split SD and does not describe a single deployed model with one calibration set. (c) eICU Wilson intervals use mean counts across seeds on the same patients, ignore hospital clustering (cluster intervals are 2-3x wider for P2, ~5x for P1; the manuscript's "5-10 times" holds only for some contrasts), and the primary eICU split is patient-level although hospital-disjoint splits show larger seed SD (0.022 vs 0.019). (d) The "hospital-disjoint splits gave the same values to the third decimal" statement is true for transport (0.902/0.901, 0.748/0.748) but not for recalibrated configurations (0.884 vs 0.881; 0.919 vs 0.918; hospital-disjoint SD larger).

**M7. The max-age-gap metric has a noise floor that is not applied consistently, and two versions of the same quantity are reported.** The per-split max |coverage - 0.90| over four strata is upward-biased (floor 0.026 deaths / 0.009 survivors from permuted labels). The pooled-vs-age-blind comparison uses the seed-averaged gap in Phase 8 (0.060/0.070 -> 0.015/0.027) and the mean per-split gap in Phase 13 (0.065/0.071 -> 0.028/0.028) in the same Results bullet list; the "60-75% reduction" is quoted from the first, noise floors from the second. After accounting for the floor, age-blind death-side gap (0.028 vs 0.026) is indistinguishable from null whereas survivor-side (0.028 vs 0.009) is not; so "removing age closes the gap" is true for deaths and only partly for survivors. The Mondrian per-split gap (0.036 death) is at the permuted-label floor, so smaller values cannot be claimed.

**M8. Outcome definition / end-of-life care is only partly addressed, and Section 2.14 is a placeholder.** In-hospital mortality with hospice discharge coded as survival (2.3% of stays, 3.9% in 75+) is the most obvious alternative explanation of 75+ survivor under-coverage (hospice survivors have high p). The hospice sensitivity analysis is sensible, but: paired differences vs the reference have SD 4-5 pp for young decedents (V1 -1.9 +/- 4.8 pp; V3 +2.0 +/- 5.2 pp), so the statement "outcome-coding choices change the size, not the direction" cannot be supported at the stated precision; V3 removes ~55% of deaths, makes prevalence 5.2% and is outcome-informative; DNR/CMO/treatment-limitation orders were not extracted (Section 2.14 says "RESULTS PENDING; do not report" inside the Methods), and eICU has no such field. Also: the cohort requires ICU LOS >= 24 h (conditioning on survival to 24 h; age-dependent early death exclusion), which defines the deployment time point but is not discussed as a selection effect; ICU-LOS-based exclusion removed 13,528 stays.

**M9. Manuscript consistency and reproducibility defects.**
- Methods state primary model has "66 MIMIC predictors" and the harmonised model 63; the code and result metadata give 52 (noflags; `phase3_baseline_metrics_noflags_a010.json`: n_features 52; flags 61, nolactate 49) and 47 after dropping temperature (3 columns), gcs_min and intubated. Phase 8 note repeats "66-predictor". Either the code or text is wrong.
- Results, Discussion and Tables/Figures are "refer to results_draft.md"; the Discussion contains no interpretation, clinical implications, comparison with prior work. This is not a reviewable manuscript for JAMIA/Lancet Digit Health. STATUS banner lists open items.
- Figure 2 values are hard-coded in `generate_paper_master_figures.py` (acknowledged); `independent_check.py` reads the same prediction parquet files (hard-coded Windows path), so it checks aggregation, not upstream correctness, and cannot be described as "independent verification" of the pipeline.
- Phase 3 and Phase 6 runs of the same model/splits are not bit-identical (AUROC 0.8726 vs 0.8725; calibration intercept 0.0383 vs 0.0453; slope 1.0033 vs 1.0086; young death coverage 0.8406 vs 0.8404), i.e. nondeterminism (`n_jobs=-1`, clipping 1e-8 vs 1e-6) or a changed feature file; the paper states exact reproducibility to 0.0005.
- "Invasive mechanical ventilation indicators" are described in Methods; the code notes MIMIC `intubated` is set only from verbal-GCS chart entries mentioning an airway device (not ventilation); the eICU feature comes from the APACHE APS flag. The MIMIC-eICU mismatch is larger than the three dropped variables suggest; lactate is 64% missing in eICU and missingness patterns (practice-dependent) also differ.

# Minor Issues
1. Intro cites [3] (Guo et al., neural-network miscalibration) to motivate miscalibrated "point probabilities"; the authors' XGBoost has calibration slope 1.00 and CITL -0.002 (Table 2 / phase3 JSON). The premise is contradicted by the paper's own data.
2. "Calibration slope/intercept" are fitted on the test set (in-sample diagnostic, fine, but say so); Phase 10 logistic recalibration is in-sample on all eICU data and thresholds for the identity are fitted on the same eICU data they are evaluated on (descriptive; state it).
3. Small-stratum break-even (n_d > 0.09/delta^2): delta = sqrt(0.052^2 - 0.043^2) = 0.029 is the difference of two nearly equal SDs from 103 hospitals (SE of the observed SD about 7% => delta CI roughly 0 to 0.04); the "90-110 deaths" threshold has no uncertainty and the binomial comparison uses median-based expected SD. Present as illustrative, with an interval. The summary quoted in two places differ (0.045 vs 0.039 and 0.052 vs 0.043: different threshold fits).
4. Age bands: "death coverage rose roughly monotonically with age" - bands 18-29/30-39/40-49 = 0.840/0.865/0.828 (non-monotonic; 28-81 deaths per split). The gradient is flat below 50.
5. Race analysis (Table 7): four unadjusted CIs, Asian/Hispanic ~39 deaths per split; keep as exploratory or drop from Results highlights. "Other/Unknown" race (18.8%) and insurance are heterogeneous composites; Other/Unknown race has CITL -0.035 (prevalence 16.3%), a signal that it is a case-mix artefact (e.g. unknown race in emergent/trauma patients) not discussed.
6. The "efficiency penalty" is measured as change in mean set size under a reallocation of thresholds; +0.029 labels in the young is by construction (the young pooled threshold was too tight). Better: report P(death | set type) by stratum under both schemes (done in Phase 12, but not in abstract). Under Mondrian the {survive}-only residual death risk is still 0.9% (18-49) vs 3.2% (75+) and {die}-only precision 32% vs 47%: the repair equalises coverage, not what the clinician sees.
7. Hospital-level SD 0.045 vs 0.039 "expected": compare variance with mean, not median, binomial variance.
8. Abstract "mean paired difference +6.36 pp" has a split SD of 3.61 pp; report only once, with the caveat that splits overlap.
9. Temporal split: MIMIC `anchor_year_group` are 3-year bands; the 2020-2022 test period includes COVID-era case-mix; report not as "robustness" but as a shift test.
10. Logistic model: set size 1.41 (pooled); it is a weak comparator and the larger gap (0.102) just reflects worse score separation.
11. Race stratification in the split (mortality x race) but not age: test stratum sizes vary slightly across seeds; acceptable but state it.

# Editorial
- Target venues "JAMIA / Lancet Digital Health" and the STATUS banner (with four nested "earlier status" notes) must be removed; Section 3 "Key Numerical Highlights" duplicates the abstract; Results bullets are 5-10 lines each with nested file paths. Convert to prose and tables.
- Terms: "disparity" vs "difference" are used interchangeably; "fairness audit" in the aims versus neutral title.
- Section 2.14 and "do not claim priority" are authoring notes inside the manuscript.
- Figure 3 caption range "12-44%" vs abstract "11.77%-39.79% across age groups": state the attribute.

# Methodological Assessment (TRIPOD+AI / STROBE)
| Item | Assessment |
|---|---|
| Source of data, eligibility, flow (STROBE 5-13) | Adequate (94,458 -> 65,366 -> 51,838, verified in `phase1_exclusion_flow.csv`). Age filter excluded 0 patients; first-stay rule applied before LOS filter (patients whose first stay < 24 h are dropped even if later stays qualify): state. |
| Outcome definition (TRIPOD+AI 6) | In-hospital death; hospice = survival; LOS >= 24 h conditioning. Partly addressed (M8). |
| Predictors (7) | 52 columns in code vs 66 in text (M9). Age is a predictor and the audit attribute. |
| Sample size / events (8) | 5,522 events; adequate for model; strata with < 50 deaths flagged "UNSTABLE" in tables but still headlined (Asian, Hispanic). |
| Missing data (9) | Native XGBoost handling; missingness differs sharply in eICU (temperature 89%, lactate 64%). Missingness-by-subgroup tables exist (phase 2) but are not discussed in the paper. |
| Model development/validation (10-11) | Single hyperparameter configuration fixed a priori, early stopping within train, calibration disjoint from test: no leakage found in `split_indices`, `fit_baseline`, `fit_*` (conformal thresholds fitted on calibration only; test used only for evaluation). Checked: split disjointness asserted; unique subject_id asserted. |
| Performance measures (12) | AUROC, AUPRC, Brier, slope, CITL reported; no net benefit/decision curve; no calibration plots by subgroup in paper. |
| Fairness considerations (TRIPOD+AI) | Attributes chosen, but intersectional cells reported only in tables; no multiplicity control; no pre-registration (acknowledged). |
| Code/data availability | Data are credentialed; code not stated as public; Windows hard-coded paths. |
| Statistical rigour | See M6, M7. |
| Generalisability | Two US sources; eICU 2014-15; primary model failed P1; no non-US data; ICU population >= 24 h only. |

Bugs and leakage review (src): (1) Conformal threshold code is correct (ceil((n+1)(1-alpha)), +inf when rank > n; unit tests exist, but tests only use sampling-error tolerances of 2.5-4 pp which cannot detect an off-by-one-rank error; the exact-rank test does exist). (2) Mondrian group missing in calibration -> +inf for that class (full set), unseen test group -> full set; fine. (3) No test-set fitting of thresholds; test-set fitting only in diagnostic recalibration (`calibration_slope/intercept`, Phase 10 recal weights, Phase 7 eICU thresholds on all eICU data). (4) Phase 6 eICU patient split stratified with fallback for tiny strata; skipping of seeds with < 5 deaths silently drops external configs for that seed (none observed). (5) Phase 11 builds its own splits per variant (different test sets than the reference V0 for V2/V3); paired differences are therefore across different test populations. (6) `07_tradeoff_analysis.py`/`make_paper_tables.py` embed hard-coded numbers (Table 1 counts; Table 7 values; Figure 2 deltas); drift risk.

# Falsification Test
Pre-registered hypothesis and criteria (from Section 2.6 and 2.9): P1 = young decedent death coverage under transport upper Wilson bound < 0.90; P2 = 75+ survivor coverage upper bound < 0.90; revised rule = contrast upper 95% bound < 0.
- P1, primary model: 0.902 [0.870, 0.926] -> hypothesis NOT supported. Harmonised model: supported. Revised rule: supported only with uncorrected hospital-cluster CI [-3.4, -0.5]; refuted after Bonferroni [-4.1, +0.15].
- P2: supported (0.748; contrast -8.6 pp), but confounded with overall survivor shortfall (0.835) and covariate/calibration shift.
- Claim "Mondrian restores coverage": cannot be refuted in exchangeable settings (theorem); refuted for young decedents under temporal shift (0.952, gap 0.052 > pooled 0.041).
- Claim "age gap is explained by base rates + calibration": refuted on the death side (R2 < 0, up to -7.6 in eICU strata).
- Claim "outcome coding changes size, not direction": not testable at the reported precision.
What would refute the paper's main conclusion: an eICU/other-site primary-model analysis in which the young-decedent contrast CI includes 0 after multiplicity control (this is what the primary-model data show), or a clinically stratified analysis showing the gap vanishes within diagnosis groups.

# Discipline-Specific Check (clinical prediction / ML)
- Clinical relevance: the largest effects are 5-7 pp coverage differences in subgroups of 150 deaths per test split; a 90% target for "deaths" produces {die}-only sets in only 14-16% of patients with 32-47% precision; no decision context, no net benefit, no clinician-facing consequences. "Harm" language is not justified.
- Generalisability: single academic centre + eICU 2014-15 with different feature definitions; the model transport itself fails (CITL +0.042, slope 0.88, survivor coverage 0.835).
- Reproducibility: seeds, fixed config, scripts supplied; but predictor count mismatch and non-bit-identical reruns (M9).

# Cited Evidence Audit (numbers and references)
Numbers checked against CSV/JSON (all matched unless noted):
| # | Manuscript claim | Source | Result |
|---|---|---|---|
| 1 | AUROC 0.8726 (SD 0.0042), AUPRC 0.5023, Brier 0.0706 | phase3_baseline_metrics_noflags_a010.json | match |
| 2 | Marginal coverage 90.02%, deaths 23.52%; class-cond deaths 90.14% | same | match |
| 3 | Young deaths 84.06% [81.43, 86.72] | phase4_rigorous_audit | match |
| 4 | Mondrian young 90.42%; paired +6.36 (SD 3.61; 0.30 to 14.58) | phase5 CSV + per-seed recomputation | match |
| 5 | Mondrian marginal 11.77%-39.79% (age) | phase5 CSV | match |
| 6 | Set-size +2.57% (18-49), +1.49% (75+), max +0.058, singleton 62-87% | phase5/Table 8 | match |
| 7 | Asian/Hispanic ~39 deaths | phase5 CSV | match |
| 8 | eICU 95,558 / 8,885 (9.30%) / 207 hospitals; 103 in table | phase6 summary | match |
| 9 | AUROC 0.873/0.834/0.810; slope 0.88/0.83; CITL +0.042/+0.051 | phase6_model_performance | match |
| 10 | Transport death 0.920/surv 0.835 (harm 0.928/0.817) | phase6 coverage csv | match |
| 11 | P1 0.902 [0.870,0.926]; harm 0.819 [0.781,0.852] | phase6 | match |
| 12 | P2 0.748 [0.741,0.756]; harm 0.677 [0.668,0.685] | phase6 | match |
| 13 | eICU recal age pattern 0.884/0.941 ... 0.919/0.844 (harm 0.778/0.966 ... 0.950/0.820) | phase6 | match |
| 14 | Hospital SD 0.045/0.042 vs 0.039 | phase6 summary | match |
| 15 | Hospital-disjoint "same to the third decimal" | phase6 hosp files | PARTLY false (recal differs 0.884 vs 0.881) |
| 16 | Mondrian eICU 0.898-0.903 in every stratum | phase6 | match (0.8984-0.9035) |
| 17 | Phase 8: 0.013/0.016, 0.060/0.070, eICU 0.006/0.006, 0.019/0.056; set size 1.26 -> 1.79; singleton 74% -> 21%; Mondrian 0.005/0.001 at 1.27 | phase8 | match |
| 18 | Age-blind 0.015/0.027, eICU 0.013/0.027; pooled | phase8 | match; Phase 13 gives 0.028/0.028 (different metric) |
| 19 | Phase 9 contrasts (-1.9 [-3.4,-0.5]; -11.0 [-12.9,-9.3]; -1.8; -12.2; P2 -8.6, -14.0, -5.6, -8.0; Bonferroni [-4.1,+0.1]) | phase9 csv | match (Bonferroni upper +0.15; recal Bonferroni [-4.3,+0.4] not reported) |
| 20 | CI "5-10x wider than seed-only" | phase9 csv | holds for P1 (~5x); P2 only 2-3x |
| 21 | Phase 10: R2 0.95 MIMIC survivors, 0.99 eICU strata, 0.92-0.93 hospitals; RMSE 0.027 vs floor 0.025 | phase10_fit | match; death R2 in eICU strata (-3.2/-7.6) omitted |
| 22 | Hospice 1,209 (2.3%); young death 0.840/0.822/0.844/0.860 (SD 0.041); 75+ surv 0.830/0.819/0.825/0.824 | phase11 | match (summary csv) |
| 23 | Bands: death 0.84 to 0.94, survivors 0.97 to 0.81 | phase11 | match (0.840 ... 0.941; 0.968 ... 0.809) but non-monotone |
| 24 | Phase 12: 99.2%/99.7% agreement; 16% vs 7% missed deaths pooled, ~10% Mondrian; 0.9%-3.2%; 32-47%; size 1.18-1.38; singleton 83-62% | phase12 | match |
| 25 | Temporal 0.870 / 0.827; Mondrian 0.894-0.903 survivors; young deaths 0.952; max gap 0.052 | phase13_temporal | match (Mondrian survivor 0.894-0.903: 0.8936-0.9031) |
| 26 | Logistic 0.799, 0.947, gap 0.102 vs 0.065 | phase13 | match |
| 27 | Alpha sweep 0.035-0.128 (surv), 0.048-0.075 (death) | phase13 | match |
| 28 | Placebo 0.026/0.009; random 0.065/0.071; age 0.028/0.028 | phase13 | match |
| 29 | Cohort 94,458 -> 51,838, 29,092 / 13,528 excluded; 5,522 deaths | phase1 flow | match |
| 30 | "66 / 63 predictors" | phase3 JSON, code | MISMATCH (52 / 47) |
| 31 | Figure 1 observed 6.3/8.9/10.5/15.4%; predicted 6.4/8.8/10.1/14.8% | phase4 | match |

Reference spot-check (bibliographic detail from my own knowledge; the web-search tool was unavailable, so not re-verified online):
| Ref | Check | Result |
|---|---|---|
| [7] Romano, Sesia, Candes 2020 NeurIPS 33:3581-3591 "Classification with valid and adaptive coverage" | title/venue/pages | Correct in manuscript; the companion file `01_LITERATURE_SEARCH_AND_COMPARISON.md` gives a wrong title ("...Valid and Equal Coverage for Inconclusive Sets") and wrongly credits it with class-conditional split CP |
| [12] Yang et al. JMIR 2024;26:e50369 | authors/venue plausible | Text in the manuscript says it used a Mondrian CP, while the literature file says it applied standard split CP and did not audit subgroups: the two internal descriptions contradict; the content claim must be verified against the paper |
| [15] Romano et al. HDSR 2020 "With malice toward none" | title/venue | Correct; but it is a group-coverage (equalised coverage) paper, which should be positioned as direct prior art for the "repair", not only "related work" |
| [16] Lu et al. AAAI 2022 36(11):12008-12016 | venue/pages | Correct |
| [3] Guo et al. ICML 2017 | scope | Correct reference, but about neural networks; used for a claim contradicted by own results (Minor 1). Also [11] Cauchois et al. is cited for "uneven coverage favouring easy examples"; class-conditional/Mondrian primary sources (Vovk 2003; Sadinle et al. 2019) would be more apt |
Unverified in this pass: refs 1, 5, 17 (flagged by the authors); I found no error in them from memory.

# Overall recommendation (adversarial)
Major revision / not publishable in current form for the claimed venues. A defensible paper exists: "Pooled class-conditional conformal prediction transmits age-dependent base-rate differences into unequal coverage; group-by-class thresholds equalise them at modest set-size cost but do not equalise predictive value and do not survive temporal shift; external replication is partial." It requires: (1) rewriting the Abstract/Conclusion to match M3/M3b; (2) dropping mechanism "explanation" language for deaths or adding stratification by diagnosis/admission type; (3) a single, noise-floor-corrected gap metric; (4) a completed Discussion with proper positioning against Romano 2020, Gibbs 2023, Zhou-Sesia 2024 and clinical CP fairness work; (5) resolving the 52/66 predictor mismatch and non-bit-identical reruns; (6) DNR/CMO sensitivity or an explicit statement that it is not done; (7) a patient/hospital-clustered uncertainty analysis that includes refitting.

## Minimum changes to move to "minor revision"
Fix M9 items; report death-side R2 (eICU) and temporal Mondrian failure in the abstract; reconcile the two max-gap metrics; state P1 failure in the Abstract Results; complete Discussion; remove placeholders.
