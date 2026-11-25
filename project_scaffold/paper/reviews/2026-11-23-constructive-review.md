---
title: "Constructive peer review: Group-Conditional Conformal Prediction for Equitable Uncertainty Quantification in ICU Mortality Risk Prediction (MIMIC-IV, eICU-CRD)"
reviewer: Claude (peer-reviewer subagent)
role: constructive
date: 2026-11-23
manuscript: /tmp/rev/00_MANUSCRIPT_MASTER.md (+ results_draft.md, phase6_7_FINAL100_NOTE.md, phase8_alternatives_NOTE.md, 09_NOVELTY_POSITIONING.md, reviewer_responses_and_methods_evidence.md, phase7_*.csv)
reporting_standard: TRIPOD+AI, STROBE
---

# Constructive Review Report

Scope note. I read all files in full. I did not have the underlying code, parquet predictions or Tables 1-8 (only their narrative descriptions), so numeric checks are internal-consistency checks between files, plus arithmetic re-derivations. The citation audit relies on my background knowledge of the cited papers; I did not retrieve full texts.

## Summary

This is an unusually honest and well-documented empirical study: 100 resplits on 51,838 MIMIC-IV stays, a second database (eICU-CRD, 95,558 patients, 207 hospitals), endpoints that are allowed to fail (P1 in the primary model, 0.902), a risk-bin baseline, an age-blind ablation, and a stated list of claims not to make. The strongest findings are (i) the age-ordered, two-sided class-conditional coverage pattern that keeps its direction in a second database, (ii) the separation of transport shift from within-database group heterogeneity, and (iii) the cost comparison of repairs (age x class Mondrian +0.015 labels versus attribute-free risk-bin about +0.5 labels). The weakest parts are that the headline "disparity" is, mathematically, the familiar equal-opportunity gap of a single score threshold under unequal base rates, that the "mechanism" analyses are partly circular and ecological, that several numbers and captions disagree across files, and that the framing ("equitable", "hidden disparities", "vulnerable groups") promises more than the evidence delivers. With reframing and about five targeted analyses this is a credible Q1 medical-informatics paper (JAMIA or JBI-tier); as currently written it would likely be desk-rejected at JAMIA/Lancet Digital Health on novelty and framing grounds.

---

## A. Evidence audit per main claim

GRADE-style strength is adapted for an observational modelling study (High / Moderate / Low / Very low certainty that the claim holds as stated, beyond this dataset).

| # | Claim (as stated) | Evidence type | Strength | Confounders / threats not addressed | Falsifiable? |
|---|---|---|---|---|---|
| C1 | Marginal split CP at alpha=0.10 covers only 23.52% of deaths (survivor coverage 97.94%) | Direct empirical measurement, 100 resplits, MIMIC internal | High for the fact; it is an arithmetic consequence of 10.65% prevalence, replicated in the literature (Yu 2026, Opoku 2026, Ding 2023 per 09 file) | None material; depends on score choice (1-p) | Trivially yes; not a contribution |
| C2 | Class-conditional CP restores overall death coverage (90.14%) | Direct measurement | High (by construction) | None | Yes, trivially |
| C3 | Pooled class-conditional CP under-covers young decedents (84.06% [81.43, 86.72]) and elderly survivors (82.94%) in MIMIC | Observational, internal, patient-level bootstrap | Moderate for direction, Low for magnitude (magnitude varies 0.78 to 0.88 across models/databases) | (a) Post-hoc selection: age was highlighted after inspecting 15 strata x 2 classes (acknowledged); (b) outcome label noise that is age-dependent: discharge to hospice / comfort-measures-only are counted as survivors, which would push elderly "survivors" to high predicted risk and mimic 75+ survivor under-coverage; (c) unmodelled case-mix (young deaths are likely a heterogeneous, diagnosis-driven group; diagnosis, admission type and code status are not predictors); (d) differential missingness by age/race; (e) random, not temporal, splits over 2008-2022 | Yes; and the P1/P2 design is the right instinct |
| C4 | The age pattern replicates in eICU (P1, P2 pre-specified) | Two-database external check, 100 seeds on the same patients, Wilson CI on mean counts | Low to Moderate. P1: 0.902 [0.870, 0.926], not replicated (primary), 0.819 replicated (harmonised). P2 replicated in both but, as the authors say, confounded by the survivor shortfall under transport | (a) Seeds reuse the same patients, so the intervals are anticonservative; (b) no hospital clustering in the CIs (207 hospitals; excess hospital SD 0.045 vs 0.039); (c) endpoints are defined on absolute coverage under pure transport, which mixes shift (+2 pp death over-coverage, -6.5 pp survivor shortfall) with the age effect; (d) "pre-specified before the final run" is weaker than pre-registered, since eICU feature building and earlier runs preceded it; (e) primary model uses GCS/intubation/temperature that are defined differently in eICU, so "primary" is not a clean external validation | Yes. P1 in the primary model is a genuine failed prediction and should be reported as such |
| C5 | Mondrian (age x class) restores about 90% coverage in every stratum at +0.015 to +0.058 labels | Empirical, plus guarantee under exchangeability | High for large strata (by construction); Moderate for the efficiency claim; Low for strata under about 40 calibration deaths (Asian, Hispanic: about 39 per split, coverage range about 78% to 100%) | Exchangeability between calibration and test is guaranteed by random splitting, so this "confirmation" in eICU is uninformative (the authors say so); temporal/site shift not tested for Mondrian itself | The coverage part is not testable except under shift; the efficiency part is |
| C6 | "Mechanism": the gap tracks base rate / score level, not within-group AUROC | Ecological Spearman correlations over 4 age strata, 15 overlapping strata (MIMIC), 11 (eICU), 103 hospitals | Low (partly circular, see Major 3) | (a) Death coverage is a functional of the decedent score distribution, so correlating it with mean predicted risk among decedents (rho 0.79/0.70) is close to tautological; (b) age, prevalence and AUROC collinear across 4 strata; (c) age/race/insurance/sex strata overlap in patients, so the 15 points are not independent; (d) sign flips between levels (hospital AUROC protective, stratum AUROC negative) without a unifying model; (e) in eICU-primary the demographic correlation is n.s. (0.42), omitted from the master file | Yes, if reformulated as a testable prediction (see Analysis 2) |
| C7 | Age-blind ablation shrinks the gap by "roughly 60-75%" | Intervention-type ablation, 100 seeds, MIMIC and eICU | Moderate for MIMIC, Low for eICU | Figures in the files do not support 60-75% in eICU (see Major 4); age also proxies physiology; creates age-dependent miscalibration (CITL +0.023 / -0.030) | Yes |
| C8 | Risk-bin Mondrian (no demographic attribute) closes the gap but costs +0.5 labels | Empirical, 100 seeds, 5 and 10 quantile bins only | Moderate | Result is specific to the binning scheme and score; only 2 bin counts; singleton share 74% to 21% suggests the thresholds degenerate into wide bands, so this may be a property of the implementation | Yes |
| C9 | "Use group x class calibration only with >= ~40 calibration deaths" | Hospital-level comparison of hospital-specific vs global thresholds | Very low as a general rule | Wrong estimand for a minimum-size rule (see Major 5); one database; hospitals have small true deviation from pooled | Yes |
| C10 | Transport shift and group heterogeneity can be separated | Same-test-patient comparison of three calibrations (MIMIC-cal, eICU-cal, eICU-Mondrian) | Moderate; this is a good design | Model-dependence (main vs harmonised) | Yes |

