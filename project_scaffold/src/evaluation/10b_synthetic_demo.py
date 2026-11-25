"""
Phase 10b: synthetic demonstration of the calibration-implied coverage identity.
File: src/evaluation/10b_synthetic_demo.py   (SYNTHETIC DATA; numpy/sklearn only)

Claim: if a score p is calibrated inside group g (P(y=1 | p, g) = p), the class-conditional coverage of a POOLED
class-conditional conformal rule (death label in set iff p >= t_d; survivor label in set iff p <= t_s) is determined by
the group's score distribution alone, without labels:
    cov_deaths(g)    = sum_{i in g} p_i 1[p_i >= t_d] / sum_{i in g} p_i
    cov_survivors(g) = sum_{i in g} (1-p_i) 1[p_i <= t_s] / sum_{i in g} (1-p_i)
Scenarios (all scores are exactly calibrated unless stated):
  A  base-rate shift: same logit spread, different mean logit (different prevalence)  -> group gaps
  B  equal prevalence, different logit spread (hence different AUROC)               -> group gaps
  C  identical groups                                                               -> no gap
  D  same as A but group-specific miscalibration (score shifted after labels drawn)  -> identity fails, flags miscalibration
Outputs: outputs/tables/phase10_synthetic_demo.csv ; prints a table.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
rng = np.random.default_rng(2026)
ALPHA = 0.10


def qhat(scores, alpha):
    n = len(scores); k = int(np.ceil((n + 1) * (1 - alpha)))
    return np.inf if k > n else np.sort(scores)[k - 1]


def scenario(name, groups, n=200_000, miscal=None):
    """groups: dict g -> (mu, sigma, share)"""
    rows = []
    eta, p, y, g = [], [], [], []
    for gi, (mu, sd, share) in groups.items():
        m = int(n * share); e = rng.normal(mu, sd, m); pr = 1 / (1 + np.exp(-e))
        yy = (rng.random(m) < pr).astype(int)           # labels drawn from the TRUE probability
        pp = pr.copy()
        if miscal and gi in miscal:                       # reported score differs from the true probability
            pp = 1 / (1 + np.exp(-(e + miscal[gi])))
        eta.append(e); p.append(pp); y.append(yy); g.append(np.full(m, gi))
    p, y, g = np.concatenate(p), np.concatenate(y), np.concatenate(g)
    # pooled class-conditional thresholds from half of the data (calibration), evaluate on all (large n)
    idx = rng.permutation(len(p)); cal = idx[: len(p) // 2]
    q0 = qhat(p[cal][y[cal] == 0], ALPHA)                 # survivor score s = p ; label 0 in set iff p <= q0
    q1 = qhat(1 - p[cal][y[cal] == 1], ALPHA)             # death score s = 1-p ; label 1 in set iff 1-p <= q1
    t_d, t_s = 1 - q1, q0
    for gi in groups:
        mk = g == gi; pg, yg = p[mk], y[mk]
        obs_d = (pg[yg == 1] >= t_d).mean(); obs_s = (pg[yg == 0] <= t_s).mean()
        pred_d = (pg * (pg >= t_d)).sum() / pg.sum(); pred_s = ((1 - pg) * (pg <= t_s)).sum() / (1 - pg).sum()
        rows.append(dict(scenario=name, group=gi, n=int(mk.sum()), prevalence=yg.mean(), mean_score=pg.mean(), auroc=roc_auc_score(yg, pg),
                         cov_deaths_obs=obs_d, cov_deaths_pred=pred_d, cov_surv_obs=obs_s, cov_surv_pred=pred_s,
                         t_death=t_d, t_surv=t_s))
    return rows


rows = []
rows += scenario("A_base_rate_shift", {"young": (-3.2, 1.6, .33), "mid": (-2.4, 1.6, .34), "old": (-1.6, 1.6, .33)})
rows += scenario("B_equal_prevalence_diff_spread", {"narrow": (-2.55, 1.0, .5), "wide": (-3.40, 2.0, .5)})
rows += scenario("C_identical_groups", {"g1": (-2.4, 1.6, .5), "g2": (-2.4, 1.6, .5)})
rows += scenario("D_group_miscalibration", {"young": (-3.2, 1.6, .33), "mid": (-2.4, 1.6, .34), "old": (-1.6, 1.6, .33)},
                 miscal={"young": 0.6, "old": -0.6})
df = pd.DataFrame(rows)
(ROOT / "outputs" / "tables").mkdir(parents=True, exist_ok=True)
df.to_csv(ROOT / "outputs" / "tables" / "phase10_synthetic_demo.csv", index=False)
pd.set_option("display.width", 220)
print(df[["scenario", "group", "prevalence", "auroc", "cov_deaths_obs", "cov_deaths_pred", "cov_surv_obs", "cov_surv_pred"]].round(3).to_string(index=False))
