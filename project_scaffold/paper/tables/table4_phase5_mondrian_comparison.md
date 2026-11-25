# Table 4: Mondrian Class-Conditional Calibration vs Baseline with Paired Differences
*Source: `outputs/tables/phase4_rigorous_audit_noflags_a010.csv` and `outputs/tables/phase5_subgroup_coverage_corrected_noflags_a010.csv`*
*Estimator note: [REVISED 2026-11-25: Δ are now computed from per-seed CSVs: mean over 100 seeds of Mondrian minus global class-conditional coverage on the same split; bracket = 2.5-97.5 percentile of the seed-level differences; SD = seed SD.] [OLD TEXT, no longer used:] Paired difference estimates (Δ) and 95% CIs are patient-level bootstrap means (B = 1,000, fixed seed 42) of the difference between Mondrian and Global sets per patient across test appearances. Delta Seed SD reflects split-to-split empirical variation across the 100 seeds.*
> **Key Takeaway:** The mean improvement is clear, but the delta varies a lot from split to split (seed SD of the delta, e.g. 3.6 pp for age 18-49). The bracket is the 2.5-97.5 percentile of the seed-level paired differences, so it reflects split and calibration-set variability (it is a spread across splits, not a confidence interval for the population effect).

### Primary Analysis: Age and Insurance Groups
| Attribute | Subgroup | Global CC Death | Mondrian CC Death [Seed Range] | Paired Δ Death [seed 2.5-97.5%] | Δ Death Seed SD | Global CC Surv | Mondrian CC Surv [Seed Range] | Paired Δ Surv [seed 2.5-97.5%] | Δ Surv Seed SD | Δ Set Size |
|---|---|---|---|---|---|---|---|---|---|---|
| **age_group** | 18-49 | 84.06% | 90.42% [82.25%, 96.09%] | **+6.36 pp** [+0.30, +14.58] | 3.61 pp | 94.90% | 89.97% [88.14%, 91.75%] | **-4.93 pp** [-6.66, -3.64] | 0.81 pp | +0.029 |
| **age_group** | 50-64 | 87.22% | 90.07% [86.03%, 94.33%] | **+2.85 pp** [+0.30, +6.00] | 1.53 pp | 92.52% | 89.95% [88.64%, 91.45%] | **-2.57 pp** [-3.67, -1.49] | 0.58 pp | +0.023 |
| **age_group** | 65-74 | 90.66% | 90.43% [86.34%, 94.52%] | **-0.23 pp** [-3.26, +3.02] | 1.52 pp | 91.07% | 90.01% [88.45%, 91.78%] | **-1.06 pp** [-2.14, -0.04] | 0.57 pp | -0.017 |
| **age_group** | 75+ | 93.14% | 90.19% [86.77%, 92.91%] | **-2.95 pp** [-5.88, -0.96] | 1.33 pp | 82.94% | 90.04% [88.66%, 91.36%] | **+7.09 pp** [+5.72, +8.98] | 0.78 pp | +0.020 |
| **insurance_group** | Medicaid | 87.97% | 90.56% [83.28%, 95.95%] | **+2.59 pp** [-1.53, +7.46] | 2.30 pp | 91.62% | 89.97% [87.84%, 91.68%] | **-1.65 pp** [-3.10, -0.46] | 0.70 pp | +0.026 |
| **insurance_group** | Medicare | 91.45% | 90.18% [87.15%, 92.21%] | **-1.26 pp** [-3.11, +0.00] | 0.85 pp | 87.27% | 90.01% [89.16%, 91.26%] | **+2.74 pp** [+2.11, +3.38] | 0.33 pp | +0.006 |
| **insurance_group** | Other/Unknown (insurance) | 92.34% | 90.52% [80.65%, 98.37%] | **-1.81 pp** [-10.08, +5.37] | 4.14 pp | 92.91% | 90.01% [86.23%, 93.06%] | **-2.89 pp** [-6.39, -0.50] | 1.54 pp | -0.060 |
| **insurance_group** | Private | 86.60% | 90.25% [85.73%, 94.04%] | **+3.65 pp** [+0.82, +7.33] | 1.77 pp | 93.72% | 89.99% [88.38%, 91.52%] | **-3.73 pp** [-4.92, -2.57] | 0.60 pp | +0.017 |

### Exploratory Analysis: Race/Ethnicity and Sex
| Attribute | Subgroup | Global CC Death | Mondrian CC Death [Seed Range] | Paired Δ Death [seed 2.5-97.5%] | Δ Death Seed SD | Global CC Surv | Mondrian CC Surv [Seed Range] | Paired Δ Surv [seed 2.5-97.5%] | Δ Surv Seed SD | Δ Set Size |
|---|---|---|---|---|---|---|---|---|---|---|
| **race_group** | Asian | 88.64% | 91.18% [79.49%, 100.00%] | **+2.54 pp** [-9.04, +12.82] | 4.88 pp | 88.27% | 89.54% [84.71%, 92.95%] | **+1.28 pp** [-2.17, +4.05] | 1.55 pp | +0.058 |
| **race_group** | Black | 91.04% | 90.87% [82.52%, 96.63%] | **-0.17 pp** [-6.80, +4.85] | 2.98 pp | 89.07% | 90.04% [87.53%, 92.30%] | **+0.97 pp** [-0.64, +2.70] | 0.85 pp | +0.015 |
| **race_group** | Hispanic | 87.62% | 90.28% [78.14%, 100.00%] | **+2.67 pp** [-6.47, +12.82] | 4.69 pp | 92.53% | 90.48% [86.73%, 93.60%] | **-2.04 pp** [-5.31, +0.00] | 1.47 pp | +0.045 |
| **race_group** | Other/Unknown (race) | 91.35% | 90.20% [85.55%, 93.85%] | **-1.15 pp** [-4.43, +0.50] | 1.35 pp | 88.93% | 90.14% [88.54%, 91.98%] | **+1.21 pp** [+0.12, +2.21] | 0.57 pp | -0.004 |
| **race_group** | White | 89.61% | 90.08% [87.13%, 92.57%] | **+0.47 pp** [-0.88, +2.19] | 0.70 pp | 90.37% | 90.01% [89.17%, 90.93%] | **-0.36 pp** [-0.75, -0.02] | 0.20 pp | +0.005 |
| **sex** | Female | 90.48% | 89.89% [86.62%, 93.09%] | **-0.59 pp** [-2.72, +1.21] | 1.07 pp | 89.21% | 89.95% [88.55%, 91.08%] | **+0.74 pp** [-0.02, +1.36] | 0.40 pp | -0.002 |
| **sex** | Male | 89.85% | 90.38% [86.92%, 92.78%] | **+0.53 pp** [-1.14, +2.09] | 0.80 pp | 90.62% | 90.11% [89.04%, 91.19%] | **-0.52 pp** [-1.11, +0.09] | 0.30 pp | +0.004 |