---

## B. The five questions

### (1) What is genuinely new and publishable

Given the 09 file, nothing here is a new method, a first audit, or a new theorem (Romano 2020; Gao 2026a pooled-threshold theory; Yu 2026 and Opoku 2026 on class-conditional failure of marginal sets; Zhong 2026 subgroup audit). I agree with the 09 file's conclusion. Additionally, one point is missing from the 09 file and should reshape the framing:

- Class-conditional conformal coverage here is a re-expression of thresholded-score error rates. With s = 1 - p(k|x), label 1 is in the set iff p(1|x) >= 1 - q_1, so death coverage among decedents is exactly the sensitivity of the rule "p >= t_low", and survivor coverage is exactly the specificity of the rule "p <= t_high" (t_high = q_0). The prediction set is a three-zone triage ({0} / {0,1} / {1}) defined by two risk thresholds. The age gap is therefore the classical result that one threshold on a calibrated score yields group-dependent TPR/TNR when base rates differ (Hardt 2016; Chouldechova 2017; Kleinberg 2017), and Mondrian class-conditional by age is group-specific thresholding (equalised-odds post-processing). The manuscript does not cite or state this. Stating it is not a weakness: it explains your mechanism result in one line, shows why within-group AUROC is not the driver, and tells readers what the conformal layer adds (a finite-sample, distribution-free guarantee and an explicit "uncertain" zone) and what it does not (it cannot escape the equalised-odds / calibration tension).

What is then genuinely contributory, in order of strength:

1. The calibration-versus-coverage tension demonstrated empirically in ICU data. The age-blind ablation is the key result: removing age shrinks the coverage gap but induces age-dependent miscalibration (CITL +0.023 in 18-49, -0.030 in 75+, versus about 0). A calibrated model plus a pooled threshold gives unequal coverage; an equal-coverage model is miscalibrated by age. "Coverage parity is not calibration parity" is a publishable, practically useful, clinically legible message, provided it is tied to the equalised-odds literature and tested with the analysis in Section (3).
2. A two-database, pre-specified, partly failed replication that separates transport shift from group heterogeneity (C4, C10). Reporting the failed primary-model P1 is a real strength and rare in this literature.
3. A cost-of-repair comparison: attribute-based Mondrian (+0.015 labels) versus attribute-free risk-bin Mondrian (+0.5 labels), which speaks directly to the practical "we cannot use age or race" objection.
4. A reporting recommendation: report class- and group-conditional coverage with calibration-cell counts and set-size equity. Position as a reporting standard for conformal clinical models, not as a new method.

The small-stratum rule (C9) is not yet publishable as stated (see Major 5), but a corrected version (a variance-versus-bias rule of thumb) could become a useful practical contribution.

### (2) Strongest honest framing, title and abstract

Reframe from "we found a disparity and fixed it" (which reviewers will read as known repair of a known problem) to "where does the coverage gap come from, does it transport, and what does each fix cost".

Proposed title (pick one):
- "Calibrated scores, unequal coverage: base-rate-driven subgroup gaps in conformal prediction for ICU mortality, with external validation in eICU-CRD"
- "Conformal coverage parity versus calibration in ICU mortality prediction: a two-database study of age-related coverage gaps and the cost of repairing them"

Drop "Equitable" and "Group-Conditional ... for Equitable Uncertainty Quantification" from the title: no equity outcome is measured, and Cresswell 2025 and Gao 2026a are exactly the papers a reviewer will use to say coverage parity is not equity.

