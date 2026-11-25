> **STATUS (2026-11-24): Sections 2.9–2.10 and the Phase 9/10 results bullets were added; title, abstract objective/conclusion and aims were reframed on 2026-11-24 (neutral wording); body and references still need the open items in fixlist Section E. Notes: `paper/phase9_endpoint_contrasts_NOTE.md`, `paper/phase10_calibration_implied_NOTE.md`.** (Earlier status:) DRAFT — updated 2026-11-22 with eICU-CRD external validation (100 seeds) and mechanism analysis; numbers from `paper/phase6_7_FINAL100_NOTE.md`, still pending author review.** (Earlier note, 2026-11-20:) Edited after independent review: removed 'first audit', 'catastrophic', 'exact 90%' and 'provable' wording; fixed reference [12]/[15]/[16] and figure file names. Open items: eICU external validation (Phase 6) not done; age finding is exploratory; see `07_REVIEW_FIXLIST_2026-11-20.md`.

# Age-Related Coverage Differences of Class-Conditional and Group-Conditional Conformal Prediction for ICU Mortality: A Retrospective Study in MIMIC-IV with External Validation in eICU-CRD

**Authors:** [Author Names Anonymized for Peer Review / Author List]  
**Affiliations:** [Department / Institution]  
**Target Venue:** *Journal of the American Medical Informatics Association (JAMIA)* / *The Lancet Digital Health*  
**Reporting Guidelines:** TRIPOD+AI & STROBE

---

## Abstract

### Objective
Clinical machine learning models predicting intensive care unit (ICU) mortality often lack statistical guarantees on individual predictions, and coverage that holds on average may differ across patient subgroups. We evaluated whether standard split conformal prediction gives similar coverage across age, race/ethnicity, biological sex, and insurance payer groups, and examined whether group-conditional (Mondrian) calibration reduces subgroup coverage differences and at what cost in prediction set size.

### Materials and Methods
In a retrospective cohort study of the MIMIC-IV v3.1 database, we analyzed 51,838 adult patients with first ICU admissions lasting at least 24 hours (overall in-hospital mortality: 10.65%, 5,522 deaths). We trained gradient boosted decision trees (XGBoost) over 100 independent random train/calibration/test (50/25/25) splits to predict in-hospital mortality using first-24-hour physiological vitals and laboratory measurements. We evaluated standard marginal split conformal prediction, standard class-conditional split conformal prediction, and Mondrian (group-conditional) conformal predictors at a nominal 90.0% coverage level ($\alpha = 0.10$). Subgroup coverage, calibration-in-the-large (CITL), and prediction set efficiency were evaluated using patient-level bootstrapping (B = 1,000) and across-split standard deviations (seed SD).

### Results
The baseline predictive model demonstrated robust discrimination (mean AUROC: 0.8726, split SD: 0.0042; AUPRC: 0.5023). Standard split conformal prediction achieved nominal overall coverage (90.02% marginal) but only 23.52% coverage among decedents; class-conditional split conformal gave 90.14% coverage for deaths. However, subgroup auditing (exploratory; age was highlighted after inspecting results) revealed marked age disparities: young decedents (aged 18–49) experienced substantial under-coverage (84.06% class-conditional death coverage [patient bootstrap 95% CI: 81.43%, 86.72%]), falling 5.94 percentage points below the nominal guarantee. As expected given 10.65% prevalence, group-conditional calibration without class conditioning (Mondrian marginal) left decedent coverage far below nominal (11.77%–39.79% across age groups), because survivors dominate each group's threshold. Mondrian class-conditional calibration, which targets nominal coverage by construction, brought mean death coverage to approximately 90% in every audited stratum (age 18–49: 90.42%; paired bootstrap difference +6.25 pp [+5.21, +7.32 pp]); in the smallest strata (Asian, Hispanic; about 39 deaths per test split) split-to-split coverage remained highly variable (about 78%–100%). The mean change in prediction set size was small (at most +0.058 labels per patient; +2.57% for age 18–49), and 62%–87% of patients per stratum retained singleton predictions (lowest in age 75+, 62%).

### Discussion & Conclusion
In these data, standard conformal prediction showed age-related coverage differences that track subgroup score distributions (base rates), not demographic attributes as such. In clinically imbalanced settings, class-conditional (and, for subgroup reporting, group-by-class) calibration is needed to obtain meaningful coverage for decedents. Mondrian class-conditional conformal prediction gives group-level coverage guarantees by construction under exchangeability, at a small average set-size cost; stability in small strata and generalisation beyond a single centre remain to be shown. In an external eICU-CRD validation, the age pattern (young decedents and elderly survivors under-covered) persisted after local recalibration, group-by-class calibration restored nominal coverage in every age stratum, and pure cross-database transport of MIMIC thresholds under-covered survivors; the absolute young-decedent endpoint replicated only in a feature-harmonised sensitivity model. As a post-hoc stratum-minus-overall contrast with hospital-cluster intervals, the young-decedent deficit was small in the primary model (about −2 percentage points) and large in the harmonised model (about −11 points).

---

