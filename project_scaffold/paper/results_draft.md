# Results & Discussion: Group-Conditional Conformal Prediction in ICU Mortality Risk

**Working Title:** Group-Conditional Conformal Prediction for Equitable Uncertainty Quantification in ICU Mortality Risk Prediction: A Retrospective Cohort Study on MIMIC-IV  
**Target Journals:** *Journal of the American Medical Informatics Association (JAMIA)*, *The Lancet Digital Health*, *Nature Digital Medicine*  
**Reporting Standards:** TRIPOD+AI (2024 Guidelines) and STROBE Checklist

---

## 1. Results

### 1.1 Study Cohort & Demographic Characteristics
> **Data Source:** Verified from [`paper/tables/table1_cohort_summary.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table1_cohort_summary.md) and derived from `outputs/results/phase1_exclusion_flow.csv` and `data/processed/cohort.parquet`.

From an initial cohort of 94,458 ICU stays in the MIMIC-IV v3.1 database, applying rigorous clinical informatics exclusion criteria established by STROBE guidelines yielded a final analytical cohort of **51,838 unique adult patients** (*Table 1*). First ICU admissions lasting at least 24 hours were retained to prevent data leakage across train, calibration, and test splits and establish a standardized 24-hour prognostic evaluation window. The overall in-hospital mortality rate across the study cohort was **10.65%** (5,522 deaths / 51,838 patients; exact: 0.106524).

The cohort exhibited demographic diversity across biological sex, age categories, self-reported race/ethnicity, and insurance payer status (*Table 1*):
- **Biological Sex:** Male 57.0% (n = 29,535; mortality: 10.20%), Female 43.0% (n = 22,303; mortality: 11.23%).
- **Age Categories:** 
  - 18–49 years: 18.4% (n = 9,540; mortality: **6.33%**, 604 deaths)
  - 50–64 years: 29.2% (n = 15,156; mortality: **8.86%**, 1,343 deaths)
  - 65–74 years: 23.5% (n = 12,162; mortality: **10.45%**, 1,271 deaths)
  - 75+ years: 28.9% (n = 14,980; mortality: **15.38%**, 2,304 deaths)
- **Race / Ethnicity:** White 65.6% (n = 33,997; mortality: 9.42%), Other/Unknown 18.8% (n = 9,760; mortality: 16.31%), Black 8.8% (n = 4,568; mortality: 9.02%), Hispanic 3.8% (n = 1,970; mortality: 7.92%), Asian 3.0% (n = 1,543; mortality: 10.11%).
- **Insurance Payer Status:** Medicare 53.4% (n = 27,698; mortality: 12.68%), Private 28.2% (n = 14,606; mortality: 7.09%), Medicaid 14.0% (n = 7,257; mortality: 9.67%), Other / Government 4.4% (n = 2,277; mortality: 11.81%).

---

### 1.2 Baseline Model Discrimination & Conformal Population Calibration
> **Data Source:** Verified from [`paper/tables/table2_phase3_baseline_metrics.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table2_phase3_baseline_metrics.md) and derived from `outputs/results/phase3_baseline_metrics_noflags_a010.json` (evaluated across 100 independent random train/calibration/test splits, nominal $\alpha = 0.10$).

Across 100 independent random splits (50% train, 25% calibration, 25% held-out test), the baseline gradient boosted decision tree classifier (XGBoost, `noflags` variant) demonstrated high discriminative performance and robust population calibration (*Table 2*):
- **Discrimination:** The mean Area Under the Receiver Operating Characteristic curve (AUROC) was **0.8726** (across-split SD: 0.0042; 2.5th–97.5th percentile range: [0.8635, 0.8801]). The Area Under the Precision-Recall Curve (AUPRC) was **0.5023** (split SD: 0.0118; range: [0.4786, 0.5255]).
- **Calibration Metrics:** The Brier score was **0.0706** (split SD: 0.0010). The calibration slope was 1.0033 (SD: 0.0383) and calibration intercept was +0.0383 (SD: 0.0610).
- **Marginal vs Class-Conditional Conformal Calibration:**
  - *Standard Marginal Conformal Prediction:* Achieved nominal overall population coverage of **90.02%** (SD: 0.25%). However, due to acute class imbalance (10.65% mortality vs 89.35% survival), nonconformity thresholds were heavily dominated by survivors: empirical coverage among decedents ($y=1$) was catastrophically low at **23.52%** (SD: 1.62%; range: [20.51%, 26.47%]), while survivor coverage was 97.94% (SD: 0.18%).
  - *Class-Conditional Split Conformal Prediction:* Stratifying calibration thresholds separately by binary outcome ($y=0$ and $y=1$) successfully satisfied nominal guarantees for both classes at the aggregate population level: overall coverage was **90.03%** (SD: 0.35%), decedent coverage ($y=1$) was **90.14%** (SD: 1.05%; range: [87.57%, 92.07%]), and survivor coverage ($y=0$) was **90.02%** (SD: 0.38%; range: [89.28%, 90.70%]).