Proposed abstract skeleton (structured; numbers are from the files and must be re-checked against final tables):
- Objective: To quantify subgroup class-conditional coverage of split conformal prediction for ICU mortality, test whether the pattern transports to an independent database, probe its source, and compare repair strategies by coverage, set size and calibration.
- Methods: MIMIC-IV v3.1, 51,838 first ICU stays >= 24 h, XGBoost, 100 random 50/25/25 splits, alpha = 0.10; external eICU-CRD (95,558 patients, 207 hospitals) with two feature sets; two pre-specified endpoints; ablation (age-blind) and alternative calibrations (age x class, risk-bin x class).
- Results (lead with the limits): marginal CP covered 23.5% of deaths; class-conditional CP restored overall death coverage but under-covered decedents aged 18-49 (84.1%) and survivors aged 75+ (82.9%). In eICU the direction persisted after local recalibration (death coverage 18-49: 0.884 primary, 0.778 harmonised; survivor 75+: 0.844 / 0.820). Of two pre-specified endpoints under pure transport, P1 replicated in the harmonised model only (0.902 vs 0.819), P2 replicated in both but was confounded by transport shift. Age x class Mondrian restored 0.90 +- 0.005 at +0.015 labels; attribute-free risk-bin calibration needed about +0.5 labels; removing age shrank the gap but induced age-dependent miscalibration.
- Conclusion: Class-conditional coverage gaps under pooled thresholds follow score-level differences between groups and are model-dependent in size; attribute-based Mondrian repair is cheap but is group-specific thresholding, and coverage parity should be reported with calibration and set-size equity.

Aims to restate in the Introduction: (1) heterogeneity of class-conditional coverage; (2) transport versus heterogeneity in a second database; (3) mechanism and calibration tension; (4) repair cost. Demote the current Aim 2 ("pitfall identification": Mondrian marginal failing for deaths) to a short methods-check paragraph; the 09 file and the manuscript itself already say this is an expected consequence.

### (3) Additional analyses (maximum five, ranked by value / effort)

1. Re-express endpoints as within-database contrasts, with cluster-aware uncertainty (very low effort, high value). Report stratum-minus-overall coverage under transport (e.g. P1: 0.902 - 0.920 = -1.8 pp primary vs 0.819 - 0.928 = -10.9 pp harmonised; P2: 0.748 - 0.835 = -8.7 pp vs 0.677 - 0.817 = -14.0 pp), which removes the shift confound that the authors currently have to caveat. Use a hospital-level cluster bootstrap (resample hospitals, then patients) and bootstrap over seeds-and-patients jointly instead of Wilson on mean counts; add CIs to the "age after eICU recalibration" table (currently point estimates only).
2. Calibration-implied coverage test of the mechanism (low-moderate effort, highest value). (a) Show the identity coverage = sensitivity/specificity of the two-threshold rule. (b) If scores are calibrated within group, class-conditional score distributions are determined by the group's risk distribution f_a(s): f(s|y=1) proportional to s f_a(s), f(s|y=0) proportional to (1-s) f_a(s). Predict each stratum's death and survivor coverage under the pooled thresholds from f_a alone (and from the empirical calibration curve) and compare to observed coverage across strata and hospitals; report agreement (slope, R-squared, residuals). This replaces correlational "tracks prevalence" language with a falsifiable prediction, tests Gao 2026a's pooled-threshold theory on your data (09 file recommendation #3), and removes the tautology of correlating coverage with mean decedent score. Add a small synthetic demonstration (perfect calibration, equal AUROC, different base rates) so readers see the gap appear with no discrimination difference.
3. Label-quality and case-mix sensitivity (medium effort, high value). Re-run the age pattern (a) excluding or re-labelling discharges to hospice / comfort-measures-only (MIMIC discharge location; eICU discharge location/status), (b) stratifying by admission type (elective surgical vs emergency/medical), (c) adding a coarse diagnostic group or illness-severity covariate as a predictor, (d) restricting to patients with complete core labs. If the 75+ survivor deficit shrinks sharply after hospice handling, the claim changes from "model/threshold artefact" to "label artefact", which is itself important. This is also the single most likely request from a clinical reviewer.
4. Utility-side metrics and baselines (low-medium effort, high value). Report, by group, the clinically operative quantities that conformal class-conditional coverage does not control: false-reassurance rate P(y=1 | set={0}) (the complement of NPV within the singleton-survive zone), PPV of {1}, set-size equity, and the dual-set share. Compare against two obvious baselines: (i) a single fixed risk threshold with group-specific thresholds chosen for equal sensitivity (equalised-odds post-processing), and (ii) per-group recalibration (isotonic/Platt) then pooled conformal. This shows whether conformal adds anything beyond group-specific thresholds and answers Cresswell 2025 / Gao 2026a. Expect inevitable differences in NPV across groups of different prevalence; saying so is the point.
5. Robustness to shift and model class (medium effort, medium-high value). (a) A temporal split within MIMIC-IV using anchor_year_group (train and calibrate on earlier years, test on 2020-2022) to test exchangeability for the Mondrian repair itself, since random splits over 2008-2022 are favourable. (b) One additional learner (logistic regression with splines, or a small neural net) to show the age gap is not XGBoost-specific, and one finer-stratum analysis (age x sex or age x race) with the minimum-cell rule applied, answering Gao 2026b.

### (4) Realistic journals (tiered)

Quartile and impact-factor positions are from my background knowledge and must be re-verified against the current JCR before choosing.