## 1. Introduction

Intensive care units (ICUs) demand rapid, high-stakes decision-making under acute physiological uncertainty. While modern machine learning algorithms—such as deep neural networks and gradient-boosted decision trees—achieve high discriminative performance in predicting clinical deterioration and in-hospital mortality [1], point probabilities output by these models frequently lack formal statistical calibration [3]. In safety-critical clinical environments, an overconfident incorrect prediction can delay life-saving interventions or misguide triage decisions. Consequently, equipping algorithmic predictions with mathematically rigorous uncertainty quantification has emerged as a fundamental prerequisite for safe clinical deployment [4, 5].

Conformal prediction provides a distribution-free, finite-sample framework that converts heuristic risk probabilities into valid prediction sets with guaranteed error bounds [6, 7]. For a pre-specified nominal miscoverage level $\alpha$ (e.g., $\alpha = 0.10$, corresponding to 90% coverage), split conformal prediction guarantees that the true patient outcome is contained within the output prediction set with probability at least $1 - \alpha$, requiring only exchangeability between calibration and test data [8]. 

However, standard conformal prediction only ensures *marginal* validity over the population as a whole [9]. In real-world clinical medicine, populations are heterogeneous, and clinical outcomes are acutely imbalanced—in the present MIMIC-IV cohort in-hospital mortality was 10.65% (Table 1), and published adult ICU cohorts commonly report values of this order [CITATION NEEDED: add a mortality-prevalence source]. When an algorithm satisfies 90% overall coverage, it can easily fulfill this mathematical guarantee by correctly predicting survival for the 90% majority while severely failing the 10% minority who die [11]. Furthermore, recent benchmark studies applying conformal prediction to critical care data (such as sepsis mortality on MIMIC-IV and eICU) have noted demographic equity as an unaddressed limitation [12 — VERIFY this claim against the paper before keeping it]. Related work on equalized coverage [15] and on fair conformal prediction in medical imaging [16], and several recent preprints on conformal prediction for ICU mortality, also exist; the present contribution should be positioned against these rather than as the first audit. It remains unknown whether standard conformal prediction guarantees equal coverage across demographic subpopulations (such as racial minorities, younger adults, or publicly insured patients), or whether coverage differs systematically for some groups.

Mondrian (group-conditional) conformal prediction has been proposed to enforce coverage guarantees within predefined sub-populations [13, 14]. In imbalanced healthcare settings, group-conditional calibration without outcome-class conditioning will leave minority-class coverage low, as follows from marginal validity at prevalence near 10% [15]. Additionally, clinicians and informaticians often fear an "efficiency penalty"—the concern that equalising coverage for under-represented subgroups will expand prediction sets into uninformative dual-label outputs ({survive, die}), thereby eroding clinical utility [16].

To resolve these open challenges, this study presents a comprehensive, multi-attribute fairness and efficiency audit of conformal prediction in critical care. Using the large-scale MIMIC-IV database ($N = 51,838$), we evaluate 100 independent train/calibration/test splits to address three core aims:
1. **Audit:** Assess whether standard split conformal prediction gives similar class-conditional coverage across age, race/ethnicity, biological sex, and health insurance payer groups.
2. **Pitfall Identification:** Investigate the empirical consequences of naive group-conditional conformal prediction in imbalanced clinical data.
3. **Repair & Trade-off Analysis:** Implement Mondrian class-conditional conformal calibration to reduce subgroup coverage differences, and quantify the prediction set size cost across every demographic stratum.

---

## 2. Materials and Methods

### 2.1 Study Setting and Cohort Selection
This study utilized the Medical Information Mart for Intensive Care IV (MIMIC-IV v3.1) database, containing electronic health records from Beth Israel Deaconess Medical Center (Boston, MA) collected between 2008 and 2022 [2, 17]. In accordance with the US Health Insurance Portability and Accountability Act (HIPAA) Safe Harbor provision, all protected health information was de-identified, and individual patient informed consent was waived by institutional review boards. Research was conducted under PhysioNet Credentialed Data Use Agreement protocols.

Cohort selection adhered to STROBE and TRIPOD+AI reporting guidelines (*Table 1*). From 94,458 total ICU admissions, we applied three clinical filtering criteria:
1. Retained only the first ICU stay per unique patient (excluding 29,092 subsequent readmissions) to ensure strict statistical independence across splits and eliminate patient-level data leakage.
2. Restricted the cohort to stays with an ICU length of stay (LOS) $\ge 24$ hours (excluding 13,528 stays) to establish a standardized 24-hour prognostic assessment window and exclude hyper-acute trauma or palliative discharges occurring within hours of admission.
3. Confirmed adult age $\ge 18$ years.

The final analyzed cohort comprised **51,838 unique adult ICU patients** with an observed in-hospital mortality rate of **10.65%** (5,522 deaths / 51,838 patients; exact: 0.106524).