- **Prediction Set Efficiency:** Population mean set size was 1.257 labels per patient (SD: 0.013). Singleton predictions ({survive} or {die}) accounted for 74.30% of cases, while inconclusive dual-label sets ({survive, die}) accounted for 25.70% (SD: 1.31%). Empty sets occurred in 0.0% of cases.

---

### 1.3 Demographic Subgroup Fairness Audit & Disparities
> **Data Sources:** Verified from [`paper/tables/table3_phase4_subgroup_audit.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table3_phase4_subgroup_audit.md) and [`paper/tables/table7_survivor_disparity_vs_white.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table7_survivor_disparity_vs_white.md). Confidence intervals computed via $B = 1,000$ patient-level bootstrap iterations (fixed seed 42).

Although class-conditional split conformal prediction met the nominal 90.0% coverage rate over the entire population, systematic auditing across 15 demographic strata exposed deep, clinically concerning coverage disparities (*Table 3*, *Table 7*, and *Figures 1 & 2*).

#### 1. Under-coverage of Young Decedents (The Age Disparity)
The primary vulnerability identified in the audit was an acute coverage gap across patient age categories (*Table 3* and *Figure 1*):
- Patients aged **18–49 years** who died achieved an empirical class-conditional death coverage of only **84.06%** (patient-level bootstrap 95% CI: [81.43%, 86.72%]), falling **5.94 percentage points below the nominal 90.0% guarantee**. In approximately 16% of young patients who died, the model's prediction set falsely excluded death.
- Conversely, decedents aged **75+ years** exhibited conservative over-coverage at **93.14%** [92.16%, 93.92%], while survivors aged 75+ suffered under-coverage at **82.94%** [82.35%, 83.50%].
- As detailed in our methodology, this age disparity is largely driven by baseline risk differences: younger patients present with substantially lower overall mortality risk (6.33% vs 15.38% in age 75+), skewing the distribution of model predicted probabilities $\hat{p}$ and nonconformity scores relative to older patients (*Figure 1A*).

---

![Figure 1: The Anatomy of the Age Disparity](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/outputs/figures/figure1_age_disparity_and_repair.png)

#### 🖼️ Detailed Description of Figure 1: The Anatomy of the Age Disparity
- **Figure Reference:** [`outputs/figures/figure1_age_disparity_and_repair.png`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/outputs/figures/figure1_age_disparity_and_repair.png)
- **Panel A (Baseline Clinical Risk by Age):** Contrasts observed in-hospital mortality (Navy bars) against mean model predicted risk $\hat{p}$ (Blue bars) across the four age strata. It visually proves that young adults (age 18–49) have 2.4× lower baseline mortality (6.3% vs 15.4% for age 75+). Because the predictive model is well-calibrated to this base rate, young patients are routinely assigned low risk scores, predisposing them to high nonconformity scores when an adverse event occurs.
- **Panel B (The Young Decedent Gap):** Displays class-conditional death coverage (Red bars) and survivor coverage (Teal bars) under baseline conformal prediction. For age 18–49, a dramatic **10.84 percentage point intra-group gap** exists between survivor coverage (94.90%) and decedent coverage (84.06%), falling 5.94 pp below the 90% dashed reference line. In contrast, for age 75+, the pattern inverts (survivor coverage drops to 82.94%, while death coverage is 93.14%).
- **Panel C (Restoration via Mondrian Calibration):** Illustrates the head-to-head comparison before and after Mondrian class-conditional calibration. For every age bracket, both death coverage (orange $\to$ red) and survivor coverage (blue $\to$ green) converge precisely to the nominal 90.0% dashed threshold, eliminating the age disparity entirely (Age 18–49 death coverage repaired by **+6.36 pp / +6.25 pp**, reaching 90.42%).

---