| Tier | Journal | Fit and realism |
|---|---|---|
| Stretch | npj Digital Medicine | Open to rigorous ML-in-health work with a clear lesson; would need the reframing plus Analyses 2-4. Lancet Digital Health is not realistic for this draft (it expects clinical-impact, prospective or policy-relevant evidence; the study has no decision or outcome impact analysis) |
| Target | Journal of the American Medical Informatics Association (JAMIA) | Natural home for methods-meets-clinical informatics with external validation and a reporting angle. Realistic only after reframing around mechanism, transport and repair cost; the current "found and fixed a disparity" framing and "equitable" language invite desk rejection |
| Target / safe | Journal of Biomedical Informatics | Strong fit for reproducible methodological ML on EHR with explicit mechanism analysis; typically more receptive to conformal/UQ papers |
| Safe Q1 | Artificial Intelligence in Medicine | Q1 in AI and medical informatics; receptive to UQ and fairness in clinical ML |
| Safe Q1 / floor | International Journal of Medical Informatics (alternatively Computers in Biology and Medicine, IEEE JBHI, or Scientific Reports as a floor) | Good fit for the descriptive audit plus validation; lowest risk of a methods-novelty objection |

### (5) Calibrated acceptance estimate at a Q1 medical-informatics / digital-health journal

These are subjective probabilities, with a wide uncertainty band (about +-10 points); base rates for top-tier informatics journals are low (roughly 15-25% of submissions accepted at JAMIA-class journals, from background knowledge, unverified).

| Scenario | Estimated probability of eventual acceptance |
|---|---|
| Current draft, submitted to JAMIA | 5-10% (most likely a desk reject or a major-revision-then-reject) |
| Current draft, Lancet Digital Health | under 3% |
| Reframed + Analyses 1-3 (+ fixes in Section D), JAMIA | 20-30% |
| Same package, Journal of Biomedical Informatics / Artificial Intelligence in Medicine / IJMI | 45-60% per submission |
| Same package, any Q1 medical-informatics journal within a sequential 2-3 journal strategy | about 65-75% |

Reasons for the discount: (a) novelty is mostly in the characterisation, not the method, and the closest competitors (Yu 2026, Zhang 2026, Zhong 2026, Gao 2026a/b, You 2026) are being posted at speed; (b) the central "disparity" is a known equal-opportunity effect of a single threshold and the mechanism analyses are not yet decisive; (c) one pre-specified endpoint failed in the primary model, and the harmonised model that rescues it is a sensitivity analysis; (d) single-centre development data and a 2014-15 external set; (e) overclaiming language ("prove", "mathematically guaranteed equity", "eliminating the disparity entirely"); (f) clinical utility is asserted rather than measured. Factors raising the estimate: scale (51,838 + 95,558), 100 resplits, transparent handling of the failed endpoint, a claim-restriction list, the age-blind / risk-bin ablations, and a clear, checkable data pipeline. Closing the gap between "good empirical work" and "accepted at JAMIA" is mainly framing, Analyses 2-4, and cleaning the numerical inconsistencies below.

---

## C. Major Issues

M1. The headline age disparity is the equal-opportunity gap of a thresholded risk score, and the manuscript does not say so (00 master, Intro, Discussion; results_draft 2.1-2.2). Death coverage is the sensitivity and survivor coverage the specificity of the two thresholds t_low = 1 - q_1 and t_high = q_0. Without this, "hidden demographic coverage disparities driven by baseline risk distributions" (master Abstract, Discussion) reads as a new discovery; with it, readers see precisely what is and is not new. Add the identity, cite the fairness-in-classification literature (Hardt 2016; Chouldechova 2017; Kleinberg 2017), and state that Mondrian-by-age is group-specific thresholding. Then compare against that baseline (Analysis 4).

M2. The "equitable"/"vulnerable groups" framing is not supported by the outcome measured (title; master Abstract Objective and Conclusion; results_draft 2.3, 2.6). Age is not the usual protected attribute in this literature; young decedents are not an established disadvantaged group; race and insurance gaps are small (survivor coverage -1.3 to -2.1 pp, 15 exploratory comparisons without multiplicity adjustment); coverage parity can increase disparate impact (Cresswell 2025, in 09 file, but not in the manuscript); and no clinical decision or outcome is modelled. Use neutral language ("subgroup coverage heterogeneity", "risk-stratum gaps") and reserve "fairness" for the metric actually equalised. Also remove "we prove" and "establish the precise mathematical calibration framework" (results_draft 2.2) and "mathematically guaranteed, equitable uncertainty quantification ... without compromising prognostic utility" (results_draft 2.6): the guarantee is marginal-within-cell under exchangeability, and no utility measure beyond set size is reported.

M3. The mechanism claim is partly circular and ecological (master 2.7, Results highlights "Mechanism"; phase6_7 note Section 5). (i) Death coverage is the fraction of decedents whose score exceeds a fixed threshold; correlating the gap with the mean predicted risk among decedents (Spearman 0.79/0.70) is nearly definitional. (ii) The 15 (MIMIC) and 11 (eICU) strata come from four overlapping partitions of the same patients (age, race, insurance, sex), and four age strata carry almost all the signal; age, prevalence and AUROC are collinear across them. (iii) In eICU-primary the demographic correlation with prevalence is n.s. (0.42); the master file drops this and says the mechanism holds across databases. (iv) Opposite signs of the AUROC association at hospital level (positive) and stratum level (negative) are described but not unified. Replace the correlational narrative with the calibration-implied coverage test (Analysis 2), keep the age-blind ablation as the interventional piece, and retain the explicit "not causal" language.

