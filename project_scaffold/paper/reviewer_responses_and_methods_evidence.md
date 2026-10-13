# Academic Evidence & Methodology Guide: Data Provenance, Ethics, and Extraction

> **Purpose:** Ready-to-use responses and official manuscript statements for peer reviewers, grant committees, and the paper's Methods section regarding data legitimacy, ethical compliance, and massive data extraction methodology.

---

## 1. Ethics, Governance, and Data Provenance (Evidence of Legitimate Access)

When reviewers ask: *"Where did you obtain the data, what is your authorization/evidence, and was ethical approval granted?"*

### A. Institutional Review Board (IRB) & Ethics Statement — UNVERIFIED
The following proposed text is UNVERIFIED. Do not include it in a manuscript until checked against authoritative documentation:
> *"The study utilized the Medical Information Mart for Intensive Care IV (MIMIC-IV v3.1) database, developed and maintained by the Laboratory for Computational Physiology at the Massachusetts Institute of Technology (MIT) and Beth Israel Deaconess Medical Center (BIDMC). The establishment and dissemination of MIMIC-IV were approved by the Institutional Review Boards (IRBs) of BIDMC (Boston, MA) and MIT (Cambridge, MA). In accordance with the US Health Insurance Portability and Accountability Act (HIPAA) Safe Harbor provision, all protected health information was de-identified. Individual patient informed consent was waived by both review boards as the study involves secondary analysis of de-identified health records without impacting clinical care."*

### B. Researcher Credentialing & CITI Training Evidence
To show compliance with PhysioNet credentialing requirements:
- **CITI Training Course:** "Data or Specimens Only Research" (Human Subjects Research / Biomedical Focus).
- **PhysioNet Credentialed Status:** Authorized credentialed user under the PhysioNet Data Use Agreement (DUA).
- *When requested by an editorial office or reviewer:* Provide your **CITI Certification Record ID / Completion Report** and registered PhysioNet username.

### C. Data Availability Statement — DOI UNVERIFIED
> *"The raw clinical dataset analyzed in this study is available via PhysioNet at https://doi.org/10.13026/83zf-8025. Access to MIMIC-IV is restricted to credentialed researchers who have completed accredited human subjects research training (CITI Program) and signed the PhysioNet Data Use Agreement. Due to these data-sharing restrictions, raw patient-level records cannot be shared directly in public repositories."*

### D. Code Availability & Reproducibility Statement — GitHub URL UNVERIFIED
> *"To ensure end-to-end reproducibility, all source code for cohort curation, feature extraction, missingness auditing, model training, and conformal prediction calibration is made publicly available in the GitHub repository: https://github.com/Anthic/ICU-analysis."*

---

## 2. Extraction from Massive ICU Data (Methodological Rigor)

When reviewers ask: *"How did you reliably extract and filter this cohort from the multi-gigabyte, hundreds-of-millions-of-rows MIMIC-IV database?"*

### A. Cohort Selection Flow (STROBE / TRIPOD Standards)
The extraction follows standard clinical informatics inclusion/exclusion hierarchy (documented in `outputs/results/phase1_exclusion_flow.csv` and executed by `src/data_processing/01_build_cohort.py`):

| Step | Cohort Filter | Count (N) | Excluded | Rationale |
|---|---|---|---|---|
| **1** | All ICU stays in MIMIC-IV v3.1 | **94,458** | — | Initial universe of all adult/pediatric stays across all hospital units |
| **2** | First ICU stay per patient | **65,366** | **29,092** | Prevents identical patient appearing across train, calibration, and test splits (data leakage) |
| **3** | ICU Length of Stay (LOS) $\ge$ 24 hours | **51,838** | **13,528** | Standard benchmark window: model predicts mortality at exactly 24h of ICU care; excludes early discharges and hyper-acute deaths |
| **4** | Adult patients (Age $\ge$ 18) | **51,838** | **0** | All first-stay patients surviving to 24h met the adult inclusion threshold |
| **—** | **Final Analyzed Cohort** | **51,838** | — | **Mortality outcome rate: 10.65% (5,521 deaths)** |