### 2.2 Predictor Variables & Clinical Feature Engineering
Predictors were extracted exclusively from clinical events recorded during the initial 24 hours of ICU care:
- **Physiological Vital Signs:** Heart rate, systolic/diastolic/mean arterial blood pressure, respiratory rate, body temperature, and pulse oximetry ($\text{SpO}_2$) captured from bedside monitors in `chartevents`.
- **Laboratory Biomarkers:** Serum creatinine, blood urea nitrogen (BUN), white blood cell count (WBC), platelets, hemoglobin, serum lactate, electrolytes (sodium, potassium, bicarbonate, chloride), and glucose from `labevents` collected between 6 hours prior to ICU admission and 24 hours post-admission.
- **Neurological & Interventional Status:** Glasgow Coma Scale (GCS) total score and invasive mechanical ventilation indicators.

For each continuous time-series variable, the minimum, maximum, and mean values across the 24-hour observation window were computed. Author-defined physiological plausibility filters (excluding 0.002% to 0.49% of extreme erroneous measurements) were applied and set to missing. Missing values were handled natively by tree-based algorithms without synthetic imputation; missing-indicator flags were evaluated and confirmed to have zero feature gain in preliminary seeds.

### 2.3 Machine Learning Baseline Architecture
To simulate standard clinical prediction model deployment, we implemented gradient-boosted decision trees using XGBoost (`noflags` variant). For each evaluation iteration, the cohort was partitioned into training (50%), calibration (25%), and held-out test (25%) splits. XGBoost models were trained to predict binary in-hospital mortality ($y \in \{0, 1\}$). Model discrimination was quantified via Area Under the Receiver Operating Characteristic curve (AUROC) and Area Under the Precision-Recall Curve (AUPRC); calibration was evaluated via Brier score, calibration slope, and calibration intercept.

### 2.4 Conformal Prediction Formulation
For each patient $i$ in the calibration split, let $x_i$ denote the feature vector and $y_i \in \{0, 1\}$ the true binary outcome. Let $\hat{p}(y|x)$ denote the model's estimated risk probability. The nonconformity score was formulated as:
$$s_i(x, y) = 1 - \hat{p}(y|x)$$
Larger scores indicate that the true label was deemed improbable by the predictive model.

#### Standard Marginal Split Conformal Prediction
At nominal significance level $\alpha = 0.10$ (90% target coverage), the marginal conformal threshold $\hat{q}$ was computed over all calibration instances $n_{\text{cal}}$:
$$\hat{q} = \text{Quantile}\left( \{s_i\}_{i=1}^{n_{\text{cal}}}, \frac{\lceil (n_{\text{cal}} + 1)(1 - \alpha) \rceil}{n_{\text{cal}}} \right)$$
For a new test patient $x_{n+1}$, the prediction set $C(x_{n+1})$ is constructed as:
$$C(x_{n+1}) = \{ y \in \{0, 1\} : 1 - \hat{p}(y|x_{n+1}) \le \hat{q} \}$$

#### Standard Class-Conditional Split Conformal Prediction
To address acute class imbalance, class-specific thresholds $\hat{q}_{y=0}$ and $\hat{q}_{y=1}$ were computed separately for survivors ($y=0$) and decedents ($y=1$):
$$\hat{q}_k = \text{Quantile}\left( \{s_i : y_i = k\}, \frac{\lceil (n_k + 1)(1 - \alpha) \rceil}{n_k} \right), \quad k \in \{0, 1\}$$
The prediction set includes label $k$ if and only if $1 - \hat{p}(k|x) \le \hat{q}_k$.

#### Mondrian Class-Conditional Conformal Prediction
To enforce coverage guarantees within demographic subgroups, we partitioned the calibration set into disjoint strata defined by the intersection of protected attribute $A \in \mathcal{A}$ and outcome class $Y \in \{0, 1\}$. For each stratum $(a, k)$, a stratum-specific threshold $\hat{q}_{a, k}$ was computed:
$$\hat{q}_{a, k} = \text{Quantile}\left( \{s_i : A_i = a, Y_i = k\}, \frac{\lceil (n_{a, k} + 1)(1 - \alpha) \rceil}{n_{a, k}} \right)$$
For small calibration cells where the requested rank exceeded the available sample size (or $n_{a, k} = 0$), the quantile conservatively assigned $\hat{q}_{a, k} = +\infty$, ensuring unconditional inclusion of label $k$ rather than falling back to an unstratified quantile.

### 2.5 Multi-Attribute Fairness Audit & Statistical Rigor
We evaluated empirical coverage across 15 single demographic subgroups:
- **Age Groups:** 18–49, 50–64, 65–74, 75+ years.
- **Race / Ethnicity:** White, Black, Hispanic, Asian, Other/Unknown.
- **Health Insurance:** Medicare, Private, Medicaid, Other/Government.
- **Biological Sex:** Female, Male.

To capture genuine variability, the entire pipeline was executed across **100 independent random splits**. For each metric, we report:
1. **Across-Seed Standard Deviation (Seed SD):** Capturing split-to-split sampling and calibration variability.
2. **Patient-Level Bootstrap 95% Confidence Intervals:** Computed via $B = 1,000$ iterations with replacement (fixed seed 42) clustered at the unique patient stay level.
3. **Calibration-in-the-Large (CITL):** Evaluated as $\text{CITL} = \bar{p} - \bar{y}$. A positive CITL indicates model over-prediction of mortality risk (under-prediction of true survival).

