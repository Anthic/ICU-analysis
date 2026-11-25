# Paper summary: what we did, what we found, why it is different, research gap (2026-11-25)

## 1. Question
Do standard split conformal prediction (CP), class-conditional CP and group-conditional (Mondrian) CP give the same coverage across age, race, sex and insurance strata in ICU mortality prediction, and why do they differ? Data: MIMIC-IV v3.1 (51,838 stays, 5,522 deaths) for development; eICU-CRD v2.0 (95,558 stays, 207 hospitals) for external validation. XGBoost baseline, alpha = 0.10, 100 random splits.

## 2. What we found
1. Marginal CP reaches 90.0% overall coverage but covers only 23.5% of deaths. Class-conditional CP fixes the pooled death coverage (90.1%).
2. Pooled class-conditional coverage still differs by age: deaths 84.1% (18-49) vs 93.1% (75+); survivors 94.9% vs 82.9%. Race and sex gaps are small and not stable.
3. Mechanism: class-conditional coverage equals sensitivity and specificity of two risk thresholds. If scores are calibrated, each group's coverage follows from its score distribution (label-free identity). It explains the survivor-side gap (R2 0.95-0.99) and the direction/order of the death-side gap, not its size.
4. Age Mondrian = group-specific thresholds = equalised-odds post-processing (sets identical for 99.2% MIMIC, 99.7% eICU). The conformal framing adds no new guarantee beyond this.
5. Cost of equalising coverage: P(death | survivor-only set) 0.9% young vs 3.2% 75+; set size rises; risk-bin sets are ~80% uninformative.
6. Robust to: end-of-life flags, temporal split, logistic model, alpha 0.05-0.20, placebo tests (permuted age: gap at noise floor).
7. eICU: age pattern transports but hospital-level variation is large; raw scores need recalibration for the identity to fit.

## 3. Why this paper can be better than others
Not better numbers. Better rigour and completeness: label-free testable mechanism, explicit equivalence to equalised odds, utility cost reporting, external validation with hospital clustering, placebo/negative controls, honest limits, reproducible scripts for every number.

## 4. Research gap
Prior work shows conformal coverage gaps or proposes Mondrian fixes. Few papers (a) explain the gap from the score distribution without labels, (b) show the equivalence to equalised odds, (c) quantify what equal coverage costs clinically, and (d) validate across hospitals. Overlap to check: Gao 2026a, Zhong 2026, Tasar 2025 (full texts not yet read).

## 5. Table 4 vs Table 8 audit (done 2026-11-25)
Table 4 paired differences were hard-coded patient-bootstrap values (+6.25 pp for 18-49 deaths); Table 8 used 100-seed means (+6.36). Now Table 4 is computed from per-seed CSVs (mean paired difference, seed SD, 2.5-97.5 percentile of split-level differences). Both tables agree (+6.36). Manuscript and results_draft updated; backups in `_backup_before_fix_2026-11-22/`.