### B. High-Volume Streaming & Windowing Pipeline
MIMIC-IV `chartevents.csv.gz` contains over 300 million rows, and `labevents.csv.gz` exceeds 120 million rows. Extraction is implemented via scalable, deterministic pipeline (`src/data_processing/02_build_features.py`):

1. **Chunked Memory-Safe Extraction:**  
   Processed using iterative chunked streams (`chunksize = 2,000,000` rows) filtering directly against pre-indexed dictionary item IDs (`d_items` and `d_labitems`).
2. **Clinical Observation Windows:**
   - **Vital Signs:** Filtered strictly within the first 24 hours of ICU stay: $[\text{intime}, \text{intime} + 24\,\text{hours}]$.
   - **Laboratory Tests:** Filtered within a 30-hour clinical window: $[\text{intime} - 6\,\text{hours}, \text{intime} + 24\,\text{hours}]$. The 6-hour pre-admission lead window captures emergency department and ward admission labs drawn immediately prior to ICU transfer.
   - **Prediction Horizon:** End of hour 24. No data recorded after ICU hour 24 is accessed by the model.
3. **Plausible Range Filtering (Outlier Management):**
   Physiologically implausible entries are converted to `NaN` (preserving patient records while eliminating recording artifacts):
   - Heart rate: 20–300 bpm (0.013% filtered)
   - SBP: 30–300 mmHg (0.010% filtered)
   - DBP: 10–200 mmHg (0.016% filtered)
   - MAP: 20–250 mmHg (0.222% filtered)
   - Resp Rate: 4–80 bpm (0.492% filtered)
   - $\text{SpO}_2$: 50–100% (0.022% filtered)
   - Temperature: 30–45 °C (0.108% filtered)
   - Lactate: 0.1–30 mmol/L (0.005% filtered)
   - Creatinine: 0.1–30 mg/dL (0.022% filtered)
   - WBC: 0.1–200 K/uL (0.061% filtered)
   - Platelets: 1–2000 K/uL (0.003% filtered)
   - BUN: 1–250 mg/dL (0.003% filtered)
   - Glucose: 10–1500 mg/dL (0.014% filtered)
   - Potassium: 1–12 mEq/L (0.009% filtered)
   - Sodium: 90–200 mEq/L (0.006% filtered)
   - Bicarbonate: 2–60 mEq/L (0.002% filtered)
4. **Deterministic Feature Aggregation:**  
   For every patient stay, the minimum, maximum, and mean are extracted across each vital and lab indicator, yielding a clean matrix of **51,838 rows $\times$ 72 feature columns**.

---

## 3. Reviewer FAQ Cheat Sheet

### Q1: "Why did you exclude patients with ICU stay < 24 hours?"
> **Answer:** *"Our clinical prediction task is framed at ICU hour 24 to inform escalation, triaging, and discharge discussions after standard initial resuscitation. Patients staying under 24 hours either experienced rapid stabilization/discharge or acute mortality before full diagnostic panels could be collected. This 24-hour inclusion threshold is the standard benchmark in ICU prognostic modeling (e.g., SAPS-II, APACHE-IV) and ensures comparable observation windows across all demographic subgroups."*

### Q2: "Did you impute missing data before splitting into train, calibration, and test sets?"
> **Answer:** *"No. Imputing before splitting causes data leakage from test and calibration distributions into training representations. Gradient boosting algorithms (XGBoost) natively handle missing values through optimal default split paths. Any optional imputation evaluated in sensitivity analyses was fit strictly on the training partition only."*

### Q3: "Were race/ethnicity and insurance status used as predictive features?"
> **Answer:** *"No. Race/ethnicity and insurance status were strictly omitted from model input features ($X$) to prevent algorithmic encoding of systemic structural disparities. They were retained solely as audit attributes to evaluate empirical coverage gaps across demographic subgroups in conformal prediction sets."*

## Prediction-set wording
Never describe a set containing only `{0}` as certain survival. It is a model prediction set, not a statement of certainty.
