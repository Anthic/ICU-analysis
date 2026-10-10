# ICU Conformal Fairness Project

Group-Conditional Conformal Prediction for Equitable Uncertainty
Quantification in ICU Mortality Risk Prediction (MIMIC-IV / eICU-CRD).

## Setup
1. Place downloaded MIMIC-IV files in `data/raw/mimic-iv/hosp/` and
   `data/raw/mimic-iv/icu/` (gzip CSVs, as downloaded from PhysioNet).
2. Place eICU-CRD files in `data/raw/eicu/`.
3. `pip install -r requirements.txt`
4. Open this folder in Antigravity. The agent reads `.agent/instructions.md`
   and `.agent/workflow.md` automatically — point it at a phase from
   `workflow.md` and it will know which folder to write to and what the
   expected output is.

## Folder map
```
.agent/            agent instructions, workflow, coding rules
data/raw/           read-only source data (MIMIC-IV, eICU)
data/processed/     cleaned/merged/feature tables
src/data_processing/  cohort + feature engineering scripts
src/models/           baseline ML model training
src/conformal/         split + Mondrian conformal prediction
src/evaluation/        coverage audits, external validation, trade-offs
notebooks/           exploratory analysis only
outputs/figures/     generated plots
outputs/tables/      generated result tables
outputs/results/     metrics, logs, intermediate result files
paper/               manuscript drafts
```

See `.agent/workflow.md` for the phase-by-phase research plan.
