# Project Memory: ICU Conformal Fairness Study

> Purpose: single source of truth for the agent and for writing the paper.
> Save as `.agent/project_memory.md` (copy to `paper/` too if wanted).
> Read this together with `.agent/instructions.md`, `workflow.md`, `rules.md`.
> Last updated: after Phase 2 completed (Oct 2026).
> Rule for the agent: when a result or decision changes, UPDATE this file
> instead of silently overwriting. Mark anything not yet checked as UNVERIFIED.

---

## 1. Research question and aims

**Working title:** Group-Conditional Conformal Prediction for Equitable
Uncertainty Quantification in ICU Mortality Risk Prediction (MIMIC-IV, with
eICU-CRD external validation planned).

**Question:** Does standard split conformal prediction give the same coverage
in every demographic subgroup (race, sex, age group, insurance)? If not, does
group-conditional (Mondrian) conformal prediction repair it, and what does the
repair cost in prediction-set size?

**Aims**
1. Audit: subgroup coverage of standard conformal prediction (MIMIC-IV).
2. Repair: Mondrian / group-conditional conformal prediction.
3. Trade-off: set-size cost of the repair, per subgroup.
4. External validation on eICU-CRD; temporal-shift analysis within MIMIC-IV.
5. Open, reproducible pipeline.

**Terminology (important):** the outcome is binary, so conformal output is a
**prediction set** over {0,1} ({survive}, {die}, {both}, or empty), NOT a
numeric interval. Coverage = the true label lies in the set. Earlier proposal
drafts said "interval"; use "prediction set" in the paper.
Never call a prediction set containing only `{0}` certain survival; it is a
model prediction set and does not establish certainty.

**Key clinical point:** mortality is about 10%, so marginal coverage near 90%
is easy to reach while coverage among patients who died can be much lower.
Always report coverage for y=1 and y=0 separately (class-conditional).

## 2. Gap and justification (cite only after verifying, see section 9)

- A JMIR 2024 paper built a conformal predictor for sepsis mortality on
  MIMIC-IV and validated it on eICU. Its authors state in their limitations
  that generalizability and bias were not addressed in depth and need future
  work. This is the stated gap we extend.
- Non-conformal fairness audits of MIMIC mortality and length-of-stay models
  report subgroup calibration and recall disparities.
- A 2026 Scientific Reports paper applied a sex-stratified Mondrian conformal
  method to sepsis triage (single attribute). Multi-attribute, multi-site ICU
  mortality has not been examined (as far as our search found; re-check before
  submission).
- A 2026 arXiv paper warns that equalizing coverage can inflate set-size
  disparities, so the trade-off must be measured and reported.

## 3. Data

- **MIMIC-IV v3.1** (Beth Israel Deaconess Medical Center), PhysioNet,
  credentialed access (CITI "Data or Specimens Only Research" completed).
- Local path: `D:\dataset\physionet.org\files\mimiciv\3.1`
  (override with env var `MIMIC_PATH`). Tables used: `icu/icustays`,
  `icu/chartevents`, `icu/d_items`, `hosp/patients`, `hosp/admissions`,
  `hosp/labevents`, `hosp/d_labitems`.
- **eICU-CRD:** NOT downloaded yet. Needed for Phase 6.
- Never modify `data/raw/`. Never write identifiers (subject_id, hadm_id,
  stay_id, dates) into `outputs/` or `paper/`.

## 4. Phase 1: cohort (DONE) - `src/data_processing/01_build_cohort.py`

**Selection order (order matters):** first ICU stay per patient -> ICU LOS
>= 24 h -> age >= 18 -> merge admission data.

| Step | N | Excluded |
|---|---|---|
| All ICU stays | 94,458 | - |
| First ICU stay per patient | 65,366 | 29,092 |
| ICU LOS >= 24 h | 51,838 | 13,528 |
| Adults (age >= 18) | 51,838 | 0 |
| Final cohort | 51,838 | 0 |

