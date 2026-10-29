# 02. Journal Targets, Formatting Guidelines, & Publication Strategy

> **Purpose:** Specific submission instructions, target journal profiles, word count limits, formatting standards, and structural guidelines for submitting this paper to top-tier (Q1) clinical informatics and digital health journals.

---

## 1. Top Target Journals & Their Profiles

### 🥇 Target 1: *Journal of the American Medical Informatics Association (JAMIA)*
- **Publisher:** Oxford University Press (Official journal of AMIA)
- **Impact Factor:** ~5.0 – 7.0 (Q1 in Medical Informatics)
- **Why this is the best fit:** JAMIA is the #1 premier venue for machine learning and statistical methods applied to Electronic Health Records (MIMIC-IV). They strongly value health equity, methodological rigor (100 seeds, bootstrap CIs), and rigorous clinical audits.
- **Article Type:** *Research and Applications*
- **Word Limit:** Up to 4,000 words (excluding abstract, references, tables, and figures).
- **Structure:**
  - Structured Abstract (max 250–300 words): Objective, Materials and Methods, Results, Discussion, Conclusion.
  - Introduction
  - Materials and Methods
  - Results
  - Discussion (including Limitations)
  - Conclusion

---

### 🥈 Target 2: *The Lancet Digital Health*
- **Publisher:** Elsevier / The Lancet
- **Impact Factor:** ~25.0+ (Top 1% in Health Informatics & Medicine)
- **Why it fits:** World-leading clinical journal focusing on high-impact AI models that directly affect patient outcomes and health disparities.
- **Article Type:** *Article*
- **Word Limit:** 3,500 – 4,500 words.
- **Structure:**
  - Summary / Abstract (max 300 words): Background, Methods, Findings, Interpretation, Funding.
  - Introduction, Methods, Results, Discussion.
  - Mandatory *Research in context* panel:
    - Evidence before this study
    - Added value of this study
    - Implications of all the available evidence

---

### 🥉 Target 3: *npj Digital Medicine* (Nature Portfolio)
- **Publisher:** Springer Nature
- **Impact Factor:** ~15.0+ (Q1 in Digital Health)
- **Why it fits:** Focuses on cutting-edge computational approaches that provide mathematical guarantees for bedside clinical care.
- **Article Type:** *Article*
- **Word Limit:** ~4,000 words.
- **Structure:**
  - Abstract (unstructured, ~200 words).
  - Introduction, Results, Discussion, Methods (Methods placed after Discussion).

---

## 2. Universal Reporting Guidelines: TRIPOD+AI & STROBE

All modern Q1 journals require compliance with **TRIPOD+AI** (Transparent Reporting of a Multivariable Prediction Model for Individual Prognosis or Diagnosis—AI):

| TRIPOD+AI Section | Item Checklist for Our Study | Where Handled in Our Pipeline |
|---|---|---|
| **Title & Abstract** | State AI model, clinical task (mortality), uncertainty method (conformal prediction), and demographic fairness | Handled in manuscript draft |
| **Source of Data** | Clear provenance of MIMIC-IV v3.1, BIDMC, institutional IRB approvals and PhysioNet DUA | Handled in `reviewer_responses_and_methods_evidence.md` |
| **Participants & Flow** | Complete exclusion cascade (All ICU -> First Stay -> 24h LOS -> Adult) | Fully documented in Table 1 (`table1_cohort_summary.md`) |
| **Outcome Definition** | In-hospital mortality; define acute observation window (24h) | Standardized in Phase 1 cohort script |
| **Predictor Variables** | Vitals and labs within 24h; explicit missingness reporting | Documented in Phase 2 feature parquet & missingness tables |
| **Handling Missingness** | Document native XGBoost handling; audited missing-indicator flags | Documented in Phase 3 experiments |
| **Model Development** | 100 independent splits (50/25/25); gain importance reporting | Completely verified in Phase 3 baseline |
| **Fairness & Subgroups** | Subgroup stratification by Race, Sex, Age, Insurance; intersectional audits | Fully evaluated in Phase 4 and Phase 5 audits |
| **Uncertainty Calibration** | Report both marginal and class-conditional coverage; set size distribution | Evaluated in Phase 4, 5, and 7 tables and figures |
| **Statistical Uncertainty** | Report split standard deviations and patient bootstrap 95% CIs | B=1,000 bootstrap executed in reaggregation script |

---

## 3. Formatting Strategy (How to Write Once, Submit Anywhere)

To ensure zero friction when submitting or adapting to different journal guidelines:

1. **Write in Standard Markdown first (`.md`):** Keep text, tables, and mathematical formulas cleanly separated.
2. **Standard Abstract Structure (JAMIA Style):**
   - **Objective:** What gap does the paper address?
   - **Materials and Methods:** Dataset, cohort size, ML baseline, conformal calibration setup, 100-seed evaluation.
   - **Results:** Primary numerical findings (84% young decedent coverage, +6.25 pp Mondrian repair, +0.029 set-size penalty).
   - **Discussion:** Clinical meaning and pitfall of unstratified marginal conformal prediction.
   - **Conclusion:** Takeaway clinical message.
3. **Reference Style:** Write using numbered citations `[1]`, `[2]`, `[3]`. We will maintain a clean `references.bib` or formatted Vancouver list.
4. **Tables and Figures Placement:** In initial submission, tables and figures are referenced inline and placed at the end or uploaded as separate high-resolution files (`outputs/figures/*.png`).

