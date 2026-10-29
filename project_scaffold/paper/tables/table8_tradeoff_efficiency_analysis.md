# Table 8: Conformal Fairness vs Efficiency Trade-off Analysis
*Source: `outputs/tables/phase7_tradeoff_efficiency_analysis.csv` (100 seeds, noflags, alpha = 0.10)*
*Comparing Global Class-Conditional Split Conformal vs Mondrian Class-Conditional Calibration*

> **Key Insight:** Achieving subgroup fairness (restoring nominal 90% coverage for vulnerable groups such as age 18–49 from 84.06% to 90.42%) incurs minimal set-size cost (at most +0.058 set-size increase, or +4.7% relative change).

| Protected Dimension | Subgroup | Global CC Death | Mondrian CC Death | Δ Death Cov | Global Set Size | Mondrian Set Size | Δ Set Size (Efficiency Cost) | % Set Size Change | Global Share {0,1} | Mondrian Share {0,1} |
|---|---|---|---|---|---|---|---|---|---|---|
| **age_group** | 18-49 | 84.06% | 90.42% | +6.36 pp | 1.147 | 1.176 | **+0.029** | +2.57% | 14.68% | 17.62% |
| **age_group** | 50-64 | 87.22% | 90.07% | +2.85 pp | 1.224 | 1.247 | **+0.023** | +1.84% | 22.44% | 24.70% |
| **age_group** | 65-74 | 90.66% | 90.43% | -0.23 pp | 1.262 | 1.245 | **-0.017** | -1.38% | 26.22% | 24.47% |
| **age_group** | 75+ | 93.14% | 90.19% | -2.95 pp | 1.356 | 1.377 | **+0.020** | +1.49% | 35.63% | 37.65% |
| **insurance_group** | Medicaid | 87.97% | 90.56% | +2.59 pp | 1.224 | 1.249 | **+0.026** | +2.12% | 22.35% | 24.94% |
| **insurance_group** | Medicare | 91.45% | 90.18% | -1.26 pp | 1.311 | 1.318 | **+0.006** | +0.47% | 31.14% | 31.76% |
| **insurance_group** | Other/Unknown (insurance) | 92.34% | 90.52% | -1.81 pp | 1.194 | 1.134 | **-0.060** | -5.04% | 19.38% | 13.39% |
| **insurance_group** | Private | 86.60% | 90.25% | +3.65 pp | 1.181 | 1.198 | **+0.017** | +1.44% | 18.07% | 19.77% |
| **race_group** | Asian | 88.64% | 91.18% | +2.54 pp | 1.240 | 1.299 | **+0.058** | +4.72% | 24.01% | 29.85% |
| **race_group** | Black | 91.04% | 90.87% | -0.17 pp | 1.254 | 1.269 | **+0.015** | +1.23% | 25.36% | 26.90% |
| **race_group** | Hispanic | 87.62% | 90.28% | +2.67 pp | 1.227 | 1.272 | **+0.045** | +3.67% | 22.73% | 27.24% |
| **race_group** | Other/Unknown (race) | 91.35% | 90.20% | -1.15 pp | 1.253 | 1.249 | **-0.004** | -0.28% | 25.26% | 24.91% |
| **race_group** | White | 89.61% | 90.08% | +0.47 pp | 1.261 | 1.266 | **+0.005** | +0.40% | 26.13% | 26.63% |
| **sex** | Female | 90.48% | 89.89% | -0.59 pp | 1.271 | 1.268 | **-0.002** | -0.18% | 27.07% | 26.85% |
| **sex** | Male | 89.85% | 90.38% | +0.53 pp | 1.247 | 1.251 | **+0.004** | +0.34% | 24.67% | 25.10% |