Outcome: in-hospital mortality (`hospital_expire_flag`), **10.65%**.
Merge integrity checks passed (no dropped rows, unique subject_id/stay_id,
no NaN in protected attributes or outcome).

**Subgroup definitions**
- Race (from the admission record): Hispanic = HISPANIC/LATINO/SOUTH
  AMERICAN/BRAZILIAN; Black = BLACK/AFRICAN/CAPE VERDEAN/CARIBBEAN; Asian;
  White = WHITE/PORTUGUESE; everything else = Other/Unknown. Hispanic is
  checked first so it overrides the other labels.
- Age: 18-49, 50-64, 65-74, 75+ (bins start at 17 so age 18 is included).
- Insurance: Medicare, Medicaid, Private, Other/Unknown.
- Sex: Male/Female.

**Subgroup sizes (N, %)**
- Sex: Male 29,535 (57.0); Female 22,303 (43.0)
- Age: 50-64 15,156 (29.2); 75+ 14,980 (28.9); 65-74 12,162 (23.5);
  18-49 9,540 (18.4)
- Race: White 33,997 (65.6); Other/Unknown 9,760 (18.8); Black 4,568 (8.8);
  Hispanic 1,970 (3.8); Asian 1,543 (3.0)
- Insurance: Medicare 27,698 (53.4); Private 14,606 (28.2);
  Medicaid 7,257 (14.0); Other/Unknown 2,277 (4.4)
- Anchor year group: 2008-2010 13,627; 2011-2013 10,575; 2014-2016 10,594;
  2017-2019 9,874; 2020-2022 7,168

**Judgement calls to disclose in Methods:** Portuguese -> White;
Brazilian and South American -> Hispanic (contested); Other/Unknown race is a
heterogeneous bucket, report it but do not interpret it as one group.
Insurance and age are strongly correlated (Medicare is mostly 65+).

## 5. Phase 2: features (DONE) - `src/data_processing/02_build_features.py`

**Output:** `data/processed/features.parquet`, 51,838 rows x 72 columns
(13 cohort + 21 vital + gcs_min + intubated + 27 lab + 9 `*_measured`).

**Windows**
- Vitals (chartevents, by stay_id): [intime, intime + 24 h].
- Labs (labevents, matched by subject_id because labevents has no stay_id):
  [intime - 6 h, intime + 24 h]. The 6 h lead captures ED/ward labs drawn just
  before ICU admission. Labs use `charttime` (collection time), not result time.
- Prediction time is therefore the end of ICU hour 24; nothing after it is used.

**Features (min / max / mean per stay):** heart rate, systolic/diastolic/mean
BP, respiratory rate, SpO2, temperature (F converted to C before range
filtering), lactate, creatinine, WBC, platelets, BUN, glucose, potassium,
sodium, bicarbonate. Plus `gcs_min` and `intubated`.
- Arterial and non-invasive BP are pooled under one feature; blood-gas and
  chemistry panel values are pooled for glucose, potassium, sodium,
  bicarbonate. State this in Methods.
- Item IDs verified against d_items / d_labitems (labels printed and asserted).

**GCS:** eye + verbal + motor summed only where all three are charted at the
same time; stay-level minimum. 99.80% of stays have a value.
**Intubation:** 125,538 verbal-response rows mentioning ETT/Trach all have
score 1.0. 23,127 stays (44.61%) flagged `intubated`. The flag only covers
stays with such a verbal chart entry. Intubated patients get an artificially
low GCS (verbal cannot be scored), and sedation also lowers GCS. Keep
`intubated` beside `gcs_min`; run a sensitivity analysis without GCS or with
eye+motor only.

**Out-of-range handling:** values outside plausible ranges become NaN (rows
are not dropped). Ranges are author-defined (not from a published standard):
HR 20-300; SBP 30-300; DBP 10-200; MAP 20-250; RR 4-80; SpO2 50-100;
temp 30-45 C; lactate 0.1-30; creatinine 0.1-30; WBC 0.1-200; platelets
1-2000; BUN 1-250; glucose 10-1500; potassium 1-12; sodium 90-200;
bicarbonate 2-60.

