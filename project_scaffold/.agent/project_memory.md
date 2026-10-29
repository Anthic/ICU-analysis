# Project Memory: ICU Conformal Fairness Study

> Purpose: single source of truth for the agent and for writing the paper.
> Save as `.agent/project_memory.md` (copy to `paper/` too if wanted).
> Read this together with `.agent/instructions.md`, `workflow.md`, `rules.md`.
> Last updated: after Phase 5 completed and Phase 4 rigorous audit reaggregation (Oct 2026).
> Rule for the agent: Propose edits; apply only after the researcher confirms.
> Status labels defined:
>   - GENERATED (made by a script)
>   - REVIEWED (researcher looked)
>   - VERIFIED (independently recomputed from the source files by a separate script)
> Process note: full result tables are auto-generated into `paper/tables/*.md` via
> `src/evaluation/make_paper_tables.py`; this memory file retains decisions,
> methodological rules, and links to those artifacts.

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

Outcome: in-hospital mortality (`hospital_expire_flag`), **10.65%**
(5,522 deaths / 51,838 patients; exact: 5,522 / 51,838 = 0.106524).
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
- Model: XGBoost, fixed hyperparameters, early stopping on a 15% validation slice
  of the training split (85% train-fit / 15% early-stopping validation).
  Calibration and test sets are never used to fit or tune.
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

### Phase 4 status (Subgroup audit on Phase 3 baseline, 100 seeds) - GENERATED - PENDING REVIEW

- **Designation:** Primary analysis (designated after an exploratory look at Phase 4 results; to be confirmed on eICU / later-period data): Class-conditional coverage audit across demographic subgroups.
- **Data source & Script:** Generated by `src/evaluation/reaggregate_phase4_audit.py` to `outputs/tables/phase4_rigorous_audit_noflags_a010.csv` (100 seeds, noflags, alpha = 0.10). Deprecated original file moved to `outputs/tables/archive/DEPRECATED_phase4_subgroup_coverage.csv`.
- **Full paper table:** See [`paper/tables/table3_phase4_subgroup_audit.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table3_phase4_subgroup_audit.md).
- **Confidence Intervals (One bootstrap, one set of CIs):** Re-run with fixed seed (BOOT_SEED = 42, B = 1,000) from `src/evaluation/reaggregate_phase4_audit.py`, using exclusively its output. The bootstrap resamples unique patient stays with replacement; earlier CIs generated from across-split percentiles or normal approximation are superseded.
- **Calibration-in-the-large (CITL):** A positive CITL means the model over-predicts risk. Overall CITL -0.0023 is small in magnitude (0.2 pp) although its CI excludes zero; Black +0.0129 and Other/Unknown (race) -0.0349 are reported as exploratory audit results (CI ignores calibration variability; many groups examined).
- **Marginal vs Class-Conditional Coverage:** Under standard marginal split conformal, marginal death coverage is uniformly low across all demographic subgroups (21%–29%). This is a mathematical consequence of class imbalance (10.65% mortality [5,522 / 51,838 = 0.106524] means covering survivors suffices to reach 90% overall coverage), not between-group disparity. The primary fairness evaluation is therefore **class-conditional (CC) death and survivor coverage**.
- **Disparity vs White:** Group survivor differences compared to White report both the difference of 100-seed means (point estimate) and the bootstrap-based difference (mean of bootstrap differences with patient bootstrap 95% CI):
  - Asian vs White: difference of 100-seed means **−2.10 pp**; bootstrap estimate **−2.06 pp** [95% CI: −3.53 pp, −0.50 pp]
  - Black vs White: difference of 100-seed means **−1.30 pp**; bootstrap estimate **−1.31 pp** [95% CI: −2.18 pp, −0.38 pp]
  - Hispanic vs White: difference of 100-seed means **+2.16 pp**; bootstrap estimate **+2.11 pp** [95% CI: +1.07 pp, +3.16 pp]
  - Other/Unknown (race) vs White: difference of 100-seed means **−1.44 pp**; bootstrap estimate **−1.45 pp** [95% CI: −2.16 pp, −0.79 pp]
  - See full table: [`paper/tables/table7_survivor_disparity_vs_white.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table7_survivor_disparity_vs_white.md).