To guarantee reproducibility, an isolated verification script (`src/evaluation/independent_check.py`) independently recomputed all metrics directly from raw parquet predictions without shared code, verifying all published values within a strict absolute tolerance $< 0.0005$.

### 2.6 External Validation in eICU-CRD
We used eICU-CRD v2.0 (208 US hospitals, 2014–2015) as an external database. Applying the same rules as in MIMIC-IV (first ICU stay per patient, unit stay ≥ 24 hours, adult, known hospital outcome and sex) gave 95,558 patients, 8,885 deaths (9.30%) and 207 hospitals. Features were rebuilt from the first 24 hours (vital signs 0–24 h, laboratory values from −6 to 24 h). Insurance is not recorded in eICU, so insurance analyses are MIMIC-only. Temperature, Glasgow Coma Scale and intubation are measured or defined differently in eICU (temperature 89% missing vs 3% in MIMIC; mean GCS 12.6 vs 9.8; intubated 18% vs 45%), so we defined a feature-harmonised sensitivity model without these three predictors (63 predictors) alongside the primary model with the 66 MIMIC predictors.

Per seed, XGBoost was trained on the MIMIC-IV training split and conformal thresholds were fitted on the MIMIC-IV calibration split. eICU was split 50/50 (patient-level, and in a stricter variant hospital-disjoint) into an eICU-calibration half and an eICU-test half. We compared on the same eICU test patients: (i) class-conditional thresholds from MIMIC calibration (pure transport), (ii) class-conditional thresholds from the eICU-calibration half, and (iii) Mondrian class-conditional thresholds by age, race and sex from the eICU-calibration half. Two endpoints (P1: death coverage in ages 18–49; P2: survivor coverage in ages 75+, both under pure transport) were defined before the final 100-seed run and called replicated if the upper Wilson bound was below 0.90; they were not publicly registered, and the same databases had been explored earlier in the project, so they are pre-planned rather than independently pre-specified. All other external analyses are secondary. Results are averaged over 100 seeds; seeds reuse the same patients, so the Wilson intervals computed on mean counts are approximate and the seed SD understates uncertainty. Per-hospital coverage was summarised for 103 hospitals with ≥ 100 patients and ≥ 20 deaths and compared with the binomial SD expected by chance.

### 2.7 Mechanism and Small-Stratum Stability (exploratory)
To examine why coverage differs between strata, we used global class-conditional thresholds (MIMIC calibration for MIMIC test data; thresholds fitted on all eICU data for eICU) and, for every stratum (age, race, sex, insurance, hospital), computed prevalence, within-stratum AUROC, mean predicted risk among decedents and survivors, and class-conditional coverage. We report Spearman correlations across strata and, for hospitals, a standardised linear regression of the death-coverage gap on prevalence and AUROC. These are ecological associations over few strata and are not causal estimates; two further analyses (Section 2.8) probe the mechanism with an intervention-type ablation. To assess when group-specific thresholds are stable, we compared hospital-specific class-conditional thresholds with the global eICU thresholds, binned by the number of deaths in the hospital calibration part.

### 2.8 Alternative Calibration and Age-Blind Ablation (exploratory)
To test whether the age pattern depends on the age predictor and on the use of demographic attributes, we (i) trained the same XGBoost model without age (age-blind) and (ii) compared four class-conditional calibrations on the same splits: pooled; Mondrian by age; and Mondrian by predicted-risk bin (5 or 10 quantile bins of the calibration-set scores), which uses no demographic attribute. Each was evaluated in MIMIC-IV (calibration split to test split) and eICU-CRD (eICU-calibration half to test half), over 100 seeds, reporting the largest absolute deviation from 0.90 across the four age strata (death and survivor coverage), mean set size and singleton share. For the age-blind model we also report AUROC and calibration-in-the-large by age stratum (10 seeds).

### 2.9 Stratum-minus-Overall Contrasts with Hospital-Cluster Intervals (post hoc)
Because absolute coverage under pure transport mixes the age effect with the overall transport shift, we also report contrast = coverage(stratum, class) minus coverage(all eICU patients, same class) for ages 18–49 (deaths, P1) and 75+ (survivors, P2), under (i) MIMIC thresholds applied to all eICU patients and (ii) class-conditional thresholds from an eICU calibration half evaluated on the other half. Uncertainty came from a two-level bootstrap (2,000 draws) resampling the 207 hospitals and the 100 model seeds, with percentile 95% intervals and Bonferroni-adjusted intervals over 8 contrasts. This analysis was defined after P1 failed on the absolute scale in the primary model; it is post hoc, and the absolute results are reported alongside. Revised replication rule: upper 95% bound below 0.