**Outlier results (share of measurements set to NaN):** resp_rate 0.492%;
map 0.222%; temperature 0.108%; wbc 0.061%; creatinine 0.022%; spo2 0.022%;
dbp 0.016%; glucose 0.014%; heart_rate 0.013%; sbp 0.010%; potassium 0.009%;
sodium 0.006%; lactate 0.005%; platelets 0.003%; bun 0.003%;
bicarbonate 0.002%. (Counts are measurements, not patients.)

**No imputation in Phase 2.** XGBoost handles NaN natively. Any imputation must
be fit on the training split only. `*_measured` flags exist for all labs;
config `INCLUDE_MEASURED_FLAGS`. The flags variant is supplementary only.

**Missingness (share of stays missing):** lactate 27.88%; temperature 3.16%;
all other features below 1.5%; gcs_min 0.20%.
Lactate missing by race: White 28.54; Black 30.21; Hispanic 29.70;
Asian 29.55; Other/Unknown 23.89. Only Other/Unknown differs clearly from
White; Black is borderline (+1.7 pp, z about 2.3) and unadjusted for severity
or admission type. By insurance: Medicaid 26.2; Medicare 27.6;
Other 28.2; Private 29.2. Descriptive only; do not claim inequity from this.
Reading: data completeness is similar across groups, so any coverage gap is
unlikely to be explained mainly by differential missingness.

## 6. Decisions log (with reasons)

| Decision | Reason |
|---|---|
| First ICU stay per patient | Avoids the same patient in train and test |
| LOS >= 24 h applied after first-stay | Standard order; prediction at hour 24 |
| Race, insurance NOT model predictors | Used only to audit subgroups |
| Age and sex ARE predictors | Clinically relevant |
| No imputation before splitting | Prevents leakage into calibration/test |
| Out-of-range -> NaN, not row drop | Keeps the patient, loses only the bad value |
| Manual conformal implementation | Full control, easy to explain in Methods |
| alpha = 0.10 (90% coverage) | Conventional; consider 0.05 as sensitivity |
| Primary variant = noflags (52 predictors) | Use native XGBoost missing-value handling without measured flags. A flags-vs-noflags comparison cannot test whether missingness drives results. |
| Zero gain for all `*_measured` flags confirmed in seeds 0-9 of the 100-seed run | Flags are supplementary only. |
| Missingness sensitivity = nolactate variant (drop all lactate_*) | Lactate is the only variable with substantial missingness (27.88%). Caveat: this removes both the lactate value and its ordering pattern, so the two cannot be separated. |

## 7. Phase 3 - baseline model + standard conformal

- Predictor **allow-list** (never "all other columns"): anchor_age, sex,
  vital features, gcs_min, intubated, lab features, (+ `*_measured` in the
  supplementary-only flag variant). **Forbidden as predictors:** subject_id, hadm_id, stay_id,
  intime, outtime, **los**, age_group, anchor_year_group, race_group,
  insurance_group, mortality. (`los` and `outtime` are known only after ICU
  exit, i.e. future information. Assert none are in X.)
- Splits: 50% train / 25% calibration / 25% test, stratified by
  mortality x race_group; repeat over 100 seeds (test with 2 first).
  Report mean, SD, 2.5/97.5 percentiles of every metric across seeds.
- Model: XGBoost, fixed hyperparameters, early stopping only on a slice of
  the TRAIN set. Calibration and test sets are never used to fit or tune.
- Conformal: score = 1 - p_hat(y|x); qhat = ceil((n+1)(1-alpha))/n quantile of
  calibration scores; set = {y : 1 - p_hat(y|x) <= qhat}. Also
  class-conditional qhat. Unit test for coverage on synthetic data.
- Report (test only): AUROC, AUPRC, Brier, calibration slope/intercept,
  marginal coverage, coverage for y=1 and y=0, mean set size, share of sets
  {0}, {1}, {0,1}, empty.
- Sanity flags: AUROC above about 0.95 suggests leakage; coverage far from 90%
  suggests a bug.

