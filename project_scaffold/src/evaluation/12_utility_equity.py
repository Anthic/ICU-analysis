"""
Phase 12 (Analysis 4): clinical utility and set-size equity of the prediction sets, plus an equalised-odds threshold baseline.
File: src/evaluation/12_utility_equity.py

Coverage alone does not say how useful the sets are. For each subgroup we report, on the test data:
  set composition: share of patients with {survive} only, {die} only, both labels, empty set; mean set size
  P(death | set): death rate among patients whose set is {survive}-only (residual risk behind a 'confident survivor' call),
                  {die}-only (precision of a 'confident death' call), both labels
  missed-death share: deaths that received a {survive}-only set / all deaths in the group
Methods (alpha = 0.10, same model and splits):
  cc_global     pooled class-conditional conformal
  mondrian_age  age x class Mondrian conformal
  eo_age        equalised-odds threshold baseline: age-specific risk thresholds chosen so that sensitivity = 0.90 and
                specificity = 0.90 in each age group (plain empirical quantiles of the calibration scores, no conformal
                finite-sample correction; Hardt et al. 2016 type post-processing). Same decision rule as mondrian_age up to the
                finite-sample correction; 'agree_with_mondrian_age' reports the share of test patients with identical sets.
  riskbin10     10 predicted-risk bins x class Mondrian
Datasets: MIMIC internal (cal -> test) and eICU (eICU cal half -> test half), model trained on the MIMIC training split.
Outputs: outputs/tables/phase12_utility{tag}.csv ; outputs/results/phase12_summary{tag}.json
Usage: python src/evaluation/12_utility_equity.py --seeds 100 [--tag x]
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.conformal.utils import (fit_class_conditional, prediction_sets, fit_mondrian_class_conditional, prediction_sets_mondrian)  # noqa: E402


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


baseline = load("baseline", "src/models/03_train_baseline.py")
ext = load("extval", "src/evaluation/06_external_validation.py")
TABLES, RESULTS = ROOT / "outputs" / "tables", ROOT / "outputs" / "results"


def bins_from_cal(p_cal, k):
    edges = np.unique(np.quantile(p_cal, np.linspace(0, 1, k + 1)[1:-1]))
    return lambda p: np.digitize(p, edges).astype(str)


def eo_fit(y, p, g, alpha):
    """per group: t_d = alpha-quantile of scores among deaths (sensitivity 1-alpha), t_s = (1-alpha)-quantile among survivors."""
    out = {}
    for a in np.unique(g):
        d, v = (g == a) & (y == 1), (g == a) & (y == 0)
        out[a] = (np.quantile(p[d], alpha) if d.any() else -np.inf, np.quantile(p[v], 1 - alpha) if v.any() else np.inf)
    return out


def eo_sets(p, g, th):
    s = np.zeros((len(p), 2), bool)
    for a, (td, ts) in th.items():
        m = g == a
        s[m, 0], s[m, 1] = p[m] <= ts, p[m] >= td
    return s


def metrics(y, sets):
    s0, s1 = sets[:, 0], sets[:, 1]
    cs, cd, cb, ce = s0 & ~s1, s1 & ~s0, s0 & s1, ~s0 & ~s1
    f = lambda m: float(y[m].mean()) if m.any() else np.nan
    return dict(n=len(y), n_deaths=int(y.sum()), set_size=float(sets.sum(1).mean()), share_surv_only=float(cs.mean()), share_die_only=float(cd.mean()),
                share_both=float(cb.mean()), share_empty=float(ce.mean()), pdeath_surv_only=f(cs), pdeath_die_only=f(cd), pdeath_both=f(cb),
                missed_death_share=float((cs & (y == 1)).sum() / max(y.sum(), 1)))


def run(n_seeds, alpha, tag):
    t0 = time.time(); sfx = f"_{tag}" if tag else ""
    mimic, eicu = ext.read_table(ext.MIMIC_FEATURES), ext.read_table(ext.EICU_FEATURES)
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    Xm, Xe = ext.encode(mimic, cols), ext.encode(eicu, cols)
    ym, ye = mimic["mortality"].astype(int).to_numpy(), eicu["mortality"].astype(int).to_numpy()
    rows = []
    for seed in range(n_seeds):
        tr, ca, te = baseline.split_indices(mimic, seed)
        e_cal, e_te = ext.split_eicu(eicu, seed, "patient")
        model = baseline.fit_baseline(Xm.iloc[tr], ym[tr], seed)
        pm_cal, pm_te, pe = model.predict_proba(Xm.iloc[ca])[:, 1], model.predict_proba(Xm.iloc[te])[:, 1], model.predict_proba(Xe)[:, 1]
        specs = [("mimic", ym[ca], pm_cal, ym[te], pm_te, mimic.iloc[ca], mimic.iloc[te], ext.MIMIC_ATTRS),
                 ("eicu", ye[e_cal], pe[e_cal], ye[e_te], pe[e_te], eicu.iloc[e_cal], eicu.iloc[e_te], ext.EXT_ATTRS)]
        for dname, yc, pc, yt, pt, dfc, dft, attrs in specs:
            gc, gt = dfc["age_group"].astype(str).to_numpy(), dft["age_group"].astype(str).to_numpy()
            sets = {"cc_global": prediction_sets(pt, fit_class_conditional(yc, pc, alpha)),
                    "mondrian_age": prediction_sets_mondrian(pt, gt, fit_mondrian_class_conditional(yc, pc, gc, alpha)),
                    "eo_age": eo_sets(pt, gt, eo_fit(yc, pc, gc, alpha))}
            f = bins_from_cal(pc, 10)
            sets["riskbin10"] = prediction_sets_mondrian(pt, f(pt), fit_mondrian_class_conditional(yc, pc, f(pc), alpha))
            agree = float((sets["eo_age"] == sets["mondrian_age"]).all(1).mean())
            for vname, st in sets.items():
                for attr in ("All",) + tuple(attrs):
                    g = np.array(["All"] * len(yt)) if attr == "All" else dft[attr].astype(str).to_numpy()
                    for sg in np.unique(g):
                        m = g == sg
                        r = dict(seed=seed, dataset=dname, variant=vname, attr=attr, subgroup=sg, **metrics(yt[m], st[m]))
                        if attr == "All":
                            r["agree_with_mondrian_age"] = agree if vname == "eo_age" else np.nan
                        rows.append(r)
        if (seed + 1) % 10 == 0:
            print(f"  seed {seed + 1}/{n_seeds} ({time.time() - t0:.0f}s)", flush=True)
    df = pd.DataFrame(rows)
    mets = [c for c in df.columns if c not in ("seed", "dataset", "variant", "attr", "subgroup")]
    agg = df.groupby(["dataset", "variant", "attr", "subgroup"])[mets].mean().reset_index()
    sd = df.groupby(["dataset", "variant", "attr", "subgroup"])[["set_size", "pdeath_surv_only", "missed_death_share"]].std().add_suffix("_sd").reset_index()
    agg = agg.merge(sd, on=["dataset", "variant", "attr", "subgroup"]); agg.to_csv(TABLES / f"phase12_utility{sfx}.csv", index=False)
    a = agg[agg.attr == "age_group"]
    summ = a.groupby(["dataset", "variant"]).agg(set_size_range=("set_size", lambda x: float(x.max() - x.min())), pdeath_surv_only_min=("pdeath_surv_only", "min"),
                                                 pdeath_surv_only_max=("pdeath_surv_only", "max"), missed_min=("missed_death_share", "min"),
                                                 missed_max=("missed_death_share", "max")).reset_index()
    ag = agg[(agg.attr == "All") & (agg.variant == "eo_age")][["dataset", "agree_with_mondrian_age"]]
    out = {"by_variant": json.loads(summ.to_json(orient="records")), "eo_vs_mondrian_agreement": json.loads(ag.to_json(orient="records"))}
    (RESULTS / f"phase12_summary{sfx}.json").write_text(json.dumps(out, indent=1))
    pd.set_option("display.width", 250)
    print(a[a.dataset == "mimic"][["variant", "subgroup", "set_size", "share_surv_only", "share_die_only", "share_both", "pdeath_surv_only", "pdeath_die_only", "pdeath_both", "missed_death_share"]].round(3).to_string(index=False))
    print(summ.round(3).to_string(index=False)); print(ag); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--alpha", type=float, default=0.10); ap.add_argument("--tag", default="")
    a = ap.parse_args(); run(a.seeds, a.alpha, a.tag)
