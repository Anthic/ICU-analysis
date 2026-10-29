# 05. Top-Class Manuscript Writing Blueprint (The Gold Standard)

> **Purpose:** A master blueprint for writing every section of your paper to match the rigorous standards of **JAMIA**, **The Lancet Digital Health**, and **npj Digital Medicine**. Follow these sentence-by-sentence templates, paragraph transitions, and strategic framing formulas.

---

## 🏛️ The Architecture of a Top-Tier Medical AI Paper

Top-tier editors reject 80% of papers within 5 minutes because the papers read like "an engineering experiment" rather than "a high-stakes clinical contribution". To ensure an immediate positive decision, structure your manuscript around this narrative arc:

```
[Clinical Stakes & Problem] ──> [Mathematical Opportunity (Conformal)] ──> [The Hidden Danger (Fairness Breach)] ──> [The Clean Solution (Mondrian CC)] ──> [Zero-Cost Practical Utility]
```

---

## Section 1: Title & Abstract (Hooking the Editor)

### The Winning Title Formula:
`[Rigorous Methodology/Intervention] + [Clinical Objective] + [Setting/Population] + [Study Design]`
- **Our Working Title:**
  > *Group-Conditional Conformal Prediction for Equitable Uncertainty Quantification in ICU Mortality Risk Prediction: A Retrospective Cohort Study on MIMIC-IV*

### The 4-Part Structured Abstract Formula (250–300 Words):
1. **Objective (3 sentences):** State the clinical task, why point predictions are inadequate, and the unaddressed gap in demographic fairness.
2. **Materials and Methods (4 sentences):** State MIMIC-IV v3.1, $N = 51,838$, 24-hour observation window, 100 independent splits, XGBoost baseline, split conformal vs Mondrian class-conditional, and patient-level bootstrap (B = 1,000).
3. **Results (5 sentences):** Give the exact striking numbers:
   - Baseline AUROC 0.8726.
   - Global calibration masks severe under-coverage of young decedents (84.06% for age 18–49, 5.9 pp below nominal).
   - Naive Mondrian marginal collapses death coverage to 11.77%–39.79%.
   - Mondrian class-conditional restores exact 90% across all 15 subgroups (age 18–49 reaches 90.42%, paired gain +6.25 pp).
   - Set-size cost is negligible (+0.029 labels, +2.57% for age 18–49; >82% singleton sets).
4. **Discussion & Conclusion (2 sentences):** Emphasize that class-conditioning is non-negotiable in imbalanced medicine, and Mondrian conformal provides provable equity for bedside AI.

---

## Section 2: Introduction (The Inverted Pyramid)

Use the strict **4-Paragraph Formula**:

### Paragraph 1: The Clinical Reality & High Stakes
- **Goal:** Establish that ICU mortality prediction is life-or-death, but heuristic AI probabilities can mislead clinicians.
- **Key sentence starters:**
  - *"Intensive care units (ICUs) represent high-stakes clinical environments where rapid, accurate risk stratification dictates clinical escalations, ICU bed allocation, and goals-of-care deliberations [1, 2]."*
  - *"Although machine learning models—particularly gradient-boosted decision trees and deep neural networks—demonstrate impressive discriminative performance [3], their output probabilities are frequently miscalibrated and fail to communicate individual prediction confidence [4]."*
  - *"In safety-critical medicine, an overconfident incorrect prediction risks catastrophic clinical outcomes, establishing robust uncertainty quantification as a foundational pillar for trustworthy artificial intelligence [5]."*

### Paragraph 2: Conformal Prediction as the Solution
- **Goal:** Introduce conformal prediction as modern distribution-free mathematics with finite-sample guarantees.
- **Key sentence starters:**
  - *"Conformal prediction offers an appealing, distribution-free mathematical framework that wraps around any predictive model to generate prediction sets with finite-sample statistical guarantees [6, 7]."*
  - *"Unlike Bayesian methods or temperature scaling that depend on parametric assumptions, split conformal prediction guarantees that the true patient outcome is captured within the prediction set at a user-defined nominal confidence level (e.g., $1 - \alpha = 90\%$), requiring only exchangeability [8]."*

### Paragraph 3: The Healthcare Trap & The Research Gap
- **Goal:** Show that standard conformal guarantees are only *marginal* across the whole population. In imbalanced ICU cohorts (10% mortality), the 90% guarantee is satisfied by covering survivors while failing vulnerable minorities.
- **Key sentence starters:**
  - *"However, standard conformal prediction guarantees validity only marginally over the aggregate patient population [9]."*
  - *"In clinical medicine, where acute mortality is heavily imbalanced (typically 8% to 15%) [10], an algorithm can achieve nominal 90% overall coverage entirely by capturing the vast survivor majority while systematically failing patients who die [11]."*
  - *"Recent critical care benchmarks applying conformal prediction to sepsis mortality (e.g., Yang et al. in JMIR 2024) demonstrated aggregate feasibility but explicitly cited demographic subgroup fairness as an unresolved limitation [12]. Whether standard conformal prediction preserves equity across demographic strata—such as age, race, biological sex, and health insurance payer—remains fundamentally uncharacterized."*

### Paragraph 4: Specific Aims of This Paper
- **Goal:** Clear, bulletproof declaration of what we did across 51,838 patients over 100 splits.
- **Key sentence starters:**
  - *"To resolve these foundational questions, this study presents a rigorous multi-attribute audit and correction of conformal prediction in critical care."*
  - *"Using the MIMIC-IV database ($N = 51,838$), we evaluate 100 independent random train/calibration/test splits to address three core aims: (1) audit subgroup coverage disparities under standard split conformal prediction; (2) expose the empirical failure of naive group-conditional conformal prediction under acute class imbalance; and (3) establish provably equitable coverage via Mondrian class-conditional conformal prediction while quantifying the exact prediction-set efficiency penalty."*

