"""
Phase 9: stratum-minus-overall coverage contrasts with hospital-cluster bootstrap CIs (eICU).
File: src/evaluation/09_endpoint_contrasts.py

Why: the Phase 6 endpoints P1/P2 are absolute coverage under pure transport, which mixes the age effect with the
overall transport shift (eICU risk is over-predicted: death coverage > 0.90 and survivor coverage < 0.90 overall), and
the Wilson intervals ignore hospital clustering and reuse the same patients across seeds. Here:
    contrast(stratum, class) = coverage(stratum, class) - coverage(all patients, class)
computed for two configurations on eICU
    transport : thresholds from the MIMIC-IV calibration split (pure transport), evaluated on ALL eICU patients
    recal     : class-conditional thresholds from an eICU-calibration half, evaluated on the other half (patient split)
Uncertainty: two-level bootstrap = resample hospitals (cluster) AND resample model seeds, B draws;
percentile 95% CI, and a Bonferroni-adjusted (8 contrasts) CI. The seed-only variation is also reported.
Revised replication rule for the contrast: upper 95% bound < 0 (P1: ages 18-49 deaths; P2: ages 75+ survivors).

Outputs: outputs/tables/phase9_endpoint_contrasts{tag}.csv ; outputs/results/phase9_summary{tag}.json
Usage: python src/evaluation/09_endpoint_contrasts.py --seeds 100 [--drop temperature gcs_min intubated --tag harm]
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.conformal.utils import fit_class_conditional, prediction_sets  # noqa: E402


def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


baseline = load("baseline", "src/models/03_train_baseline.py")
ext = load("extval", "src/evaluation/06_external_validation.py")
TABLES, RESULTS = ROOT / "outputs" / "tables", ROOT / "outputs" / "results"
AGES = ["18-49", "50-64", "65-74", "75+"]
STRATA = AGES + ["All"]          # index 4 = All
K = len(STRATA)


def counts(hosp_idx, H, strat_idx, y, hit):
    """returns hit[H,K,2], n[H,K,2]; class axis 0 = survivors, 1 = deaths; strata include 'All' (index 4)."""
    hit_a = np.zeros((H, K, 2)); n_a = np.zeros((H, K, 2))
    for k in list(range(4)) + [4]:
        m = np.ones(len(y), bool) if k == 4 else strat_idx == k
        for c in (0, 1):
            mm = m & (y == c)
            n_a[:, k, c] = np.bincount(hosp_idx[mm], minlength=H)
            hit_a[:, k, c] = np.bincount(hosp_idx[mm], weights=hit[mm], minlength=H)
    return hit_a, n_a


def boot(hit, n, B, seed_boot, per_seed_n):
    """hit: [S,H,K,2]; n: [H,K,2] (transport) or [S,H,K,2] (recal). returns (point, draws[B,4,2]) contrasts and raw coverage."""
    S, H = hit.shape[:2]
    rng = np.random.default_rng(seed_boot)

    def contrast(w, sidx):
        h = hit[sidx]
        nn = n[sidx] if per_seed_n else n[None]
        num = np.einsum("h,shkc->skc", w, h)
        den = np.einsum("h,shkc->skc", w, np.broadcast_to(nn, h.shape))
        cov = num / den                                        # [S,K,2]
        return (cov[:, :4, :] - cov[:, 4:5, :]).mean(0), cov[:, :4, :].mean(0), cov[:, 4, :].mean(0)

    pt, cov_s, cov_all = contrast(np.ones(H), np.arange(S))
    draws = np.empty((B, 4, 2)); seed_only = np.empty((B, 4, 2))
    for b in range(B):
        w = rng.multinomial(H, np.ones(H) / H).astype(float)
        sidx = rng.integers(0, S, S)
        draws[b] = contrast(w, sidx)[0]
        seed_only[b] = contrast(np.ones(H), sidx)[0]
    return pt, cov_s, cov_all, draws, seed_only


def run(n_seeds, alpha, drop, tag, B):
    t0 = time.time(); sfx = f"_{tag}" if tag else ""
    mimic, eicu = ext.read_table(ext.MIMIC_FEATURES), ext.read_table(ext.EICU_FEATURES)
    cols = baseline.predictor_columns(mimic, use_measured_flags=False)
    if drop:
        cols = [c for c in cols if not any(c.startswith(d) for d in drop)]
    Xm, Xe = ext.encode(mimic, cols), ext.encode(eicu, cols)
    ym, ye = mimic["mortality"].astype(int).to_numpy(), eicu["mortality"].astype(int).to_numpy()
    hosp_ids, hosp_idx = np.unique(eicu["hospitalid"].to_numpy(), return_inverse=True); H = len(hosp_ids)
    age_idx = eicu["age_group"].astype(str).map({a: i for i, a in enumerate(AGES)}).fillna(-1).astype(int).to_numpy()
    T_hit = np.zeros((n_seeds, H, K, 2)); R_hit = np.zeros_like(T_hit); R_n = np.zeros_like(T_hit)
    for seed in range(n_seeds):
        tr, ca, te = baseline.split_indices(mimic, seed)
        model = baseline.fit_baseline(Xm.iloc[tr], ym[tr], seed)
        p_cal, pe = model.predict_proba(Xm.iloc[ca])[:, 1], model.predict_proba(Xe)[:, 1]
        q = fit_class_conditional(ym[ca], p_cal, alpha)
        sets = prediction_sets(pe, q); hit = np.where(ye == 1, sets[:, 1], sets[:, 0]).astype(float)
        T_hit[seed], T_n = counts(hosp_idx, H, age_idx, ye, hit)
        e_cal, e_te = ext.split_eicu(eicu, seed, "patient")
        qe = fit_class_conditional(ye[e_cal], pe[e_cal], alpha)
        st = prediction_sets(pe[e_te], qe); h2 = np.where(ye[e_te] == 1, st[:, 1], st[:, 0]).astype(float)
        R_hit[seed], R_n[seed] = counts(hosp_idx[e_te], H, age_idx[e_te], ye[e_te], h2)
        if (seed + 1) % 20 == 0:
            print(f"  seed {seed + 1}/{n_seeds} ({time.time() - t0:.0f}s)")

    rows = []
    for cfg, hit, nn, per in (("transport_mimic_thresholds", T_hit, T_n, False), ("recalibrated_eicu_half", R_hit, R_n, True)):
        pt, cov_s, cov_all, d, so = boot(hit, nn, B, 42, per)
        bonf = 100 * (0.05 / 8 / 2)
        for ki, a in enumerate(AGES):
            for ci, cname in ((1, "deaths"), (0, "survivors")):
                x = d[:, ki, ci]; y = so[:, ki, ci]
                rows.append(dict(config=cfg, stratum=a, class_=cname, coverage=cov_s[ki, ci], overall_coverage=cov_all[ci],
                                 contrast=pt[ki, ci], ci_low=np.percentile(x, 2.5), ci_high=np.percentile(x, 97.5),
                                 bonf_low=np.percentile(x, bonf), bonf_high=np.percentile(x, 100 - bonf),
                                 seed_only_low=np.percentile(y, 2.5), seed_only_high=np.percentile(y, 97.5),
                                 boot_sd=float(x.std()), n_hospitals=H,
                                 deaths_total=int(nn[..., ki, 1].sum() / (nn.shape[0] if per else 1)),
                                 survivors_total=int(nn[..., ki, 0].sum() / (nn.shape[0] if per else 1))))
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / f"phase9_endpoint_contrasts{sfx}.csv", index=False)
    pick = lambda cfg, a, c: out[(out.config == cfg) & (out.stratum == a) & (out.class_ == c)].iloc[0]
    summ = {}
    for cfg in out.config.unique():
        p1, p2 = pick(cfg, "18-49", "deaths"), pick(cfg, "75+", "survivors")
        summ[cfg] = {"P1_contrast": p1.contrast, "P1_ci": [p1.ci_low, p1.ci_high], "P1_replicated_upper_lt_0": bool(p1.ci_high < 0),
                     "P2_contrast": p2.contrast, "P2_ci": [p2.ci_low, p2.ci_high], "P2_replicated_upper_lt_0": bool(p2.ci_high < 0)}
    (RESULTS / f"phase9_summary{sfx}.json").write_text(json.dumps(summ, indent=1, default=float))
    pd.set_option("display.width", 220)
    print(out[["config", "stratum", "class_", "coverage", "overall_coverage", "contrast", "ci_low", "ci_high", "seed_only_low", "seed_only_high"]].round(3).to_string(index=False))
    print(json.dumps(summ, indent=1, default=float)); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=20); ap.add_argument("--alpha", type=float, default=0.10)
    ap.add_argument("--drop", nargs="*", default=None); ap.add_argument("--tag", default=""); ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args(); run(a.seeds, a.alpha, a.drop, a.tag, a.boot)
