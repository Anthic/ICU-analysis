# Novelty positioning and literature synthesis (2026-11-22)  [GENERATED — PENDING AUTHOR REVIEW]

Project: group-conditional conformal prediction for equitable uncertainty quantification in ICU mortality prediction (MIMIC-IV, eICU-CRD).
Method of this synthesis: OpenAlex keyword searches (web search was not available), about 16 queries, 2019–2026; metadata (authors, year, venue, DOI) verified through OpenAlex records; **only abstracts were read, not full texts**. Many 2026 items are preprints or registry entries, not peer reviewed. The search can miss papers. Re-run before submission and read the full text of every paper in Table 2.

## 1. Executive summary
The ingredients of this project are all known: class-conditional and Mondrian calibration give group-wise coverage by construction; pooled thresholds are known to distort group-wise coverage, now with theory; subgroup audits of conformal coverage exist in other clinical areas; conformal prediction has been transported between MIMIC-IV and eICU. No contribution should be framed as a new method, a first audit, or a new theorem. What the abstracts do not show, and what this project adds, is a single ICU-mortality study that (a) separates cross-database transport shift from within-database group heterogeneity, (b) shows a two-sided age pattern (young decedents and elderly survivors under-covered) that replicates in a second database with pre-specified endpoints (one of which failed in the primary model), (c) attributes the gap to the model shifting scores with age under a pooled threshold, with an age-blind ablation and a risk-bin alternative, and (d) reports a minimum-calibration-deaths rule for group-specific thresholds. The honest contribution is a rigorous empirical characterisation with a mechanism, not a new technique.

## 2. Key themes in the literature (prevalence = papers among the 21 reviewed)

### Theme 1: Group-wise coverage can be repaired by conditioning on groups or classes (8 of 21)
Romano 2020, Lu 2022, Ding 2023, Vadlamani 2025, Zhou & Sesia 2024, Gibbs 2025, Bairaktari 2025, Gao 2026b. Mondrian, class-conditional and adaptive-group variants guarantee coverage within the chosen cells under exchangeability.
Implication: our Mondrian result (death and survivor coverage 0.898–0.903 in every age stratum, both databases) is expected by construction and must be described that way.

