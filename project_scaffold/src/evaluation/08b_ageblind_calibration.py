"""Phase 8b: age-blind vs with-age model, MIMIC-IV test split: AUROC and calibration-in-the-large (CITL = mean p - mean y) by age group,
plus pooled class-conditional coverage by age. Replaces the earlier unsaved 10-seed check.
Usage: python src/evaluation/08b_ageblind_calibration.py --seeds 100 [--start 0] [--tag _s0]
Outputs: outputs/tables/phase8b_ageblind_rows{tag}.csv  (merge chunk files with the same columns for the final table)."""
from __future__ import annotations
import argparse, importlib.util, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.conformal.utils import fit_class_conditional, prediction_sets  # noqa: E402


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


baseline = load("baseline", "src/models/03_train_baseline.py")
ext = load("extval", "src/evaluation/06_external_validation.py")


def main(n_seeds, start, tag, alpha=0.10):
    t0 = time.time()
    mimic = ext.read_table(ext.MIMIC_FEATURES)
    cols_all = baseline.predictor_columns(mimic, use_measured_flags=False)
    models = {"with_age": cols_all, "age_blind": [c for c in cols_all if not c.startswith("anchor_age")]}
    y_all = mimic["mortality"].astype(int).to_numpy(); ag_all = mimic["age_group"].astype(str).to_numpy()
    rows = []
    for seed in range(start, n_seeds):
        tr, ca, te = baseline.split_indices(mimic, seed)
        for name, cols in models.items():
            X = ext.encode(mimic, cols)
            model = baseline.fit_baseline(X.iloc[tr], y_all[tr], seed)
            pc, pt = model.predict_proba(X.iloc[ca])[:, 1], model.predict_proba(X.iloc[te])[:, 1]
            yt, at = y_all[te], ag_all[te]
            sets = prediction_sets(pt, fit_class_conditional(y_all[ca], pc, alpha)); hit = np.where(yt == 1, sets[:, 1], sets[:, 0])
            for sg in ["All", "18-49", "50-64", "65-74", "75+"]:
                m = np.ones(len(yt), bool) if sg == "All" else at == sg
                d, v = (yt == 1) & m, (yt == 0) & m
                rows.append(dict(seed=seed, model=name, stratum=sg, auroc=roc_auc_score(yt[m], pt[m]), citl=float(pt[m].mean() - yt[m].mean()),
                                 cov_deaths=float(hit[d].mean()), cov_surv=float(hit[v].mean())))
        if (seed + 1) % 10 == 0:
            print(f"seed {seed + 1}/{n_seeds} {time.time() - t0:.0f}s", flush=True)
    out = ROOT / "outputs" / "tables" / f"phase8b_ageblind_rows{tag}.csv"
    pd.DataFrame(rows).to_csv(out, index=False); print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=100); ap.add_argument("--start", type=int, default=0); ap.add_argument("--tag", default="")
    a = ap.parse_args(); main(a.seeds, a.start, a.tag)