#### 2. Racial and Insurance Disparities in Survivor Coverage vs White Patients
Auditing survivor coverage ($y=0$) relative to White patients revealed persistent statistical deficits for racial minorities (*Table 7* and *Figure 2A*):
- **Asian survivors:** Difference of 100-seed means was **−2.10 pp**; bootstrap-based difference was **−2.06 pp** [patient bootstrap 95% CI: −3.53, −0.50 pp].
- **Black survivors:** Difference of 100-seed means was **−1.30 pp**; bootstrap-based difference was **−1.31 pp** [95% CI: −2.18, −0.38 pp].
- **Other/Unknown race survivors:** Difference of 100-seed means was **−1.44 pp**; bootstrap-based difference was **−1.45 pp** [95% CI: −2.16, −0.79 pp].
- **Hispanic survivors:** Exhibited higher survivor coverage compared to White patients (+2.16 pp 100-seed difference; **+2.11 pp** [95% CI: +1.07, +3.16 pp]), but experienced reduced death coverage (87.62% [83.27%, 92.03%]).

#### 3. Model Calibration-in-the-Large (CITL) Bias Audit
Evaluating demographic miscalibration via CITL ($\bar{p} - \bar{y}$) demonstrated that model risk over/under-prediction contributes directly to coverage heterogeneity (*Table 3* and *Figure 2B*):
- At the population level, CITL was −0.0023 [95% CI: −0.0046, −0.0003] (a negligible 0.2 pp discrepancy).
- In exploratory subgroup audits, **Black patients** exhibited modest mortality risk over-prediction (CITL: **+0.0129** [95% CI: +0.0048, +0.0192]), whereas patients in the **Other/Unknown race category** experienced systematic under-prediction of mortality risk (CITL: **−0.0349** [95% CI: −0.0412, −0.0287]). Among insurance groups, Medicaid had CITL −0.0023, Medicare had −0.0036, and Private insurance had +0.0029.

---

![Figure 2: Racial and Socioeconomic Fairness Audit](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/outputs/figures/figure2_racial_and_payer_equity.png)

#### 🖼️ Detailed Description of Figure 2: Racial and Payer Fairness Audit
- **Figure Reference:** [`outputs/figures/figure2_racial_and_payer_equity.png`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/outputs/figures/figure2_racial_and_payer_equity.png)
- **Panel A (Survivor Disparities vs White Reference):** Horizontal forest bar plot documenting survivor coverage gaps relative to White patients. The solid navy vertical line represents White parity ($0.0\text{ pp}$). Red bars highlight statistically significant deficits for Asian (−2.10 pp [−3.53, −0.50]) and Black patients (−1.30 pp [−2.18, −0.38]), while the green bar depicts higher coverage for Hispanic patients (+2.16 pp [+1.07, +3.16]).
- **Panel B (Calibration-in-the-Large across Subgroups):** Horizontal bar chart mapping demographic miscalibration ($\bar{p} - \bar{y} \times 10^{-3}$). Red bars extending leftward indicate risk under-prediction (most severe in Other/Unknown race at $-34.9 \times 10^{-3}$ and Other insurance at $-19.0 \times 10^{-3}$), while blue bars extending rightward indicate risk over-prediction (most pronounced in Black patients at $+12.9 \times 10^{-3}$).
- **Panel C (Restoration of Demographic Parity):** Side-by-side grouped bar chart showing decedent coverage across all racial and payer categories before (Navy bars) and after (Teal bars) Mondrian class-conditional calibration. All groups—including Hispanic (87.6% $\to$ 90.3%), Private (86.6% $\to$ 90.3%), and Medicaid (88.0% $\to$ 90.6%)—are aligned directly along the nominal 90.0% red dashed threshold.

---

### 1.4 Group-Conditional (Mondrian) Conformal Repair & Variance Analysis
> **Data Sources:** Verified from [`paper/tables/table4_phase5_mondrian_comparison.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table4_phase5_mondrian_comparison.md) and [`paper/tables/table5_variance_ratio_audit.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table5_variance_ratio_audit.md).

