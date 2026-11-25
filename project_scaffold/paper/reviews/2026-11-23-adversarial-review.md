---
title: Adversarial peer review - Group-conditional conformal prediction for ICU mortality (MIMIC-IV, eICU-CRD)
reviewer: Reviewer 2 (adversarial)
role: adversarial
date: 2026-11-23
manuscript: /tmp/rev/00_MANUSCRIPT_MASTER.md (+ results_draft.md, phase6_7_FINAL100_NOTE.md, phase8_alternatives_NOTE.md, 09_NOVELTY_POSITIONING.md, reviewer_responses_and_methods_evidence.md, two phase7 CSVs)
reporting_standard: TRIPOD+AI, STROBE
---

# Summary

The authors train one XGBoost mortality model on 51,838 first ICU stays (>=24 h) in MIMIC-IV and apply split conformal prediction (LAC score, alpha=0.10) over 100 random splits of the same patients. Marginal CP covers 23.5% of deaths. Class-conditional CP restores ~90% death coverage overall. Within class-conditional CP, young decedents (84%) and elderly survivors (83%) are under-covered. Group x class Mondrian restores ~90% in every stratum "by construction" at a small set-size cost. eICU-CRD "external validation" has two "pre-specified" endpoints: P1 did not replicate in the primary model and replicated only in a harmonised model that drops the three strongest-shifted predictors; P2 replicated but is confounded by transport shift. A correlational "mechanism" analysis and an age-blind ablation attribute the gap to base-rate-shifted scores under a pooled threshold.

What I can verify is internally careful in places. The draft has already been stripped of "first" and "provable" in the master file, and the failed P1 is reported. But the paper has three structural problems.

1. Nearly every positive result is either by construction (Mondrian restoration, 90% marginal and class-conditional coverage), a known result (marginal CP failure for the rare class; pooled-threshold distortion), or a mechanical consequence of the score definition (age gap, "replication" of its sign, the hospital-level "mechanism").
2. The one empirical claim that could be non-trivial, that the age gap is real, replicates externally only in a degraded model and is statistically indistinguishable from nominal in the primary eICU model (about 1 SE, computed below).
3. Statistical uncertainty is understated, the clinical meaning of the "equity" is never established, and the text still contains stale or overreaching statements.

Verdict: **MAJOR REVISION**, bordering on reject in current form. A rigorous reframing is needed, with demonstrably non-circular analyses. See the minimum-change list at the end.

# Major Issues

**M1. In a binary task, class-conditional "coverage" is sensitivity/specificity, and Mondrian-by-group is group-specific operating-point equalisation. The paper does not say this, and the novelty claim depends on not saying it.**
- Section 2.4, LAC score s = 1 - p(y|x). The set contains 1 iff p >= 1 - q1 and 0 iff p <= q0. Death coverage is exactly sensitivity at threshold 1 - q1. Survivor coverage is specificity at q0.
- "Death coverage 84% in young" means "sensitivity 84% at the pooled 90%-sensitivity threshold". Mondrian-by-age means age-specific thresholds. This is equalised-odds/equal-opportunity post-processing (Hardt et al. 2016), with a conformal finite-sample quantile. The "dual-label" set is the grey zone between two thresholds.
- None of this is cited. The paper does not cite Hardt 2016, Pleiss et al. 2017 (calibration vs equalised odds incompatibility), Sadinle-Lei-Wasserman 2019 (set-valued classifiers with class-wise error bounds), or Vovk's Mondrian/class-conditional original work.
- The paper's own late finding, that "coverage parity does not imply calibration parity" (age-blind ablation), is the Kleinberg/Chouldechova/Pleiss impossibility result. It is not a discovery.
- Requested: state the equivalence explicitly, and compare against plain age-specific sensitivity-matched thresholds (the same predictions, no CP vocabulary). If the CP framing adds nothing in a binary two-class problem, say so.

