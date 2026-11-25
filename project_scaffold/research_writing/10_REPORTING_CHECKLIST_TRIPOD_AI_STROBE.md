# Reporting checklist status: TRIPOD+AI and STROBE (working draft, 2026-11-24)  [GENERATED — PENDING REVIEW]

Status key: Done = reported in `00_MANUSCRIPT_MASTER.md`; Partial = reported but incomplete; To do = missing. Items are listed by topic. Before submission, map each row to the official item numbers in the current TRIPOD+AI checklist (Collins et al., BMJ 2024) and the STROBE checklist (von Elm et al., 2007) from their own files; numbering is deliberately not used here because it was not verified in this session. The study is a prediction-model evaluation and uncertainty-quantification study (no new model is proposed for clinical use), so TRIPOD+AI items on model development apply to the baseline XGBoost model.

## STROBE (cohort study)
| Topic | Status | Where / what is missing |
|---|---|---|
| Design stated in title and abstract | Partial | Title now says "Retrospective Study"; abstract states design; add that analyses are exploratory where applicable |
| Background and rationale | Done | Introduction |
| Objectives (including pre-specified hypotheses) | Partial | Aims in Introduction; state that P1/P2 are pre-planned, not registered (Section 2.6) |
| Study design | Done | 2.1 |
| Setting, dates, data sources | Done | 2.1 (MIMIC-IV 2008–2022), 2.6 (eICU-CRD 2014–2015) |
| Participants: eligibility, selection | Done | 2.1 (first ICU stay, LOS ≥ 24 h, adult) |
| Participant flow numbers / diagram | Partial | Exclusion counts given for MIMIC-IV; a flow diagram and the eICU counts at each step are missing |
| Variables: outcome, exposures, predictors, groups | Partial | Outcome and predictors defined; give the coding of race/ethnicity and insurance groups and the rationale for the age cut points |
| Data sources / measurement | Partial | Describe how race and insurance were taken from MIMIC-IV tables and how eICU differs |
| Bias (selection, information, confounding) | Partial | Add hospice/code-status coding (Sections 2.11, 2.14), eICU differences, left-truncation by LOS ≥ 24 h |
| Study size | Done | All eligible patients |
| Quantitative variables | Partial | Age groups and 10-year bands described; justify |
| Statistical methods, subgroup and sensitivity analyses | Done | 2.4–2.13 |
| Missing data | Partial | Tree-model handling stated; give missingness by variable and the eICU temperature missingness (89%) in a table |
| Loss to follow-up / clustering | Done | Hospital-cluster bootstrap (2.9) |
| Descriptive data (Table 1) | Partial | Table 1 exists; add eICU column and hospice/code-status rows |
| Outcome data | Done | Mortality counts |
| Main results with precision | Done | Results; cluster-aware CIs for eICU contrasts |
| Other analyses | Done | Phases 8–14 |
| Key results, limitations, interpretation, generalisability | Partial | Discussion must be rewritten after the reframe; the limitations text is in place |
| Funding | To do | Add funding and role of funders |

## TRIPOD+AI (evaluation of a prediction model and its uncertainty sets)
| Topic | Status | Where / what is missing |
|---|---|---|
| Title and abstract (and abstract checklist) | Partial | Reframed; check the abstract against the TRIPOD+AI abstract checklist |
| Background, objectives | Done | Introduction |
| Data source, dates, participants, eligibility | Done | 2.1, 2.6 |
| Data preparation | Partial | Physiological plausibility filters stated; list units, time windows and harmonisation rules for eICU in a supplement |
| Outcome definition and assessment | Done | In-hospital mortality; hospice discharge coded as survival (limitations, 2.11) |
| Predictors | Done | 2.2; 52 predictors, harmonised 47 |
| Sample size justification | Partial | All eligible patients; add events-per-variable and the number of deaths per subgroup |
| Missing data handling | Partial | See STROBE row |
| Analytical methods: model type, hyperparameters, tuning, validation | Partial | Give the XGBoost hyperparameter table (from `03_train_baseline.py`, early stopping 50, 15% validation slice) |
| Class imbalance | Done | Class-conditional conformal calibration |
| Fairness | Done | Core of the paper: subgroup definitions, metrics (class-conditional coverage), mitigation (Mondrian), and the equal-odds equivalence (2.12) |
| Model output | Done | Probabilities and prediction sets |
| Training versus evaluation data, splits | Done | 50/25/25 splits, temporal split (2.13), external eICU |
| Ethical approval and consent | Partial | State waiver and DUA (2.1); add PhysioNet credentialing statement |
| Open science: code, data access, protocol, registration | To do | Add code repository statement, data access via PhysioNet, state not registered |
| Patient and public involvement | To do | State none |
| Participant flow and descriptive data | Partial | See STROBE rows |
| Model performance (discrimination, calibration, with CIs) | Done | AUROC, AUPRC, Brier, calibration slope and CITL with seed SD and bootstrap CIs |
| Model updating / recalibration | Done | eICU recalibration and class-conditional recalibration |
| Interpretation, limitations, usability | Partial | Discussion to be rewritten; state that sets are not validated for clinical decisions |
| Subgroup and fairness performance with uncertainty | Done | Tables 3–8 and Phase 9–14 notes |

## Items to add to the manuscript before submission
Flow diagram; funding statement; code and data availability; registration statement ("not registered; P1/P2 pre-planned"); hyperparameter table; missingness table; ethics statement; list of subgroup coding rules; PPI statement.
