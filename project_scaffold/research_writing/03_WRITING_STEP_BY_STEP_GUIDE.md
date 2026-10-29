# 03. Step-by-Step Research Writing Action Plan (A Clear Roadmap)

> **Don't feel overwhelmed!** You have already completed the most difficult, computationally intensive 80% of the entire research project (100-seed machine learning modeling, rigorous audits, statistical bootstrap, tables, and figures).
> 
> Academic paper writing is simply assembling pre-computed evidence into a standard 5-chapter story. Here is the exact roadmap:

---

## 🗺️ The Complete Paper Writing Roadmap

```
[Phase A: Evidence (100% DONE)] ──> Tables 1–8, Figures 1–3, 100-Seed Verifications
                                            │
                                            ▼
[Phase B: Results & Discussion (100% DONE)] ──> paper/results_draft.md
                                            │
                                            ▼
[Phase C: Introduction & Methods (NEXT STEP)] ──> 4-Paragraph Intro & Methods Sections
                                            │
                                            ▼
[Phase D: Abstract & Title] ──> Structured 250-word executive summary
                                            │
                                            ▼
[Phase E: Master Manuscript Assembly] ──> 00_MANUSCRIPT_MASTER.md (Submission-ready)
```

---

## Step 1: The Introduction (The 4-Paragraph Formula)
Every top-tier journal paper (JAMIA, Lancet, Nature) uses the exact same 4-paragraph formula for the Introduction:

- **Paragraph 1: The Clinical Reality & Promise of AI**  
  *Content:* Intensive care units require urgent prognostic decisions. AI models (like XGBoost) can predict mortality, but black-box point probabilities lack statistical guarantees. Clinicians need reliable uncertainty quantification.
- **Paragraph 2: The Conformal Prediction Solution & The Healthcare Gap**  
  *Content:* Conformal prediction provides distribution-free, finite-sample guarantees by outputting prediction sets. However, standard conformal prediction only guarantees *marginal* coverage over the aggregate population.
- **Paragraph 3: The Clinical Fairness Trap (The Problem)**  
  *Content:* In critical care, mortality is heavily imbalanced (~10%). If an algorithm covers 90% overall, it can achieve this by covering survivors while failing young or minority decedents. Prior clinical benchmarks (e.g. JMIR 2024 sepsis paper) acknowledged subgroup disparities as an open limitation.
- **Paragraph 4: What This Paper Does (Specific Aims)**  
  *Content:* We audit 51,838 MIMIC-IV ICU stays across 15 demographic subgroups over 100 independent splits. We show where standard conformal fails, prove why naive Mondrian conformal fails catastrophically, and demonstrate that class-conditional Mondrian conformal restores exact equity with negligible set-size cost.

---

## Step 2: The Methods Section (Pre-Computed Facts)
The Methods section simply documents the exact code pipelines we have already run:
1. **Cohort & Data Source:** MIMIC-IV v3.1, Beth Israel Deaconess Medical Center, adult first ICU admissions $\ge 24$ hours ($N = 51,838$, 10.65% mortality).
2. **Features:** 24-hour vitals and labs, min/max/mean aggregation, missingness handled natively by XGBoost.
3. **Model & Conformal Framework:** 100 random splits (50% train, 25% calibration, 25% test), XGBoost baseline, nonconformity score $s_i = 1 - \hat{p}(y_i|x_i)$.
4. **Mondrian Calibration & Fairness:** Class-conditional calibration vs Mondrian group-conditional calibration. Handling small strata ($n=0$ conservative $\infty$ quantile rule).
5. **Statistical Metrics & Bootstrap:** Patient-level bootstrap (B = 1,000, fixed seed 42), across-seed standard deviations (seed SD), paired differences, and calibration-in-the-large (CITL).

---

## Step 3: The Results Section (Already Done!)
You don't need to write this from scratch! We already compiled this in [`paper/results_draft.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/results_draft.md), citing:
- **Table 1:** Cohort inclusion & demographics
- **Table 2:** Baseline model AUROC (0.8726) & standard conformal calibration
- **Table 3 & Table 7:** Phase 4 Subgroup audit (Age 18–49 under-coverage at 84.06%; survivor disparities vs White)
- **Table 4 & Table 5:** Mondrian class-conditional repair (+6.25 pp gain) & seed SD analysis
- **Table 6:** Naive Mondrian marginal failure (11.77% death coverage)
- **Table 8 & Figure 3:** Set-size tradeoff analysis (+0.029 set-size penalty)

---

## Step 4: The Discussion Section (Already Done!)
Also already compiled in [`paper/results_draft.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/results_draft.md):
- Core clinical insights
- Comparison with existing literature (JMIR 2024, Romano et al.)
- Clinical implications for ICU triage & bedside care
- Methodological recommendations for health data scientists
- Thorough limitations (single-center, coarse race labels, multiple testing)

---

## Step 5: The Abstract (The 5-Minute Summary)
Once the manuscript is assembled, the abstract is created by pulling 1–2 sentences from each section into a structured 250–300 word summary.

---

## ✅ What You Need to Do Right Now
Nothing complicated! You don't have to worry or be confused.
Let us assemble the full **Master Manuscript (`00_MANUSCRIPT_MASTER.md`)** in this `research_writing/` folder so you have a complete, cohesive paper ready to review, cite, and polish.