M4. The "60-75%" age-blind figure holds only for MIMIC (master Results highlights; phase8 note B). From the same numbers: MIMIC death 0.060 to 0.015 (75% shrink), survivor 0.070 to 0.027 (61%); eICU death 0.019 to 0.013 (32%), survivor 0.056 to 0.027 (52%). The eICU death-gap baseline is already small (0.019), so a ratio is unstable. Report absolute changes per dataset and class, with seed-aware CIs, and drop the pooled percentage. The 09 file's statement that removal "shrinks the gap by about 60-75%" repeats the error.

M5. The "minimum 40 calibration deaths" rule answers the wrong question (phase6_7 note Section 6; master 2.7 and Results; 09 file Section 4 item 5). The comparison is hospital-specific versus global thresholds around 0.90, but hospitals have a small true deviation from the pooled threshold (excess hospital SD about 0.022 = sqrt(0.045^2 - 0.039^2)), so a group-specific threshold cannot win; the result mostly measures estimation noise. The relevant trade-off is variance versus bias: the SE of a group's death threshold coverage is about sqrt(0.09 / n_deaths) (about 4.7 pp at n = 40, 2.4 pp at n = 150) against the pooled threshold's bias (about 6 pp for age 18-49, about 2 pp for hospitals). Hence the break-even n depends on the effect size (roughly n > 0.09 / delta^2: about 25 for delta = 6 pp, about 225 for delta = 2 pp). Replace the fixed rule with this formulation and validate it by simulation or by subsampling the MIMIC age cells. Note also the manuscript's own race strata (Asian, Hispanic, about 39 test deaths per split, hence about 39 calibration deaths) sit at the rule's threshold while the abstract states Mondrian works "in every audited stratum".

M6. Confounding of the elderly-survivor and young-decedent findings by outcome and case-mix artefacts is not discussed (Limitations, results_draft 2.5). Hospice / comfort-measures discharges coded as survival, DNR/limitation-of-treatment decisions that rise with age, diagnosis and admission-type heterogeneity (a young death is typically trauma, overdose, hepatic failure or malignancy), and differential missingness across groups can each generate class-conditional score shifts. See Analysis 3. A limitation paragraph and at least one sensitivity analysis are needed before claiming a model/threshold mechanism.

M7. The external-validation design and its inference are weaker than the text implies (master 2.6; phase6_7 note Sections 1-4). (a) "Pre-specified" endpoints were fixed after eICU feature building and earlier runs; state exactly what was seen beforehand and the date, or call them "a priori hypotheses specified before the final 100-seed run". (b) Seeds reuse the same patients; Wilson intervals on mean counts understate uncertainty (acknowledged) and ignore clustering by hospital; use hospital-cluster bootstrap. (c) The primary model is trained on features that are defined differently in eICU (GCS, intubation, temperature 89% missing), so it is arguably not a valid external test; the harmonised model is the defensible one, and P1 replicates only there. Say plainly: "the young-decedent endpoint replicated in 1 of 2 pre-specified model variants". (d) The effect size varies from 0.884 to 0.778 for 18-49 death coverage after eICU recalibration, so the honest claim is "direction replicates, magnitude is model-dependent".

M8. Independence language is inaccurate (master 2.5; results_draft 1.2, 2.4). "100 independent random splits" resample the same 51,838 patients; the SD across seeds reflects split noise and does not measure sampling uncertainty of the population-level coverage; the patient-level bootstrap does. Please also (i) describe how the bootstrap interacts with the 100 splits (resample patients, then pool their per-seed coverage?), (ii) drop "hierarchical bootstrapping" (one stay per patient, so a single-level patient bootstrap), and (iii) correct the variance explanation in results_draft 1.4.2: binomial test-sampling SE for 151 test deaths is 2.44 pp, but the observed seed SD is 3.03-3.49 pp, so test sampling explains only about 50-65% of the variance (2.44^2/3.03^2 = 65%; 2.44^2/3.49^2 = 49%). The remainder is calibration-set sampling of similar size (sqrt(2) x 2.44 = 3.45 pp, matching the observed SD), not "the vast majority" test sampling.

M9. Reporting gaps against TRIPOD+AI (see Section F): no hyperparameter tuning or early-stopping protocol (if early stopping used calibration or test data, the guarantee is voided); no class-imbalance handling statement (affects calibration and the score distribution); no sample-size justification; no statement of the full predictor list (the extraction guide says 72 feature columns, the Methods say 66 predictors; with min/max/mean aggregation, removing "temperature, gcs_min, intubated" cannot yield 63 predictors unless temperature and GCS were reduced to single summaries); sex and age are presumably predictors, but this is not stated; fairness-assessment methods are not mapped to the TRIPOD+AI items.

---

## D. Minor Issues

Internal numerical and textual inconsistencies (checked across files):

m1. Singleton-share claim in Figure 3 caption (master Section 6): ">82% of patients across all subgroups retain definitive singleton predictions" contradicts the Abstract and Section 3 (62%-87%, lowest in age 75+, 62%). 82% applies to age 18-49 only. Also "exact group-conditional coverage" there contradicts the removed "exact 90%" wording.

m2. Set-size bounds: Abstract and Section 3 say the change is "at most +0.058", while results_draft 1.6 reports a range of -0.060 to +0.058 (so the largest absolute change is 0.060, a decrease). Say "between -0.060 and +0.058".

