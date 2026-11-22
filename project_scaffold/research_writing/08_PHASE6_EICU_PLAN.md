# Phase 6 — eICU-CRD external validation: plan (v1, 2026-11-20)

Status: PLAN + SCRIPTS READY, NOT RUN on real data (eICU not yet downloaded). Scripts were smoke-tested only on fabricated eICU-schema tables; no real eICU number exists yet.

## 1. Why this phase matters
Single-centre MIMIC-IV with random splits is the main reason a Q1 reviewer will say "generalisability unknown". Phase 6 answers two questions that the current paper cannot:
1. Does the subgroup coverage gap (age: ages 18–49 death coverage low, ages 75+ survivor coverage low) appear in a different set of hospitals, or is it a MIMIC/BIDMC artefact?
2. When a model + conformal calibration trained in one database is moved to another, does coverage survive, and does target-domain (eICU) recalibration or group-by-class (Mondrian) calibration fix it?

## 2. Get the data (you must do this; I cannot)
eICU-CRD v2.0 is credentialed: https://physionet.org/content/eicu-crd/2.0/
You need (a) PhysioNet credentialed status (you already have it for MIMIC-IV), (b) the CITI "Data or Specimens Only Research" training on file, (c) to sign the eICU-CRD data use agreement (separate from MIMIC's).
Download only the six tables the pipeline reads (same wget approach as MIMIC; check exact file names on the Files tab first — the script looks them up case-insensitively):

    patient, vitalPeriodic, vitalAperiodic, lab, nurseCharting, apacheApsVar   (all *.csv.gz)

Put them in `data/raw/eicu/` (or set the environment variable `EICU_PATH`). Several GB in total; nurseCharting and vitalPeriodic are the large ones and are read in chunks.

## 3. Run order
    python tests/synthetic_eicu_smoke.py <tmp_dir> 4000          # optional: test on FAKE data first
    EICU_PATH=<tmp_dir> python src/data_processing/06_build_eicu_features.py --sample 2000
    python src/data_processing/06_build_eicu_features.py         # real run -> data/processed/eicu_features.parquet
    python src/evaluation/06_external_validation.py --seeds 20   # exploration
    python src/evaluation/06_external_validation.py --seeds 100  # final, patient split
    python src/evaluation/06_external_validation.py --seeds 100 --split hospital   # hospital-disjoint

Before looking at any coverage result, check the Phase 6a printout: exclusion flow, mortality (record the number; do not assume), hospitals, race/age counts, features with >50 % missing.

## 4. Design
Per seed: train XGBoost on the MIMIC-IV train split (identical to Phase 3), calibrate on the MIMIC-IV calibration split, then evaluate on eICU. eICU is split 50/50 (patient-level, or hospital-disjoint) into an eICU-calibration half and an eICU-test half so that all external configurations are compared on the same eICU test patients.

| Config | Thresholds from | Evaluated on | Question |
|---|---|---|---|
| internal_mimic_cc / internal_mimic_mondrian_cc | MIMIC cal | MIMIC test | reference (= Phase 4 / 5) |
| ext_mimiccal_cc | MIMIC cal, global class-conditional | eICU test | pure transport: does the guarantee survive? |
| ext_mimiccal_mondrian_cc | MIMIC cal, group x class | eICU test | do MIMIC group thresholds transfer? |
| ext_eicucal_cc | eICU cal half | eICU test | target-domain recalibration |
| ext_eicucal_mondrian_cc | eICU cal half, group x class | eICU test | target-domain group-by-class |
| ext_mimiccal_cc_alleicu | MIMIC cal | all eICU | per-hospital table (no eICU split needed) |

Audited externally: age group, race/ethnicity, sex, plus per hospital. **Insurance cannot be audited in eICU (no such field)** — insurance findings remain MIMIC-only and the paper must say so.

## 5. Pre-specified endpoints (write these in the paper before running the 100-seed job)
Primary (2 only, to keep multiplicity under control):
- P1: eICU death coverage, ages 18–49, config ext_mimiccal_cc (MIMIC finding: ~84 %).
- P2: eICU survivor coverage, ages 75+, config ext_mimiccal_cc (MIMIC finding: ~83 %).
A primary finding is "replicated" if the eICU estimate is below 90 % with the upper Wilson bound (table column `*_wilson_high`) also below 90 %. Everything else (race, sex, Mondrian configs, hospital analysis) is secondary/exploratory and must be labelled so.
Groups with fewer than 50 deaths per test half are flagged `UNSTABLE_lt50_deaths` in the output; do not interpret them.

## 6. How to read the possible outcomes
- Gap replicates in eICU and Mondrian/eICU-recalibration closes it -> strongest story: the problem is general, the fix works across databases.
- Gap replicates but only eICU recalibration (not MIMIC thresholds) fixes it -> calibration must be done on local data; say so.
- Overall transport coverage itself fails (death or survivor coverage far from 90 %) -> shift dominates group effects; the paper becomes "coverage under cross-database shift", which is itself publishable but a different framing. Check `phase6_model_performance.csv` (AUROC, calibration slope, CITL on eICU) to explain why.
- Gap does not replicate -> report honestly as MIMIC-specific; do not drop the result.
Hospital analysis: `phase6_hospital_coverage.csv` gives per-hospital death/survivor coverage for hospitals with >=100 patients and >=20 deaths, with the binomial SD expected by chance (`expected_sd_binomial`) and a z-score; compare the observed SD of hospital death coverage in `phase6_summary.json` with the expected one to separate real site heterogeneity from sampling noise.

## 7. Known differences from MIMIC (put in Methods/Limitations)
- eICU is 2014–2015 data from 208 hospitals; MIMIC-IV is one hospital, 2008–2022.
- "First ICU stay per patient" uses discharge year only, so the order across hospitalisations is approximate.
- GCS: nurse-charted "GCS Total" (min over 24 h), APACHE eyes+motor+verbal as fallback; `intubated` is the APACHE first-day flag (MIMIC used charted verbal text). Missing-pattern differences can shift model scores; the model is NOT retrained on eICU in the main analysis (a retrain-on-eICU sensitivity analysis is a sensible add-on).
- Vital-sign sampling frequency differs (5-min periodic data) although min/max/mean are used in both.
- Race/ethnicity categories are recorded differently; "Other/Unknown" is heterogeneous in both.
- The 24 h LOS filter excludes early deaths/discharges (selection effect) in both databases.

## 8. Not done / next after Phase 6
- Reverse direction (train eICU -> test MIMIC) and a model retrained on eICU.
- Mechanism analysis (group-wise AUROC / score distributions vs coverage gap) and small-stratum stability rule — these provide the novelty angle; see review fix-list item C6.
- Update the manuscript only after the 100-seed run; until then no eICU number may be written into the paper.

## 9. Test status
Scripts executed end-to-end on fabricated eICU-schema data (cohort flow incl. duplicate-stay removal, vitals/labs/GCS extraction, 1–2 seeds of both split modes, hospital table). The internal-MIMIC reference configs reproduced Phase 3 values (death/survivor coverage ~0.90). External numbers from fake data are meaningless by design.