- **Errata:**
  1. Marginal death coverage was wrong in 11 of 13 groups in an earlier summary.
  2. The earlier global SD column came from a different computation and is superseded by the single-script SD table (`phase4_rigorous_audit_noflags_a010.csv` and `paper/tables/table5_variance_ratio_audit.md`).
  3. In earlier draft notes, only the sex rows were traced to Phase 5 values; for age and insurance class-conditional values, and for race death values, their origin is undetermined; do not say Hispanic 89.95 came from Phase 5 (in Phase 5, Hispanic Mondrian death coverage is 90.28%), and do NOT say 3.6% was a rounding of 3.49%.
- **Intersectional pairs:** Only `race_group x sex` (10 cells) and `age_group x insurance_group` (16 cells) are evaluated. `race_group x insurance_group` was removed/labeled as "dropped pair" due to severe data sparsity (<50 deaths in almost all cells). Cells with <50 mean deaths/seed are labeled **UNSTABLE** (Asian, Hispanic, and small intersectional strata).

### Phase 5 status (Mondrian Conformal Correction, 100 seeds) - EXPLORATORY

- **Script:** `src/conformal/05_mondrian_conformal.py`
- **Data source:** `outputs/tables/phase5_subgroup_coverage_corrected_noflags_a010.csv` (100 seeds, noflags, alpha = 0.10).
- **Full paper tables:**
  - Comparison & Paired Differences: [`paper/tables/table4_phase5_mondrian_comparison.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table4_phase5_mondrian_comparison.md)
  - Variance Ratio Audit: [`paper/tables/table5_variance_ratio_audit.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table5_variance_ratio_audit.md)
  - Mondrian Marginal Failure: [`paper/tables/table6_mondrian_marginal_failure.md`](file:///d:/dataset/icu_conformal_fairness_project%20(1)/project_scaffold/paper/tables/table6_mondrian_marginal_failure.md)
- **Calibration property:** Mondrian class-conditional conformal prediction is **calibrated to nominal by construction** per (subgroup x outcome class) on the calibration split, evaluated on the held-out test split. Do NOT describe this as "repaired" or "restored".
- **n = 0 rule (Code-verified behavior):** When a calibration cell has $n = 0$ examples for a given class (or when $k = \lceil(n+1)(1-\alpha)\rceil > n$, such that the requested quantile exceeds the available sample size), the code in `src/conformal/utils.py` assigns `+infinity` (`float("inf")`), NOT the overall class quantile. In prediction set generation, $1 - \hat{p}(y|x) \le \infty$ is unconditionally satisfied, guaranteeing conservative inclusion of that class label in the prediction set.
- **Calibration variability warning:** Patient bootstrap CIs ignore calibration-set variability, which is the main source of variation for Mondrian cells. Next to every Mondrian value, we report the across-seed standard deviation (seed SD) and the 2.5th–97.5th percentile across-seed range.
- **Variance wording:** Mondrian seed SD is 7–50% larger than global (ratio 1.07–1.50; 1.80 for Other/Unknown insurance), as expected because the calibration cell adds sampling noise.
  - *Explanation of seed SD:* The seed SD of about 3 pp for age 18-49 is mainly test-sampling variation from about 151 test deaths per split.
- **Paired differences (Mondrian minus Global):**
  - Estimator reported: both the difference of 100-seed means and the bootstrap-based difference (mean of bootstrap differences with patient bootstrap 95% CIs) along with the across-split seed SD of each delta.
  - Crucial insight: the mean improvement is clear, but the delta varies a lot from split to split (seed SD of the delta, e.g. 3.6 pp for age 18-49).
  - *Primary analysis (Age):*
    - 18–49: death diff +6.36 pp (100-seed) / **+6.25 pp** [boot 95% CI: +5.21, +7.32] (delta seed SD: 3.61 pp); surv diff −4.93 pp / **−4.94 pp** [−5.22, −4.66] (delta seed SD: 0.81 pp)
    - 50–64: death diff +2.85 pp / **+2.86 pp** [+2.51, +3.25] (delta seed SD: 1.53 pp); surv diff −2.57 pp / **−2.55 pp** [−2.68, −2.44] (delta seed SD: 0.58 pp)
    - 65–74: death diff −0.23 pp / **−0.22 pp** [−0.34, −0.10] (delta seed SD: 1.52 pp); surv diff −1.06 pp / **−1.06 pp** [−1.13, −1.00] (delta seed SD: 0.57 pp)
    - 75+: death diff −2.95 pp / **−2.96 pp** [−3.28, −2.66] (delta seed SD: 1.33 pp); surv diff +7.09 pp / **+7.10 pp** [+6.85, +7.35] (delta seed SD: 0.78 pp)
  - *Primary analysis (Insurance):*
    - Medicaid: death diff +2.59 pp / **+2.63 pp** [+2.17, +3.13] (delta seed SD: 2.30 pp); surv diff −1.65 pp / **−1.62 pp** [−1.74, −1.50] (delta seed SD: 0.70 pp)
    - Medicare: death diff −1.26 pp / **−1.27 pp** [−1.39, −1.15] (delta seed SD: 0.85 pp); surv diff +2.74 pp / **+2.74 pp** [+2.66, +2.83] (delta seed SD: 0.33 pp)
    - Other/Unknown: death diff −1.81 pp / **−1.89 pp** [−2.56, −1.23] (delta seed SD: 4.14 pp); surv diff −2.89 pp / **−2.93 pp** [−3.32, −2.61] (delta seed SD: 1.54 pp)
    - Private: death diff +3.65 pp / **+3.63 pp** [+3.12, +4.21] (delta seed SD: 1.77 pp); surv diff −3.73 pp / **−3.74 pp** [−3.92, −3.56] (delta seed SD: 0.60 pp)
  - *Exploratory (Race & Sex):*
    - Asian: death diff +2.54 pp / **+2.66 pp** [+1.53, +3.88] (delta seed SD: 4.88 pp); surv diff +1.28 pp / **+1.29 pp** [+1.08, +1.50] (delta seed SD: 1.55 pp)
    - Black: death diff −0.17 pp / **−0.13 pp** [−0.41, +0.17] (delta seed SD: 2.98 pp); surv diff +0.97 pp / **+0.96 pp** [+0.87, +1.07] (delta seed SD: 0.85 pp)
    - Hispanic: death diff +2.67 pp / **+2.66 pp** [+1.68, +3.77] (delta seed SD: 4.69 pp); surv diff −2.04 pp / **−2.06 pp** [−2.33, −1.80] (delta seed SD: 1.47 pp)
    - Other/Unknown (race): death diff −1.15 pp / **−1.16 pp** [−1.33, −1.00] (delta seed SD: 1.35 pp); surv diff +1.21 pp / **+1.21 pp** [+1.13, +1.29] (delta seed SD: 0.57 pp)
    - White: death diff +0.47 pp / **+0.47 pp** [+0.41, +0.54] (delta seed SD: 0.70 pp); surv diff −0.36 pp / **−0.36 pp** [−0.38, −0.34] (delta seed SD: 0.20 pp)
    - Female: death diff −0.59 pp / **−0.58 pp** [−0.67, −0.49] (delta seed SD: 1.07 pp); surv diff +0.74 pp / **+0.73 pp** [+0.70, +0.77] (delta seed SD: 0.40 pp)
    - Male: death diff +0.53 pp / **+0.55 pp** [+0.48, +0.62] (delta seed SD: 0.80 pp); surv diff −0.52 pp / **−0.52 pp** [−0.55, −0.50] (delta seed SD: 0.30 pp)
- **Empirical evidence that Mondrian marginal fails (EXPLORATORY):**
  From `outputs/tables/phase5_subgroup_coverage_corrected_noflags_a010.csv`, group-conditional conformal without class conditioning (Mondrian marginal) fails to protect patients who die because the ~89% survivor majority dominates each group's calibration threshold:
  - Age 18–49 death coverage: **11.77%** [seed range 6.27%, 18.10%]
  - Age 50–64 death coverage: **18.15%** [seed range 14.32%, 22.59%]
  - Age 65–74 death coverage: **22.52%** [seed range 16.61%, 28.03%]
  - Age 75+ death coverage: **39.79%** [seed range 35.12%, 45.26%]
- **Intersectional pairs:** `race_group x sex` (10 cells) and `age_group x insurance_group` (16 cells) evaluated. `race_group x insurance_group` was removed/labeled as "dropped pair" due to small cell sample sizes (<50 deaths/seed in almost all cells). Cells with <50 deaths/seed are flagged UNSTABLE.
- **Visualization:** `outputs/figures/phase5_mondrian_coverage_by_group_noflags_a010.png`.

## 8. Later phases (summary)

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
- Calibration-set variability: patient bootstrap CIs ignore calibration-set
  variability, which is the main source of variation for Mondrian cells. Small
  calibration cells produce wide across-seed ranges even when bootstrap CIs on
  pooled predictions appear narrow.
- Small cell instability: Asian and Hispanic have about 39 test deaths per
  split; 100% coverage in a split occurs by chance (about 1.6% of splits at 90%
  coverage); no seed had q = infinity for single attributes.
- Mondrian coverage is calibrated to nominal by construction on exchangeable
  calibration data; it does not confer out-of-distribution robustness or
  guarantee equal coverage under domain, hospital, or temporal shifts.
- Dropped intersection pairs: race x insurance was dropped from primary
  reporting due to severe data sparsity across multiple joint categories.
- n = 0 handling: when a calibration stratum contains zero instances of an
  outcome class (or fewer than required for the rank order statistic), the
  quantile conservatively defaults to +infinity, guaranteeing inclusion of the
  label rather than falling back to an unstratified quantile.
- Multiple comparisons: auditing multiple demographic attributes and
  intersections inflates family-wise error rates; reported intervals should be
  interpreted as exploratory audits pending external confirmation.
- Predicted-risk distributions: baseline conformal coverage differences across age
  groups likely reflect different predicted-risk distributions across age groups
  (not tested here).
- Calibration-in-the-large disparities: Other/Unknown (race) exhibits
  systematic under-prediction of mortality (CITL about −0.035), whereas Black
  patients show modest risk over-prediction (CITL about +0.013).
- Finite-sample over-coverage: small Mondrian cells with low event counts
  exhibit discrete finite-sample over-coverage due to the conservative ceil
  rank formulation $\lceil (n+1)(1-\alpha) \rceil / n$.

## 11. Methods text snippets (edit freely)

**Cohort.** We used MIMIC-IV v3.1. We included adult patients (age >= 18) and
retained each patient's first ICU stay lasting at least 24 hours (N = 51,838
from 94,458 ICU stays). The outcome was in-hospital mortality (10.65%, 5,522 deaths / 51,838 patients; exact: 0.106524).

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

