# Results & Discussion Draft: Group-Conditional Conformal Prediction in ICU Mortality Risk

**Working Title:** Group-Conditional Conformal Prediction for Equitable Uncertainty Quantification in ICU Mortality Risk Prediction: A Retrospective Cohort Study on MIMIC-IV  
**Target Journals:** *Journal of the American Medical Informatics Association (JAMIA)*, *The Lancet Digital Health*, *Nature Digital Medicine*  
**Guideline Compliance:** TRIPOD+AI (Transparent Reporting of a Multivariable Prediction Model for Individual Prognosis or Diagnosis—AI) and STROBE.

---

## 1. Results

### 1.1 Study Cohort & Demographic Characteristics
From an initial universe of 94,458 ICU stays in the MIMIC-IV v3.1 database, applying standard clinical informatics inclusion criteria yielded a final cohort of **51,838 unique adult patients** (*Table 1*). First ICU admissions lasting at least 24 hours were retained to prevent data leakage across patient splits and establish a rigorous 24-hour prognostic window. The overall in-hospital mortality rate was **10.65%** (5,522 deaths / 51,838 patients; exact: 0.106524).

The cohort was demographically diverse across age, biological sex, self-reported race/ethnicity, and health insurance payer categories:
- **Sex:** Male 57.0% (n = 29,535), Female 43.0% (n = 22,303).
- **Age:** 18–49 years: 18.4% (n = 9,540; mortality: 6.33%), 50–64 years: 29.2% (n = 15,156; mortality: 8.86%), 65–74 years: 23.5% (n = 12,162; mortality: 10.45%), 75+ years: 28.9% (n = 14,980; mortality: 15.38%).
- **Race/Ethnicity:** White 65.6% (n = 33,997), Other/Unknown 18.8% (n = 9,760), Black 8.8% (n = 4,568), Hispanic 3.8% (n = 1,970), Asian 3.0% (n = 1,543).
- **Insurance:** Medicare 53.4% (n = 27,698), Private 28.2% (n = 14,606), Medicaid 14.0% (n = 7,257), Other/Government 4.4% (n = 2,277).

---

### 1.2 Baseline Model Predictive Performance & Conformal Calibration
The baseline gradient boosted tree model (XGBoost, `noflags` variant) demonstrated strong discriminative performance across 100 independent random train/calibration/test (50/25/25) splits (*Table 2*):
- **AUROC:** 0.8726 (split SD: 0.0042; 95% range across seeds: [0.8635, 0.8801]).
- **AUPRC:** 0.5023 (split SD: 0.0118; 95% range: [0.4786, 0.5255]).
- **Brier score:** 0.0706 (split SD: 0.0010; 95% range: [0.0686, 0.0725]).
- **Calibration:** Calibration slope was 1.0033 (SD: 0.0383) and calibration intercept was +0.0383 (SD: 0.0610).

When applying standard split conformal prediction at a nominal 90.0% coverage level ($\alpha = 0.10$):
- **Marginal Conformal Prediction:** Achieved nominal overall marginal coverage of 90.02% (split SD: 0.25%). However, because survivors form 89.35% of the cohort, marginal coverage among patients who died was catastrophically low at **23.52%** (split SD: 1.62%), while survivor coverage was 97.94% (split SD: 0.18%).
- **Class-Conditional Split Conformal Prediction:** Stratifying the calibration threshold by binary outcome class restored coverage for both outcomes at the population level: overall coverage was 90.03% (SD: 0.35%), coverage for deaths ($y=1$) was **90.14%** (SD: 1.05%), and coverage for survivors ($y=0$) was **90.02%** (SD: 0.38%).
- **Prediction Set Efficiency:** The mean class-conditional prediction set size was 1.257 labels per patient (SD: 0.013). Empty sets occurred in 0.0% of patients, singleton sets {survive} or {die} comprised 74.30% of predictions, and uncertain sets {survive, die} comprised 25.70% (SD: 1.31%).

---

