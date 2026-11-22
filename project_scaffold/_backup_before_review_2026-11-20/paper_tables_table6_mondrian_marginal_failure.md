# Table 6: Empirical Failure of Mondrian Marginal Conformal Prediction (EXPLORATORY)
*Source: `outputs/tables/phase5_subgroup_coverage_corrected_noflags_a010.csv` (100 seeds, noflags, $\alpha = 0.10$)*

> **Mechanism of Failure:** Group-conditional conformal prediction without class conditioning satisfies 90% overall group coverage but catastrophically undercovers patients who die (11.8% to 39.8%) because the ~89% survivor majority dominates each stratum's nonconformity threshold.

| Age Subgroup | Mondrian Marginal Death Coverage | Across-Seed Range [2.5%, 97.5%] | Mondrian Marginal Survivor Coverage |
|---|---|---|---|
| **18-49** | **11.77%** | [6.27%, 18.10%] | 95.33% |
| **50-64** | **18.15%** | [14.32%, 22.59%] | 97.05% |
| **65-74** | **22.52%** | [16.61%, 28.03%] | 97.98% |
| **75+** | **39.79%** | [35.12%, 45.26%] | 99.08% |