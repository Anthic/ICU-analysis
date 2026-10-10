# Project Institutional Memory & Decision Log
**Project:** Group-Conditional Conformal Prediction for Equitable Uncertainty Quantification in ICU Mortality Risk Prediction (MIMIC-IV / eICU-CRD Study)

This document records all critical architectural decisions, clinical rationale, data engineering gotchas, bug fixes, and exact parameters established across the research phases.

---

## 1. Project & Paper Strategy
- **Core Research Question:** Does standard split conformal prediction provide equitable confidence interval coverage across demographic subgroups (race/ethnicity, sex, age, insurance) in ICU mortality risk prediction? Can multi-attribute Mondrian (group-conditional) conformal prediction restore fairness guarantees without unacceptable interval width expansion?
- **Scientific Benchmark:** Directly addresses the published limitations of CPMORS (JMIR, Q1), which built conformal predictors for sepsis mortality on MIMIC-IV/eICU but explicitly flagged generalizability, demographic bias, and multi-center equity as unaddressed future work.
- **Data Footprint & Portability Strategy:**
  - Raw MIMIC-IV 3.1 files (30–40+ GB uncompressed) remain read-only at `D:\dataset\physionet.org\files\mimiciv\3.1`.
  - Only processed parquet files (`cohort.parquet` ~2.6 MB, `features.parquet` ~15 MB) and outputs are portable. Moving the project to another machine requires transferring only `project_scaffold` (~50–80 MB without `.venv`).
  - Downstream phases (Phase 3–7) operate solely on `features.parquet`.

---

## 2. Phase 1 — Cohort Construction (`01_build_cohort.py`)
### Clinical Inclusion/Exclusion Criteria & Order (CONSORT Flow)
1. **All ICU Stays:** 94,458 total stays in MIMIC-IV 3.1 (`icustays.csv.gz`).
2. **First ICU Stay per Patient (Index Stay):** Filtered to 65,366 stays (`drop_duplicates(subset=['subject_id'], keep='first')`).
   - *Rationale:* Eliminates survival and repeat-admission selection bias. Enforces patient-level independence (I.I.D.) across train/calibration/test splits.
3. **ICU Length of Stay $\ge$ 24h:** Filtered to 51,838 stays (`los >= 1.0` days). Excluded 13,528 stays.
   - *Rationale:* Ensures complete observation window for first-24h physiological vitals and labs.
4. **Adult Patients (Age $\ge$ 18):** 51,838 patients (0 excluded; MIMIC-IV contains only adult ICU records).
5. **Complete Admission & Outcome Link:** 51,838 unique patients. Verified `n_final == n_adults` and `subject_id.is_unique`.
6. **In-Hospital Mortality Rate:** Exactly **10.65%** (clinically textbook-normal ICU baseline).

### Demographic Harmonization
- **Age Groups:** Bins `[17, 49, 64, 74, 150]` with labels `['18-49', '50-64', '65-74', '75+']`.
  - *Bug Fix:* Bin starts at 17 so `(17, 49]` strictly includes 18-year-old patients without creating NaNs.
- **Race / Ethnicity (5 Standard Groups):**
  - `Hispanic`: Matches `HISPANIC`, `LATINO`, `SOUTH AMERICAN`, `BRAZILIAN` (captures Latin American ethnicity).
  - `White`: Matches `WHITE`, `PORTUGUESE` (strictly excludes Brazilian/South American).
  - `Black`: Matches `BLACK`, `AFRICAN`, `CAPE VERDEAN`, `CARIBBEAN`.
  - `Asian`: Matches `ASIAN`.
  - `Other/Unknown`: Composite heterogeneous group (Native American, Pacific Islander, declined, unknown). Transparently audited in fairness tables but acknowledged as non-unified in methods.
  - Distribution: White 65.6% (33,997), Other/Unknown 18.8% (9,760), Black 8.8% (4,568), Hispanic 3.8% (1,970), Asian 3.0% (1,543). Every minoritized group has $>1,500$ patients, ensuring statistical power.
- **Insurance:** `Medicare` (53.4%), `Private` (28.2%), `Medicaid` (14.0%), `Other/Unknown` (4.4%).
  - *Rationale:* `Private` kept separate from `Other` to preserve commercial vs government assistance socioeconomic disparities.