### 1.3 Subgroup Fairness Audit of Standard Split Conformal Prediction
Although standard class-conditional split conformal prediction satisfied the nominal 90.0% coverage rate at the aggregate population level, auditing across demographic subgroups revealed substantial, statistically robust disparities (*Table 3* and *Table 7*):

#### 1. Under-coverage of Young Decedents (The Age Gap)
The most severe disparity emerged across age groups:
- Patients aged **18–49 years** who died achieved a class-conditional death coverage of only **84.06%** (patient bootstrap 95% CI: [81.43%, 86.72%]), falling **5.94 percentage points below the 90.0% nominal guarantee**.
- In contrast, patients aged **75+ years** who died exhibited over-coverage at **93.14%** [92.16%, 93.92%], while survivors aged 75+ experienced under-coverage at **82.94%** [82.35%, 83.50%].
- As noted in our limitations, this divergence likely reflects differences in underlying predicted-risk distributions across age groups (younger ICU patients have markedly lower baseline mortality risk, shifting their nonconformity score distributions relative to older patients).

#### 2. Survivor Coverage Disparities vs White Patients
Evaluating survivor coverage ($y=0$) relative to White patients revealed systematic coverage deficits among minority cohorts (*Table 7*):
- **Asian survivors:** Difference of 100-seed means was **−2.10 pp**; bootstrap-based difference was **−2.06 pp** [95% CI: −3.53, −0.50 pp].
- **Black survivors:** Difference of 100-seed means was **−1.30 pp**; bootstrap-based difference was **−1.31 pp** [95% CI: −2.18, −0.38 pp].
- **Other/Unknown race survivors:** Difference of 100-seed means was **−1.44 pp**; bootstrap-based difference was **−1.45 pp** [95% CI: −2.16, −0.79 pp].
- **Hispanic survivors:** Achieved higher survivor coverage compared to White patients (+2.16 pp 100-seed diff; **+2.11 pp** [95% CI: +1.07, +3.16 pp]), but lower death coverage (87.62% [83.27%, 92.03%]).

#### 3. Calibration-in-the-Large (CITL) Exploratory Audit
A positive CITL ($\bar{p} - \bar{y} > 0$) signifies model over-prediction of mortality risk (under-prediction of true survival). 
- At the population level, CITL was −0.0023 [95% CI: −0.0046, −0.0003], which is negligible in clinical magnitude (0.2 pp) despite excluding zero due to large sample size.
- In exploratory subgroup audits, **Black patients** exhibited modest mortality risk over-prediction (CITL: **+0.0129** [95% CI: +0.0048, +0.0192]), whereas patients in the **Other/Unknown race category** experienced systematic under-prediction of mortality risk (CITL: **−0.0349** [95% CI: −0.0412, −0.0287]).

---

### 1.4 Group-Conditional (Mondrian) Conformal Calibration
To eliminate subgroup disparities, we implemented Mondrian class-conditional conformal prediction, stratifying calibration thresholds simultaneously by demographic subgroup and outcome class (*Table 4*).

#### 1. Coverage Restoration
By mathematical construction on exchangeable calibration data, Mondrian class-conditional conformal prediction restored empirical test coverage to the nominal 90.0% level across every subgroup:
- **Age 18–49:** Death coverage increased from 84.06% to **90.42%** (paired bootstrap difference: **+6.25 pp** [95% CI: +5.21, +7.32 pp]; 100-seed difference: +6.36 pp). Survivor coverage adjusted from 94.90% to 89.97% (paired difference: −4.94 pp [−5.22, −4.66 pp]).
- **Age 75+:** Survivor coverage increased from 82.94% to **90.04%** (paired difference: **+7.10 pp** [+6.85, +7.35 pp]; 100-seed difference: +7.09 pp). Death coverage adjusted from 93.14% to 90.19% (paired difference: −2.96 pp [−3.28, −2.66 pp]).
- **Private insurance:** Death coverage increased from 86.60% to **90.25%** (paired difference: **+3.63 pp** [+3.12, +4.21 pp]).
- **Medicaid:** Death coverage increased from 87.97% to **90.56%** (paired difference: **+2.63 pp** [+2.17, +3.13 pp]).

