## 6. Figure Legends & Visual Artifacts

*(Rewritten 2026-11-24 to match the figure files; figure titles were also made neutral and the figures regenerated. Figure 2 panel A and B values are hard-coded in `generate_paper_master_figures.py`; re-derive them from Table 7 and the CITL table before submission.)*

### Figure 1: Age pattern of class-conditional coverage (MIMIC-IV)
- **File:** `outputs/figures/figure1_age_disparity_and_repair.png` (script `src/evaluation/generate_paper_master_figures.py`)
- **Caption:** **Figure 1. Age-related coverage differences under pooled class-conditional calibration (MIMIC-IV, 100 random splits, nominal 90%).** (A) Observed in-hospital mortality (dark bars) and mean model-predicted risk (light bars) by age group (observed 6.3%, 8.9%, 10.5%, 15.4%; predicted 6.4%, 8.8%, 10.1%, 14.8%). (B) Class-conditional coverage with pooled thresholds: death coverage (red) 84.1%, 87.2%, 90.7%, 93.1% and survivor coverage (teal) 94.9%, 92.5%, 91.1%, 82.9% for ages 18–49, 50–64, 65–74 and 75+; error bars are patient-level bootstrap 95% confidence intervals; the dashed line is 90%. (C) Pooled (orange, blue) versus age x class Mondrian calibration (red, green) for deaths and survivors, with the change in percentage points; Mondrian coverage is close to 90% in every stratum by construction.

### Figure 2: Race and payer
- **File:** `outputs/figures/figure2_racial_and_payer_equity.png`
- **Caption:** **Figure 2. Survivor-coverage differences, calibration-in-the-large and death coverage by race and payer (MIMIC-IV; exploratory).** (A) Difference in survivor coverage from White patients, in percentage points, with 95% confidence intervals (unadjusted for multiple comparisons): Asian −2.10, Black −1.30, Other/Unknown −1.44, Hispanic +2.16. (B) Calibration-in-the-large (mean predicted minus observed mortality, ×10⁻³) by race and payer. (C) Class-conditional death coverage by race and payer with pooled thresholds (dark blue) and Mondrian class-conditional calibration (teal); the dashed line is the nominal 90%. Small strata (Asian, Hispanic) have about 39 deaths per test split and variable coverage.

### Figure 3: Set size and the cost of Mondrian calibration
- **File:** `outputs/figures/figure3_fairness_efficiency_tradeoff.png` (script `src/evaluation/07_tradeoff_analysis.py`)
- **Caption:** **Figure 3. Death coverage and prediction-set size for 15 subgroups (MIMIC-IV, 100 splits, nominal 90%).** (A) Death coverage versus mean set size for each subgroup under pooled class-conditional calibration (circles) and Mondrian class-conditional calibration (diamonds); arrows join the two. (B) Mondrian calibration without class conditioning (squares) gives death coverage of about 12–44% across subgroups, compared with Mondrian class-conditional calibration (diamonds). (C) Change in mean set size, Mondrian minus pooled, by subgroup (range −0.060 to +0.058 labels; 18–49 +0.029, 75+ +0.020).

### Figure 4: Observed versus calibration-implied coverage
- **File:** `outputs/figures/figure4_calibration_implied_coverage.png`
- **Caption:** **Figure 4. Observed class-conditional coverage versus the coverage implied by the scores alone (mean of 100 seeds).** The calibration identity predicts a stratum's coverage from its predicted risks, assuming the scores are calibrated within the stratum. (A) Survivor coverage for 103 eICU hospitals (grey), eICU demographic strata (blue; eICU-recalibrated scores) and MIMIC test strata (red). (B) Death coverage for the same units with raw scores. The dashed line is equality; light lines mark 0.90. Survivor-side agreement is close (R² against the 0.90 baseline 0.92 across hospitals, 0.95 for MIMIC strata); death-side agreement is looser (hospital R² 0.50).

### Figure 5: Coverage by 10-year age band
- **File:** `outputs/figures/figure5_age_bands.png`
- **Caption:** **Figure 5. Class-conditional coverage by 10-year age band with pooled thresholds (MIMIC-IV, 100 splits).** (A) Death coverage and (B) survivor coverage for the reference outcome (death), for death-or-hospice discharge as the outcome, and with hospice discharges removed; points are means over splits and bars are seed standard deviations. Bands below age 50 have 28–81 test deaths per split. The dashed line is 90%.
