"""
Phase 8: (A) risk-bin-conditioned Mondrian baseline and (B) age-blind ablation (exploratory).
File: src/evaluation/08_alternatives_ablation.py

A. Does calibrating by predicted-risk bin x class (NO demographic attribute used) close the age
   coverage gap as well as age x class Mondrian? Compared on coverage by age/race/sex(/insurance) and set size.
B. If age is removed from the predictors, does the age gap shrink (is it the age feature / its base-rate
   effect), or does it persist because of physiology-driven risk differences?

Datasets: MIMIC internal (cal split -> test split) and eICU (eICU-cal half -> eICU-test half, patient split),
model trained on MIMIC train split as in Phase 6.
Variants: cc_global, mondrian_age, riskbin5, riskbin10 (risk bins = quantiles of calibration-set scores).
Outputs: outputs/tables/phase8_alternatives{tag}.csv ; outputs/results/phase8_summary{tag}.json
Usage: python src/evaluation/08_alternatives_ablation.py --seeds 100 [--tag x]
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.conformal.utils import (fit_class_conditional, prediction_sets,  # noqa: E402
                                 fit_mondrian_class_conditional, prediction_sets_mondrian)

def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
baseline = load("baseline", "src/models/03_train_baseline.py")
ext = load("extval", "src/evaluation/06_external_validation.py")
TABLES, RESULTS = ROOT / "outputs" / "tables", ROOT / "outputs" / "results"


def bins_from_cal(p_cal, k):
    edges = np.unique(np.quantile(p_cal, np.linspace(0, 1, k + 1)[1:-1]))
    return lambda p: np.digitize(p, edges).astype(str)


def run(n_seeds, alpha, tag):
    t0 = time.time()
    mimic, eicu = ext.read_table(ext.MIMIC_FEATURES), ext.read_table(ext.EICU_FEATURES)
    cols_all = baseline.predictor_columns(mimic, use_measured_flags=False)
    variants_models = {"with_age": cols_all, "age_blind": [c for c in cols_all if not c.startswith("anchor_age")]}
    ym, ye = mimic["mortality"].astype(int).to_numpy(), eicu["mortality"].astype(int).to_numpy()
    rows = []
    for seed in range(n_seeds):
        tr, ca, te = baseline.split_indices(mimic, seed)
        e_cal, e_te = ext.split_eicu(eicu, seed, "patient")
        for mname, cols in variants_models.items():
            Xm, Xe = ext.encode(mimic, cols), ext.encode(eicu, cols)
            model = baseline.fit_baseline(Xm.iloc[tr], ym[tr], seed)
            pm_cal, pm_te = model.predict_proba(Xm.iloc[ca])[:, 1], model.predict_proba(Xm.iloc[te])[:, 1]
            pe = model.predict_proba(Xe)[:, 1]
            # dataset specs: name, y_cal, p_cal, y_te, p_te, group frames
            specs = [("mimic", ym[ca], pm_cal, ym[te], pm_te, mimic.iloc[ca], mimic.iloc[te], ext.MIMIC_ATTRS),
                     ("eicu", ye[e_cal], pe[e_cal], ye[e_te], pe[e_te], eicu.iloc[e_cal], eicu.iloc[e_te], ext.EXT_ATTRS)]
            for dname, yc, pc, yt, pt, dfc, dft, attrs in specs:
                gt = {a: dft[a].astype(str).to_numpy() for a in attrs}
                sets_by = {}
                q = fit_class_conditional(yc, pc, alpha)
                sets_by["cc_global"] = prediction_sets(pt, q)
                if mname == "with_age":  # age Mondrian only needs one model
                    qa = fit_mondrian_class_conditional(yc, pc, dfc["age_group"].astype(str).to_numpy(), alpha)
                    sets_by["mondrian_age"] = prediction_sets_mondrian(pt, gt["age_group"], qa)
                for k in (5, 10):
                    f = bins_from_cal(pc, k)
                    qb = fit_mondrian_class_conditional(yc, pc, f(pc), alpha)
                    sets_by[f"riskbin{k}"] = prediction_sets_mondrian(pt, f(pt), qb)
                for vname, sets in sets_by.items():
                    hit = np.where(yt == 1, sets[:, 1], sets[:, 0]); size = sets.sum(1)
                    for attr in ("All",) + tuple(attrs):
                        subs = ["All"] if attr == "All" else np.unique(gt[attr])
                        for sg in subs:
                            m = np.ones(len(yt), bool) if attr == "All" else gt[attr] == sg
                            d, v = (yt == 1) & m, (yt == 0) & m
                            rows.append(dict(seed=seed, model=mname, dataset=dname, variant=vname, attr=attr, subgroup=str(sg),
                                             n=int(m.sum()), n_deaths=int(d.sum()),
                                             cov_deaths=float(hit[d].mean()) if d.any() else np.nan,
                                             cov_surv=float(hit[v].mean()) if v.any() else np.nan,
                                             set_size=float(size[m].mean()), share_single=float((size[m] == 1).mean())))
        if (seed + 1) % 10 == 0:
            print(f"  seed {seed + 1}/{n_seeds} ({time.time() - t0:.0f}s)")
    df = pd.DataFrame(rows)
    sfx = f"_{tag}" if tag else ""
    agg = df.groupby(["model", "dataset", "variant", "attr", "subgroup"]).agg(
        n_mean=("n", "mean"), deaths_mean=("n_deaths", "mean"), cov_deaths=("cov_deaths", "mean"), cov_deaths_sd=("cov_deaths", "std"),
        cov_surv=("cov_surv", "mean"), cov_surv_sd=("cov_surv", "std"), set_size=("set_size", "mean"),
        share_single=("share_single", "mean")).reset_index()
    agg.to_csv(TABLES / f"phase8_alternatives{sfx}.csv", index=False)
    # worst-gap summary per (model,dataset,variant) over age strata
    age = agg[agg.attr == "age_group"].copy()
    age["gap_d"] = (age.cov_deaths - (1 - alpha)).abs(); age["gap_s"] = (age.cov_surv - (1 - alpha)).abs()
    w = age.groupby(["model", "dataset", "variant"]).agg(max_abs_gap_deaths=("gap_d", "max"), max_abs_gap_surv=("gap_s", "max")).reset_index()
    allr = agg[agg.attr == "All"][["model", "dataset", "variant", "set_size", "share_single"]]
    w = w.merge(allr, on=["model", "dataset", "variant"])
    (RESULTS / f"phase8_summary{sfx}.json").write_text(w.to_json(orient="records", indent=1))
    print(w.round(3).to_string(index=False)); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=20); ap.add_argument("--alpha", type=float, default=0.10); ap.add_argument("--tag", default="")
    a = ap.parse_args(); run(a.seeds, a.alpha, a.tag)