- **Temporal Grouping:** `anchor_year_group` preserved from `patients.csv.gz` (2008–2010 to 2020–2022) to enable temporal distribution shift testing.
- **Output Artifacts:** `data/processed/cohort.parquet` and `outputs/results/phase1_exclusion_flow.csv`.

---

## 3. Phase 2 — Feature Engineering (`02_build_features.py`)
### Major Architectural Gotchas & Solutions
1. **The `labevents` Gotcha (`stay_id` missing & null `hadm_id`):**
   - In MIMIC-IV `labevents.csv.gz`, `stay_id` does not exist, and `hadm_id` is null in **61.4%** of rows (ED/outpatient/specimen orders).
   - *Fix:* Filtered strictly on `subject_id.isin(cohort['subject_id'])`, merged `cohort[['subject_id', 'stay_id', 'intime']]`, and filtered by timestamp. Prevents dropping over 60% of critical labs.
2. **Observation Windows:**
   - **Vitals Window:** $[\text{intime},\; \text{intime} + 24\text{h}]$.
   - **Labs Window:** $[\text{intime} - 6\text{h},\; \text{intime} + 24\text{h}]$. Captures resuscitation and baseline emergency department labs drawn immediately prior to ICU physical transfer.
3. **No Imputation in Phase 2 (Leakage Prevention):**
   - All missing values kept strictly as `NaN`. Fitting imputers across the whole dataset prior to train/calibration/test split induces catastrophic data leakage. Imputation deferred to Phase 3 fitted on training set only.
4. **Informative Missingness (`*_measured` Flags):**
   - Created binary 0/1 indicator flags (`<lab>_measured`) for all 9 routine/sparse labs (Lactate, Creatinine, WBC, Platelets, BUN, Glucose, Potassium, Sodium, Bicarbonate).
   - Governed by `INCLUDE_MEASURED_FLAGS = True` config toggle for downstream sensitivity analysis.
5. **GCS Triplets & Intubation Flag:**
   - Components: Eye (220739), Verbal (223900), Motor (223901).
   - Pivoted by `(stay_id, charttime)` and summed **only complete triplets** where all three components are non-null. Extracted `gcs_min` per stay.
   - Text matching on verbal entry (`ETT|TRACH|INTUBAT`) sets `intubated = 1`. In MIMIC-IV, intubated patients have `valuenum = 1.0` and verbal text indicating ETT.
6. **Clinical Plausibility Outlier Guards:**
   - All vital and lab ranges enforced.
   - Out-of-range readings set to `NaN` (rows are never dropped).
   - `temp_f` (223761) converted to Celsius `(F - 32) * 5 / 9` before the 30.0–45.0 °C range filter.
7. **Cache & Resumability Engineering:**
   - Checkpoint files: `checkpoint_vitals_extracted.parquet` and `checkpoint_labs_extracted.parquet`.
   - `checkpoint_metadata.json` stores SHA-256 hash of cohort + feature configs (invalidates cache on config change).
   - **Bug Fix for `TypeError: Object of type int64 is not JSON serializable`:** NumPy `int64` from `bad.sum()` converted to native Python `int` via `to_clean_serializable()`.
   - Preserves completed 5.6-minute vitals extraction (2.18 MB) on disk, enabling instant 0.1s cache loads.
8. **Smoke Test Mode:**
   - Controlled via `MAX_CHUNKS` environment variable. Evaluates 3 chunks in 11.4s and writes to `*_smoke` files without contaminating production caches.

---

## 4. Current State & Next Steps
- **Environment:** Dedicated Python 3.14 virtual environment `.venv` with `uv`, all 126+ dependencies installed (xgboost, lightgbm, scikit-learn, mapie, crepes, statsmodels, pyarrow, fastparquet).
- **Phase 1:** Complete and validated (`cohort.parquet`).
- **Phase 2:** Fully coded, debugged, and smoke-tested (`02_build_features.py`). Vitals checkpoint intact. Running full execution generates `features.parquet` and stratified missingness reports.
- **Phase 3:** Baseline Model Training (XGBoost, 60/20/20 Train/Calibration/Test split) and Standard Split Conformal Prediction.
