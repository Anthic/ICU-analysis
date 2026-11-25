# Round-2 verification review (2026-11-25) - collated summary
Verdict: still major revision; IJMI-level after M1-M9. (Full reviewer texts were conversation-only; this file records the findings.)

## Fixed (factual, commit 2385c4f)
- Predictor counts 66/63 -> 52/47 (Sec 2.6, checklist)
- AUROC 0.874->0.866 -> 0.872->0.864
- Predictive values: pooled 1.3%/2.6% vs Mondrian 0.9%/3.2% (ratio ~2.0 -> ~3.7); Sec 3.6 and 4.3
- Insurance sentence (Medicare only follows age pattern)
- Set-size range -0.060..+0.058; "Negligible" header reworded
- R2 reporting: survivor vs death side, label-free vs recalibrated; Spearman 0.004
- "third decimal" wording; stale "remains to be written"; banner; typo; target venue line

## Open - need decision (accept/reject/defer)
- M1 code-status test has little power (7% of deaths flagged); reword abstract/3.6/4.4; fix window text (-6h..+24h) and item 229784
- M2 mechanism wording (death-side magnitude fails; abstract "why it differs")
- M3 add Gao 2026a / Zhong 2026 / Tasar 2025 to 4.2 + refs; rewrite Introduction aims
- M4 replication reporting: both intervals both configs; report transported age-Mondrian failure (young survivors 0.798, 75+ 0.840); external OSF/Zenodo deposit
- M5 Sec 3.7 duplicates 3.1-3.6; race/sex "small and unstable" overstated
- M6 abstract "enlarges sets in older patients"; "3.6 pp" is SD of paired gain
- M7 tests: tautological Mondrian=thresholds test, leakage test, independent_check circular, Windows paths, unpinned requirements
- M8 TRIPOD+AI gaps (hyperparameters, ethics, COI, eICU flow, missingness, Table 1 eICU)
- M9 reruns not bit-identical note; Bonferroni bound +0.15; V5 2.65%; refs [1],[7],[12]