### 2.10 Calibration-Implied Coverage Test and Synthetic Demonstration (exploratory)
With a pooled class-conditional rule, the death label is included when the predicted risk p is at least t_d and the survivor label when p is at most t_s, so class-conditional coverage equals the sensitivity and specificity of two risk thresholds. If scores are calibrated within a stratum, coverage of deaths equals the sum of p over the stratum's patients with p ≥ t_d divided by the sum of p, and coverage of survivors equals the sum of (1−p) over patients with p ≤ t_s divided by the sum of (1−p); these predictions use scores only. We compared them with observed coverage across demographic strata (MIMIC: age, race, sex, insurance; eICU: age, race, sex) and 103 eICU hospitals, in eICU with raw and logistic-recalibrated scores, reporting the share of the squared deviation from 0.90 explained (R²), the slope, rank correlation, RMSE and a binomial noise floor. A synthetic demonstration with exactly calibrated scores (four scenarios: base-rate shift, equal prevalence with different score spread, identical groups, group-specific miscalibration) shows when the identity holds and fails.

### 2.11 End-of-Life Coding Sensitivity and Continuous Age (exploratory, MIMIC-IV only)
Hospital discharge to hospice is coded as survival. We rebuilt the analysis (own 50/25/25 splits, same predictors, pooled class-conditional thresholds, 100 seeds) with the outcome redefined as death or hospice discharge, with hospice discharges removed, and with hospice and palliative-care-coded (ICD-10 Z51.5 / ICD-9 V66.7) stays removed (a bound, since palliative codes are outcome-informative), and reported coverage by four age strata and by 10-year age bands. eICU-CRD has no hospice field; code-status orders were not extracted.

### 2.12 Clinical Utility, Set-Size Equity and Equalised-Odds Baseline (exploratory)
For each stratum we report set composition ({survive} only, {die} only, both, empty), mean set size, the death rate among patients with each set type (P(death | set)) and the share of deaths that received a {survive}-only set. We compared pooled class-conditional conformal, age x class Mondrian, an equalised-odds threshold baseline (age-specific risk thresholds giving sensitivity and specificity of 0.90 by empirical quantiles) and 10-bin risk Mondrian, over 100 seeds in MIMIC-IV and eICU-CRD.

---

## 3. Results

*(Refer to `paper/results_draft.md` for the complete verified statistical narratives, Tables 1–8, and Figures 1–3).*

### Key Numerical Highlights:
- **Cohort:** $N = 51,838$, in-hospital mortality: 10.65% (5,522 deaths) (*Table 1*).
- **Baseline Model:** AUROC: 0.8726, AUPRC: 0.5023, Brier: 0.0706 (*Table 2*).
- **The Young Decedent Disparity:** Baseline class-conditional death coverage for patients aged 18–49 was only **84.06%** [81.43%, 86.72%], falling 5.94 pp below nominal (*Table 3*).
- **Racial Survivor Differences (exploratory; many comparisons; difference of point estimates):** Asian survivors experienced −2.10 pp and Black survivors experienced −1.30 pp lower coverage compared to White patients (*Table 7*).
- **Mondrian Marginal (expected consequence of class imbalance):** Mondrian conformal prediction without class conditioning gave death coverage of to **11.77%** for age 18–49 and **18.15%** for age 50–64 (*Table 6, Figure 3B*).
- **Mondrian Class-Conditional Calibration:** Mean death coverage was approximately 90% in every group (by construction; small strata highly variable) (age 18–49 death coverage reached **90.42%**, paired gain: +6.25 pp [5.21, 7.32]) (*Table 4*).
- **Negligible Efficiency Penalty:** Mean prediction set size increased by at most +0.058 labels across all 15 subgroups (+2.57% for age 18–49, +1.49% for age 75+), with singleton predictions in 62%–87% of patients by stratum (lowest: age 75+, 62%) (*Table 8, Figure 3A & 3C*).

