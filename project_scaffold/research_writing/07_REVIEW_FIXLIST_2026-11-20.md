# Review fix-list (2026-11-20)

Originals of every edited file are in `_backup_before_review_2026-11-20/`.

## A. Analysis check (done)
- Independent re-run (10 seeds, project's own split/conformal code) reproduced the headline results:
  age 18-49 CC death coverage 84.5% (reported 84.06%); age 75+ CC survivor coverage 83.4% (reported 82.94%); Mondrian class-conditional about 90% in large groups; n = 51,838, 5,522 deaths.
- Temporal holdout (train/cal 2008-2019, test 2020-2022, 5 seeds): overall CC coverage held (death 0.909 / survivor 0.897); the age pattern persisted (18-49 death 0.886, 75+ survivor 0.833). Mondrian near nominal in large groups; over-covered small groups (Asian death ~0.99, n ~22 deaths). Not yet in the paper; could be a supplementary robustness result.
- Verdict: analysis is internally consistent and reproducible. It is not wrong. The problems are claims and novelty, not computation.

## B. Done in the files (wording / consistency)
1. Removed "first systematic audit", "catastrophic", "exact 90%", "provable", "mandatory" (master, results_draft, table6, 01, 03, 05).
2. Deaths = 5,522 everywhere reachable (reviewer_responses had 5,521).
3. Ref [12] placeholder replaced with the CPMORS DOI record (author list still to be completed). Refs [15]/[16] replaced with Romano 2020 and Lu 2022, Seyyed-Kalantari/Obermeyer moved to [18]/[19] (need an in-text cite where clinical-AI bias is introduced).
4. Figure file names in the master now point to existing files; captions are marked TODO because they describe plots that do not exist; CITL bubble plot marked NOT YET GENERATED.
5. Age finding and race survivor differences labelled exploratory.

## C. Still open (needs analysis or your decision)
1. eICU external validation (Phase 6) not done; title/aims mention eICU.
2. Not edited on purpose (project rule: memory files need your confirmation): `.agent/project_memory.md`, `paper/project_memory.md` (line ~316 still says "Restoring exact 90%").
3. 10.65% vs 10.66% appears in `corrected_project_status...md`; use 10.65% (5,522/51,838 = 0.10652).
4. Singleton share ">82%" in abstract: re-verify against Table 8.
5. Ref [10] (Zimmerman, length of stay) is cited for 8-15% mortality; replace with a mortality source.
6. Add: group-wise AUROC / score-distribution analysis (why does the age gap exist), small-stratum stability, comparison with equalized coverage and Conformal Fairness (ICLR 2025), intersectional results (coded, dropped), SOFA/APACHE baseline, comfort-care deaths, state the 24 h LOS selection.
7. Novelty: position against 2026 preprints (OSF LLM-ICU conformal fairness; Research Square MIMIC-IV/eICU conformal; Research Square ICU AKI Mondrian; arXiv missingness-aware Mondrian). Do not claim "first".

## D. Update 2026-11-22
Done: eICU external validation (Phase 6, 100 seeds, patient and hospital-disjoint splits) and mechanism/stability analysis (`src/evaluation/07_mechanism_analysis.py`); results in `paper/phase6_7_FINAL100_NOTE.md`, and Methods 2.6/2.7, Results and limitations added to `00_MANUSCRIPT_MASTER.md`. Memory files corrected ("nominal 90% ... by construction"). 10.65% used consistently. Singleton claim ">82%" was wrong: singleton share is 62%–87% by stratum (age 75+ 62%, age 18–49 82%); fixed in master, results_draft and blueprint.
Still open: replace former ref [10] with a real mortality-prevalence source (marked CITATION NEEDED in 05 blueprint; check master intro too); in-text cites for [18]/[19]; rewrite figure captions after regenerating figures; intersectional results exist in `phase5_*` CSVs (small cells, singleton share as low as 11%) but are not written up; SOFA/APACHE baseline; comfort-care handling; comparison with Conformal Fairness (ICLR 2025) and 2026 preprints; complete ref [12] author list. Note: the name "phase7" is already used by `phase7_tradeoff_efficiency_analysis.csv` (Table 8); the mechanism outputs are `phase7_stratum_stats*`, `phase7_mechanism_summary*`, `phase7_stability*`.

Update 2026-11-22 (later): Phase 8 (risk-bin Mondrian baseline and age-blind ablation, 100 seeds) added as Methods 2.8 and Results bullets in the master; see `paper/phase8_alternatives_NOTE.md`.


## Section E — Phase 9/10 integration (2026-11-24)
- Manuscript 00_MANUSCRIPT_MASTER.md: added Methods 2.9 (stratum-minus-overall contrasts, hospital-cluster CI; post hoc), 2.10 (calibration-implied coverage + synthetic demo), two Results bullets, abstract sentence, limitations text; the P1/P2 "specified before" wording softened to "pre-planned, not registered"; Figure 3 caption ">82%" corrected to 62-87%.
- Still open: reframe title/abstract/'equitable' wording; cite and verify Hardt 2016, Chouldechova 2017, Kleinberg 2017; replace ref [10]; correct refs [8], [14], [16]; complete ref [12]; Figure 1-4 captions vs actual files; hospice/comfort-care sensitivity; P(death|set); temporal split, second model, alpha sweep; replace the 40-death rule.
- Phase 10 caveat: death-side calibration-implied coverage is only partly predicted (MIMIC RMSE about at noise floor); write 'explains survivor-side gap and direction/ordering of the death-side gap'.
- 2026-11-24: Analysis 3 done (Phase 11, hospice/palliative sensitivity + 10-year age bands, MIMIC-only): paper/phase11_endoflife_NOTE.md; manuscript 2.11 + Results bullet added. Title/abstract/aims reframed to neutral wording. Still open: code-status extraction, P(death|set), temporal split, second model, alpha sweep.
- 2026-11-24: Analysis 4 done (Phase 12): paper/phase12_utility_equity_NOTE.md; manuscript 2.12 + Results bullet + limitation. Mondrian-by-age = equalised-odds thresholds (99%+ identical sets). Still open: temporal split, second model, alpha sweep, placebo ablation, references.
- 2026-11-24: Analysis 5 done (Phase 13): paper/phase13_robustness_NOTE.md (temporal split, logistic model, alpha sweep, placebo); manuscript 2.13 + Results bullet + limitation. Remaining: reference verification/fixes, figures/captions, TRIPOD+AI/STROBE, replace 40-death rule.
- 2026-11-24: References fixed in 00_MANUSCRIPT_MASTER.md against OpenAlex: [7] title corrected (Classification with valid and adaptive coverage), [8] replaced by Lei et al. 2018 (split conformal; Tibshirani 2019 moved to [20] for covariate shift), [10] replaced by eICU-CRD (Pollard 2018; the unverifiable prevalence claim removed), [11] title corrected, [12] full author list, [13] Mach Learn 2013 version, [14] replaced (Lei & Wasserman is not Mondrian) by Toccaceli & Gammerman 2019, [16] authors/pages fixed and the 'clinicians fear' attribution removed, [15] unsupported in-text attribution removed, [18]/[19] cited in the Introduction, new [21]-[23] Hardt 2016, Chouldechova 2017, Kleinberg 2017. Not re-checked: refs 1, 3, 5, 17. 04_CURATED_REFERENCES_LIBRARY.md not audited. Still open: figures/captions vs files, TRIPOD+AI/STROBE checklist, replace the 40-death rule, hospice code-status extraction, P(death|set) net benefit.
- 2026-11-24: Figure captions 1-3 rewritten to match files, figure titles made neutral (scripts patched, backups in _backup_before_fix_2026-11-22), new Figures 4-5 added; 40-death rule replaced by break-even rule (paper/small_stratum_rule_NOTE.md); reporting checklist research_writing/10_REPORTING_CHECKLIST_TRIPOD_AI_STROBE.md; code-status scripts written but NOT run (extract script must be run on the PC, see 2.14). Open: run code-status extraction + analysis; flow diagram, funding/code/data statements; Figure 2 panel A/B values hard-coded in the script (verify against tables); refs 1,3,5,17.
- 2026-11-24: literature-review pass: research_writing/11_LITERATURE_GUIDE_AND_NOVELTY_REVIEW_2026-11-24.md (weighted source table, search log, novelty verdict, risk register). New to cite/read: Tasar 2025, Liu 2026, Zhong & Tai 2026, Kwon 2026. Read full texts of Gao 2026a, Zhong 2026, Tasar 2025 before claiming the calibration-implied coverage test as new.
