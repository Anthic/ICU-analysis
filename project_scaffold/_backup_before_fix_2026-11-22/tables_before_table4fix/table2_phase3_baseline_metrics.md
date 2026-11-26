# Table 2: Phase 3 Baseline Model & Split Conformal Prediction Performance
*Source: `outputs/results/phase3_baseline_metrics_noflags_a010.json` (100 random train/cal/test splits, noflags, nominal $\alpha = 0.10$)*

| Performance Metric | Mean | Split SD | Across-Seed [2.5th, 97.5th %ile] |
|---|---|---|---|
| **AUROC** | 0.8726 | 0.0042 | [0.8635, 0.8801] |
| **AUPRC** | 0.5023 | 0.0118 | [0.4786, 0.5255] |
| **Brier score** | 0.0706 | 0.0010 | [0.0686, 0.0725] |
| **Calibration slope** | 1.0033 | 0.0383 | [0.9370, 1.0832] |
| **Calibration intercept** | 0.0383 | 0.0610 | [-0.0654, 0.1518] |
| **Marginal coverage overall** | 90.02% | 0.25% | [89.55%, 90.49%] |
| **Marginal coverage (deaths, y=1)** | 23.52% | 1.62% | [20.51%, 26.47%] |
| **Marginal coverage (survivors, y=0)** | 97.94% | 0.18% | [97.65%, 98.25%] |
| **Class-conditional coverage overall** | 90.03% | 0.35% | [89.36%, 90.64%] |
| **Class-conditional coverage (deaths, y=1)** | 90.14% | 1.05% | [87.57%, 92.07%] |
| **Class-conditional coverage (survivors, y=0)** | 90.02% | 0.38% | [89.28%, 90.70%] |
| **Mean set size (class-conditional)** | 1.2570 | 0.0131 | [1.2331, 1.2814] |
| **Share {0, 1} sets (class-conditional)** | 25.70% | 1.31% | [23.31%, 28.14%] |

> Note: Across-seed percentiles reflect split-to-split sampling variation (random train/calibration/test splits), not patient-level confidence intervals.