### External validation in eICU-CRD and mechanism (100 seeds; numbers from `paper/phase6_7_FINAL100_NOTE.md`):
- **Transport of the model:** AUROC 0.873 in MIMIC test vs 0.834 in eICU (0.810 for the harmonised model); calibration slope 0.88 (0.83); eICU risk over-prediction CITL +0.042 (+0.051).
- **Pure transport of MIMIC thresholds to eICU:** death coverage 0.920 and survivor coverage 0.835 overall (harmonised: 0.928 / 0.817); survivors were under-covered, decedents over-covered.
- **Primary endpoints:** P1 (ages 18–49 death coverage) 0.902 [0.870, 0.926], not replicated, in the primary model, and 0.819 [0.781, 0.852], replicated, in the harmonised model. P2 (ages 75+ survivor coverage) 0.748 [0.741, 0.756] and 0.677 [0.668, 0.685], replicated in both, but confounded by the overall survivor shortfall under transport. Hospital-disjoint splits gave the same values to the third decimal.
- **Age pattern after eICU recalibration (class-conditional):** death/survivor coverage 0.884/0.941 (18–49) to 0.919/0.844 (75+) in the primary model, and 0.778/0.966 to 0.950/0.820 in the harmonised model; the direction matches MIMIC (0.84/0.95 to 0.93/0.83).
- **Mondrian class-conditional calibration in eICU:** death and survivor coverage 0.898–0.903 in every age stratum, both models, both split types (by construction; not an independent confirmation of the guarantee).
- **Between-hospital variation:** SD of hospital death coverage 0.045 (primary) / 0.042 (harmonised) vs 0.039 expected from binomial noise.
- **Mechanism (exploratory):** across 103 hospitals the death-coverage gap tracked mean predicted risk among decedents (Spearman 0.79 / 0.70) and hospital AUROC (0.42 / 0.43); +1 SD AUROC ≈ +0.02 to +0.03 death coverage. Across demographic strata the gap tracked stratum prevalence (MIMIC 0.89 / 0.79) and was not explained by within-stratum AUROC, which was highest in young patients (age and prevalence and AUROC are collinear across four age strata). Interpretation: calibrated scores with group-specific base rates and one pooled threshold produce unequal class-conditional coverage.
- **Calibration alternatives (100 seeds; `paper/phase8_alternatives_NOTE.md`):** calibrating by predicted-risk bin x class, without any demographic attribute, nearly closed the age gap (largest age-stratum deviation from 0.90, death/survivor: MIMIC 0.013/0.016 for 10 bins vs 0.060/0.070 pooled; eICU 0.006/0.006 vs 0.019/0.056) but increased mean set size from 1.26 to about 1.79 labels in MIMIC (singleton share from 74% to 21%). Age x class Mondrian reached 0.005/0.001 at set size 1.27.
- **Age-blind ablation:** removing age shrank the age coverage gap by roughly 60–75% (MIMIC 0.060/0.070 to 0.015/0.027; eICU 0.019/0.056 to 0.013/0.027), supporting that the gap arises largely because the model shifts scores with age under a pooled threshold. The cost: AUROC 0.874 to 0.866 and age-dependent miscalibration (calibration-in-the-large +0.023 in ages 18–49 and −0.030 in ages 75+, versus about 0 with age). Coverage parity therefore does not imply calibration parity.
- **Small-stratum stability:** with fewer than 10 calibration deaths the death threshold was infinite in 84% of hospital-seeds; hospital-specific thresholds did not reduce deviation from 0.90 below about 40 calibration deaths (mean absolute deviation 0.047 at 40–79 deaths for both global and hospital-specific thresholds).

- **Stratum-minus-overall contrasts, hospital-cluster 95% CI (post hoc; `paper/phase9_endpoint_contrasts_NOTE.md`):** P1 (ages 18–49 death coverage minus overall), transport: −1.9 pp [−3.4, −0.5] primary and −11.0 pp [−12.9, −9.3] harmonised; eICU-recalibrated −1.8 [−3.5, −0.2] and −12.2 [−14.2, −10.3]. P2 (ages 75+ survivor coverage minus overall), transport: −8.6 pp [−9.3, −7.9] and −14.0 pp [−14.8, −13.2]; recalibrated −5.6 and −8.0. The primary-model P1 interval is Bonferroni-adjusted over 8 contrasts [−4.1, +0.1] (transport) and crosses zero. Hospital-cluster intervals were roughly 5–10 times wider than seed-only intervals.
- **Calibration-implied coverage (exploratory; `paper/phase10_calibration_implied_NOTE.md`):** in synthetic data with exactly calibrated scores the label-free prediction reproduced observed group coverage to about 1 pp, produced a 17 pp death-coverage gap between groups with near-equal AUROC (0.83–0.84) from base-rate differences alone, and failed under group miscalibration. Survivor-side coverage was predicted well in real data (R² 0.95 in MIMIC strata; 0.99 across eICU demographic strata and 0.92–0.93 across 103 hospitals with recalibrated scores; much worse with raw eICU scores, R² 0.17–0.61, because eICU risk is over-predicted). Death-side coverage was predicted only in direction and ordering (Spearman 0.75–0.97 in demographic strata); in MIMIC the RMSE (0.027) was about the binomial noise floor (0.025), the predicted death coverage was 2–4 pp below observed in the three age strata under 75, and R² against the 0.90 baseline was negative; recalibrating the weights improved survivor but not death predictions.

- **End-of-life coding sensitivity and continuous age (MIMIC-only, exploratory; `paper/phase11_endoflife_NOTE.md`):** 1,209 stays (2.3%) were discharged to hospice (0.8% in ages 18–49 to 3.9% in 75+). The age pattern persisted in every variant: young (18–49) decedent coverage 0.840 (reference), 0.822 (hospice as event), 0.844 (hospice removed), 0.860 (hospice and palliative-coded stays removed; seed SD 0.041); 75+ survivor coverage 0.830, 0.819, 0.825, 0.824. Across 10-year bands death coverage rose and survivor coverage fell roughly monotonically with age (death 0.84 at 18–29 to 0.94 at 80+; survivors 0.97 to 0.81). Outcome-coding choices change the size, not the direction, of the pattern; bands below age 50 have 28–81 test deaths per split.