**M2. The headline "disparity" is largely a restatement of the base-rate/score relationship, with no demonstration that it is an equity problem.**
- Any attribute correlated with predicted risk will show class-conditional gaps. Conditioning on predicted-risk deciles itself gives death coverage ~0% in the lowest decile, which is the Barber et al. 2021 impossibility the authors cite as [9].
- Age is a proxy for prior risk. Young decedents are low-risk per the model, so their scores are high. Nothing demographic or discriminatory is demonstrated. The pre-specified "equity" framing, and wording such as "systematically fails vulnerable subpopulations" and "irrespective of age, insurance coverage, or racial background", is not supported.
- Race and sex show nothing material. The insurance gaps are confounded with age and not adjusted: Private is young and low-prevalence (7.1%), Medicare is old. In the phase7 CSV, Medicare death coverage is 0.914 and Private is 0.865, which is the age gradient. The "15 single subgroups" are overlapping partitions of the same patients, not 15 independent audits.
- The language "falling 5.94 pp below the nominal guarantee" (Section 1.3; Abstract) is wrong. No guarantee is breached. Class-conditional CP guarantees marginal class-conditional coverage, not group-conditional coverage. The gap is expected from theory and cited [9]. Replace "guarantee" and "breach" language throughout.

**M3. Clinical relevance of a 6 pp sensitivity gap is not established, and the CP sets themselves are not evaluated against any decision.**
- The absolute effect: young stratum mortality 6.33% x 5.94 pp = ~3.8 additional missed deaths per 1,000 young ICU patients, relative to a pooled-threshold set. No decision (triage, escalation, goals-of-care) is specified for which a {survive}-only set changes management.
- The 25.7% dual-label sets are the output for a quarter of patients. The authors call them "inconclusive". "Negligible efficiency penalty" is judged only by mean set size.
- The clinically relevant conditional quantities are never reported: P(death | set = {survive}) and P(death | set = {die}) (NPV/PPV of the singleton sets), and by subgroup. Coverage given Y says nothing about error rate given the set shown to the clinician.
- No comparison with a plain risk threshold or SOFA/APACHE-style baseline.

**M4. The "pre-specified" external endpoints are not credibly pre-specified and are badly designed.**
- Sections 2.6 and 3 say endpoints were "specified before the final run". The age finding was highlighted after inspecting MIMIC results (stated in the abstract). The status banner (2026-11-20) says eICU validation was "not done". The note filenames ("FINAL100") imply earlier runs with fewer seeds. There is no registration, timestamp, or commit hash. "Pre-specified" is not supportable unless the authors provide dated evidence. Otherwise describe it as "a priori hypotheses formed after the MIMIC analysis".
- The "pre-specified harmonised model" is stated as such in Methods, but it is the only model in which P1 passes. The primary model fails P1 (0.902, upper Wilson 0.926, and the point estimate is above 0.90). Whether the harmonised model was truly pre-specified or conceived after the P1 failure cannot be determined. Hence it is a plausible post-hoc rescue; the abstract admits P1 replicated "only" there, which is honest but does not remove the concern.
- P1 and P2 are defined under pure MIMIC->eICU transport. Transport inflates death coverage (0.920 overall, because eICU risk is over-predicted, CITL +0.042) and deflates survivor coverage (0.835). P1 is therefore biased against replication, and P2 is trivially satisfied (the overall survivor coverage is already 0.835; the 75+ survivors at 0.748 are simply lower still). P2 "replicated in both" has essentially no evidential value, as the authors concede. The correct test of the age hypothesis is the within-eICU contrast under recalibration. That was not the pre-specified endpoint.
- Under eICU recalibration (the setting that actually isolates the group effect), the primary-model young death coverage is 0.884. The young eICU decedents number 890 in total (phase7 CSV), so ~445 per 50% test half. SE = sqrt(0.884 x 0.116 / 445) = 1.5 pp. The deficit from 0.90 is 1.6 pp, i.e. ~1 SE, not distinguishable from nominal. The abstract's "the age pattern ... persisted after local recalibration" is thus unsupported for the primary model. Only the harmonised model (0.778) shows a clear gap.
- The "hospital-disjoint splits gave the same values to the third decimal" for P1/P2 is uninformative. Under pure transport the eICU calibration half is never used (thresholds come from MIMIC), so hospital-disjointness changes nothing but which random half is the test set. It cannot be presented as a robustness check for those endpoints. For the eICU-recalibrated results it is meaningful (0.881 vs 0.884).
- The eICU "replication" of the age pattern is a sign test on a gradient that is nearly guaranteed by the mechanism: eICU prevalence rises 5.0% -> 13.1% with age, the model is calibrated-ish, so the sign must follow. A hypothesis that cannot fail is not a strong replication.