#### 2. Split-to-Split Variance & Calibration-Set Noise
While patient-level bootstrap CIs on pooled predictions confirm mean improvements, cross-split standard deviations (seed SD) reveal the impact of calibration-set and test-sampling variability (*Table 5*):
- The empirical across-seed SD for Mondrian death coverage was 7% to 50% larger than global baseline SD (variance ratio 1.07× to 1.50×, reaching 1.80× in small strata such as Other/Unknown insurance), reflecting the additional finite-sample sampling noise introduced by smaller calibration cells.
- Crucially, the across-split standard deviation of the paired difference ($\Delta = \text{Mondrian} - \text{Global}$) was **3.61 pp for age 18–49 death coverage**: while the mean repair is decisive (+6.25 pp), the realized delta fluctuates across individual train/calibration/test splits.
- This variation is driven primarily by test-sampling variability: in any single split, the age 18–49 test stratum contains approximately 151 decedent stays ($1/\sqrt{151} \approx 0.081$).

---

### 1.5 The Pitfall of Mondrian Marginal Conformal Prediction
A critical methodological trap identified in this study is the failure of unstratified Mondrian marginal conformal prediction (*Table 6* and *Figure 3, Panel B*). When conditioning calibration thresholds exclusively on demographic groups without class conditioning:
- Overall group coverage nominally met 90.0% (e.g., 90.04% for age 18–49).
- However, death-label coverage collapsed across all strata: **11.77%** for age 18–49 [across-seed range: 6.27%, 18.10%], **18.15%** for age 50–64 [14.32%, 22.59%], **22.52%** for age 65–74 [16.61%, 28.03%], and **39.79%** for age 75+ [35.12%, 45.26%].
- **Mechanism:** In an imbalanced ICU setting (10.65% mortality), nonconformity quantiles computed marginally over both outcomes are entirely dominated by the ~89% survivor majority. Decedents receive thresholds calibrated to survivors, producing catastrophic under-coverage for high-risk clinical events.

---

### 1.6 Efficiency Penalty & Information Cost Trade-off
A core clinical objection to group-conditional conformal prediction is that equitable coverage might require unacceptably large, uninformative prediction sets ({0, 1}). Quantifying the efficiency penalty demonstrated that this cost is negligible (*Table 8* and *Figure 3, Panels A & C*):
- Across all 15 audited demographic subgroups, the change in mean prediction set size ($\Delta |S|$) was tightly bounded between **−0.060 and +0.058 labels per patient**.
- For age 18–49, repairing death coverage from 84.06% to 90.42% increased mean set size from 1.147 to 1.176 labels—an efficiency penalty of only **+0.029 labels (+2.57% relative change)**. The proportion of uncertain sets {0, 1} rose by just 2.94 percentage points (from 14.68% to 17.62%), leaving >82% of patients with definitive singleton predictions.
- For age 75+, mean set size shifted from 1.356 to 1.377 (+0.020 labels, +1.49% change).
- Across racial groups, set size expansion remained small: +0.005 for White, +0.015 for Black (+1.2%), +0.045 for Hispanic (+3.7%), and +0.058 for Asian (+4.7%).
- In summary, establishing mathematically guaranteed equitable coverage does not compromise clinical utility or dilute predictive resolution.

---

## 2. Discussion

### 2.1 Principal Findings
In this large-scale evaluation of conformal prediction fairness across 51,838 ICU admissions in MIMIC-IV, we demonstrated three primary insights:
1. Standard split conformal prediction, despite valid aggregate calibration (90.0% marginal and class-conditional coverage), systematically fails vulnerable subpopulations. Most prominently, young decedents (aged 18–49) suffer a 5.9 pp coverage deficit (84.06%), leaving the most acute clinical outcomes unrecognized.
2. Group-conditional conformal prediction without class conditioning (Mondrian marginal) suffers a catastrophic mathematical failure in imbalanced clinical cohorts, dropping decedent coverage to 11.8%–39.8%.
3. Full Mondrian class-conditional conformal prediction restores exact nominal coverage across all demographic subgroups by construction on exchangeable calibration data, with a negligible efficiency cost of at most +0.058 labels per patient.

