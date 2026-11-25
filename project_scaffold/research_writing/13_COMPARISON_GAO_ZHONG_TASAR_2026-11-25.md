# Closest-paper comparison: Gao 2026a, Zhong 2026, Tasar 2025 (2026-11-25)
Status of reading: Zhong 2026 = about 80% of full text read (arXiv PDF truncated; limitations section only via summary). Tasar 2025 = about first 40K of 88K characters verbatim, rest via model summary. **Gao 2026a = full-text summary supplied by the user (2026-11-25), not independently read by me** (arXiv PDF was rate-limited for my fetches). Verify the points marked [user] against the PDF before submission.

## 1. Gao, Liu, Yang, Belbahri, Cresswell, Asgharian. "On the Burden of Achieving Fairness in Conformal Prediction", arXiv 2605.14260 (NeurIPS 2026 per first-page footnote [user]; arXiv v1 May 2026, alphaXiv lists Nov 2026: cite the proceedings/final version)
Abstract (read by me): pooled split-conformal threshold hides cross-group score-distribution differences; "conservation law" and a lower bound give irreducible group-wise coverage distortion scaled by cross-group quantile heterogeneity; Equalized Coverage and Equalized Set Size are in tension.
Full-text points [user]:
- Data: no clinical or ICU data. Real data are Bias in Bios (DistilBERT, 10 professions, gender), MultiNLI (DistilBERT, 10 genres as groups) and FACET (zero-shot CLIP ViT-L/14, 20 occupations, 4 age groups), plus synthetic Gaussian, wide Gaussian, Gamma and heavy-tail t distributions.
- Coverage: marginal (pooled threshold) and group-conditional (group-specific thresholds, "Equalized Coverage"). Class-conditional coverage (given Y) is not studied; "groups" are covariate subgroups G(X).
- Theory: Theorem 1 conservation law, sum_g p_g * eps_g(q) = F_S(q) - (1 - alpha) (assumes the mixture CDF is continuous at the pooled quantile; randomised ties otherwise). Theorem 2 uncertainty relation / lower bound, Var(eps_G(q)) >= m_eff^2 Var(q_G), under local absolute continuity with a positive density infimum per group.
- Scores need not be calibrated; the class base rate pi_g does not enter. Appendix A.4 contrasts with Chouldechova 2017 and Kleinberg 2017: there base-rate differences drive the trade-off, here cross-group quantile heterogeneity does.
- No label-free prediction of coverage gaps from unlabeled test data; gaps are measured with test labels.
- Equalised odds (Hardt 2016) is cited as a conceptual precedent only; their fairness notions are Equalized Coverage and Equalized Set Size.
- Limitations: pre-specified discrete groups; local regularity assumptions (positive density lower bound, set-size responsiveness); population-level theorems with finite-sample noise when calibration sets are small; non-normative scope.
Overlap with us: same pooled-threshold intuition, expressed through score quantiles; cost of moving between pooled and group-separate calibration.
Our difference: clinical (ICU mortality, MIMIC-IV + eICU); class-conditional coverage (deaths vs survivors), where sensitivity and specificity of two risk thresholds give an identity that does involve calibration and base rates; label-free calibration-implied test that fails when calibration fails; equivalence of age Mondrian and equalised-odds-type thresholds; predictive-value cost (P(death | set)); external hospital-level validation. Their conservation law and lower bound are general theory we should cite and build on, not claim.
Careful wording: "Pooled-threshold coverage distortion has been formalised in terms of cross-group score quantiles [Gao 2026a]. We study the class-conditional case in ICU data, where, under within-group calibration, the distortion is determined by each group's score distribution and base rate."

## 2. Zhong, Wang, Huang, Shi. "When Is a Conformal Guarantee Fair? Auditing Silent Subgroup Under-Coverage in Alzheimer's Disease Longitudinal Prediction", arXiv 2608.04254 (Aug 2026)
- Data: ADNI (400 subjects) and OASIS-3 (658); biomarker forecasting, not mortality; 9 audited attributes.
- Finding: marginal coverage nominal but the a priori high-risk subgroup under-covered in 57 of 68 combinations; clinical-risk subgroups short by mean 6.1 pp, demographic subgroups about 0.
- Mechanisms: (A) rarity (cell with n calibration points covers k/(n+1); starved below ceil(1/alpha)-1), (B) tail-heaviness of subgroup scores (Prop. 2). Calibration/base-rate account not named.
- Their repair: per-subgroup calibration + cross-conformal pooling + one-sided marginal floor; compares with Gibbs-Candes conditional conformal.
- Closest to our "label-free" idea: coverage tracks k/(n+1) and a calibration-estimated tail ratio (r = -0.83) but checked against test coverage, not a falsifiable identity from calibrated scores.
- Our difference: classification with class-conditional coverage; mechanism = calibrated scores and base rates under one pooled threshold, tested with a label-free identity and failure case; equalised-odds equivalence; clinical utility cost; ICU external validation. Their small-cell rarity mechanism is complementary and relevant to our small strata (Asian, Hispanic about 39 deaths per split).
- Note: Zhong's high-risk subgroup under-coverage (clinical-risk subgroups) vs our age pattern: both show marginal guarantees hiding subgroup shortfalls.

## 3. Tasar. "The Coverage-Deferral Trade-Off: Fairness Implications of Conformal Prediction in Human-in-the-Loop Decision Systems", Preprints.org 202512.2631 v1 (30 Dec 2025, single author, not peer reviewed)
- Data: six non-clinical tabular datasets (Adult, COMPAS, German Credit, Taiwan Credit, ACS Income, Bank Marketing); APS scores; 100 seeds, alpha 0.10.
- Finding (abstract): Mondrian CP raises deferral disparity by 143% (gap 0.052 -> 0.125 in the summary) while reducing coverage disparity by 26% on average; coverage gaps do not fall on every dataset (COMPAS, German, Taiwan rose).
- Mechanism: forcing equal coverage needs larger sets for harder or lower-base-rate groups; Kleinberg-style impossibility between coverage parity and deferral parity.
- Claim of invariance of equalised odds to CP method (CP changes sets, not point predictions).
- Our difference: clinical mortality, class-conditional coverage, age; we show Mondrian-by-age = group thresholds (equalised-odds-type), directly measuring set-size gap (about 0.2 labels) and predictive value (P(death | survivor-only set) 0.9% vs 3.2%), which is the clinical analogue of their deferral cost. Their invariance claim concerns point-prediction metrics, ours concerns what the sets deliver.
- Our result supports theirs: Mondrian raised set size in 3 of 4 age strata and the 75+ stratum got larger sets.

## Positioning sentences (draft, fill after Gao full text)
"Pooled-threshold theory for group coverage distortion has recently been formalised through score quantiles, without class-conditional coverage or calibration [Gao 2026a], rarity and tail-heaviness have been identified as causes of subgroup under-coverage [Zhong 2026], and group-conditional calibration has been shown to shift deferral burden [Tasar 2025]. We add a clinical classification study with class-conditional coverage in two ICU databases, a label-free calibration-implied test that fails when calibration fails, an explicit equivalence to equalised-odds thresholds, and measurement of what equal coverage costs in predictive value."
## Not to claim
That the pooled-threshold mechanism, the coverage-deferral trade-off, or subgroup under-coverage auditing is new in itself.
