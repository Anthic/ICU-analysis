# Phase 11 — end-of-life coding sensitivity and continuous-age coverage (MIMIC-IV, 100 seeds), 2026-11-24  [GENERATED — PENDING REVIEW]

Script `src/evaluation/11_endoflife_sensitivity.py`; tables `outputs/tables/phase11_endoflife_{rows,summary}_main_100.csv`; `outputs/results/phase11_summary_main_100.json`; flag file `data/processed/mimic_endoflife_flags.parquet` (built from MIMIC-IV hosp `admissions` discharge_location and `diagnoses_icd`; raw data untouched).
Responds to review issue: outcome/case-mix confounding (hospice and comfort-care coded as survival) was untested; continuous-age view.

## Data facts (analysed cohort, 51,838 stays)
Discharged to hospice: 1,209 (2.3%), none of them in-hospital deaths (all coded as survivors); share rises with age: 0.8% (18–49), 1.8% (50–64), 2.3% (65–74), 3.9% (75+). Palliative-care diagnosis codes (ICD-10 Z51.5 / ICD-9 V66.7): 4,368 stays; they occur in 55% of deaths (3,053 of 5,522) and are outcome-informative (assigned during or after the stay). eICU-CRD has no hospice field, so this analysis is MIMIC-only. Code status (DNR/comfort measures in chartevents) was NOT extracted.

## Variants (own 50/25/25 split per variant and seed, same predictors, pooled class-conditional thresholds, alpha = 0.10)
V0 reference (y = death); V1 y = death or hospice discharge; V2 hospice discharges removed; V3 hospice and palliative-code stays removed (a bound, removes ~55% of deaths; not recommended as a primary analysis).

## Results (mean over 100 seeds; death coverage / survivor coverage)
| Age | V0 original | V1 death-or-hospice | V2 excl. hospice | V3 excl. hospice+palliative |
|---|---|---|---|---|
| 18–49 | 0.840 / 0.949 | 0.822 / 0.956 | 0.844 / 0.949 | 0.860 / 0.942 |
| 50–64 | 0.871 / 0.925 | 0.865 / 0.929 | 0.872 / 0.926 | 0.870 / 0.931 |
| 65–74 | 0.907 / 0.911 | 0.896 / 0.910 | 0.907 / 0.908 | 0.907 / 0.911 |
| 75+ | 0.931 / 0.830 | 0.939 / 0.819 | 0.931 / 0.825 | 0.941 / 0.824 |
Prevalence in the test split (V0 / V1 / V2 / V3): 10.6 / 13.0 / 10.9 / 5.2%. Seed SD of young-stratum death coverage: 0.030 (V0), 0.034 (V1), 0.025 (V2), 0.041 (V3; about 77 deaths per test split).
Differences from V0 (young deaths; 75+ survivors; mean difference between seed-level values, not a paired comparison because test sets differ across variants): V1 −1.9 pp and −1.0 pp; V2 +0.4 pp and −0.4 pp; V3 +2.0 pp and −0.6 pp. All within about one seed SD.

## Continuous age (10-year bands, V0; death coverage / survivor coverage; test deaths per band per split in brackets)
18–29 0.840 / 0.968 (28); 30–39 0.865 / 0.947 (42); 40–49 0.828 / 0.940 (81); 50–59 0.880 / 0.928 (200); 60–69 0.885 / 0.918 (306); 70–79 0.907 / 0.888 (320); 80–91+ 0.941 / 0.809 (403). Death coverage rises and survivor coverage falls with age, roughly monotonically, with a dip at 40–49 (death) that is within noise (SD about 0.03–0.05 in bands below 50). The four-stratum age pattern is therefore not an artefact of the cut points. Same pattern in V1–V3 (see summary CSV).

## Reading
1. The age pattern (young decedents and elderly survivors under-covered) persists when hospice discharges are treated as events (V1), removed (V2), or removed together with palliative-coded stays (V3); in V3 the young-decedent deficit is smaller (0.860 vs 0.840) but with a wide seed SD (0.041), so it is not distinguishable. The elderly survivor deficit (0.82–0.83) is stable in every variant.
2. Treating hospice as an event slightly widens the age gap (young deaths 0.822), consistent with hospice being more common in older patients (older prevalence rises 15.4% to 19.3%), so coding choices change the size but not the direction of the pattern.
3. This does not exclude goals-of-care confounding through unmeasured routes (DNR/comfort-measure orders, early withdrawal), and eICU could not be examined.

## Caveats
Cross-variant comparisons are not paired; hospice and palliative codes are only proxies for end-of-life care; palliative codes depend on coding practice; bands below age 50 have 28–81 test deaths per split; single model (XGBoost), single alpha.