m3. Verification tolerance: master 2.5 states "within an absolute tolerance < 0.0005"; results_draft 2.4 states "within 0.000000 absolute tolerance". Choose one and state what was compared. The "independent" check is by the same author without shared code; call it "independent re-implementation" and, ideally, have a second person or a clean-room run reproduce the headline tables.

m4. CITL narrative contradicts the mechanism section. results_draft 1.3.3 says CITL over/under-prediction "contributes directly to coverage heterogeneity", and Figure 4's caption says negative CITL "partially accounts for under-coverage in younger adult cohorts". But the phase8 note shows the with-age model is about calibrated in every age stratum (CITL about 0), and age-blind young patients are over-predicted (+0.023). The calibrated-model mechanism and the miscalibration narrative cannot both stand; revise 1.3.3 and delete or redo Figure 4 (not generated). Also, "Other/Unknown" race has the largest CITL (-0.035) but its coverage is never reported in the highlights; either report it or explain.

m5. Primary versus harmonised model labels: the master calls the 66-predictor model "primary" although the harmonised model is the more defensible external test and the only one in which P1 replicates. Report both with equal prominence, and explain why removing temperature, GCS and intubation (strong predictors of death) increases the young-decedent gap (0.884 to 0.778): this is presumably because weaker discrimination lowers decedent scores, which is itself evidence for the mechanism and worth one sentence.

m6. Abstract Discussion states the age pattern "persisted after local recalibration" without qualification. In the primary model the 18-49 death coverage is 0.884 (a 1.6 pp shortfall, no CI reported), versus 5.6 pp shortfall for 75+ survivors. Distinguish strong (75+ survivors, harmonised 18-49 deaths) from weak (primary 18-49 deaths) evidence.

m7. Mondrian "by construction" in eICU (0.898-0.903) is uninformative as confirmation; the phase6_7 note still says "Confirms the by-construction repair in a second database"; the master text is more careful. Align.

m8. Race/insurance subgroup claims (Asian -2.10 pp, Black -1.30 pp, Hispanic +2.16 pp survivor coverage) are from 15 strata and 4 attributes with no multiplicity control; the 100-seed difference and bootstrap difference both appear. Report one primary estimate, adjust (Holm or false-discovery rate), and move to a supplement.

m9. Missingness: "missing-indicator flags confirmed to have zero feature gain in preliminary seeds" is not evidence about differential missingness by subgroup. Report missingness rates by age and race for the key features, and the effect of complete-case restriction.

m10. Cohort flow: Methods list the order (first stay, LOS, adult); the extraction guide lists the same counts but describes the universe as "adult/pediatric stays" (MIMIC-IV is adult), and the ranges table omits hemoglobin and chloride that the Methods list. Reconcile. Also the LOS >= 24 h criterion is a post-baseline selection on future ICU stay; describe it as a landmark design (alive and in ICU at 24 h) and discuss early-death exclusion as generalisation limit.

m11. Age-stratum pooling: the Methods define 4 strata chosen a priori? State whether cut-points were fixed before results; a sensitivity analysis with age as a continuous covariate (coverage by age decile / spline) would remove the cut-point concern and show the monotone age gradient directly.

m12. Results_draft Limitation 1 still says external validation on eICU "is planned as Phase 6"; Section 2.2 still says findings "extend ... substantially" and "we prove"; the master's status banner says "Open items: eICU external validation not done". Update all.

m13. Hospital heterogeneity: SD 0.045 versus 0.039 expected from binomial noise gives an excess SD of about 2.2 pp; describe it as such (modest) and report hospital-level random-effect variance with CI.

m14. The master reports "103 hospitals with >= 100 patients and >= 20 deaths" while the small-stratum table covers calibration halves; clarify that the death count in the table refers to the calibration half (so a hospital with 20 deaths in total has about 10 in calibration).

---

## E. Editorial

e1. Master Section 5 reference list: order is 1-16, then 18, 19, then 17; renumber. Reference [10] is removed but referenced by "[CITATION NEEDED: add a mortality-prevalence source]" in the Introduction; supply the source (e.g. a multicentre ICU mortality benchmark) or delete the sentence.

e2. Reference [12] (Yang et al., JMIR 2024; DOI 10.2196/50369) still says "[author list to be completed]"; the 09 file already supplies "Yang M, Chen H, Hu W, Mischi M, Shan C, Li J, et al.; J Med Internet Res 2024;26:e50369". The reviewer-response file's data DOI and GitHub URL are flagged as UNVERIFIED and must be checked before submission; the IRB text is UNVERIFIED and should be replaced by the actual MIMIC-IV/eICU data-use and exemption statements (the authors' own institutional determination, if any).

e3. Figure legends (master Section 6) describe a radar plot, a forest plot and a stacked-bar chart that do not match the files; Figure 4 does not exist. The results_draft figure descriptions ("converge precisely", "eliminating the age disparity entirely", "visually proving") should be replaced by neutral descriptions.

e4. Typo "death coverage of to 11.77%" (master Section 3, Mondrian Marginal bullet). Mixed spelling (generalisation / generalization, harmonised / harmonized): pick one.

e5. Replace "harbor hidden disparities", "catastrophic", "collapsed", "non-negotiable", "deep, clinically concerning", "vulnerable" with measured numbers and wording (the 2026-11-20 clean-up missed several; results_draft 1.3, 1.5 and 2.2 still use them).

e6. Prediction-set wording: the reviewer-response file correctly says {0} is not certain survival; apply the same wording in Section 2.3 of the results_draft ("falsely reassured"; "algorithmic certainty").

