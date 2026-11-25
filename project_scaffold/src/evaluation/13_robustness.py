"""
Phase 13 (Analysis 5): robustness of the age coverage pattern (MIMIC-IV).
File: src/evaluation/13_robustness.py
Parts:
  temporal : train 2008-2013, calibrate 2014-2016, test 2017-2022 (anchor_year_group); XGBoost; pooled class-conditional and age Mondrian.
  logistic : second model class (median-impute + standardise + L2 logistic regression), random 50/25/25 splits.
  alpha    : XGBoost, alpha in {0.05, 0.10, 0.15, 0.20}, pooled class-conditional and age Mondrian.
  placebo  : (i) age-group labels randomly permuted among patients (null: no gap expected); (ii) one random non-age predictor dropped
             (placebo for the age-blind ablation) vs age dropped vs full model, same splits.
Outputs: outputs/tables/phase13_{part}_rows{tag}.csv, phase13_{part}_summary{tag}.csv ; outputs/results/phase13_summary{tag}.json (gap summaries)
Usage: python src/evaluation/13_robustness.py --part temporal|logistic|alpha|placebo --seeds 100 [--tag x]
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.conformal.utils import (fit_class_conditional, prediction_sets, fit_mondrian_class_conditional, prediction_sets_mondrian)  # noqa: E402


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


baseline = load("baseline", "src/models/03_train_baseline.py")
ext = load("extval", "src/evaluation/06_external_validation.py")
TABLES, RESULTS = ROOT / "outputs" / "tables", ROOT / "outputs" / "results"
AGES = ["18-49", "50-64", "65-74", "75+"]


def cov_rows(base, y, sets, g, extra=None):
    out = []; hit = np.where(y == 1, sets[:, 1], sets[:, 0]); size = sets.sum(1)
    for sg in ["All"] + AGES:
        m = np.ones(len(y), bool) if sg == "All" else g == sg
        d, v = (y == 1) & m, (y == 0) & m
        out.append(dict(**base, stratum=sg, n=int(m.sum()), n_deaths=int(d.sum()), cov_deaths=float(hit[d].mean()) if d.any() else np.nan,
                        cov_surv=float(hit[v].mean()) if v.any() else np.nan, set_size=float(size[m].mean()), **(extra or {})))
    return out


def two_methods(base, yc, pc, gc, yt, pt, gt, alpha, extra=None):
    rows = []
    rows += cov_rows(dict(base, method="pooled", alpha=alpha), yt, prediction_sets(pt, fit_class_conditional(yc, pc, alpha)), gt, extra)
    rows += cov_rows(dict(base, method="mondrian_age", alpha=alpha), yt,
                     prediction_sets_mondrian(pt, gt, fit_mondrian_class_conditional(yc, pc, gc, alpha)), gt, extra)
    return rows


def run(part, n_seeds, tag):
    t0 = time.time(); sfx = f"_{tag}" if tag else ""
    mimic = ext.read_table(ext.MIMIC_FEATURES)
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    X = ext.encode(mimic, cols); y = mimic["mortality"].astype(int).to_numpy(); age = mimic["age_group"].astype(str).to_numpy()
    rows = []
    if part == "temporal":
        yg = mimic["anchor_year_group"].astype(str)
        tr = np.where(yg.isin(["2008 - 2010", "2011 - 2013"]))[0]; ca = np.where(yg == "2014 - 2016")[0]
        te = np.where(yg.isin(["2017 - 2019", "2020 - 2022"]))[0]
        for seed in range(n_seeds):
            model = baseline.fit_baseline(X.iloc[tr], y[tr], seed)
            pc, pt = model.predict_proba(X.iloc[ca])[:, 1], model.predict_proba(X.iloc[te])[:, 1]
            rows += two_methods(dict(seed=seed, part=part, variant="temporal_test_2017_2022"), y[ca], pc, age[ca], y[te], pt, age[te], 0.10,
                                dict(auroc=float(roc_auc_score(y[te], pt)), prevalence=float(y[te].mean())))
            for lab in ("2017 - 2019", "2020 - 2022"):
                mm = (yg.iloc[te] == lab).to_numpy()
                rows += two_methods(dict(seed=seed, part=part, variant=f"temporal_test_{lab.replace(' ', '')}"), y[ca], pc, age[ca], y[te][mm], pt[mm], age[te][mm], 0.10,
                                    dict(auroc=float(roc_auc_score(y[te][mm], pt[mm])), prevalence=float(y[te][mm].mean())))
    else:
        rng_master = np.random.default_rng(13)
        non_age = [c for c in cols if c != "anchor_age"]
        for seed in range(n_seeds):
            tr, ca, te = baseline.split_indices(mimic, seed)
            if part == "logistic":
                lr = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
                lr.fit(X.iloc[tr], y[tr]); pc, pt = lr.predict_proba(X.iloc[ca])[:, 1], lr.predict_proba(X.iloc[te])[:, 1]
                rows += two_methods(dict(seed=seed, part=part, variant="logistic"), y[ca], pc, age[ca], y[te], pt, age[te], 0.10,
                                    dict(auroc=float(roc_auc_score(y[te], pt)), prevalence=float(y[te].mean())))
            else:
                model = baseline.fit_baseline(X.iloc[tr], y[tr], seed)
                pc, pt = model.predict_proba(X.iloc[ca])[:, 1], model.predict_proba(X.iloc[te])[:, 1]
                if part == "alpha":
                    for a in (0.05, 0.10, 0.15, 0.20):
                        rows += two_methods(dict(seed=seed, part=part, variant="xgb"), y[ca], pc, age[ca], y[te], pt, age[te], a)
                if part == "placebo":
                    rows += two_methods(dict(seed=seed, part=part, variant="full"), y[ca], pc, age[ca], y[te], pt, age[te], 0.10)
                    # (i) permuted age labels
                    rng = np.random.default_rng(1000 + seed)
                    pa_c, pa_t = rng.permutation(age[ca]), rng.permutation(age[te])
                    rows += two_methods(dict(seed=seed, part=part, variant="placebo_permuted_age_labels"), y[ca], pc, pa_c, y[te], pt, pa_t, 0.10)
                    # (ii) drop age / drop one random non-age predictor
                    drop_rnd = non_age[int(rng_master.integers(len(non_age)))]
                    for vname, dcol in (("age_blind", "anchor_age"), ("drop_random_predictor", drop_rnd)):
                        cc = [c for c in cols if c != dcol]
                        m2 = baseline.fit_baseline(X[cc].iloc[tr], y[tr], seed)
                        rows += two_methods(dict(seed=seed, part=part, variant=vname), y[ca], m2.predict_proba(X[cc].iloc[ca])[:, 1], age[ca],
                                            y[te], m2.predict_proba(X[cc].iloc[te])[:, 1], age[te], 0.10, dict(dropped=dcol))
            if (seed + 1) % 10 == 0:
                print(f"  seed {seed + 1}/{n_seeds} ({time.time() - t0:.0f}s)", flush=True)
    df = pd.DataFrame(rows); df.to_csv(TABLES / f"phase13_{part}_rows{sfx}.csv", index=False)
    keys = [k for k in ("variant", "method", "alpha", "stratum") if k in df.columns]
    summ = df.groupby(keys).agg(n=("n", "mean"), n_deaths=("n_deaths", "mean"), cov_deaths=("cov_deaths", "mean"), sd_deaths=("cov_deaths", "std"),
                                cov_surv=("cov_surv", "mean"), sd_surv=("cov_surv", "std"), set_size=("set_size", "mean")).reset_index()
    summ.to_csv(TABLES / f"phase13_{part}_summary{sfx}.csv", index=False)
    # per-seed max age gap
    a = df[df.stratum.isin(AGES)].copy(); a["gd"] = (a.cov_deaths - (1 - a.alpha)).abs(); a["gs"] = (a.cov_surv - (1 - a.alpha)).abs()
    gap = a.groupby(["variant", "method", "alpha", "seed"]).agg(gd=("gd", "max"), gs=("gs", "max")).reset_index()
    gs = gap.groupby(["variant", "method", "alpha"]).agg(max_gap_deaths=("gd", "mean"), sd_gd=("gd", "std"), max_gap_surv=("gs", "mean"), sd_gs=("gs", "std")).reset_index()
    (RESULTS / f"phase13_{part}_gaps{sfx}.json").write_text(gs.to_json(orient="records", indent=1))
    pd.set_option("display.width", 250)
    print(summ.round(3).to_string(index=False)); print(gs.round(4).to_string(index=False)); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--part", required=True, choices=["temporal", "logistic", "alpha", "placebo"])
    ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--tag", default="")
    a = ap.parse_args(); run(a.part, a.seeds, a.tag)