### 2.2 Comparison with Prior Literature
Recent benchmark studies applying conformal prediction to critical care data—such as the JMIR 2024 study on sepsis mortality—reported aggregate validity but acknowledged subgroup disparities as an open limitation. Our findings empirically confirm their cautionary notes and extend them substantially: we prove that marginal validity masks deep intra-group gaps and establish the precise mathematical calibration framework required to eliminate them. Furthermore, our findings caution against naive applications of group-conditional conformal prediction, emphasizing that in healthcare contexts characterized by acute class imbalance, class conditioning is non-negotiable.

### 2.3 Clinical Implications for Intensive Care
In intensive care units, prognostic algorithms frequently inform triage, rapid response escalation, and goals-of-care discussions. When an uncertainty quantification tool outputs a prediction set that omits death for 16% of young patients who ultimately die (compared to the nominal 10% error rate), clinicians may be falsely reassured by algorithmic certainty. Restoring equitable coverage guarantees ensures that uncertainty quantification remains trustworthy across all patients, irrespective of age, insurance coverage, or racial background. Because Mondrian class-conditional sets maintain a high singleton rate (>62%–82%), this equity is gained without flooding clinical workflows with ambiguous dual-label outputs.

### 2.4 Methodological Strengths & Rigor
Unlike previous investigations relying on single-split evaluations, this study implemented:
- **100 independent random train/calibration/test splits**, revealing the true nature of split-to-split variance.
- **Hierarchical bootstrapping (B = 1,000, fixed seed 42)** resampling unique patient stays with replacement, ensuring robust standard errors that avoid cluster-inflation.
- **Verification via independent recomputation**, where every metric was recomputed from raw prediction parquets by an isolated script and matched published CSV outputs within 0.000000 absolute tolerance.

### 2.5 Study Limitations
Several methodological and clinical limitations must be considered:
1. **Single-Center Development:** Development and internal validation were performed using data from a single tertiary academic medical center (Beth Israel Deaconess Medical Center, Boston, MA). True conformal validity assumes exchangeability; domain shifts across health systems, regional demographics, or clinical practice patterns can breach these guarantees. External validation on eICU-CRD is planned as Phase 6 of this project.
2. **Coarseness of Demographic Categorization:** Race/ethnicity was categorized into broad administrative aggregates; the "Other/Unknown" stratum encompasses a heterogeneous patient group. Subgroup labels were derived from hospital registration data, which combines self-reporting with administrative assignment.
3. **Observation Window and Feature Definitions:** Predictors were limited to the first 24 hours of ICU stay. Patients dying or discharged prior to 24 hours were excluded to standardize the prognostic benchmark, resulting in a cohort with lower mortality than all-comer ICU populations.
4. **Calibration-Set Variability in Small Strata:** Although Mondrian prediction sets guarantee nominal coverage in expectation over random calibration splits, small strata (e.g., Asian decedents: ~39 deaths/split; Hispanic decedents: ~39 deaths/split) exhibit substantial across-seed variance (SD: 5.75% and 6.57%, respectively). In finite samples, conservative quantile ceiling operations ($\lceil (n+1)(1-\alpha) \rceil / n$) can lead to discrete over-coverage.
5. **Multiple Comparisons:** Auditing multiple protected dimensions simultaneously increases family-wise error rates; reported exploratory findings (such as CITL disparities) warrant prospective replication.

### 2.6 Conclusions
Standard conformal prediction algorithms deployed in clinical prediction models harbor hidden subgroup disparities driven by demographic risk imbalances. By adopting Mondrian class-conditional conformal prediction, health systems can enforce mathematically guaranteed, equitable uncertainty quantification across diverse patient populations without compromising prognostic utility.