1. Final alpha: 0.10 only, or also 0.05? (alpha 0.05 was run for the noflags variant in Phase 3 only).
2. Check whether measured flags have zero gain for seeds 10-99.
3. Which pairs of attributes (if any) to analyse jointly in Phase 4-5? -> Resolved: race_group x sex and age_group x insurance_group evaluated; race_group x insurance_group dropped due to sparsity.
4. Target journal and reporting guideline (TRIPOD+AI is likely relevant).

## 13. Ethics, Data Provenance, and Reviewer Statements

- **IRB statement:** UNVERIFIED. Do not use the proposed approval/waiver language until checked against authoritative documentation.
- **Credentialing:** CITI Program "Data or Specimens Only Research" completed. Authorized PhysioNet credentialed user.
- **Data DOI:** UNVERIFIED — proposed DOI: https://doi.org/10.13026/83zf-8025; verify before citing.
- **GitHub URL:** UNVERIFIED — proposed URL: https://github.com/Anthic/ICU-analysis; verify before citing.
- **STROBE Flow:** All ICU stays 94,458 -> First ICU stay 65,366 -> LOS >= 24h 51,838 -> Adults >= 18: 51,838 (10.65% mortality, 5,522 deaths / 51,838 patients; exact: 5,522 / 51,838 = 0.106524).
- **Extraction Protocol:** Streamed chunked extraction (chunksize 2,000,000) from `chartevents` & `labevents`. Observation windows: vitals [intime, intime+24h], labs [intime-6h, intime+24h]. Features: min/max/mean. Outlier filtering per physiological ranges (NaN conversion, no patient row drop).
- **Full Guide:** See `paper/reviewer_responses_and_methods_evidence.md` for verbatim text snippets and reviewer FAQ answers.
