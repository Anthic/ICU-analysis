# Table 4: Mondrian Class-Conditional Calibration vs Baseline with Paired Differences
*Source: `outputs/tables/phase4_rigorous_audit_noflags_a010.csv` and `outputs/tables/phase5_subgroup_coverage_corrected_noflags_a010.csv`*
*Estimator note: Paired difference estimates (Δ) and 95% CIs are patient-level bootstrap means (B = 1,000, fixed seed 42) of the difference between Mondrian and Global sets per patient across test appearances. Delta Seed SD reflects split-to-split empirical variation across the 100 seeds.*
> **Key Takeaway:** The mean improvement is clear, but the delta varies a lot from split to split (seed SD of the delta, e.g. 3.6 pp for age 18-49). Patient bootstrap CIs ignore calibration-set variability, which is the main source of variation for Mondrian cells.

### Primary Analysis: Age and Insurance Groups
| Attribute | Subgroup | Global CC Death | Mondrian CC Death [Seed Range] | Paired Δ Death [Boot 95% CI] | Δ Death Seed SD | Global CC Surv | Mondrian CC Surv [Seed Range] | Paired Δ Surv [Boot 95% CI] | Δ Surv Seed SD | Δ Set Size |
|---|---|---|---|---|---|---|---|---|---|---|
| **age_group** | 18-49 | 84.06% | 90.42% [82.25%, 96.09%] | **+6.25 pp** [+5.21, +7.32] | 3.61 pp | 94.90% | 89.97% [88.14%, 91.75%] | **-4.94 pp** [-5.22, -4.66] | 0.81 pp | +0.029 |
| **age_group** | 50-64 | 87.22% | 90.07% [86.03%, 94.33%] | **+2.86 pp** [+2.51, +3.25] | 1.53 pp | 92.52% | 89.95% [88.64%, 91.45%] | **-2.55 pp** [-2.68, -2.44] | 0.58 pp | +0.023 |
| **age_group** | 65-74 | 90.66% | 90.43% [86.34%, 94.52%] | **-0.22 pp** [-0.34, -0.10] | 1.52 pp | 91.07% | 90.01% [88.45%, 91.78%] | **-1.06 pp** [-1.13, -1.00] | 0.57 pp | -0.017 |
| **age_group** | 75+ | 93.14% | 90.19% [86.77%, 92.91%] | **-2.96 pp** [-3.28, -2.66] | 1.33 pp | 82.94% | 90.04% [88.66%, 91.36%] | **+7.10 pp** [+6.85, +7.35] | 0.78 pp | +0.020 |
| **insurance_group** | Medicaid | 87.97% | 90.56% [83.28%, 95.95%] | **+2.63 pp** [+2.17, +3.13] | 2.30 pp | 91.62% | 89.97% [87.84%, 91.68%] | **-1.62 pp** [-1.74, -1.50] | 0.70 pp | +0.026 |
| **insurance_group** | Medicare | 91.45% | 90.18% [87.15%, 92.21%] | **-1.27 pp** [-1.39, -1.15] | 0.85 pp | 87.27% | 90.01% [89.16%, 91.26%] | **+2.74 pp** [+2.66, +2.83] | 0.33 pp | +0.006 |
| **insurance_group** | Other/Unknown (insurance) | 92.34% | 90.52% [80.65%, 98.37%] | **-1.89 pp** [-2.56, -1.23] | 4.14 pp | 92.91% | 90.01% [86.23%, 93.06%] | **-2.93 pp** [-3.32, -2.61] | 1.54 pp | -0.060 |
| **insurance_group** | Private | 86.60% | 90.25% [85.73%, 94.04%] | **+3.63 pp** [+3.12, +4.21] | 1.77 pp | 93.72% | 89.99% [88.38%, 91.52%] | **-3.74 pp** [-3.92, -3.56] | 0.60 pp | +0.017 |

### Exploratory Analysis: Race/Ethnicity and Sex
| Attribute | Subgroup | Global CC Death | Mondrian CC Death [Seed Range] | Paired Δ Death [Boot 95% CI] | Δ Death Seed SD | Global CC Surv | Mondrian CC Surv [Seed Range] | Paired Δ Surv [Boot 95% CI] | Δ Surv Seed SD | Δ Set Size |
|---|---|---|---|---|---|---|---|---|---|---|
| **race_group** | Asian | 88.64% | 91.18% [79.49%, 100.00%] | **+2.66 pp** [+1.53, +3.88] | 4.88 pp | 88.27% | 89.54% [84.71%, 92.95%] | **+1.29 pp** [+1.08, +1.50] | 1.55 pp | +0.058 |
| **race_group** | Black | 91.04% | 90.87% [82.52%, 96.63%] | **-0.13 pp** [-0.41, +0.17] | 2.98 pp | 89.07% | 90.04% [87.53%, 92.30%] | **+0.96 pp** [+0.87, +1.07] | 0.85 pp | +0.015 |
| **race_group** | Hispanic | 87.62% | 90.28% [78.14%, 100.00%] | **+2.66 pp** [+1.68, +3.77] | 4.69 pp | 92.53% | 90.48% [86.73%, 93.60%] | **-2.06 pp** [-2.33, -1.80] | 1.47 pp | +0.045 |
| **race_group** | Other/Unknown (race) | 91.35% | 90.20% [85.55%, 93.85%] | **-1.16 pp** [-1.33, -1.00] | 1.35 pp | 88.93% | 90.14% [88.54%, 91.98%] | **+1.21 pp** [+1.13, +1.29] | 0.57 pp | -0.004 |
| **race_group** | White | 89.61% | 90.08% [87.13%, 92.57%] | **+0.47 pp** [+0.41, +0.54] | 0.70 pp | 90.37% | 90.01% [89.17%, 90.93%] | **-0.36 pp** [-0.38, -0.34] | 0.20 pp | +0.005 |
| **sex** | Female | 90.48% | 89.89% [86.62%, 93.09%] | **-0.58 pp** [-0.67, -0.49] | 1.07 pp | 89.21% | 89.95% [88.55%, 91.08%] | **+0.73 pp** [+0.70, +0.77] | 0.40 pp | -0.002 |
| **sex** | Male | 89.85% | 90.38% [86.92%, 92.78%] | **+0.55 pp** [+0.48, +0.62] | 0.80 pp | 90.62% | 90.11% [89.04%, 91.19%] | **-0.52 pp** [-0.55, -0.50] | 0.30 pp | +0.004 |