- **Utility and set-size equity (exploratory; `paper/phase12_utility_equity_NOTE.md`):** age x class Mondrian sets and equalised-odds threshold sets were identical for 99.2% (MIMIC) and 99.7% (eICU) of test patients, i.e. the Mondrian repair is group-specific thresholding to equal sensitivity and specificity. It equalised the share of deaths that received a {survive}-only set (about 10% in every age stratum, versus 16% in ages 18–49 and 7% in 75+ under pooled calibration) but not predictive values: in MIMIC the death rate behind a {survive}-only set was 0.9% (18–49) to 3.2% (75+) and a {die}-only set was correct for 32% to 47%. Older patients received larger sets (mean 1.18 to 1.38 labels, singleton share 83% to 62%) under Mondrian, and the age gap in set size (about 0.2 labels) was not reduced. Risk-bin calibration equalised set size (1.77–1.84) only by making about 80% of sets uninformative.

---

## 4. Discussion

*(Refer to `paper/results_draft.md` Section 2 for the complete Discussion, Clinical Implications, Comparison with Prior Work, and Limitations).*

**Added limitations for the external validation and mechanism work:** eICU is 2014–2015 data with different feature definitions (GCS, intubation, temperature), so the primary and harmonised models bracket the result; the primary young-decedent endpoint did not replicate in the primary model. Insurance cannot be audited in eICU. Race and outcome coding differ between databases. The random 50/50 eICU split shares hospitals between halves (checked with hospital-disjoint splits, which gave the same results). Seeds reuse the same patients, so the reported intervals are approximate. Mechanism findings are ecological correlations over few strata and are not causal. The age-blind ablation removes age from the predictors but does not separate age from correlated physiology; it is not a causal proof. Risk-bin calibration was only tested with 5 and 10 quantile bins. The contrast analysis (Section 2.9) is post hoc and the endpoints were not publicly registered. Class-conditional coverage equals sensitivity and specificity of two risk thresholds, and Mondrian calibration by age is group-specific thresholding (equalised-odds-type post-processing; Hardt et al. 2016, Chouldechova 2017 and Kleinberg et al. 2017 must be cited after verification [CITATION NEEDED]). The calibration-implied test (Section 2.10) is a consistency check conditional on within-stratum calibration; it explains survivor-side gaps well but death-side magnitudes only partly, and it does not explain why score distributions differ by age. Hospice discharge and palliative-code sensitivity (Section 2.11) did not change the direction of the age pattern in MIMIC-IV, but code-status (DNR/comfort-measure) orders were not extracted and eICU could not be examined. Equalising coverage across age does not equalise predictive values or set size (Section 2.12); no net-benefit or decision-curve analysis was done. Comparison with equalized coverage (Romano 2020), Conformal Fairness and 2026 preprints on conformal fairness in ICU data remains to be written; do not claim priority.

---

## 5. References

1. Rajkomar A, Oren E, Chen K, et al. Scalable and accurate deep learning with electronic health records. *npj Digit Med*. 2018;1:18.
2. Johnson AEW, Pollard TJ, Shen L, et al. MIMIC-IV, a freely accessible electronic health record dataset. *Sci Data*. 2023;10:1.
3. Guo C, Pleiss G, Sun Y, Weinberger KQ. On calibration of modern neural networks. *ICML*. 2017:1321-1330.
4. Kompa B, Snoek J, Beam AL. Second opinion needed: communicating uncertainty in medical machine learning. *npj Digit Med*. 2021;4:4.
5. Vovk V, Gammerman A, Shafer G. *Algorithmic Learning in a Random World*. Springer Science & Business Media; 2005.
6. Angelopoulos AN, Bates S. A gentle introduction to conformal prediction and distribution-free uncertainty quantification. *arXiv:2107.07511*. 2021.
7. Romano Y, Sesia M, Candès E. Classification with valid and equal coverage for inconclusive sets. *Adv Neural Inf Process Syst*. 2020;33:3582-3592.
8. Tibshirani RJ, Barber RF, Candes E, Ramdas A. Conformal prediction under covariate shift. *Adv Neural Inf Process Syst*. 2019;32.
9. Foygel Barber R, Candes EJ, Ramdas A, Tibshirani RJ. The limits of distribution-free conditional predictive inference. *Inf Inference*. 2021;10(2):455-482.
10. [REMOVED: Zimmerman et al. is a length-of-stay paper, not a mortality-prevalence source; replace.] Zimmerman JE, Kramer AA, McNair DS, Malila FM. Intensive care unit length of stay: Benchmarking based on Acute Physiology and Chronic Health Evaluation (APACHE) IV. *Crit Care Med*. 2006;34(10):2517-2529.
11. Cauchois M, Gupta S, Duchi JC. Knowing what you know: valid and intuitive prediction sets. *J Mach Learn Res*. 2021;22(81):1-42.
12. Development and Validation of an Interpretable Conformal Predictor to Predict Sepsis Mortality Risk: Retrospective Cohort Study. *J Med Internet Res*. 2024. doi:10.2196/50369 [author list to be completed from the DOI record].
13. Vovk V. Conditional validity of inductive conformal predictors. *Asian Conference on Machine Learning*. 2012:475-490.
14. Lei J, Wasserman L. Distribution-free prediction bands for non-parametric regression. *J R Stat Soc Series B*. 2014;76(1):71-96.
15. Romano Y, Barber RF, Sabatti C, Candès E. With malice toward none: assessing uncertainty via equalized coverage. *Harv Data Sci Rev*. 2020. doi:10.1162/99608f92.03f00592
16. Lu C, Lemay A, Chang K, Höbel K, Kalpathy-Cramer J. Fair conformal predictors for applications in medical imaging. *Proc AAAI Conf Artif Intell*. 2022;36(11). doi:10.1609/aaai.v36i11.21459
18. Seyyed-Kalantari L, Zhang H, McDermott MBA, Chen IY, Ghassemi M. Underdiagnosis bias of artificial intelligence algorithms applied to chest radiographs in under-served patient populations. *Nat Med*. 2021;27(12):2176-2182. [cite where clinical-AI bias is introduced]
19. Obermeyer Z, Powers B, Vogeli C, Mullainathan S. Dissecting racial bias in an algorithm used to manage the health of populations. *Science*. 2019;366(6464):447-453. [cite where clinical-AI bias is introduced]
17. Goldberger AL, Amaral LA, Glass L, et al. PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. *Circulation*. 2000;101(23):e215-e220.


