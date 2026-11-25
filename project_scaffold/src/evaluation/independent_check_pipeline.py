"""Independent re-derivation check (seeds 0-2): rebuilds split, model, calibration thresholds and prediction sets from raw features,
with the order-statistic threshold written out by hand (no src.conformal.utils), and compares with the stored Phase 3 sets.

Unlike independent_check.py (which re-aggregates stored sets), this re-derives the thresholds. XGBoost reruns are not bit-identical, so
agreement is judged by overall class-conditional coverage within 0.01 of the stored values; patient-level set agreement is reported but not used as a pass criterion (library-version score differences flip patients close to the threshold; observed 92.8% for seed 0 with xgboost 3.2.0).
Usage: python src/evaluation/independent_check_pipeline.py [--seeds 3]"""
import argparse, importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def thr(v, alpha=0.10):
    v = np.sort(np.asarray(v)); n = len(v); k = int(np.ceil((n + 1) * (1 - alpha)))
    return np.inf if k > n else v[k - 1]


def main(n_seeds):
    baseline = load("baseline", "src/models/03_train_baseline.py"); ext = load("extval", "src/evaluation/06_external_validation.py")
    mimic = ext.read_table(ext.MIMIC_FEATURES)
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    X = ext.encode(mimic, cols); y = mimic["mortality"].astype(int).to_numpy(); age = mimic["age_group"].astype(str).to_numpy()
    stored = pd.read_parquet(ROOT / "outputs/results/phase3_test_predictions_noflags_a010.parquet",
                             columns=["seed", "stay_id", "set_classcond_has0", "set_classcond_has1"])
    ok = True
    for seed in range(n_seeds):
        tr, ca, te = baseline.split_indices(mimic, seed)
        model = baseline.fit_baseline(X.iloc[tr], y[tr], seed)
        pc, pt = model.predict_proba(X.iloc[ca])[:, 1], model.predict_proba(X.iloc[te])[:, 1]
        q0 = thr(pc[y[ca] == 0]); q1 = thr((1 - pc)[y[ca] == 1])          # survivor score = p ; death score = 1-p
        h0, h1 = pt <= q0, (1 - pt) <= q1
        st = pd.DataFrame({"stay_id": mimic["stay_id"].to_numpy()[te], "h0": h0, "h1": h1}).merge(
            stored[stored.seed == seed], on="stay_id", how="inner")
        agree = float(((st.h0 == st.set_classcond_has0.astype(bool)) & (st.h1 == st.set_classcond_has1.astype(bool))).mean())
        yt = y[te]
        cov_d = h1[yt == 1].mean(); cov_s = h0[yt == 0].mean()
        sd = stored[stored.seed == seed].merge(pd.DataFrame({"stay_id": mimic["stay_id"].to_numpy()[te], "y": yt}), on="stay_id")
        sd_d = sd.loc[sd.y == 1, "set_classcond_has1"].mean(); sd_s = sd.loc[sd.y == 0, "set_classcond_has0"].mean()
        good = len(st) == len(te) and abs(cov_d - sd_d) < 0.01 and abs(cov_s - sd_s) < 0.01
        ok &= good
        print(f"seed {seed}: n={len(st)}/{len(te)} set agreement {agree:.4f}; death cov {cov_d:.4f} vs stored {sd_d:.4f}; "
              f"surv cov {cov_s:.4f} vs stored {sd_s:.4f} -> {'PASS' if good else 'FAIL'}")
    print("FINAL:", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=3); main(ap.parse_args().seeds)