---

## Section 3: Materials and Methods (TRIPOD+AI Compliance)

Structure Methods into 5 distinct, numbered subsections:

1. **2.1 Cohort Selection & Provenance:**
   - Mention Beth Israel Deaconess Medical Center, MIMIC-IV v3.1, PhysioNet credentialing, IRB waiver.
   - Describe Table 1 exclusion hierarchy: All ICU (94,458) $\to$ First stay only (65,366) $\to$ LOS $\ge 24$ hours (51,838) $\to$ Adult $\ge 18$ (51,838).
   - Observed mortality rate: **10.65%** (5,522 deaths / 51,838 patients; exact: 0.106524).
2. **2.2 Feature Engineering & Missingness Handling:**
   - 24-hour observation window.
   - Vitals from `chartevents`, labs from `labevents` (6h prior to 24h post-admission).
   - Summary statistics: min, max, mean.
   - Author-defined physiological outlier filtering (NaN conversion).
   - Native XGBoost missingness handling; audited missingness flags (zero importance).
3. **2.3 Predictive Modeling & Experimental Splitting:**
   - 100 independent splits (50% train, 25% calibration, 25% test).
   - XGBoost baseline architecture.
   - Discrimination metrics: AUROC, AUPRC; Calibration: Brier score, slope, intercept.
4. **2.4 Conformal Prediction Formulation:**
   - Nonconformity score: $s_i = 1 - \hat{p}(y_i|x_i)$.
   - Mathematical formula for standard marginal quantile.
   - Mathematical formula for standard class-conditional quantiles ($\hat{q}_{y=0}, \hat{q}_{y=1}$).
   - Mathematical formula for Mondrian class-conditional quantiles $\hat{q}_{a, k}$ per subgroup stratum.
   - Exact code rule for $n=0$ or small cells: assign $+\infty$ to guarantee conservative inclusion of label $k$ ($1 - \hat{p} \le \infty$).
5. **2.5 Multi-Attribute Fairness Audit & Statistical Rigor:**
   - Single attributes: Age (4 groups), Insurance (4 groups), Race (5 groups), Sex (2 groups).
   - 100-seed standard deviations (seed SD) to capture split-to-split variance.
   - Patient-level bootstrap (B = 1,000, fixed seed 42) for 95% CIs.
   - Calibration-in-the-large (CITL = $\bar{p} - \bar{y}$). Positive CITL = model over-predicts mortality risk.

---

## Section 4: Results (Telling the 5-Act Story)

Walk the reader through the 5 acts, referencing the exact tables and figures:

- **Act 1: Model Discrimination & Population Validity (*Table 1 & 2*)**
  - XGBoost achieved AUROC 0.8726, AUPRC 0.5023.
  - Overall class-conditional coverage met nominal: 90.14% for deaths, 90.02% for survivors.
- **Act 2: The Hidden Disparity in Standard Conformal Prediction (*Table 3, Table 7*)**
  - Young decedents (18–49) achieved only **84.06%** death coverage (5.94 pp below nominal).
  - Older decedents (75+) had 93.14% death coverage, but survivors had 82.94% coverage.
  - Asian and Black survivors experienced −2.10 pp and −1.30 pp lower coverage compared to White patients (*Table 7*).
  - Other/Unknown race exhibited CITL −0.0349 (under-prediction of risk), Black patients exhibited +0.0129 (over-prediction of risk).
- **Act 3: The Trap of Naive Mondrian Marginal Conformal Prediction (*Table 6, Figure 3B*)**
  - When conditioning only on groups without classes, death coverage collapsed to **11.77%** for age 18–49 and **18.15%** for age 50–64.
  - Explain mechanism: ~89% survivor majority dominates the threshold.
- **Act 4: The Mondrian Class-Conditional Solution (*Table 4, Table 5*)**
  - Restores exact 90% across all groups (Age 18–49 death coverage reached **90.42%**, paired gain +6.25 pp).
  - Seed SD explanation: 3.6 pp seed SD of delta is test-sampling variation from ~151 deaths per split (*Table 5*).
- **Act 5: The Negligible Efficiency Penalty (*Table 8, Figure 3A & 3C*)**
  - Set size delta $\Delta |S|$ bounded within $-0.060$ to $+0.058$ labels.
  - Age 18–49 set size increased by only **+0.029 labels (+2.57%)**.
  - >82% of patients retain definitive singleton predictions {survive} or {die}.

---

## Section 5: Discussion (The Intellectual Powerhouse)

Address these 4 pillars:

1. **Comparison with Prior Benchmarks (e.g. JMIR 2024):**
   - Directly contrast with Yang et al. (JMIR 2024): our AUROC is higher (0.8726 vs 0.858), and we address the exact subgroup disparity gap they left unsolved.
2. **Clinical Implications for Intensive Care:**
   - Under standard conformal, clinicians are falsely reassured when death is omitted for 16% of young dying patients.
   - Mondrian class-conditional guarantees that "90% means 90% for every patient, regardless of demographic background".
3. **Methodological Lessons for Healthcare AI:**
   - In clinical medicine with class imbalance, class conditioning is not optional—it is mathematically mandatory.
4. **Honest Limitations:**
   - Single-center development (MIMIC-IV); eICU external validation planned.
   - Coarse administrative race categories.
   - Predictors restricted to first 24h.
   - Small strata (Asian/Hispanic deaths: ~39/split) show finite-sample variance.

