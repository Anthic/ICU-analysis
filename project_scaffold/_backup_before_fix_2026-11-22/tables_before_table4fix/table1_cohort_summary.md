# Table 1: Study Cohort Inclusion and Demographic Profile
*Source: `data/processed/cohort.parquet` and `outputs/results/phase1_exclusion_flow.csv`*

### Inclusion / Exclusion Flow (STROBE Standards)
| Step | Filter Description | Remaining Stays (N) | Excluded | Clinical Rationale |
|---|---|---|---|---|
| 1 | All ICU stays in MIMIC-IV v3.1 | 94,458 | — | Complete ICU database universe |
| 2 | First ICU stay per patient | 65,366 | 29,092 | Prevents data leakage across patient splits |
| 3 | ICU Length of Stay $\ge$ 24 hours | 51,838 | 13,528 | Standard 24h diagnostic/prognostic benchmark window |
| 4 | Adult patients (Age $\ge$ 18) | 51,838 | 0 | All eligible first stays met adult criteria |
| **Final** | **Analyzed ICU Patient Cohort** | **51,838** | — | **5,522 deaths (10.65%, exact: 5,522 / 51,838 = 0.106524)** |

### Cohort Demographic Composition
- **Sex:** Male 29,535 (57.0%), Female 22,303 (43.0%)
- **Age Groups:** 18–49: 9,540 (18.4%), 50–64: 15,156 (29.2%), 65–74: 12,162 (23.5%), 75+: 14,980 (28.9%)
- **Race / Ethnicity:** White 33,997 (65.6%), Other/Unknown 9,760 (18.8%), Black 4,568 (8.8%), Hispanic 1,970 (3.8%), Asian 1,543 (3.0%)
- **Insurance:** Medicare 27,698 (53.4%), Private 14,606 (28.2%), Medicaid 7,257 (14.0%), Other/Unknown 2,277 (4.4%)