### Phase 3 status (100-seed results)

- Conformal quantile uses the exact k-th order statistic,
  k = ceil((n+1)(1-alpha)); exact-rank unit tests pass.
- Primary noflags, alpha 0.10: mean AUROC 0.8726, Brier 0.0706, calibration
  slope 1.0033. Marginal coverage 0.9002 overall, 0.2352 for deaths, and
  0.9794 for survivors. Class-conditional coverage is 0.9003 overall, 0.9014
  for deaths, and 0.9002 for survivors; mean set size 1.257, with 25.70% of
  sets {0,1}. Always predicting {0} covers 0.8935 because mortality is 10.65%.
  Do not report marginal coverage without the per-class numbers.
- Nolactate, alpha 0.10 (Phase 3 sensitivity only): mean AUROC 0.8695, a
  decrease of 0.0031 from noflags; marginal coverage 0.9002 overall and
  class-conditional coverage 0.9002 overall (0.9013 for deaths); mean set size
  1.261. This does not establish results for Phases 4-5.
- Noflags, alpha 0.05: mean marginal coverage 0.9504; death coverage 0.5544
  (2.5th-97.5th percentiles 0.5144-0.5868), survivor coverage 0.9976.
  Class-conditional coverage is 0.9508 for deaths and 0.9503 for survivors;
  mean set size 1.431, with 43.14% of sets {0,1}. Marginal sets at alpha 0.05
  cover 55.4% of deaths.
- The bound (0.95 - 0.8935) / 0.1065 = 0.5305 assumes survivors are fully
  covered; it is a mean-level bound, not a per-split one. Some seed-level death
  coverage is below 0.53 because overall coverage varies across random splits
  (test and calibration sampling), e.g. 0.9456 in some splits, which allows
  death coverage near 0.518.
- Measured-flag gain was zero in seeds 0-9. Across 100 seeds, best_iteration
  averaged 326 for noflags at alpha 0.10 (early stopping worked); forbidden
  columns were excluded. In the primary noflags model (seed 0) the highest-
  ranked features by gain were BUN, lactate, GCS, respiratory rate,
  bicarbonate and sodium; intubation ranked 12th and age 13th. The script
  exports XGBoost importance_type="gain".
- Percentiles and SDs reported for the 100 runs describe split-to-split
  variability (random train/calibration/test splits), not confidence
  intervals for the true coverage.

## 8. Later phases (summary)

- **Phase 4:** subgroup coverage from `phase3_test_predictions.parquet`;
  Wilson CIs; y=1 and y=0 separately; single attributes and at most pairs
  (avoid fine intersections: Asian, Hispanic cells get tiny).
- **Phase 5:** Mondrian calibration per subgroup; re-run the audit on the
  held-out test set (never audit on the calibration set).
- **Phase 6:** eICU-CRD external validation, per hospital where possible.
  Needs eICU download and a harmonization of variables and subgroup labels.
- **Phase 7:** set-size cost per subgroup; write-up.
- **Secondary analyses:** temporal split using `anchor_year_group` (train and
  calibrate on older years, test on 2020-2022) to show exchangeability
  breaking; supplementary-only `*_measured` flags; GCS sensitivity; alternative
  race mapping; alpha = 0.05.

## 9. Verify before citing or submitting (UNVERIFIED items)

- Exact author list and numbers of the JMIR 2024 conformal sepsis paper;
  quote its limitations only by paraphrase.
- Scientific Reports 2026 (conformal selective prediction, sex-stratified
  Mondrian) and arXiv 2602.16794 (substantive fairness): re-read before relying
  on the characterisations above.
- Original Mondrian conformal citation (Vovk et al., 2003) and the
  "equalized coverage" reference (Romano et al., 2020): confirm titles/venues.
- Pulse-oximetry bias citation (Sjoding et al., NEJM 2020): confirm before use.
- The cited fairness audits of MIMIC (Scientific Data 2022 etc.): confirm
  authors and findings.