**M5. The harmonised model result undermines the generality claim and exposes model dependence.**
- The harmonised model drops temperature, GCS, and intubation. These are likely among the highest-gain predictors. The young-decedent gap goes from 0.884 (primary) to 0.778 (harmonised); in MIMIC it is 0.84. A 10-pp swing in the headline quantity from deleting three features shows the "hidden disparity" is a property of how much a given model relies on age and base-rate proxies, not a general property of "standard conformal prediction algorithms in healthcare" (Abstract, Conclusions).
- Only one model class (XGBoost), one score (LAC), and one alpha (0.10) were run. There is no logistic regression, no recalibrated model (Platt/isotonic), no alpha sweep (0.05, 0.2), no alternative score. The title and abstract generalise from n=1 model class, n=1 alpha.
- The age-blind ablation has no control ablation. Removing any strong feature changes score distributions; a placebo ablation (drop a feature with comparable gain, or permute age) is needed to show that age specifically, rather than any perturbation, shrinks the gap.

**M6. The mechanism section is circular, ecologically confounded, and over-interpreted; the phase-8 ablation overstates its effect.**
- The hospital-level correlation between death-coverage gap and mean predicted risk among decedents (Spearman 0.79; I reproduce 0.786 from the phase7 CSV) is nearly tautological. Death coverage is P(p >= 1 - q1 | Y=1), and mean predicted risk among decedents summarises the same distribution of the same deaths. They also share sampling noise: with 20-320 deaths per hospital (median 59), the Pearson correlation between mean_p_deaths and cov_deaths is 0.74 in the CSV. This is a measurement-error artefact as much as a finding.
- The hospital AUROC and prevalence correlations (0.42, 0.23 in my recomputation) are modest. The note's own R-squared is 0.22-0.30.
- Across "four age strata", any two monotone-in-age quantities yield |rho| = 1; with n=4 there is no inference. The 15 (MIMIC) / 11 (eICU) "demographic strata" are overlapping partitions of the same patients (age, race, sex, insurance), so effective n is far below 15. In eICU main the correlations are non-significant (0.42 n.s.), and in the CSV eICU race and sex strata are essentially flat (0.89-0.91), so the eICU "mechanism" rests on the four age rows.
- The mechanism table mixes designs: MIMIC strata use out-of-sample MIMIC-calibrated thresholds; eICU strata use thresholds fitted on all eICU data and evaluated on the same patients (in-sample; Section 2.7). These are not comparable.
- The ablation claim "gap shrinks roughly 60-75%" is true only for MIMIC (death 0.060->0.015 = 75%; survivor 0.070->0.027 = 61%). In eICU it is 32% (death 0.019->0.013) and 52% (survivor 0.056->0.027). The eICU death-side pooled gap was only 0.019 to begin with. Master Section 3 and phase8 NOTE should not generalise.
- Removing age makes the young over-predicted (CITL +0.023), so decedents' scores rise and coverage improves. This is exactly offsetting miscalibration, not evidence that "the gap arises from base-rate-shifted scores under a pooled threshold" beyond what theory already gives (Gao 2026a). The authors concede it is not causal; the Discussion/Abstract/09 file still call it "mechanism evidence beyond correlation".
- Unconsidered alternative mechanisms: age-dependent withdrawal of care/DNR/comfort-measures (older decedents are more often predictable, young deaths more sudden, e.g. overdose, trauma, haemorrhage); age-dependent exclusion of deaths in the first 24 h; discharge to hospice counted as survival (MIMIC `hospital_expire_flag` = 0), which is age-differential outcome misclassification; case-mix heterogeneity of young decedents.

