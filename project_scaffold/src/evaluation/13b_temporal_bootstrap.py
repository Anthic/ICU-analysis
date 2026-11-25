"""Temporal split uncertainty: one fixed split (train 2008-2013, calibrate 2014-2016, test 2017-2022) and one model (seed 0);
bootstrap patients in the calibration and test sets (B resamples), recompute max death-side and survivor-side age gaps for pooled and age-Mondrian
calibration, and report the paired Mondrian-minus-pooled difference with 95% percentile intervals.
Usage: python src/evaluation/13b_temporal_bootstrap.py --boot 500"""
import argparse, importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from src.conformal.utils import fit_class_conditional, prediction_sets, fit_mondrian_class_conditional, prediction_sets_mondrian  # noqa: E402
AGES = ["18-49", "50-64", "65-74", "75+"]


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def gaps(y, sets, g, alpha=0.10):
    hit = np.where(y == 1, sets[:, 1], sets[:, 0]); gd, gs = [], []
    for a in AGES:
        d, v = (y == 1) & (g == a), (y == 0) & (g == a)
        if d.any(): gd.append(abs(hit[d].mean() - (1 - alpha)))
        if v.any(): gs.append(abs(hit[v].mean() - (1 - alpha)))
    return max(gd), max(gs)


def main(B):
    baseline = load("baseline", "src/models/03_train_baseline.py"); ext = load("extval", "src/evaluation/06_external_validation.py")
    mimic = ext.read_table(ext.MIMIC_FEATURES)
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    X = ext.encode(mimic, cols); y = mimic["mortality"].astype(int).to_numpy(); age = mimic["age_group"].astype(str).to_numpy()
    yg = mimic["anchor_year_group"].astype(str)
    tr = np.where(yg.isin(["2008 - 2010", "2011 - 2013"]))[0]; ca = np.where(yg == "2014 - 2016")[0]
    te = np.where(yg.isin(["2017 - 2019", "2020 - 2022"]))[0]
    model = baseline.fit_baseline(X.iloc[tr], y[tr], 0)
    pc, pt = model.predict_proba(X.iloc[ca])[:, 1], model.predict_proba(X.iloc[te])[:, 1]
    yc, yt, gc, gt = y[ca], y[te], age[ca], age[te]
    rng = np.random.default_rng(2026); rows = []
    for b in range(B):
        ic = rng.integers(0, len(ca), len(ca)); it = rng.integers(0, len(te), len(te))
        s_pool = prediction_sets(pt[it], fit_class_conditional(yc[ic], pc[ic], 0.10))
        s_mond = prediction_sets_mondrian(pt[it], gt[it], fit_mondrian_class_conditional(yc[ic], pc[ic], gc[ic], 0.10))
        gp, mp = gaps(yt[it], s_pool, gt[it]), gaps(yt[it], s_mond, gt[it])
        rows.append(dict(pool_d=gp[0], pool_s=gp[1], mond_d=mp[0], mond_s=mp[1]))
    df = pd.DataFrame(rows); df["diff_d"] = df.mond_d - df.pool_d; df["diff_s"] = df.mond_s - df.pool_s
    out = {c: dict(mean=float(df[c].mean()), lo=float(df[c].quantile(.025)), hi=float(df[c].quantile(.975))) for c in df.columns}
    out["share_boot_mondrian_gap_smaller_deaths"] = float((df.diff_d < 0).mean()); out["B"] = B
    (ROOT / "outputs/results/phase13_temporal_bootstrap.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--boot", type=int, default=500); main(ap.parse_args().boot)