- A claim made during development that about 61% of labevents rows lack
  hadm_id: not checked by us; do not put in the paper without checking.
- Whether "no prior conformal study covers multi-attribute ICU mortality" is
  still true at submission time: repeat the literature search.
- SD and percentiles from the 2-seed smoke run are superseded; report the
  100-seed results.

## 10. Limitations to write

- Cohort requires survival to ICU hour 24 and first stays only: early deaths
  are excluded, mortality is lower than in all-comer ICU populations.
- Single-center (Boston) data for development; eICU only for external check.
- Race is recorded per admission, partly self-reported, partly not; the
  Other/Unknown group is heterogeneous. Subgroup labels are coarse.
- Small groups (Asian N=1,543; Hispanic N=1,970) give wide uncertainty for
  class-conditional coverage, especially among deaths.
- Pooling arterial and non-invasive BP, and blood-gas with chemistry panel
  values.
- GCS is affected by intubation and sedation; SpO2 may be biased by skin
  pigmentation.
- Plausible ranges are author-defined. Lactate (28% missing) ordering is
  informative and may reflect care patterns.
- Conformal guarantees are marginal over exchangeable data; temporal and site
  shifts can break them (we test this explicitly).

## 11. Methods text snippets (edit freely)

**Cohort.** We used MIMIC-IV v3.1. We included adult patients (age >= 18) and
retained each patient's first ICU stay lasting at least 24 hours (N = 51,838
from 94,458 ICU stays). The outcome was in-hospital mortality (10.65%).

**Features.** Predictors were derived from the first 24 hours of the ICU stay
(vital signs, Glasgow Coma Scale) and from laboratory results collected between
6 hours before and 24 hours after ICU admission. For each variable we computed
the minimum, maximum and mean. Values outside author-defined plausible ranges
(0.002% to 0.49% of measurements) were set to missing. Missing values were not
imputed before modelling.

**Subgroups.** Race/ethnicity, age group, sex and insurance type were used only
to evaluate model and uncertainty performance; race and insurance were not
model inputs.

## Methods wording (approved)

Missing values were handled natively by XGBoost without imputation.
Missing-indicator flags had zero importance in seeds 0-9 and were therefore
redundant. As a Phase 3 sensitivity analysis, we repeated the analysis
excluding lactate, the only variable with substantial missingness (27.9%).

This wording covers Phase 3 only; do not claim all analyses excluded lactate
until the nolactate variant has been run for Phases 3-5. The zero-importance
claim is verified for seeds 0-9.

## 12. Open questions for the researcher

1. Final alpha: 0.10 only, or also 0.05?
2. Check whether measured flags have zero gain for seeds 10-99.
3. Which pairs of attributes (if any) to analyse jointly in Phase 4-5?
4. Target journal and reporting guideline (TRIPOD+AI is likely relevant).

## 13. Ethics, Data Provenance, and Reviewer Statements

- **IRB statement:** UNVERIFIED. Do not use the proposed approval/waiver language until checked against authoritative documentation.
- **Credentialing:** CITI Program "Data or Specimens Only Research" completed. Authorized PhysioNet credentialed user.
- **Data DOI:** UNVERIFIED — proposed DOI: https://doi.org/10.13026/83zf-8025; verify before citing.
- **GitHub URL:** UNVERIFIED — proposed URL: https://github.com/Anthic/ICU-analysis; verify before citing.
- **STROBE Flow:** All ICU stays 94,458 -> First ICU stay 65,366 -> LOS >= 24h 51,838 -> Adults >= 18: 51,838 (10.65% mortality).
- **Extraction Protocol:** Streamed chunked extraction (chunksize 2,000,000) from `chartevents` & `labevents`. Observation windows: vitals [intime, intime+24h], labs [intime-6h, intime+24h]. Features: min/max/mean. Outlier filtering per physiological ranges (NaN conversion, no patient row drop).
- **Full Guide:** See `paper/reviewer_responses_and_methods_evidence.md` for verbatim text snippets and reviewer FAQ answers.
