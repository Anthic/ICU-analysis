"""Figures 3-5, generated only from saved CSV tables (no hard-coded values).
Fig 3: set-size cost of Mondrian calibration (phase7_tradeoff_efficiency_analysis.csv)
Fig 4: observed vs calibration-implied coverage, raw and recalibrated scores (phase10_cells_main_100.csv)
Fig 5: coverage by 10-year age band (phase11_endoflife_summary_main_100.csv)"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
T, F = ROOT / "outputs" / "tables", ROOT / "outputs" / "figures"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def fig3():
    d = pd.read_csv(T / "phase7_tradeoff_efficiency_analysis.csv"); d = d[d["dimension"] != "All"].reset_index(drop=True)
    fig = plt.figure(figsize=(15, 9)); gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], hspace=0.35, wspace=0.22)
    a, b, c = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    for _, r in d.iterrows():
        a.annotate("", xy=(r.mond_cc_set_size, 100 * r.mond_cc_death_cov), xytext=(r.global_set_size, 100 * r.global_cc_death_cov),
                   arrowprops=dict(arrowstyle="->", color="#9ca3af", lw=1))
    a.scatter(d.global_set_size, 100 * d.global_cc_death_cov, c="#1e293b", s=45, label="Pooled class-conditional", zorder=3)
    a.scatter(d.mond_cc_set_size, 100 * d.mond_cc_death_cov, c="#0d9488", marker="D", s=45, label="Mondrian class-conditional", zorder=3)
    a.axhline(90, ls="--", c="k", lw=1); a.set_ylim(83.2, 94.2)
    for sg, dx, dy in [("18-49", 0.004, 0.2), ("75+", -0.022, 0.0), ("Asian", 0.004, -0.5), ("Private", 0.004, -0.5)]:
        r = d[d.subgroup == sg].iloc[0]; a.text(r.global_set_size + dx, 100 * r.global_cc_death_cov + dy, sg, fontsize=9, fontweight="bold")
    a.set_xlabel("Mean prediction set size"); a.set_ylabel("Death coverage (%)"); a.set_title("A. Death coverage vs set size (pooled to Mondrian)", fontweight="bold"); a.legend(loc="lower right", fontsize=8)
    for _, r in d.iterrows():
        b.plot([r.mond_marg_set_size, r.mond_cc_set_size], [100 * r.mond_marg_death_cov, 100 * r.mond_cc_death_cov], c="#f87171", lw=0.8, ls="--")
    b.scatter(d.mond_marg_set_size, 100 * d.mond_marg_death_cov, c="#dc2626", marker="s", s=40, label="Mondrian marginal (no class conditioning)", zorder=3)
    b.scatter(d.mond_cc_set_size, 100 * d.mond_cc_death_cov, c="#0d9488", marker="D", s=40, label="Mondrian class-conditional", zorder=3)
    b.axhline(90, ls="--", c="k", lw=1)
    for sg in ["18-49", "50-64", "75+"]:
        r = d[d.subgroup == sg].iloc[0]; b.text(r.mond_marg_set_size + 0.01, 100 * r.mond_marg_death_cov - 4, f"{sg} ({100 * r.mond_marg_death_cov:.1f}%)", fontsize=8, color="#7f1d1d")
    b.set_xlabel("Mean prediction set size"); b.set_ylabel("Death coverage (%)"); b.set_title("B. Mondrian marginal leaves death coverage low", fontweight="bold"); b.legend(fontsize=8)
    dd = d.assign(lab=d.subgroup).sort_values("delta_set_size")
    c.barh(range(len(dd)), dd.delta_set_size, color=np.where(dd.delta_set_size >= 0, "#0d9488", "#5b86a7"), edgecolor="#0f172a", lw=0.6)
    for i, (_, r) in enumerate(dd.iterrows()):
        c.text(r.delta_set_size + (0.001 if r.delta_set_size >= 0 else -0.001), i, f"{r.delta_set_size:+.3f} ({r.pct_set_size_change:+.1f}%)", va="center", ha="left" if r.delta_set_size >= 0 else "right", fontsize=8)
    c.set_yticks(range(len(dd))); c.set_yticklabels(dd.lab); c.axvline(0, c="k", lw=1); c.set_xlim(-0.08, 0.08)
    c.set_xlabel("Change in mean set size (Mondrian minus pooled)"); c.set_title("C. Set-size change by subgroup", fontweight="bold")
    fig.suptitle("Figure 3. Set-size cost of subgroup class-conditional calibration (MIMIC-IV, 100 splits, nominal 90%)", fontweight="bold")
    fig.savefig(F / "figure3_fairness_efficiency_tradeoff.png", dpi=200, bbox_inches="tight"); plt.close(fig)


def fig4():
    d = pd.read_csv(T / "phase10_cells_main_100.csv")
    fig, ax = plt.subplots(2, 2, figsize=(12, 10)); 
    for row, (side, ocol, pcol, name) in enumerate([("s", "obs_s", "pred_s", "Survivor"), ("d", "obs_d", "pred_d", "Death")]):
        for col, w in enumerate(["raw", "recal"]):
            x = ax[row, col]
            h = d[(d.dataset == "eicu_all") & (d.level == "hospital") & (d.weights == w)]
            e = d[(d.dataset == "eicu_all") & (d.level == "demographic") & (d.weights == w)]
            m = d[(d.dataset == "mimic_test")]
            x.scatter(h[pcol], h[ocol], s=14, c="#94a3b8", label="eICU hospitals (n=103)")
            x.scatter(e[pcol], e[ocol], s=40, c="#1d4ed8", label="eICU demographic strata")
            if w == "raw":
                x.scatter(m[pcol], m[ocol], s=45, c="#dc2626", marker="D", label="MIMIC test strata (own scores)")
            lo, hi = min(d[pcol].min(), d[ocol].min()) - 0.01, max(d[pcol].max(), d[ocol].max()) + 0.01
            x.plot([lo, hi], [lo, hi], "k--", lw=1); x.axhline(0.9, c="#cbd5e1", lw=1); x.axvline(0.9, c="#cbd5e1", lw=1)
            x.set_xlim(lo, hi); x.set_ylim(lo, hi)
            x.set_title(f"{'AB'[row] if False else ''}{name} coverage, eICU {'raw' if w == 'raw' else 'recalibrated'} scores", fontweight="bold", fontsize=10)
            x.set_xlabel("Predicted coverage from scores alone"); x.set_ylabel("Observed coverage")
            if row == 0 and col == 0: x.legend(fontsize=8, loc="upper left")
    fig.suptitle("Figure 4. Observed vs calibration-implied class-conditional coverage (mean of 100 seeds; dashed = identity)", fontweight="bold")
    fig.savefig(F / "figure4_calibration_implied_coverage.png", dpi=200, bbox_inches="tight"); plt.close(fig)


def fig5():
    e = pd.read_csv(T / "phase11_endoflife_summary_main_100.csv"); e = e[e.attr == "age_band"]
    order = ["18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-91+"]
    fig, ax = plt.subplots(1, 2, figsize=(14, 5.2))
    for k, (cov, sd, name) in enumerate([("cov_deaths", "sd_deaths", "A. Death coverage"), ("cov_surv", "sd_surv", "B. Survivor coverage")]):
        for v, lab, colr in [("V0_original", "Reference (death)", "#1f2937"), ("V1_death_or_hospice", "Death or hospice", "#2563eb"), ("V2_excl_hospice", "Hospice removed", "#059669")]:
            s = e[e.variant == v].set_index("stratum").reindex(order)
            ax[k].errorbar(range(len(order)), s[cov], yerr=s[sd], marker="o", capsize=3, c=colr, label=lab, lw=1.5)
        ax[k].axhline(0.9, ls="--", c="#6b7280"); ax[k].set_xticks(range(len(order))); ax[k].set_xticklabels(order, rotation=30)
        ax[k].set_xlabel("Age band (years)"); ax[k].set_ylabel("Class-conditional coverage"); ax[k].set_title(name, loc="left")
    ax[0].legend(fontsize=8, loc="lower right")
    fig.suptitle("Figure 5. Coverage by 10-year age band, pooled class-conditional thresholds (MIMIC-IV, 100 splits; bars = seed SD; bands with fewer than 50 test deaths per split are noisy)", fontsize=10)
    fig.savefig(F / "figure5_age_bands.png", dpi=200, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    fig3(); fig4(); fig5(); print("figures 3-5 written")
