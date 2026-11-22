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