#### 1. Coverage Restoration via Stratified Calibration
Implementing Mondrian class-conditional conformal prediction—computing calibration thresholds independently for each (subgroup $\times$ class) stratum—restored empirical coverage to the nominal 90.0% level across every audited demographic group (*Table 4*):
- **Age 18–49:** Death coverage increased from 84.06% to **90.42%** (paired bootstrap difference: **+6.25 pp** [95% CI: +5.21, +7.32 pp]; difference of 100-seed means: **+6.36 pp**). Survivor coverage adjusted from 94.90% to 89.97% (paired difference: −4.94 pp [−5.22, −4.66 pp]).
- **Age 75+:** Survivor coverage increased from 82.94% to **90.04%** (paired difference: **+7.10 pp** [+6.85, +7.35 pp]). Death coverage adjusted from 93.14% to 90.19% (paired difference: −2.96 pp [−3.28, −2.66 pp]).
- **Private insurance:** Death coverage increased from 86.60% to **90.25%** (paired difference: **+3.63 pp** [+3.12, +4.21 pp]).
- **Medicaid:** Death coverage increased from 87.97% to **90.56%** (paired difference: **+2.63 pp** [+2.17, +3.13 pp]).
- **Hispanic patients:** Death coverage increased from 87.62% to **90.28%** (paired difference: **+2.66 pp** [+1.68, +3.77 pp]).

#### 2. Split-to-Split Variance & Calibration-Set Sampling Noise
Auditing across the 100 independent splits revealed the true statistical origin of split-to-split variance (*Table 5*):
- Across-seed standard deviations for Mondrian calibration were only 7% to 50% larger than global baseline SD (variance ratio 1.07× to 1.50×, reaching 1.80× in small strata such as Other/Unknown insurance). This modest inflation reflects the finite-sample sampling noise inherent to smaller calibration cells.
- The empirical across-seed standard deviation of the paired difference ($\Delta = \text{Mondrian} - \text{Global}$) was **3.61 pp for age 18–49 death coverage**: while the mean repair is decisive (+6.25 pp), the realized delta fluctuates from split to split.
- **Statistical Resolution:** This split-to-split variation is primarily driven by test-sampling variability: in any single 25% test split, the age 18–49 stratum contains on average only **151 decedent stays**. The binomial standard error from test sampling alone is approximately $\sqrt{0.90 \times 0.10 / 151} \approx 2.44\text{ pp}$, which accounts for the vast majority of the observed 3.03%–3.49% seed SD.

---

### 1.5 The Pitfall of Mondrian Marginal Conformal Prediction
> **Data Source:** Verified from [`paper/tables/table6_mondrian_marginal_failure.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table6_mondrian_marginal_failure.md) and derived from `outputs/tables/phase5_subgroup_coverage_corrected_noflags_a010.csv`.

A crucial methodological insight established in this study is the catastrophic failure of unstratified Mondrian marginal conformal prediction in imbalanced clinical data (*Table 6* and *Figure 3B*). When calibration thresholds were conditioned exclusively on demographic groups without outcome class stratification:
- Overall group coverage nominally met 90.0% (e.g., 90.04% for age 18–49, 90.01% for age 50–64).
- However, decedent coverage collapsed catastrophically across every single stratum:
  - Age 18–49 death coverage collapsed to **11.77%** [across-seed range: 6.27%, 18.10%]
  - Age 50–64 death coverage collapsed to **18.15%** [across-seed range: 14.32%, 22.59%]
  - Age 65–74 death coverage collapsed to **22.52%** [across-seed range: 16.61%, 28.03%]
  - Age 75+ death coverage collapsed to **39.79%** [across-seed range: 35.12%, 45.26%]
- **Mechanism:** In an ICU population with 10.65% mortality, nonconformity quantiles computed marginally over both outcomes are entirely governed by the ~89% survivor majority. Decedents receive thresholds calibrated to survivors, resulting in the omission of death from prediction sets for up to 88% of dying patients.

---

### 1.6 Conformal Fairness vs Efficiency Trade-off Analysis
> **Data Source:** Verified from [`paper/tables/table8_tradeoff_efficiency_analysis.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table8_tradeoff_efficiency_analysis.md) and derived from `outputs/tables/phase7_tradeoff_efficiency_analysis.csv` and `outputs/figures/phase7_width_vs_fairness.png`.

A central concern regarding subgroup-calibrated conformal prediction is that enforcing equitable coverage will expand prediction sets to uninformative sizes ({survive, die}), degrading clinical utility. Quantifying the efficiency penalty demonstrated that this cost is remarkably small (*Table 8* and *Figure 3*):
- Across all 15 audited demographic strata, the change in mean prediction set size ($\Delta |S| = |S|_{\text{Mondrian}} - |S|_{\text{Global}}$) was tightly bounded between **−0.060 and +0.058 labels per patient**.
- For patients aged 18–49, repairing death coverage from 84.06% to 90.42% increased mean set size from 1.147 to 1.176 labels—an efficiency penalty of only **+0.029 labels (+2.57% relative change)**. The proportion of inconclusive dual-label sets rose by only 2.94 percentage points (from 14.68% to 17.62%), meaning that **>82% of young patients retained definitive singleton predictions** ({survive} or {die}).
- For patients aged 75+, mean set size shifted from 1.356 to 1.377 (+0.020 labels, +1.49% change).
- Across racial minorities, set-size expansion was minimal: +0.005 for White (+0.4%), +0.015 for Black (+1.2%), +0.045 for Hispanic (+3.7%), and +0.058 for Asian (+4.7%).
- In summary, establishing mathematically guaranteed subgroup equity does not dilute clinical predictive resolution or overwhelm bedside clinicians with uninformative sets.

