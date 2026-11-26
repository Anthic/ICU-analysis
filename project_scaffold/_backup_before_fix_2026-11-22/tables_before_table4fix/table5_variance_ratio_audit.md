# Table 5: Across-Seed Standard Deviation Comparison & Variance Ratios
*Source: Computed across identical 100 random splits from per-seed tables*

> **Key Finding:** Mondrian seed SD is 7–50% larger than global (ratio 1.07–1.50; 1.80 for Other/Unknown insurance), as expected because the calibration cell adds sampling noise.

| Dimension | Subgroup | Global CC Death Mean | Global Seed SD | Mondrian CC Death Mean | Mondrian Seed SD | Ratio (Mondrian/Global SD) | Mondrian Seed Range [2.5%, 97.5%] |
|---|---|---|---|---|---|---|---|
| **age_group** | 18-49 | 84.06% | 3.03% | 90.42% | 3.49% | **1.15×** | [82.25%, 96.09%] |
| **age_group** | 50-64 | 87.22% | 2.09% | 90.07% | 2.23% | **1.07×** | [86.03%, 94.33%] |
| **age_group** | 65-74 | 90.66% | 1.88% | 90.43% | 2.22% | **1.18×** | [86.34%, 94.52%] |
| **age_group** | 75+ | 93.14% | 1.15% | 90.19% | 1.71% | **1.49×** | [86.77%, 92.91%] |
| **insurance_group** | Medicaid | 87.97% | 2.56% | 90.56% | 3.18% | **1.24×** | [83.28%, 95.95%] |
| **insurance_group** | Medicare | 91.45% | 1.07% | 90.18% | 1.22% | **1.15×** | [87.15%, 92.21%] |
| **insurance_group** | Other/Unknown (insurance) | 92.34% | 2.92% | 90.52% | 5.28% | **1.80×** | [80.65%, 98.37%] |
| **insurance_group** | Private | 86.60% | 2.12% | 90.25% | 2.38% | **1.12×** | [85.73%, 94.04%] |
| **race_group** | Asian | 88.64% | 4.64% | 91.18% | 5.75% | **1.24×** | [79.49%, 100.00%] |
| **race_group** | Black | 91.04% | 2.36% | 90.87% | 3.53% | **1.50×** | [82.52%, 96.63%] |
| **race_group** | Hispanic | 87.62% | 5.18% | 90.28% | 6.57% | **1.27×** | [78.14%, 100.00%] |
| **race_group** | Other/Unknown (race) | 91.35% | 1.51% | 90.20% | 2.07% | **1.37×** | [85.55%, 93.85%] |
| **race_group** | White | 89.61% | 1.16% | 90.08% | 1.37% | **1.18×** | [87.13%, 92.57%] |
| **sex** | Female | 90.48% | 1.33% | 89.89% | 1.70% | **1.28×** | [86.62%, 93.09%] |
| **sex** | Male | 89.85% | 1.22% | 90.38% | 1.48% | **1.22×** | [86.92%, 92.78%] |

### Variance Analysis & Test-Sampling Variation:
- The seed SD of about 3 pp for age 18-49 is mainly test-sampling variation from about 151 test deaths per split.
- Mondrian calibration adds stratum-specific calibration-cell sampling noise, slightly increasing seed SD from 3.03% to 3.49% (ratio 1.15×).