---

## 6. Figure Legends & Visual Artifacts

### Figure 1: Clinical Fairness Shield (Radar / Spider Chart)
- **File:** `outputs/figures/figure1_age_disparity_and_repair.png` [TODO: caption below was written for a radar chart that does not exist; rewrite to match this file]
- **Caption:** **Figure 1. Empirical Subgroup Death-Label Coverage Across 15 Demographic Strata.** Polar radar chart displaying class-conditional coverage among decedents ($y=1$) under baseline global split conformal prediction (Navy line), naive Mondrian marginal conformal prediction (Red dotted line), and Mondrian class-conditional conformal prediction (Teal line) against the nominal 90.0% target coverage boundary (Red dashed ring). Baseline global conformal prediction exhibits notable inward indentation for young adults aged 18–49 (84.06%), Hispanic patients (87.62%), and privately insured patients (86.60%). Mondrian marginal calibration (no class conditioning) gives low decedent coverage, as expected under class imbalance (11.77% to 39.79%). Mondrian class-conditional calibration brings mean decedent coverage to about 90% across demographic axes (small strata remain variable).

### Figure 2: Subgroup Class-Conditional Death Coverage (Lancet-Style Forest Plot)
- **File:** `outputs/figures/figure2_racial_and_payer_equity.png` [TODO: caption below was written for a forest plot that does not exist; rewrite to match this file]
- **Caption:** **Figure 2. Subgroup Death Coverage and Paired Calibration Differences Across 100 Random Splits.** Subgroup forest plot displaying point estimates and uncertainty bounds across 15 demographic strata (Age, Insurance, Race/Ethnicity, Biological Sex, and Overall). Baseline global conformal coverage is depicted by Navy circles with patient-level bootstrap 95% confidence intervals ($B = 1,000$ iterations). Mondrian class-conditional coverage is depicted by Teal diamonds with 2.5th–97.5th percentile across-seed empirical split ranges. The red dashed vertical line indicates nominal 90.0% coverage. Paired differences ($\Delta = \text{Mondrian} - \text{Global}$) and exact coverage intervals are tabulated adjacent to each stratum.

### Figure 3: Clinical Utility and Prediction Set Composition Breakdown
- **File:** `outputs/figures/figure3_fairness_efficiency_tradeoff.png` [TODO: caption below was written for a stacked-bar chart that does not exist; rewrite to match this file]
- **Caption:** **Figure 3. Prediction Set Composition and Efficiency Across Demographic Subpopulations.** 100% horizontal stacked bar chart showing the distribution of output prediction set topologies for each demographic stratum under baseline global split conformal prediction (upper bar) and Mondrian class-conditional calibration (lower bar). Blue segments denote informative singleton predictions ({survive} or {die}). Amber/Orange segments denote inconclusive dual predictions ({survive, die}). Under Mondrian class-conditional calibration, 62%–87% of patients per stratum retained singleton predictions (lowest: age 75+, 62%); the efficiency cost is moderate and varies by stratum [regenerate this figure and verify the caption against it].

### Figure 4: Miscalibration (CITL) vs Conformal Coverage Disparity
- **File:** NOT YET GENERATED (no CITL bubble plot exists in outputs/figures; generate or delete this figure)
- **Caption:** **Figure 4. Relationship Between Calibration-in-the-Large (CITL) and Conformal Death Coverage Disparity.** Scatter plot mapping baseline demographic CITL ($\bar{p} - \bar{y}$, expressed in $10^{-3}$) on the horizontal axis against empirical class-conditional death coverage on the vertical axis. Bubble diameters are proportional to subgroup sample sizes ($N_{\text{test}}$). Negative CITL corresponds to systematic risk under-prediction, partially accounting for empirical under-coverage in younger adult cohorts.