### Theme 2: Pooled calibration hides, and theory says it must distort, group-wise coverage (3 of 21)
Gao 2026a (conservation law and lower bound for pooled calibration, tension between equalized coverage and equalized set size), Zhong 2026 (rarity and tail-heaviness mechanisms in Alzheimer's forecasting), Gao 2026b (finer-stratum disparities remain inside Mondrian groups).
Implication: the general statement "pooled threshold plus heterogeneous scores gives unequal coverage" is not ours. Our addition is the clinical instance, the direction (two-sided, age-ordered), and the ablation showing that removing the age predictor shrinks the gap.

### Theme 3: Marginal sets fail for the rare class; class-conditional repairs it (4 of 21)
Yu 2026 (marginal sets covered 1.4% and 0.0% of deaths, class-conditional 91.6% and 84.9% externally), Opoku 2026 (AKI: marginal 92.1% overall but 31.3% in AKI-positive; proves class-conditional validity under label shift), Ding 2023, our own 23.5%.
Implication: this finding is replicated, not new. The label-shift result in Opoku 2026 helps interpret our transport result: with class-conditional thresholds, residual under-coverage on a new site comes from within-class score shift (risk over-prediction in eICU), not from the prevalence difference.

### Theme 4: Conformal prediction across MIMIC-IV and eICU exists (5 of 21)
Yang 2024 (sepsis, AUROC 0.858 internal to 0.800 external), Yu 2026 (reciprocal MIMIC-IV/eICU, hospital-disjoint partitions), You 2026 (missingness-aware Mondrian across eICU hospitals), Patel 2026 (calibration drift MIMIC-IV to eICU), Tan 2026 (subgroup performance when combining MIMIC-IV and eICU).
Implication: "external validation in eICU" alone is not novel. The new element is subgroup (age, race, sex) class-conditional coverage and its replication, with hospital-disjoint splits and a harmonised-feature sensitivity model.

### Theme 5: Fairness and conformal uncertainty in ICU mortality is already under study (2 of 21)
Zhang 2026 (pre-registered, LLM-generated mortality probabilities, MIMIC-IV with MIMIC-III external, conformal sets and subgroup fairness) and Tan 2026. Zhang concerns LLM predictors and is a registry entry; it is the closest topical competitor.
Implication: state clearly that ours uses a standard tabular model with class-by-group calibration and two databases; avoid any "first conformal fairness study in ICU mortality" claim.

### Theme 6: Coverage parity is not the only fairness question (3 of 21)
Cresswell 2025 (equalized coverage can increase disparate impact in human decisions; equal set sizes help), Gao 2026a (coverage and set-size equity conflict), de Matos 2026 (Lancet Digit Health scoping review: fragmented fairness metrics, gaps in uncertainty quantification and intersectionality).
Implication: our set-size results (+0.015 labels for age Mondrian in MIMIC; risk-bin about +0.5) and the age-blind miscalibration result (calibration-in-the-large +0.023 young, −0.030 old) fit here. We should report set size and calibration together with coverage and avoid calling Mondrian "fair" without qualification.

## 3. Per-paper comparison (what they did, how this project differs)

| Paper (verified record) | What it did | Difference from this project |
|---|---|---|
| Romano, Barber, Sabatti, Candès 2020, Harv Data Sci Rev 2(2) | Defines equalized coverage; class/group-conditional conformal | Method origin; we apply and audit it in ICU mortality, no method claim |
| Lu et al. 2022, AAAI 36(11):12008–12016 | Fair conformal predictors, medical imaging | Imaging, not ICU tabular mortality, no cross-database replication |
| Ding et al. 2023, NeurIPS (64555–64576) | Class-conditional CP with many classes | Many-class setting; we have 2 classes, 10% prevalence |
| Vadlamani et al. 2025, ICLR | Generic conformal fairness framework controlling coverage gaps between sensitive groups | General framework, graph and tabular benchmarks; no clinical mechanism analysis |
| Gibbs, Cherian, Candès 2025, JRSSB 87(4):1100–1126 | Conditional guarantees over covariate-shift classes, includes subgroup coverage | Methodological; our Mondrian groups are a special case of its subgroup guarantee |
| Zhou & Sesia 2024, NeurIPS | Equalized coverage for adaptively selected groups | Method; our groups are pre-specified clinical attributes |
| Bairaktari, Wu, Wu 2025 (arXiv 2502.17264) | Kandinsky CP: overlapping groups, unifies Mondrian/class-conditional | Method; our intersectional strata could be framed with it |
| Gao et al. 2026a (arXiv 2605.14260) | Theory: pooled calibration incurs irreducible group-wise distortion; coverage vs set-size tension | Theory, synthetic/real data; we give the clinical mechanism evidence and age-blind ablation. Overlaps our general mechanism statement |
| Gao et al. 2026b (arXiv 2610.24813), Tilted Mondrian | Finer-stratum disparities inside Mondrian groups, propensity standardisation | Methodological; relevant to our small-stratum and intersectional limits |
| Zhong et al. 2026 (arXiv 2608.04254) | Subgroup under-coverage audit in Alzheimer's forecasting (ADNI, OASIS-3), two mechanisms and corrections | Closest audit-and-mechanism design, but regression bands in a different disease; demographic groups were on target there while ours (age) are not, because age carries base risk in ICU mortality |
| You et al. 2026 (arXiv 2609.30781) | Missingness-aware Mondrian across eICU hospitals/MIMIC-IV units; hospital-level decomposition; risk-based calibration gave smaller gaps | Groups by missingness, not demographics; supports adding our risk-bin baseline (done: gap closes but set size +0.5) |
| Yu 2026 (Research Square, doi 10.21203/rs.3.rs-11173088/v1) | Reciprocal MIMIC-IV/eICU transport, hospital-disjoint partitions, marginal vs class-conditional coverage | Six vital-sign concepts and reciprocal transport; no demographic subgroup coverage or mechanism |
| Opoku & Banahene 2026 (Research Square, AKI) | Class-conditional/Mondrian CP for AKI, external site; proves class-conditional validity under label shift | AKI, two sites, no demographic audit; its label-shift result informs how we interpret transport |
| Yang et al. 2024, JMIR 26:e50369 | Conformal predictor for sepsis mortality, MIMIC-IV to eICU | Single-population marginal sets, no subgroup audit |
| Zhang 2026 (OSF pre-registration) | LLM mortality probabilities, conformal sets, subgroup fairness, MIMIC-IV with MIMIC-III | LLM predictors, registry entry without results in the record; closest topical competitor |
| Cresswell et al. 2025, ICLR | Equalized coverage can raise disparate impact in human-AI decisions | Behavioural study; supports reporting set size, no clinical data |
| Tan, Shen, Chen 2026 (arXiv 2604.03478) | Data-addition and post-hoc calibration for subgroup fairness, eICU and MIMIC-IV | Point-prediction fairness, not conformal coverage |
| Patel & Beedala 2026 (Research Square) | Calibration drift MIMIC-IV to eICU, sex and race subgroups | Probability calibration, not conformal sets |
| de Matos, Van Calster, Celi 2026, Lancet Digit Health | Scoping review of fairness metrics in clinical prediction | Background; identifies uncertainty quantification as a gap |

## 4. What is distinctive here (supported by our results)
1. **Two-sided, age-ordered pattern replicated externally.** Young decedents (death coverage 0.84 MIMIC, 0.88 / 0.78 eICU primary / harmonised) and elderly survivors (0.83 MIMIC, 0.84 / 0.82 eICU) are under-covered; 100 seeds, patient and hospital-disjoint splits. Primary endpoint P1 did not replicate in the primary model (0.902) but did in the harmonised model (0.819); P2 replicated in both but is confounded by transport shift.
2. **Transport shift versus group heterogeneity separated.** Pure transport over-covers decedents (0.92) and under-covers survivors (0.835) because eICU risk is over-predicted (CITL +0.042); recalibration on eICU restores overall coverage but not the age pattern.
3. **Mechanism evidence beyond correlation.** Gap tracks base rate and decedent score level, not within-group AUROC (youngest group has the highest AUROC); removing the age predictor shrinks the gap by about 60–75% at a cost of AUROC 0.874 to 0.866 and age-dependent miscalibration.
4. **Fix comparison.** Age x class Mondrian: gap 0.005 at +0.015 labels; risk-bin Mondrian (no demographic attribute): gap about 0.013 at +0.5 labels (singleton share 74% to about 21%).
5. **Small-stratum rule (empirical, one database).** Group-specific thresholds did not beat pooled ones below about 40 calibration deaths; below 10 the death threshold was infinite in 84% of hospital-seeds.
6. **Reporting.** Pre-specified endpoints, a failed endpoint reported as failed, hospital-level excess heterogeneity (SD 0.045 vs 0.039 expected).

## 5. Claims we should not make
- "First" (or "novel framework", "novel mechanism", "novel theorem"); several preprints cover subgroup conformal audits, MIMIC/eICU conformal transport and pooled-threshold theory.
- That Mondrian "guarantees fairness" or "provably repairs" the gap beyond group-wise coverage under exchangeability; report set size, calibration and finer-stratum behaviour.
- That the age gap is caused by age in a causal sense; the ablation and correlations are suggestive (age is entangled with physiology; only four age strata).
- That our coverage numbers beat other papers; datasets, features and splits differ and no head-to-head comparison was run.
- That P1 replicated; it replicated only in the harmonised model.
- Anything about insurance in eICU (not recorded) or intersectional conclusions (small cells, not analysed for the paper).
- That the 40-death rule is general; it is an empirical working rule from one dataset.

## 6. Insights to opportunities

| Insight | Opportunity | Impact | Effort |
|---|---|---|---|
| Pooled-threshold theory exists (Gao 2026a) | Cite it, test its prediction (quantile heterogeneity across age strata) with our score distributions | High | Low |
| Risk-bin calibration is a known alternative (You 2026) | Already added; discuss efficiency cost | Medium | Done |
| Finer-stratum disparities inside Mondrian groups (Gao 2026b) | Report age x sex or age x race Mondrian coverage with unstable cells flagged | Medium | Medium |
| Coverage parity may raise disparate impact (Cresswell 2025) | Report set size and discuss; no human study | Medium | Low |
| Label-shift validity of class-conditional CP (Opoku 2026) | Use it to interpret the transport result; check that eICU shortfall is within-class shift | Medium | Low |
| Closest competitors are preprints (Yu 2026, Zhang 2026) | Recheck status at submission; cite as preprints | High | Low |

## 7. Recommendations
1. **Reframe title, abstract and aims** around "where the subgroup coverage gap comes from in ICU mortality and whether it replicates", not around finding and fixing a gap. (Based on Themes 1–2.)
2. **Cite and position against** Romano 2020, Gao 2026a, Zhong 2026, Yu 2026, You 2026, Opoku 2026, Zhang 2026, Gibbs 2025, Gao 2026b, Cresswell 2025 and the Lancet Digital Health scoping review.
3. **Add one analysis**: test the pooled-threshold theory prediction directly (quantile gap of class-specific scores across age strata versus observed coverage gap), so the mechanism claim is tied to the published theory.
4. **Add finer-stratum results** (age x sex, age x race) with the stability rule applied, in answer to Gao 2026b.
5. **Keep every claim at the level in section 5.**

## 8. Questions for further research
- Does the age pattern appear for other outcomes or for models with different feature sets (the age-blind ablation suggests the age feature is the lever)?
- Does the effect hold in data after 2015 (eICU is 2014–2015; MIMIC-IV to 2022)?
- Would proportional multicalibration or group-wise recalibration remove the pattern at lower set-size cost than risk-bin Mondrian?
- What does the 40-death rule look like on other databases?
- Does the Zhang 2026 pre-registered study report results by the time of submission?

## 9. Methodology notes and limitations of this synthesis
Abstract-level reading only; no full texts; keyword search over a single index; preprints and registry entries are unreviewed; arXiv and Research Square identifiers as recorded by OpenAlex (verify that each resolves before citing; a few 2026 arXiv numbers could not be checked); the You et al. author list is partly garbled in OpenAlex ("You L, et al." used). Counts of "n of 21" are counts of reviewed papers, not a systematic review (PRISMA not followed).

## 10. Verified reference list (metadata checked against OpenAlex; add page ranges where blank)
1. Romano Y, Barber RF, Sabatti C, Candès E. With malice toward none: assessing uncertainty via equalized coverage. Harv Data Sci Rev. 2020;2(2). doi:10.1162/99608f92.03f00592
2. Lu C, Lemay A, Chang K, Höbel K, Kalpathy-Cramer J. Fair conformal predictors for applications in medical imaging. Proc AAAI Conf Artif Intell. 2022;36(11):12008-12016. doi:10.1609/aaai.v36i11.21459
3. Ding T, Angelopoulos AN, Bates S, Jordan MI, Tibshirani RJ. Class-conditional conformal prediction with many classes. Adv Neural Inf Process Syst. 2023:64555-64576. doi:10.52202/075280-2817
4. Vadlamani A, Srinivasan A, Maneriker P, Payani A, Parthasarathy S. A generic framework for conformal fairness. ICLR. 2025. arXiv:2505.16115. doi:10.48550/arxiv.2505.16115
5. Gibbs I, Cherian JJ, Candès EJ. Conformal prediction with conditional guarantees. J R Stat Soc Series B. 2025;87(4):1100-1126. doi:10.1093/jrsssb/qkaf008
6. Zhou Y, Sesia M. Conformal classification with equalized coverage for adaptively selected groups. Adv Neural Inf Process Syst. 2024:108760-108823. doi:10.52202/079017-3454
7. Bairaktari K, Wu J, Wu ZS. Kandinsky conformal prediction: beyond class- and covariate-conditional coverage. arXiv:2502.17264. 2025. doi:10.48550/arxiv.2502.17264
8. Gao Z, Liu P, Yang AY, Belbahri M, Cresswell JC, Asgharian M. On the burden of achieving fairness in conformal prediction. arXiv:2605.14260. 2026. (preprint)
9. Gao Z, Liu P, Yang AY, Belbahri M, Cresswell JC, Asgharian M. Tilted Mondrian: triage and mitigation of fine-grained disparities in conformal prediction. arXiv:2610.24813. 2026. (preprint)
10. Cresswell JC, Kumar B, Sui Y, Belbahri M. Conformal prediction sets can cause disparate impact. ICLR. 2025. arXiv:2410.01888.
11. Zhong L, Wang X, Huang S, Shi Y. When is a conformal guarantee fair? Auditing silent subgroup under-coverage in Alzheimer's disease longitudinal prediction. arXiv:2608.04254. 2026. (preprint)
12. You L, et al. Missingness-aware conformal prediction under cross-hospital distribution shift. arXiv:2609.30781. 2026. (preprint; author list to check)
13. Yu T. Retrospective evaluation of transportability and uncertainty in ICU mortality prediction across MIMIC-IV and eICU. Research Square. 2026. doi:10.21203/rs.3.rs-11173088/v1 (preprint)
14. Opoku J, Banahene D. Conformalized prediction of acute kidney injury in the ICU: distribution-free coverage guarantees with class-conditional validity and external validation. Research Square. 2026. doi:10.21203/rs.3.rs-10463539/v1 (preprint)
15. Yang M, Chen H, Hu W, Mischi M, Shan C, Li J, et al. Development and validation of an interpretable conformal predictor to predict sepsis mortality risk: retrospective cohort study. J Med Internet Res. 2024;26:e50369. doi:10.2196/50369
16. Zhang T. Calibration, conformal uncertainty, and fairness of large language models for in-hospital mortality prediction after ICU admission: evaluation on MIMIC-IV with external validation on MIMIC-III. OSF pre-registration. 2026. doi:10.17605/osf.io/y3jqa
17. Tan E, Shen JH, Chen IY. Investigating data interventions for subgroup fairness: an ICU case study. arXiv:2604.03478. 2026. (preprint)
18. Patel K, Beedala P. Calibration drift under cross-institutional deployment: an external validation framework for ICU mortality prediction across MIMIC-IV and eICU. Research Square. 2026. doi:10.21203/rs.3.rs-9602675/v1 (preprint)
19. de Matos JCRG, Van Calster B, Celi LA. Critical appraisal of fairness metrics for artificial intelligence-based clinical prediction models: a scoping review. Lancet Digit Health. 2026. doi:10.1016/j.landig.2026.101001 (volume/pages to add)
20. Johnson AEW, Bulgarelli L, Shen L, et al. MIMIC-IV, a freely accessible electronic health record dataset. Sci Data. 2023;10:1. doi:10.1038/s41597-022-01899-x
21. Pollard TJ, Johnson AEW, Raffa JD, Celi LA, Mark RG, Badawi O. The eICU Collaborative Research Database, a freely available multi-center database for critical care research. Sci Data. 2018;5:180178. doi:10.1038/sdata.2018.178
Existing manuscript references still to fix: former [10] (replace), [12] (author list now available: Yang M, Chen H, Hu W, Mischi M, Shan C, Li J, et al.; the OpenAlex record lists six authors followed by more).