**M7. Selection, outcome, and measurement choices that plausibly change the age pattern are untested.**
- The >=24 h ICU LOS filter (13,528 stays removed) conditions on survival and on staying; it removes early deaths, differentially by age. The stated rationale ("exclude hyper-acute trauma or palliative discharges") is an assertion without data. The FAQ claim that SAPS-II/APACHE-IV exclude <24 h stays is incorrect; those scores include patients who die early. No sensitivity analysis (e.g. >=12 h, or all stays with prediction at a different landmark).
- First-stay only: changes case mix, no sensitivity analysis.
- The in-hospital mortality definition is undescribed with respect to hospice discharge, comfort-measures-only, and transfers. In eICU, transfers to other hospitals count as survivors. The authors acknowledge "outcome coding differs" but did not quantify.
- GCS and lactate: GCS mean 9.8 (MIMIC) vs 12.6 (eICU) and intubation 45% vs 18% show the predictors are not the same construct, so the "primary" eICU model is not a like-for-like external validation. Lactate is measured selectively (informative missingness, handled natively, not discussed). Race coding differs between databases (not mappable one-to-one).
- Random splits within one centre over 2008-2022 satisfy exchangeability trivially. The paper audits "validity" only in the one setting where validity is guaranteed. Temporal validation (train early MIMIC, test late) is absent, and the one real shift test (eICU) shows the guarantee fails (survivor coverage 0.835). This is the paper's clinically most important result and it is under-emphasised relative to the age story.

**M8. Uncertainty quantification is not valid for the stated inferences.**
- 100 seeds reuse the same 51,838 patients. The across-seed SD measures split resampling, not population sampling. The patient bootstrap resamples only test predictions and ignores training/calibration variance (no nested bootstrap). Neither supports the "hierarchical bootstrapping ... robust standard errors" claim in results_draft 2.4. The Wilson intervals on per-seed mean counts in eICU (Section 2.6) are approximate in an unknown direction; the authors say they are "somewhat narrow", but the Wilson n is the test-half count. A cleaner design is a nested (outer patient bootstrap, inner full re-fit) or K x repeated cross-fitting with a patient-level cluster bootstrap over the whole pipeline.
- The binomial-SE argument (results_draft 1.4) says test sampling of 151 deaths explains "the vast majority" of the 3.0-3.5% seed SD. 2.44^2 / 3.26^2 = 56% of the variance; "vast majority" is overstated.
- Multiplicity: 15 strata x 2 classes x 3 methods plus 4 race comparisons versus White; Asian survivors -2.10 pp has CI [-3.53, -0.50], which would not survive any multiplicity correction. There is no formal heterogeneity test. A single pre-registered model would be: death-coverage indicator ~ age (continuous, spline) among decedents, with cluster-robust SE.
- The age cut-points (18-49, 50-64, 65-74, 75+) were not justified a priori. Continuous-age coverage curves would remove the forking path.
- Small-stratum rule: the rule "use group x class calibration only with >= ~40 calibration deaths" does not follow from the table. Hospital-specific thresholds match or are worse than pooled in mean deviation at every size (0.047 vs 0.046 at 40-79; 0.032 vs 0.030 at 80+). So there is no size at which group-specific wins in mean deviation; ~40 is where parity is reached, not where benefit appears. The tail share <0.80 favours hospital-specific at 40-79 (0.042 vs 0.065) but not at 80+ (0.012 vs 0.003). "84% infinite threshold when <10 cal deaths" is a mathematical fact (rank ceil(0.9(n+1)) > n for n <= 8), not an empirical finding. The hospital-seed denominators (3309+3898+3413+1941+1383 = 13,944) exceed 103 hospitals x 100 seeds = 10,300, so the hospital set used is not the one stated; it is undefined in Methods. The rule is also derived on hospitals as groups, with no true coverage bias (SD 0.045 vs 0.039), so it says little about when Mondrian is needed.

