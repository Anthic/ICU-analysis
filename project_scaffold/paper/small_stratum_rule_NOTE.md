# Small-stratum rule: variance-versus-bias criterion (replaces the "40 calibration deaths" rule), 2026-11-24  [GENERATED — PENDING REVIEW]

Source data: `outputs/tables/phase10_cells_{main_100,harm_100}.csv` (103 eICU hospitals, thresholds fitted on all eICU, raw scores). Responds to review issue M5: the earlier rule compared hospital-specific with pooled thresholds across hospitals and was not a valid minimum-size rule.

## Criterion
For a stratum with n_d calibration deaths, a stratum-specific death threshold has coverage sampling SD of about sqrt(0.09 / n_d) (binomial, p(1-p) about 0.09 at 90% coverage), while the pooled threshold has a bias of delta = (the stratum's true coverage under the pooled threshold) - 0.90. Stratum-specific calibration reduces the mean squared deviation from 0.90 only if delta^2 > 0.09 / n_d, i.e. n_d > n* = 0.09 / delta^2. The same applies to survivors with the survivor count. At alpha = 0.10, a finite conformal threshold also needs n_d >= 9 (smaller strata give an infinite threshold, i.e. always include the label).

## Estimates from the eICU hospitals
Observed SD across hospitals of death coverage under the pooled threshold: 0.052 (primary model), 0.050 (harmonised). Expected sampling SD from binomial noise given each hospital's deaths (mean 78.6, median 59, range 20-320): 0.043 and 0.040. Implied between-hospital SD of true coverage (delta): sqrt(0.052^2 - 0.043^2) = 0.029 (primary), 0.031 (harmonised), giving n* of about 106 and 92 deaths. Worked values: delta 0.01 -> n* 900; 0.02 -> 225; 0.03 -> 100; 0.05 -> 36; 0.08 -> 14.

## Reading for the paper
1. Replace the 40-death rule by: use stratum-specific (Mondrian) calibration when the stratum's expected shortfall delta under the pooled threshold satisfies n_d > 0.09 / delta^2; with hospital-level shortfalls of about 0.03 this means roughly 90-110 calibration deaths per stratum, and with an age-type shortfall of about 0.05-0.10 (MIMIC age strata) 14-36 deaths suffice. Below roughly 10 deaths the threshold is infinite or unstable.
2. This is a heuristic based on one database (hospitals as strata), an estimate of delta that is itself noisy, and a standard-deviation decomposition that assumes binomial noise and uses seed-averaged cells; treat the numbers as indicative.
3. The earlier empirical observation (hospital-specific thresholds did not beat the pooled threshold in mean absolute deviation below about 40-80 deaths) is consistent with n* of about 100 but was not a derived rule.
