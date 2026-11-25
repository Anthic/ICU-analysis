"""
Phase 14: code-status (DNR / DNI / comfort measures only) sensitivity of the age coverage pattern (MIMIC-IV only).
File: src/evaluation/14_code_status_sensitivity.py
Requires data/processed/mimic_code_status_raw.csv.gz (built by src/data_processing/11_extract_code_status.py).
Flags per ICU stay, using only entries charted within the first 24 hours after ICU admission (no use of later orders):
  cmo_24h         'Comfort measures only' charted in the first 24 h
  dnr_dni_24h     DNR / DNI / DNAR (any) charted in the first 24 h (includes CMO stays that also carry DNR)
  limited_24h     cmo_24h OR dnr_dni_24h (any limitation of treatment documented in the first 24 h)
Variants (own 50/25/25 split per variant and seed; same predictors; pooled class-conditional conformal, alpha = 0.10):
  V0_original ; V4_excl_cmo_24h ; V5_excl_limited_24h
Outputs: outputs/tables/phase14_codestatus_{flags,rows,summary}{tag}.csv ; outputs/results/phase14_summary{tag}.json
Usage: python src/evaluation/14_code_status_sensitivity.py --seeds 100 [--tag x]
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
START = 0  # first seed; set with --start to run long jobs in chunks (rows files are merged afterwards)
sys.path.insert(0, str(ROOT))
from src.conformal.utils import fit_class_conditional, prediction_sets  # noqa: E402


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


baseline = load("baseline", "src/models/03_train_baseline.py")
ext = load("extval", "src/evaluation/06_external_validation.py")
TABLES, RESULTS = ROOT / "outputs" / "tables", ROOT / "outputs" / "results"


def build_flags(mimic):
    cs = pd.read_csv(ROOT / "data" / "processed" / "mimic_code_status_raw.csv.gz")
    cs["charttime"] = pd.to_datetime(cs["charttime"], errors="coerce"); cs = cs.dropna(subset=["charttime", "stay_id"]); cs["value"] = cs["value"].fillna("").str.lower()
    ic = mimic[["stay_id", "intime"]].copy(); ic["intime"] = pd.to_datetime(ic["intime"])
    cs = cs.merge(ic, on="stay_id", how="inner"); h = (cs["charttime"] - cs["intime"]).dt.total_seconds() / 3600
    cs = cs[(h >= -6) & (h <= 24)]
    cs["cmo"] = cs["value"].str.contains("comfort measures")
    cs["dnr"] = cs["value"].str.contains(r"dnr|dnar|dni|do not resus|do not intub|do not attempt", regex=True)
    g = cs.groupby("stay_id").agg(cmo_24h=("cmo", "max"), dnr_dni_24h=("dnr", "max")).reset_index()
    f = mimic[["stay_id"]].merge(g, on="stay_id", how="left").fillna(False)
    f["cmo_24h"] = f["cmo_24h"].astype(int); f["dnr_dni_24h"] = f["dnr_dni_24h"].astype(int)
    f["limited_24h"] = ((f.cmo_24h == 1) | (f.dnr_dni_24h == 1)).astype(int)
    return f


def run(n_seeds, alpha, tag):
    t0 = time.time(); sfx = f"_{tag}" if tag else ""
    mimic = ext.read_table(ext.MIMIC_FEATURES)
    flags = build_flags(mimic); flags.to_csv(TABLES / f"phase14_codestatus_flags{sfx}.csv", index=False)
    mimic = mimic.merge(flags, on="stay_id", how="left", validate="one_to_one")
    prof = mimic.groupby("age_group").agg(n=("stay_id", "size"), mortality=("mortality", "mean"), cmo=("cmo_24h", "mean"), dnr_dni=("dnr_dni_24h", "mean"),
                                          limited=("limited_24h", "mean"), mort_if_limited=("mortality", lambda s: float(s[mimic.loc[s.index, "limited_24h"] == 1].mean())))
    print(prof.round(3)); prof.to_csv(TABLES / f"phase14_codestatus_profile{sfx}.csv")
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    y_all = mimic["mortality"].astype(int).to_numpy(); lim, cmo = mimic["limited_24h"].to_numpy(), mimic["cmo_24h"].to_numpy()
    variants = {"V0_original": np.ones(len(mimic), bool), "V4_excl_cmo_24h": cmo == 0, "V5_excl_limited_24h": lim == 0}
    rows = []
    for seed in range(START, n_seeds):
        for vname, keep in variants.items():
            df = mimic[keep].reset_index(drop=True).copy(); y = df["mortality"].astype(int).to_numpy(); X = ext.encode(df, cols)
            tr, ca, te = baseline.split_indices(df, seed)
            model = baseline.fit_baseline(X.iloc[tr], y[tr], seed)
            p_cal, p_te = model.predict_proba(X.iloc[ca])[:, 1], model.predict_proba(X.iloc[te])[:, 1]
            sets = prediction_sets(p_te, fit_class_conditional(y[ca], p_cal, alpha)); yt = y[te]; hit = np.where(yt == 1, sets[:, 1], sets[:, 0])
            ag = df.iloc[te]["age_group"].astype(str).to_numpy()
            for sg in ["All", "18-49", "50-64", "65-74", "75+"]:
                m = np.ones(len(te), bool) if sg == "All" else ag == sg; d, v = (yt == 1) & m, (yt == 0) & m
                rows.append(dict(seed=seed, variant=vname, stratum=sg, n=int(m.sum()), n_deaths=int(d.sum()), prevalence=float(yt[m].mean()),
                                 cov_deaths=float(hit[d].mean()) if d.any() else np.nan, cov_surv=float(hit[v].mean()) if v.any() else np.nan))
        if (seed + 1) % 10 == 0:
            print(f"  seed {seed + 1}/{n_seeds} ({time.time() - t0:.0f}s)", flush=True)
    df = pd.DataFrame(rows); df.to_csv(TABLES / f"phase14_codestatus_rows{sfx}.csv", index=False)
    s = df.groupby(["variant", "stratum"]).agg(n=("n", "mean"), n_deaths=("n_deaths", "mean"), prevalence=("prevalence", "mean"), cov_deaths=("cov_deaths", "mean"),
                                               sd_deaths=("cov_deaths", "std"), cov_surv=("cov_surv", "mean"), sd_surv=("cov_surv", "std")).reset_index()
    s.to_csv(TABLES / f"phase14_codestatus_summary{sfx}.csv", index=False)
    (RESULTS / f"phase14_summary{sfx}.json").write_text(s.to_json(orient="records", indent=1))
    pd.set_option("display.width", 220); print(s.round(3).to_string(index=False)); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--alpha", type=float, default=0.10); ap.add_argument("--tag", default="")
    ap.add_argument('--start', type=int, default=0); a = ap.parse_args(); START = a.start; run(a.seeds, a.alpha, a.tag)