**M9. Novelty positioning (09 file) is more generous than the evidence supports in four places.**
- 09 is commendably honest in Section 5 ("do not claim first"). But Section 4 still lists as distinctive: (1) "replicated externally ... with pre-specified endpoints" (see M4: failed in primary, trivial for P2); (3) "mechanism evidence beyond correlation" (see M6); (5) the 40-death rule (see M8); (2) "transport shift vs group heterogeneity separated" is the standard class-conditional-under-label-shift decomposition (Opoku 2026 per the file's own Theme 3), and the paper does not separate them formally.
- Themes 1-3 (8+3+4 of 21 papers) already contain the Mondrian repair, pooled-threshold distortion theory (Gao 2026a), and marginal CP failure on the rare class with class-conditional repair in ICU (Yu 2026: 1.4%/0.0% marginal; 91.6%/84.9% class-conditional; Opoku 2026 AKI). The paper's 23.5% death coverage is a replication, as the file says. After removing these, the remaining distinctive element is "age pattern in MIMIC/eICU", which is M2.
- The search is abstract-only, single-index (OpenAlex), 16 queries, with a "n of 21" count that the file itself says is not systematic. Most closest competitors are 2026 preprints or an OSF registration with no results; I cannot independently verify these identifiers and the file says some could not be checked. A Q1 reviewer will expect full-text reading and a PRISMA-style or at least reproducible search. It omits Hardt 2016, Pleiss 2017, Sadinle 2019, Vovk's Mondrian, and the fairness-of-subgroup-thresholds literature in clinical risk scores (M1).
- Reference spot-checks (5):
  1. Yang 2024 JMIR (ref 12, results_draft 2.2): I fetched the paper. AUROC 0.858 internal and 0.800 external (so "AUROC 0.858" is the internal figure only), error rate 10.5% (internal). The paper says only "this work was not designed to directly address generalizability and bias issues". It does not "cite demographic fairness as an unaddressed limitation" in the sense claimed, and does not report subgroup performance. "Our findings empirically confirm their cautionary notes" overreaches.
  2. Ref [8] Tibshirani et al. 2019 (covariate shift) is cited for the basic split-conformal guarantee. Wrong source (use Vovk/Papadopoulos or Lei et al. 2018).
  3. Ref [14] Lei & Wasserman 2014 (regression bands) is cited for Mondrian/group-conditional CP. Not about Mondrian.
  4. Ref [16] Lu et al. 2022 (medical imaging fairness) is cited for "clinicians often fear an efficiency penalty". It does not establish clinician attitudes.
  5. Ref [15] Romano et al. 2020 equalized coverage is cited for the statement that group-conditional calibration without class conditioning leaves minority-class coverage low "at prevalence near 10%". The paper concerns equal coverage across groups, not that specific statement. Also "[11] Cauchois" is cited for ICU class-imbalance failure, which is not what it is about. The reference list is also out of order (17 after 19) and still has "[CITATION NEEDED]" and a "[REMOVED]" entry.

# Minor Issues

1. **Stale and inconsistent text.** The status banner and results_draft 2.5(1) say eICU validation is "planned as Phase 6" / "not done", while the abstract and Section 3 report it. Figure 3 caption says ">82% of patients across all subgroups retain definitive singleton predictions" and "exact group-conditional coverage"; the body says 62%-87% (lowest 62% in 75+). Fig 4 legend claims negative CITL "partially accounting" for young under-coverage, but the age-blind result implies the opposite sign and Fig 4 does not exist. Figure legends 1-3 describe chart types that do not exist (TODOs in file).
2. **Language not cleaned.** results_draft still says "we prove that marginal validity masks deep intra-group gaps and establish the precise mathematical calibration framework" (2.2), "eliminating the age disparity entirely" (Fig 1 panel C), "mathematically guaranteed, equitable uncertainty quantification" (2.6), "negligible efficiency penalty", "strictly bounded". The master file claims these words were removed; they were not removed from the supporting draft. Nothing was proved; the framework is existing.
3. **Verification claim is inconsistent.** Methods 2.5 says independent recomputation "within a strict absolute tolerance < 0.0005"; results_draft 2.4 says "0.000000". Further, my comparison of the phase7 CSV with Table 3 values gives discrepancies larger than 0.0005: Hispanic death coverage 0.8703 (CSV, MIMIC test, global thresholds) vs 87.62% (Table 3/abstract); race survivor differences vs White from the CSV are -1.94, -1.22, -1.38, +2.12 pp vs -2.10, -1.30, -1.44, +2.16 pp in the text. These may reflect different estimators (mean of ratios vs ratio of means), but then the "independent check" cannot be exact. Also an "independent check" that recomputes from the same stored predictions cannot detect leakage or pipeline error.
4. **Suspicious duplicate number.** Calibration slope SD 0.0383 and calibration intercept mean +0.0383 (Section 1.2) are identical; likely a copy error.
5. **Possible undisclosed stratified splitting.** In the phase7 MIMIC rows, the mean test death counts for several small race strata are exactly integer to two decimals (Asian 39.00, Hispanic 39.00, Black 103.00, Other/Unknown 398.00; age 18-49 151.00) while total n is not (e.g. Black 1141.71). A genuinely random split gives mean counts with SD ~1 (e.g. SD of 604 x 0.25 x 0.75 count is ~10.6 per split, ~1.1 on a 100-split mean). This suggests splits are stratified by race x outcome (or similar). That is not described in Methods and affects the variance interpretation ("~39 deaths per test split", "random splits", binomial SE argument). Please clarify.
6. **Quantile formula and threshold fallback.** Mondrian cells with unattainable rank get q = +inf (full set). That is an arbitrary conservative policy that inflates coverage and set size in small cells; the reported variability (78%-100%) partly reflects it. Report set sizes for those cells.
7. **Mean-of-100-seeds tables** hide split-level failures. Report fraction of seeds where each stratum's death coverage < 0.85, and the distribution, not only means.
8. **Hyperparameters/early stopping** are not described. If early stopping or tuning used the calibration split, exchangeability is violated. TRIPOD+AI requires this. Also missing: sample-size justification, handling of the single model's calibration plots, decision-curve or net-benefit analysis, model comparison baseline, and fairness-evaluation items.
9. **Eligibility arithmetic is fine** (94,458 - 29,092 = 65,366; - 13,528 = 51,838; stratum sums reconcile: 9,540+15,156+12,162+14,980 = 51,838; deaths 604+1,343+1,271+2,304 = 5,522). Set size change 1.147 -> 1.176 = +0.029 / 1.147 = 2.53%, not 2.57% (rounding; check). 75+: +0.021 vs +0.020. Minor.
10. **Intended Mondrian use of protected attributes at deployment** (age/race at test time) raises disparate-treatment and legal concerns, in contrast to the reviewer-FAQ claim that race/insurance were "strictly omitted ... to prevent algorithmic encoding" (used as Mondrian partition keys). Discuss.
11. **Unverified items.** The reviewer_responses file labels the IRB text, DOI, and GitHub URL as UNVERIFIED; they must be verified before submission. There is no eICU ethics/DUA statement. The "Target venue: JAMIA / Lancet Digital Health" line must be removed from a submission.

# Editorial

- Remove the dual target venue line, the TODO/CITATION NEEDED markers, and the draft banner; reconcile the master file and results_draft into a single manuscript (the master defers to `paper/results_draft.md`, which is stale).
- Retitle: the current title ("for Equitable Uncertainty Quantification") over-promises. Something like "Class- and age-conditional coverage of conformal ICU mortality prediction: an audit in MIMIC-IV and eICU-CRD" matches the evidence.
- The abstract Discussion paragraph is too long and contains eICU results that belong under Results. Define "coverage", "singleton" and "set size" for a clinical readership; show a worked example (N patients, N deaths missed).
- Cut "Clinical Fairness Shield", "radar" and emoji-style figure titles. Replace dense numeric bullets with tables.
- Use "sensitivity-equivalent" language alongside "coverage" so clinicians can follow.

# Methodological Assessment (TRIPOD+AI / STROBE)

| Item | Assessment |
|---|---|
| Source of data, dates (TRIPOD 4, STROBE 5) | Present for MIMIC-IV; eICU ethics/DUA statement missing. |
| Participants, eligibility, flow (STROBE 6, 13) | Flow numbers reconcile. Selection effects (24 h LOS, first stay, hospice/comfort care) not examined. |
| Outcome definition (TRIPOD 6a) | Under-specified (hospice, transfers, comfort-measures; eICU coding). |
| Predictors (TRIPOD 7) | Listed; lactate/GCS/intubation definitions not equivalent across databases; informative missingness not discussed. |
| Sample size (TRIPOD 8) | No justification; subgroup power (Asian/Hispanic ~39 test deaths) acknowledged. |
| Missing data (TRIPOD 9) | Native XGBoost handling; sensitivity analysis absent. |
| Model building, tuning, validation (TRIPOD 10, 13) | Hyperparameters/early-stopping not given; no temporal validation; random splits only; single model class. |
| Performance measures (TRIPOD 16) | AUROC/AUPRC/Brier/slope reported; no calibration plot, no decision-curve/net-benefit, no comparison model. |
| Fairness (TRIPOD+AI) | Subgroup coverage reported; age cut-points and attribute choice post hoc; multiplicity uncontrolled; overlapping attributes unadjusted. |
| Statistical methods, uncertainty (STROBE 12) | Seeds reuse patients; bootstrap omits training/calibration variance; Wilson on mean counts approximate; no heterogeneity test. |
| Bias (STROBE 9) | Not addressed beyond limitations list. |
| Open science | Code URL, DOI and IRB text flagged UNVERIFIED; no data/code release for eICU pipeline; no pre-registration artefact. |
| Overall | Does not meet TRIPOD+AI/STROBE in several items above. |

# Falsification Test

**Hypothesis (from the Abstract/Methods):** (H1) standard split CP, even class-conditional, under-covers young decedents and elderly survivors because the model shifts scores with age under a pooled threshold; (H2) Mondrian by age restores coverage at small set-size cost; (H3) the pattern replicates in eICU (P1: young death coverage, P2: elderly survivor coverage under pure transport, "replicated" if upper Wilson bound < 0.90).

**Outcome against own criteria:**
- P1 in the primary model: **fails** (0.902, [0.870, 0.926]). Passes only in the harmonised model (0.819). P2 passes, but its pass is guaranteed by the transport survivor shortfall (overall 0.835) and says nothing about age.
- Under eICU recalibration the primary young-decedent deficit (0.884) is ~1 SE from nominal.
- H2 cannot fail (it is a coverage guarantee for each cell by construction) and H1's sign cannot fail given prevalence rises with age. The only falsifiable quantities are magnitude and model-dependence; the magnitude fell from 6 pp (MIMIC) to 1.6 pp (eICU primary) and rose to 12 pp (harmonised).

**Falsification criteria the authors have not stated, and which I would apply:**
1. Placebo ablation: removing a feature of equal gain (or permuting age) shrinks the gap equally => the age-specific mechanism is not supported.
2. A logistic-regression and/or Platt-recalibrated model shows no age gap => "hidden disparity of standard CP" is a property of the XGBoost configuration.
3. Continuous-age coverage curves with cluster-robust inference show no monotone trend after excluding the post-hoc age cut-points.
4. Age-specific sensitivity-matched thresholds (no CP) reproduce every Mondrian result => CP adds nothing.
5. Alpha sweep: the gap vanishes at alpha=0.2 or is larger at 0.05 => alpha-dependence.
6. Temporal split in MIMIC: Mondrian guarantees fail under temporal drift => validity claims should be confined.
7. Sensitivity to >=12 h LOS, hospice-as-death, and comfort-care exclusion: pattern disappears => selection artefact.

**Evidence audit (claim / evidence / GRADE-style strength / main unaddressed confounder or fallacy):**

| Claim | Evidence type | Strength | Confounders / fallacies |
|---|---|---|---|
| Marginal CP covers 23.5% of deaths | Single-centre internal, 100 resamples | High for the number; **not new** (Yu 2026, Opoku 2026, Ding 2023) | Reported as discovery in places. |
| Young decedents under-covered (84%); elderly survivors (83%) | Internal subgroup estimate, post-hoc selection | Low-moderate (post hoc, forking path, same-patient resamples) | Base-rate/risk proxy; hospice/DNR; early-death exclusion; multiplicity. Framing as "breached guarantee" is a fallacy. |
| Pattern replicates in eICU | Pure-transport P1/P2 (fails/trivial); recalibrated (1 SE in primary, large only in degraded model) | Low | Transport shift; non-equivalent predictors; sign guaranteed by prevalence gradient. |
| Mondrian restores ~90% at small set-size cost | By construction; coverage and mean set size only | High but **circular** | No conditional error rates (NPV/PPV); small cells inflated by +inf fallback. |
| Gap is caused by age-shifted scores under pooled threshold | Ecological correlations (n=4 / overlapping 15); age-blind ablation without placebo | Very low | Circular hospital-level metric; collinearity; measurement error; offsetting miscalibration. |
| Risk-bin Mondrian is less efficient | Two bin counts, 100 resamples | Moderate | Only 5/10 quantile bins; tuned number of bins not explored. |
| 40-death small-stratum rule | One database, hospitals as groups | Low | No benefit shown at any size; undefined hospital set. |

# Cited Evidence Audit (5-row table)

| # | Citation / claim | What the source actually says | Verdict |
|---|---|---|---|
| 1 | Yang 2024 JMIR (ref 12; results_draft 2.2): "AUROC 0.858, error 10.5%; cited demographic fairness as an unaddressed limitation" | Verified by fetch. AUROC 0.858 internal (eICU external 0.800); 10.5% internal error. Mentions only that the work "was not designed to directly address generalizability and bias issues". No subgroup results. | Partly supported; stretched ("confirm their cautionary notes"). |
| 2 | Tibshirani et al. 2019 (ref 8): basic split-CP guarantee | Covariate-shift extension, not the basic guarantee. | Wrong source. |
| 3 | Lei & Wasserman 2014 (ref 14): Mondrian/group-conditional CP | Regression prediction bands; not Mondrian. | Mis-cited (Vovk). |
| 4 | Lu et al. 2022 (ref 16): clinicians fear an efficiency penalty | Fair conformal predictors for imaging; does not document clinician concerns. | Unsupported attribution. |
| 5 | Romano et al. 2020 (ref 15) and Cauchois 2021 (ref 11): marginal vs minority-class coverage failure at ~10% prevalence | Equalized coverage across groups and valid intuitive sets; neither makes the stated ICU-prevalence claim. | Loosely supported at best. |

(Further 2026 preprint identifiers in 09 were not verifiable by me; per the file itself some were unchecked.)

# Overall Recommendation

**Major revision (current form is close to reject).** The empirical audit is large and carefully caveated in the master file, but the contribution is mainly a re-demonstration of known properties, the external replication is weak, uncertainty is understated, and the mechanism is circular.

## Minimum changes to move to "minor revision"

1. Reframe honestly (title, abstract, aims): an audit of class- and age-conditional coverage with a mechanism check, not a repair method; state the sensitivity/specificity equivalence (M1) and compare against age-specific sensitivity-matched thresholds; cite Hardt 2016, Pleiss 2017, Sadinle 2019, Vovk.
2. Remove "guarantee breached", "we prove", "eliminates entirely", "irrespective of..."; reconcile the master and results_draft files (stale Phase 6 text, ">82%" figure legend, Fig 4, tolerance statement, duplicated 0.0383).
3. Provide dated evidence (commit hashes, timestamps) for the pre-specification of P1/P2 and the harmonised model, or relabel them as a priori hypotheses formed after seeing MIMIC; present the within-eICU recalibrated contrast with a proper CI as the primary external test, and state plainly that the primary-model deficit (0.884) is about 1 SE from nominal.
4. Fix the uncertainty: nested patient-level bootstrap over the full pipeline; a formal test of coverage vs continuous age with cluster-robust SE; multiplicity control; adjust insurance/race for age; drop the hospital-disjoint "same to third decimal" claim for P1/P2.
5. Rebuild the mechanism analysis: delete or de-emphasise the mean-predicted-risk correlation (circular, shared noise); add a placebo ablation and at least one other model class (logistic regression, recalibrated XGBoost) and an alpha sweep (0.05, 0.10, 0.20); correct the "60-75%" statement to MIMIC only (eICU 32%/52%).
6. Add sensitivity analyses for selection and outcome: >=12 h LOS (or other landmark), hospice-as-death, comfort-care exclusion, temporal MIMIC split.
7. Report set-conditional error (P(death | {survive}), P(death | {die}), by age), absolute counts of missed deaths, and one concrete decision context; add a risk-threshold baseline.
8. Clarify split design (is it stratified by race x outcome?), hyperparameter/early-stopping data, hospital set in the small-stratum analysis (13,944 vs 10,300 hospital-seeds), and reconcile Hispanic death coverage (87.62% vs 0.8703) and race survivor differences with the independent check.
9. Rewrite the literature positioning from full texts, with a reproducible search, correct mis-cited references [8], [14], [16], [11], [15], and verify all identifiers; remove or relabel the 40-death "rule" as a descriptive observation.
10. Complete TRIPOD+AI/STROBE checklists and verify IRB/DOI/GitHub/eICU DUA statements.