---

![Figure 3: Conformal Fairness vs Efficiency Trade-off Analysis](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/outputs/figures/figure3_fairness_efficiency_tradeoff.png)

#### 🖼️ Detailed Description of Figure 3: Fairness vs Efficiency Trade-off Analysis
- **Figure Reference:** [`outputs/figures/figure3_fairness_efficiency_tradeoff.png`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/outputs/figures/figure3_fairness_efficiency_tradeoff.png) (also preserved as `phase7_width_vs_fairness.png`).
- **Panel A (Subgroup Death Coverage vs Set Size):** Scatter plot with directional arrows depicting the trajectory from baseline global conformal (Navy circles) to Mondrian class-conditional calibration (Teal diamonds). The horizontal dashed line denotes the nominal 90.0% target. Arrows move vertically towards 90% with almost negligible horizontal movement, visually proving that coverage is restored with near-zero set-size inflation.
- **Panel B (The Pitfall: Collapse of Mondrian Marginal):** Compares Mondrian class-conditional sets (Teal diamonds, perfectly aligned at 90.0%) against naive Mondrian marginal sets (Red squares). Red dashed trajectory lines show the catastrophic collapse of death coverage down to 11.8% (age 18–49), 18.2% (age 50–64), 22.5% (age 65–74), and 39.8% (age 75+), demonstrating why class conditioning is non-negotiable.
- **Panel C (Efficiency Penalty by Subgroup):** Horizontal bar chart illustrating the net set-size change ($\Delta |S|$) and percentage expansion for all 15 demographic subgroups. Positive bars (teal) and negative bars (blue) demonstrate that the efficiency penalty is strictly bounded within $[-0.060, +0.058]$ labels per patient across the entire cohort.

---

## 2. Discussion

### 2.1 Summary of Principal Findings
In this large-scale evaluation of conformal prediction fairness across 51,838 ICU admissions in MIMIC-IV, we established three primary insights:
1. Standard split conformal prediction, despite meeting population-level 90.0% coverage, systematically fails vulnerable subpopulations. Most prominently, young decedents (aged 18–49) suffer a 5.94 pp coverage deficit (84.06%), leaving acute life-threatening events unrecognized.
2. Naive group-conditional conformal prediction without class conditioning (Mondrian marginal) suffers a catastrophic mathematical failure in imbalanced clinical cohorts, reducing decedent coverage to 11.8%–39.8%.
3. Full Mondrian class-conditional conformal prediction restores exact nominal coverage across all demographic subgroups by construction on exchangeable calibration data, with a negligible efficiency cost of at most +0.058 labels per patient.

### 2.2 Direct Comparison with Prior Literature
Recent benchmark studies applying conformal prediction to critical care data—such as the JMIR 2024 study on sepsis mortality (Yang et al., AUROC 0.858, error rate 10.5%)—demonstrated the feasibility of conformal inference but cited demographic fairness as an unaddressed limitation. Our findings empirically confirm their cautionary notes and extend them substantially: we prove that marginal validity masks deep intra-group gaps and establish the precise mathematical calibration framework required to eliminate them. Furthermore, our findings caution against naive applications of group-conditional conformal prediction, emphasizing that in healthcare contexts characterized by acute class imbalance, class conditioning is non-negotiable.

### 2.3 Clinical Implications for Intensive Care
In intensive care units, prognostic algorithms frequently inform triage, rapid response escalation, and goals-of-care discussions. When an uncertainty quantification tool outputs a prediction set that omits death for 16% of young patients who ultimately die (compared to the nominal 10% error rate), clinicians may be falsely reassured by algorithmic certainty. Restoring equitable coverage guarantees ensures that uncertainty quantification remains trustworthy across all patients, irrespective of age, insurance coverage, or racial background. Because Mondrian class-conditional sets maintain a high singleton rate (>82%), this equity is gained without flooding clinical workflows with ambiguous dual-label outputs.

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