e7. Add a one-line mathematical explanation in Methods 2.4 that for the nonconformity score 1 - p(y|x) the sets are defined by two risk thresholds; this is the paper's hinge (M1).

---

## F. Methodological Assessment (TRIPOD+AI / STROBE)

TRIPOD+AI (selected items; Met / Partial / Missing)

| Item area | Status | Comment |
|---|---|---|
| Title/abstract identify prediction model, development and validation (T1-2) | Partial | Title lacks outcome horizon (in-hospital, 24 h landmark) and "development and validation"; abstract does not report the external-validation endpoint failure up front |
| Objectives, intended use, population, setting (3-4) | Partial | Intended use of the conformal sets (decision support? triage?) is not specified; this determines which coverage matters |
| Source of data, eligibility, dates (5-7) | Met | MIMIC-IV v3.1 2008-2022, eICU 2014-15; flow counts consistent (94,458 -> 65,366 -> 51,838) |
| Outcome definition, handling of post-discharge death (8) | Partial | In-hospital death only; hospice and transfers to other facilities not discussed; ties to M6 |
| Predictors, time-zero (9) | Partial | 24 h landmark clear; full predictor list and counts (66 vs 72 vs 63) not reconciled; sex/age use not stated |
| Sample size (10) | Missing | No sample-size rationale (e.g. Riley criteria for XGBoost EPV; for subgroup coverage, cell-size justification) |
| Missing data (11) | Partial | Native handling; no subgroup missingness table; indicator check not reported |
| Analytical methods: tuning, class imbalance, calibration, fairness approach (12) | Partial | Hyperparameters/early stopping/imbalance handling absent; fairness metric choice rationale absent; multiplicity not handled |
| Performance measures (13) | Met | AUROC, AUPRC, Brier, slope, intercept, coverage, set size; calibration plots by subgroup should be added |
| Model updating, heterogeneity (14-15) | Partial | Recalibration on eICU explored; hospital-level heterogeneity reported; no random-effect analysis |
| Fairness (TRIPOD+AI) | Partial | Subgroups defined from registration data, categories coarse; Other/Unknown heterogeneous; fairness criteria not mapped to equalised odds |
| Flow, participant characteristics (16-17) | Met | Table 1 present (verified internally: age, race, sex, insurance counts sum to 51,838; deaths sum to 5,522) |
| Model performance with CIs (18-19) | Met/Partial | CIs patient-level; external CIs approximate (seeds reuse patients) |
| Limitations, interpretation, implications (20-22) | Partial | Good list of limits but several stale or contradictory (m12); clinical implications overstated |
| Open science: protocol, code, data, model (23-26) | Partial | GitHub URL and DOI unverified; no registered protocol (hypotheses specified in-project only); model not shared (acceptable) |
| Patient and public involvement | Missing | Not reported |

STROBE (selected)

| Item | Status | Comment |
|---|---|---|
| Study design stated, setting, participants | Met | |
| Variables, data sources, measurement | Partial | Race/insurance definition and the mapping of race categories between MIMIC and eICU are thin |
| Bias | Partial | Selection (>= 24 h), label noise, missingness, temporal heterogeneity not addressed |
| Study size | Missing | See TRIPOD item 10 |
| Statistical methods, subgroups, sensitivity | Partial | Exploratory selection of age acknowledged; multiplicity not controlled; sensitivity analyses limited to feature harmonisation |
| Results: participants, descriptive, outcome | Met | |
| Limitations, generalisability | Partial | Single centre plus 2014-15 external set; stale statements |

Statistical rigour. Strengths: repeated splits, patient-level bootstrap, paired differences, pre-declared failure criterion, hospital-disjoint check, explicit "not causal" language, claim-restriction document. Weaknesses: pseudo-replication across seeds, no hospital clustering in CIs, ecological mechanism analysis, an un-derived minimum-size rule, and no formal handling of multiple comparisons.

---

## G. Falsification Test

The pre-registered/a priori hypotheses (phase6_7 note Section 1; master 2.6) were:

- H-P1: Under pure transport of MIMIC thresholds, death coverage for ages 18-49 in eICU is below 0.90 (replicated if the upper Wilson bound < 0.90).
- H-P2: Under pure transport, survivor coverage for ages 75+ in eICU is below 0.90 (same criterion).

Outcome, honestly assessed:

- H-P1, primary model: not supported (0.902, upper bound 0.926). A genuine falsification. The harmonised model gives 0.819 [0.781, 0.852], so the hypothesis survives only in a sensitivity model. A fair summary is "1 of 2 variants". Moreover, H-P1 as specified is confounded in the other direction: pure transport over-covers decedents overall (0.920), so the primary result is a net of +2 pp shift and a (hypothesised) age effect; a stratum-minus-overall contrast (-1.8 pp primary; -10.9 pp harmonised) is the cleaner test (Analysis 1).
- H-P2, both models: supported (0.748, 0.677), but transport shifts survivor coverage overall to 0.835 / 0.817, so the test is passed for a reason unrelated to age (at the level of the contrast: -8.7 and -14.0 pp, which would count as a stronger result). As specified it was a weak test: any over-prediction shift would pass it.
- The recalibrated eICU age pattern (same direction as MIMIC) is the stronger evidence, but it was not among the declared endpoints and has no confidence interval.

Falsification criteria for the mechanism claim, which the manuscript should declare in advance for the next analyses:

- F1: If, under calibration-implied coverage (Analysis 2), predicted and observed stratum coverage gaps disagree (e.g. slope not near 1 across the 4 age x 2 class cells and across hospitals, or residuals comparable in size to the gaps), the "calibrated scores + base-rate heterogeneity" explanation is rejected.
- F2: If excluding hospice/comfort-care discharges removes most of the 75+ survivor under-coverage, the elderly-survivor finding is a label artefact rather than a threshold mechanism.
- F3: If the age-blind and age-aware models differ in coverage gap but not after age-group recalibration of the age-blind model, then the "tension between calibration and coverage parity" claim stands; if group recalibration of the age-aware model also equalises coverage at no set-size cost, the tension claim is falsified.
- F4: If an age x class Mondrian calibrated on early MIMIC years fails to hold 0.90 +- 0.02 on 2020-2022 test data, the guarantee does not transport over time (a sharper statement than "exchangeability may be violated").

---

## H. Discipline-Specific Check (medical ML / biostatistics)

- Data leakage: first stay only; 24 h landmark; native missingness; no imputation before split. Good. Confirm early-stopping and hyperparameter search use only training data.
- Calibration: marginal calibration reported (slope 1.003, intercept +0.038), age-conditional calibration reported only for the age-blind check (10 seeds). Add calibration curves by age, race and sex for the final model (100 seeds).
- Exchangeability: assumed; tested nowhere except cross-database. Temporal and site split analysis would turn assumption into evidence (Analysis 5).
- Outcome validity: in-hospital mortality with unknown handling of hospice, transfers, DNR.
- Generalisability: one US academic centre plus a 2014-15 multi-centre sample with different definitions.
- Clinical meaning of "coverage": equivalent to sensitivity/specificity of two thresholds; the quantity clinicians act on (P(death | set)) is not controlled and is not reported (Analysis 4).
- Reproducibility: strong in intent (scripts, seeds, independent check), weakened by unverified code URL/DOI and by a non-independent verification script.

---

## I. Cited Evidence Audit (5 spot checks)

Based on my knowledge of the cited works; I did not fetch the papers. Confidence noted.

| # | Citation and where used | Attributed claim | Assessment | Confidence |
|---|---|---|---|---|
| 1 | [14] Lei & Wasserman 2014, J R Stat Soc B (master Intro, para 4): Mondrian / group-conditional conformal | "Mondrian (group-conditional) conformal prediction has been proposed ... [13, 14]" | Not supported. Lei & Wasserman 2014 concerns locally adaptive regression prediction bands; Mondrian conformal is from Vovk (2003 and Vovk et al. 2005, Ch. 4) and Vovk 2012 [13]. Replace [14] | High |
| 2 | [8] Tibshirani et al. 2019 NeurIPS (master Intro, para 2): split CP guarantee "requiring only exchangeability" | Marginal coverage under exchangeability | Mis-attributed. That paper is about weighted conformal prediction under covariate shift; cite Vovk et al. 2005, Papadopoulos 2002 or Lei et al. 2018 for split conformal, and use Tibshirani 2019 only when discussing the eICU shift | High |
| 3 | [16] Lu et al. 2022 AAAI (master Intro, para 5): clinicians "often fear an efficiency penalty" | Cited for the concern that repair expands sets | Not supported as phrased. Lu et al. evaluate fairness of conformal predictors in medical imaging and propose methods for equal coverage; they do not document clinician concern. Cite it for the existence of fair conformal methods in medical imaging, and find a different source (or none) for the concern | Moderate-high |
| 4 | [12] Yang et al., JMIR 2024 (master Intro; results_draft 2.2): "noted demographic equity as an unaddressed limitation" and "AUROC 0.858, error rate 10.5%" | Prior work cautioned on equity | Cannot verify the "limitation" statement: the 09 file read abstracts only, and the abstract-level summary says only "single-population marginal sets, no subgroup audit". The AUROC 0.858 matches the 09 file (internal; 0.800 external). Quote the actual limitation sentence from the full text or soften | Moderate |
| 5 | [5] Vovk, Gammerman, Shafer 2005 and [4] Kompa 2021 (master Intro para 1): UQ "has emerged as a fundamental prerequisite for safe clinical deployment [4, 5]" | Clinical-safety prerequisite | [4] supports the clinical motivation; the Vovk book is a theory text and does not support a clinical-deployment claim. Also [11] Cauchois 2021 is cited for "success on 90% majority while failing 10% minority", which is about conditional-coverage notions in general; the class-imbalance point is better supported by Romano 2020 or Ding 2023 | Moderate-high |

Net: 3 of 5 spot checks fail or are weakly supported, which suggests the whole reference list needs a full-text audit before submission (the 09 file itself warns it only read abstracts).

---

## J. Overall recommendation (constructive)

Major revision before submission, with a good prognosis. Priorities in order: (1) add the two-threshold / equal-opportunity identity and reframe around calibration-versus-coverage tension, transport and repair cost; (2) fix the mechanism analysis (Analysis 2) and the 60-75% / 40-death statements (M3-M5); (3) run the confounder sensitivity (Analysis 3, M6) and the cluster-aware re-analysis of endpoints (Analysis 1); (4) reconcile every number/caption listed in Minor m1-m14 and Editorial; (5) audit the reference list against full texts and complete the TRIPOD+AI items (hyperparameters, predictor list, sample-size rationale, fairness approach); (6) choose a journal tier per the table in B(4), target JAMIA or JBI.

Things to keep exactly as they are: the failed-endpoint reporting, the "claims we should not make" list, the by-construction caveats, the age-blind miscalibration result, and the set-size accounting for each repair.
