"""
Builds a tiny FABRICATED eICU-schema dataset (6 tables) so the Phase 6 scripts can be smoke-tested
before the real eICU-CRD download is available.

*** SYNTHETIC DATA FOR PIPELINE TESTING ONLY. Any number produced from it is meaningless and must
*** never appear in the paper. Output goes to a throw-away folder, never to data/raw/eicu.

Usage:
    python tests/synthetic_eicu_smoke.py <out_dir> [n_patients]
    EICU_PATH=<out_dir> python src/data_processing/06_build_eicu_features.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

out = Path(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(0)

ids = np.arange(1000, 1000 + n)
age = rng.integers(16, 95, n)
sex = rng.choice(["Male", "Female"], n)
risk = 1 / (1 + np.exp(-(-2.2 + 0.04 * (age - 60) + rng.normal(0, 1, n))))
dead = rng.random(n) < risk
pat = pd.DataFrame({
    "patientunitstayid": ids, "patienthealthsystemstayid": ids + 5000, "uniquepid": [f"U{i}" for i in ids],
    "hospitalid": rng.integers(1, 41, n), "gender": sex,
    "age": np.where(age > 89, "> 89", age.astype(str)),
    "ethnicity": rng.choice(["Caucasian", "African American", "Hispanic", "Asian", "Native American", "Other/Unknown"],
                            n, p=[.7, .12, .06, .04, .02, .06]),
    "hospitaldischargeyear": rng.choice([2014, 2015], n), "unitvisitnumber": 1,
    "unitdischargeoffset": rng.integers(600, 6000, n),
    "hospitaldischargestatus": np.where(dead, "Expired", "Alive"),
})
dup = pat.sample(60, random_state=1).copy()          # repeat stays of same patient -> must be dropped
dup["patientunitstayid"] += 90000
dup["unitvisitnumber"] = 2
pat = pd.concat([pat, dup], ignore_index=True)
pat.to_csv(out / "patient.csv.gz", index=False)

sick = (risk - risk.mean()) / risk.std()
rows = []
for k, pid in enumerate(ids):
    for off in range(0, 1500, 120):
        rows.append((pid, off, 85 + 6 * sick[k] + rng.normal(0, 8), 18 + 2 * sick[k] + rng.normal(0, 3),
                     96 - 1.5 * sick[k] + rng.normal(0, 2), 36.8 + rng.normal(0, .5),
                     np.nan if rng.random() < .7 else 120 - 8 * sick[k] + rng.normal(0, 12),
                     np.nan if rng.random() < .7 else 70 + rng.normal(0, 8),
                     np.nan if rng.random() < .7 else 85 + rng.normal(0, 8)))
pd.DataFrame(rows, columns=["patientunitstayid", "observationoffset", "heartrate", "respiration", "sao2",
                            "temperature", "systemicsystolic", "systemicdiastolic", "systemicmean"]
             ).to_csv(out / "vitalPeriodic.csv.gz", index=False)

rows = [(pid, off, 118 + rng.normal(0, 15), 68 + rng.normal(0, 9), 84 + rng.normal(0, 9))
        for pid in ids for off in (30, 400, 900)]
pd.DataFrame(rows, columns=["patientunitstayid", "observationoffset", "noninvasivesystolic",
                            "noninvasivediastolic", "noninvasivemean"]).to_csv(out / "vitalAperiodic.csv.gz", index=False)

names = {"lactate": (1.5, .8), "creatinine": (1.1, .5), "WBC x 1000": (10, 3), "platelets x 1000": (220, 60),
         "BUN": (22, 10), "glucose": (130, 30), "potassium": (4.1, .4), "sodium": (139, 4), "bicarbonate": (24, 3)}
rows = []
for k, pid in enumerate(ids):
    for nm, (mu, sd) in names.items():
        if rng.random() < .85:
            rows.append((pid, int(rng.integers(-300, 1400)), nm, mu + sd * (0.4 * sick[k] + rng.normal())))
pd.DataFrame(rows, columns=["patientunitstayid", "labresultoffset", "labname", "labresult"]
             ).to_csv(out / "lab.csv.gz", index=False)

rows = [(pid, int(rng.integers(0, 1400)), "GCS Total", int(np.clip(round(14 - 2 * sick[k] + rng.normal(0, 2)), 3, 15)))
        for k, pid in enumerate(ids) if rng.random() < .8]
pd.DataFrame(rows, columns=["patientunitstayid", "nursingchartoffset", "nursingchartcelltypevalname",
                            "nursingchartvalue"]).to_csv(out / "nurseCharting.csv.gz", index=False)

pd.DataFrame({"patientunitstayid": ids, "intubated": (rng.random(n) < .15 + .1 * (sick > 1)).astype(int),
              "eyes": rng.integers(1, 5, n), "motor": rng.integers(1, 7, n), "verbal": rng.integers(1, 6, n)}
             ).to_csv(out / "apacheApsVar.csv.gz", index=False)
print(f"synthetic eICU-schema tables written to {out} (FAKE DATA, testing only)")
