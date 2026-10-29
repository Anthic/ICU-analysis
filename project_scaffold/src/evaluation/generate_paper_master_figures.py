"""Generate Figure 1 and Figure 2 Master Multi-Panel Figures for ICU Conformal Fairness Study.

Redesigned with publication-grade spacing:
- Zero text-line collisions (lines never cut through text labels).
- Ample top margin (top=0.85) so two-line suptitles NEVER collide with subpanel titles.
- Balanced vertical proportions eliminating any awkward whitespace gap in the middle.
- Strict xlim padding in Panel B so brackets never touch the y-axis spine or tick labels.
- Standard scientific notation and elegant pill badges.
"""

from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

P4_PATH = TABLES_DIR / "phase4_rigorous_audit_noflags_a010.csv"
P5_PATH = TABLES_DIR / "phase5_subgroup_coverage_corrected_noflags_a010.csv"


def generate_figures():
    df4 = pd.read_csv(P4_PATH)
    df5 = pd.read_csv(P5_PATH)
    df5_cc = df5[df5["calibration_type"] == "mondrian_class_conditional"].copy()

    # Apply clean scientific styling
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "axes.edgecolor": "#334155",
        "axes.linewidth": 1.0,
        "grid.color": "#E2E8F0",
        "grid.linestyle": ":",
        "grid.linewidth": 0.8,
    })

    # =========================================================================
    # FIGURE 1: THE ANATOMY OF THE AGE DISPARITY AND MONDRIAN REPAIR
    # =========================================================================
    print("Generating Figure 1: The Anatomy of the Age Disparity...")
    fig1 = plt.figure(figsize=(15.5, 10.5))
    # top=0.85 gives abundant clearance below the two-line suptitle
    fig1.subplots_adjust(top=0.85, bottom=0.10, left=0.07, right=0.96, hspace=0.32, wspace=0.22)
    gs1 = fig1.add_gridspec(2, 2, height_ratios=[1.0, 1.12])

    ax1_a = fig1.add_subplot(gs1[0, 0])
    ax1_b = fig1.add_subplot(gs1[0, 1])
    ax1_c = fig1.add_subplot(gs1[1, :])

    age_sub = df4[df4["attribute"] == "age_group"].copy().sort_values("subgroup")
    age_groups = ["18-49", "50-64", "65-74", "75+"]
    x = np.arange(len(age_groups))
    width = 0.34

    # -------------------------------------------------------------------------
    # Panel A: Underlying Clinical Risk & Mortality across Age Groups
    # -------------------------------------------------------------------------
    obs_mort = age_sub["observed_mortality"].to_numpy() * 100.0
    pred_risk = age_sub["mean_p_hat"].to_numpy() * 100.0

    ax1_a.bar(x - width/2, obs_mort, width, label="Observed In-Hospital Mortality Rate (%)",
              color="#1E3A8A", edgecolor="#0F172A", linewidth=1.0, zorder=3)
    ax1_a.bar(x + width/2, pred_risk, width, label=r"Mean Model Predicted Risk ($\hat{p}$) [%]",
              color="#3B82F6", edgecolor="#0F172A", linewidth=1.0, zorder=3)

    for i in range(len(age_groups)):
        ax1_a.text(x[i] - width/2, obs_mort[i] + 0.45, f"{obs_mort[i]:.1f}%",
                   ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#1E3A8A")
        ax1_a.text(x[i] + width/2, pred_risk[i] + 0.45, f"{pred_risk[i]:.1f}%",
                   ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#1D4ED8")

    ax1_a.set_xticks(x)
    ax1_a.set_xticklabels([f"Age {ag}" for ag in age_groups], fontsize=11, fontweight="bold")
    ax1_a.set_ylabel("Mortality / Risk Probability (%)", fontsize=11, fontweight="bold")
    ax1_a.set_ylim(0, 20.0)
    ax1_a.set_title("A. Baseline Clinical Risk by Age Group\n(Young Adults Exhibit 2.4× Lower In-Hospital Mortality)",
                    fontsize=11.5, fontweight="bold", pad=10)
    ax1_a.legend(loc="upper left", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.5)
    ax1_a.grid(True, axis="y", zorder=0)

    # -------------------------------------------------------------------------
    # Panel B: The Young Decedent Under-coverage Gap (Baseline Conformal)
    # -------------------------------------------------------------------------
    death_cov = age_sub["cc_death_cov_mean"].to_numpy() * 100.0
    surv_cov = age_sub["cc_surv_cov_mean"].to_numpy() * 100.0
    d_low = age_sub["cc_death_cov_boot_ci_low"].to_numpy() * 100.0
    d_high = age_sub["cc_death_cov_boot_ci_high"].to_numpy() * 100.0
    s_low = age_sub["cc_surv_cov_boot_ci_low"].to_numpy() * 100.0
    s_high = age_sub["cc_surv_cov_boot_ci_high"].to_numpy() * 100.0

    ax1_b.bar(x - width/2, death_cov, width, label="Death Coverage (y = 1)",
              color="#DC2626", edgecolor="#7F1D1D", linewidth=1.0, zorder=3)
    ax1_b.bar(x + width/2, surv_cov, width, label="Survivor Coverage (y = 0)",
              color="#0D9488", edgecolor="#134E4A", linewidth=1.0, zorder=3)

    ax1_b.errorbar(x - width/2, death_cov, yerr=[death_cov - d_low, d_high - death_cov],
                   fmt="none", color="#1F2937", capsize=4.0, elinewidth=1.3, capthick=1.3, zorder=4)
    ax1_b.errorbar(x + width/2, surv_cov, yerr=[surv_cov - s_low, s_high - surv_cov],
                   fmt="none", color="#1F2937", capsize=4.0, elinewidth=1.3, capthick=1.3, zorder=4)

    ax1_b.axhline(90.0, color="#0F172A", linestyle="--", linewidth=1.5,
                  label="Nominal 90.0% Target Coverage", zorder=2)

    # Percentage labels inside bars at safe height (y = 74.0) — zero collisions!
    for i in range(len(age_groups)):
        ax1_b.text(x[i] - width/2, 74.0, f"{death_cov[i]:.1f}%",
                   ha="center", va="center", color="white", fontsize=9.5, fontweight="bold", zorder=5)
        ax1_b.text(x[i] + width/2, 74.0, f"{surv_cov[i]:.1f}%",
                   ha="center", va="center", color="white", fontsize=9.5, fontweight="bold", zorder=5)

    # Clean Scientific Comparison Bracket over Age 18-49 with abundant left padding
    x_d = 0 - width/2
    x_s = 0 + width/2
    y_br = 97.5
    ax1_b.plot([x_d, x_d, x_s, x_s], [y_br - 1.2, y_br, y_br, y_br - 1.2],
               color="#991B1B", lw=1.4, zorder=6)
    ax1_b.text(0, y_br + 0.8, "10.8 pp Coverage Gap\n(−5.9 pp vs Target)",
               ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#991B1B",
               bbox=dict(boxstyle="round,pad=0.25", facecolor="#FEF2F2", edgecolor="#FECACA", lw=0.9),
               zorder=6)

    ax1_b.set_xticks(x)
    ax1_b.set_xticklabels([f"Age {ag}" for ag in age_groups], fontsize=11, fontweight="bold")
    ax1_b.set_ylabel("Class-Conditional Coverage (%)", fontsize=11, fontweight="bold")
    ax1_b.set_xlim(-0.65, 3.65)
    ax1_b.set_ylim(68.0, 107.0)
    ax1_b.set_title("B. The Young Decedent Under-coverage Gap\n(Baseline Conformal Calibration Fails in Low-Prevalence Strata)",
                    fontsize=11.5, fontweight="bold", pad=10)
    ax1_b.legend(loc="upper right", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.0)
    ax1_b.grid(True, axis="y", zorder=0)

    # -------------------------------------------------------------------------
    # Panel C: Complete Restoration of Age Equity (Global vs Mondrian CC)
    # -------------------------------------------------------------------------
    age_p5 = df5_cc[df5_cc["stratification_attribute"] == "age_group"].set_index("subgroup").reindex(age_groups)
    m_death = age_p5["coverage_deaths_mean"].to_numpy() * 100.0
    m_surv = age_p5["coverage_survivors_mean"].to_numpy() * 100.0

    w4 = 0.19
    ax1_c.bar(x - 1.5*w4, death_cov, w4, label="Baseline: Death Coverage (y = 1)",
              color="#F59E0B", edgecolor="#78350F", linewidth=0.9, zorder=3)
    ax1_c.bar(x - 0.5*w4, m_death, w4, label="Mondrian CC: Death Coverage (y = 1) [Repaired]",
              color="#DC2626", edgecolor="#7F1D1D", linewidth=0.9, zorder=3)
    ax1_c.bar(x + 0.5*w4, surv_cov, w4, label="Baseline: Survivor Coverage (y = 0)",
              color="#3B82F6", edgecolor="#1E3A8A", linewidth=0.9, zorder=3)
    ax1_c.bar(x + 1.5*w4, m_surv, w4, label="Mondrian CC: Survivor Coverage (y = 0) [Repaired]",
              color="#10B981", edgecolor="#064E3B", linewidth=0.9, zorder=3)

    ax1_c.axhline(90.0, color="#0F172A", linestyle="--", linewidth=1.5,
                  label="Nominal 90.0% Target Coverage", zorder=2)

    # Place percentage numbers inside bars at safe height (y = 75.0)
    for i in range(len(age_groups)):
        ax1_c.text(x[i] - 1.5*w4, 75.0, f"{death_cov[i]:.1f}%", ha="center", va="center",
                   color="white", fontsize=8.0, fontweight="bold", zorder=5)
        ax1_c.text(x[i] - 0.5*w4, 75.0, f"{m_death[i]:.1f}%", ha="center", va="center",
                   color="white", fontsize=8.0, fontweight="bold", zorder=5)
        ax1_c.text(x[i] + 0.5*w4, 75.0, f"{surv_cov[i]:.1f}%", ha="center", va="center",
                   color="white", fontsize=8.0, fontweight="bold", zorder=5)
        ax1_c.text(x[i] + 1.5*w4, 75.0, f"{m_surv[i]:.1f}%", ha="center", va="center",
                   color="white", fontsize=8.0, fontweight="bold", zorder=5)

    # Place delta labels above bars with staggered heights if necessary to prevent horizontal overlap
    for i in range(len(age_groups)):
        d_diff = m_death[i] - death_cov[i]
        s_diff = m_surv[i] - surv_cov[i]

        d_y = max(m_death[i], death_cov[i]) + 1.6
        s_y = max(m_surv[i], surv_cov[i]) + 1.6

        if abs(d_y - s_y) < 2.0:
            if d_y >= s_y:
                d_y += 1.8
            else:
                s_y += 1.8

        ax1_c.text(x[i] - 1.0*w4, d_y, f"Δ {d_diff:+.2f} pp", ha="center", va="bottom",
                   fontsize=8.5, fontweight="bold", color="#B91C1C",
                   bbox=dict(boxstyle="round,pad=0.25", facecolor="#FEF2F2", edgecolor="#FECACA", lw=0.8),
                   zorder=5)
        ax1_c.text(x[i] + 1.0*w4, s_y, f"Δ {s_diff:+.2f} pp", ha="center", va="bottom",
                   fontsize=8.5, fontweight="bold", color="#047857",
                   bbox=dict(boxstyle="round,pad=0.25", facecolor="#ECFDF5", edgecolor="#A7F3D0", lw=0.8),
                   zorder=5)

    ax1_c.set_xticks(x)
    ax1_c.set_xticklabels([f"Age {ag}" for ag in age_groups], fontsize=11.5, fontweight="bold")
    ax1_c.set_ylabel("Empirical Test Coverage (%)", fontsize=11, fontweight="bold")
    ax1_c.set_xlim(-0.55, 3.55)
    ax1_c.set_ylim(70.0, 103.0)
    ax1_c.set_title("C. Complete Restoration of Age Equity (All Strata Converge to 90.0% Coverage via Mondrian CC)",
                    fontsize=12, fontweight="bold", pad=10)
    ax1_c.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=True,
                 facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.5, columnspacing=1.8)
    ax1_c.grid(True, axis="y", zorder=0)

    # Master Figure Suptitle safely in top margin (y=0.96)
    fig1.suptitle(
        "Figure 1: The Anatomy of the Age Disparity in Critical Care Conformal Prediction\n"
        "Baseline Risk Misdistribution Induces a 5.9 pp Decedent Under-coverage in Young Adults, Resolved by Mondrian Calibration",
        fontsize=13.5, fontweight="bold", y=0.96
    )

    out_fig1 = FIGURES_DIR / "figure1_age_disparity_and_repair.png"
    fig1.savefig(out_fig1, dpi=300, bbox_inches="tight")
    plt.close(fig1)
    print(f"Saved: {out_fig1}")

    # =========================================================================
    # FIGURE 2: RACIAL AND PAYER EQUITY AUDIT VS WHITE PARITY
    # =========================================================================
    print("Generating Figure 2: Racial and Payer Equity Audit...")
    fig2 = plt.figure(figsize=(15.5, 10.5))
    fig2.subplots_adjust(top=0.85, bottom=0.10, left=0.07, right=0.96, hspace=0.32, wspace=0.22)
    gs2 = fig2.add_gridspec(2, 2, height_ratios=[1.0, 1.12])

    ax2_a = fig2.add_subplot(gs2[0, 0])
    ax2_b = fig2.add_subplot(gs2[0, 1])
    ax2_c = fig2.add_subplot(gs2[1, :])

    # -------------------------------------------------------------------------
    # Panel A: Survivor Coverage Disparities vs White Reference (Table 7)
    # -------------------------------------------------------------------------
    races = ["Asian", "Black", "Hispanic", "Other/Unknown"]
    deltas = [-2.10, -1.30, +2.16, -1.44]
    boot_low = [-3.53, -2.18, +1.07, -2.16]
    boot_high = [-0.50, -0.38, +3.16, -0.79]

    y_pos = np.arange(len(races))
    bar_colors = ["#DC2626" if d < 0 else "#0D9488" for d in deltas]

    ax2_a.barh(y_pos, deltas, height=0.40, color=bar_colors, edgecolor="#0F172A",
               linewidth=1.0, alpha=0.90, zorder=3)

    ax2_a.errorbar(deltas, y_pos,
                   xerr=[[deltas[i] - boot_low[i] for i in range(len(races))],
                         [boot_high[i] - deltas[i] for i in range(len(races))]],
                   fmt="none", ecolor="#0F172A", elinewidth=1.4, capsize=4.5, capthick=1.4, zorder=4)

    ax2_a.axvline(0, color="#0F172A", linestyle="-", linewidth=1.5,
                  label="White Reference Parity (0.0 pp)", zorder=2)

    # Place text badge ABOVE each bar at (y_pos + 0.28) -> ZERO collision with error bar whiskers!
    for i in range(len(races)):
        d_val = deltas[i]
        b_l = boot_low[i]
        b_h = boot_high[i]

        text_str = f"{d_val:+.2f} pp (95% CI: {b_l:.2f} to {b_h:.2f})"
        x_center = d_val / 2.0

        ax2_a.text(x_center, y_pos[i] + 0.26, text_str,
                   ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0F172A",
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="#F8FAFC", edgecolor="#94A3B8", lw=0.7),
                   zorder=5)

    ax2_a.set_yticks(y_pos)
    ax2_a.set_yticklabels(races, fontsize=11, fontweight="bold")
    ax2_a.set_xlabel("Survivor Coverage Difference vs White Reference (pp)", fontsize=11, fontweight="bold")
    ax2_a.set_xlim(-4.6, 4.6)
    ax2_a.set_ylim(-0.5, len(races) - 0.3)
    ax2_a.set_title("A. Subgroup Survivor Disparity vs White Patients (Table 7)\n(Asian & Black Patients Face Statistically Significant Under-coverage)",
                    fontsize=11.5, fontweight="bold", pad=10)
    ax2_a.legend(loc="lower right", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.5)
    ax2_a.grid(True, axis="x", zorder=0)

    # -------------------------------------------------------------------------
    # Panel B: Calibration-in-the-Large (CITL = p_hat - y) across Demographics
    # -------------------------------------------------------------------------
    groups_citl = ["Black", "White", "Asian", "Hispanic", "Other Race", "Medicaid", "Medicare", "Private", "Other Ins."]
    citl_vals = [+12.9, +4.1, +8.1, +7.3, -34.9, -2.3, -3.6, +2.9, -19.0]  # in 10^-3
    citl_colors = ["#DC2626" if c < 0 else "#2563EB" for c in citl_vals]

    y_citl = np.arange(len(groups_citl))
    ax2_b.barh(y_citl, citl_vals, height=0.52, color=citl_colors, edgecolor="#0F172A",
               linewidth=0.9, alpha=0.90, zorder=3)
    ax2_b.axvline(0, color="#0F172A", linestyle="--", linewidth=1.3, zorder=2)

    for i in range(len(groups_citl)):
        val = citl_vals[i]
        if val < 0:
            ax2_b.text(val - 1.2, i, f"{val:+.1f}", va="center", ha="right",
                       fontsize=8.5, fontweight="bold", color="#7F1D1D", zorder=5)
        else:
            ax2_b.text(val + 1.2, i, f"{val:+.1f}", va="center", ha="left",
                       fontsize=8.5, fontweight="bold", color="#1E3A8A", zorder=5)

    ax2_b.set_yticks(y_citl)
    ax2_b.set_yticklabels(groups_citl, fontsize=10, fontweight="bold")
    ax2_b.set_xlabel(r"CITL ($\bar{p} - \bar{y}$) [$\times 10^{-3}$] (← Risk Under-prediction | Over-prediction →)",
                     fontsize=10.5, fontweight="bold")
    ax2_b.set_xlim(-46.0, 22.0)
    ax2_b.set_ylim(-0.6, len(groups_citl) - 0.4)
    ax2_b.set_title("B. Model Calibration-in-the-Large (Exploratory Bias Audit)\n(Black: Over-prediction [+12.9]; Other Race: Under-prediction [−34.9])",
                    fontsize=11.5, fontweight="bold", pad=10)
    ax2_b.grid(True, axis="x", zorder=0)

    # -------------------------------------------------------------------------
    # Panel C: Complete Repair across Racial and Payer Subgroups
    # -------------------------------------------------------------------------
    demo_groups = ["Asian", "Black", "Hispanic", "Other Race", "White", "Medicaid", "Medicare", "Private", "Other Ins."]
    g_d = [88.64, 91.04, 87.62, 91.35, 89.61, 87.97, 91.45, 86.60, 92.34]
    m_d = [91.18, 90.87, 90.28, 90.20, 90.08, 90.56, 90.18, 90.25, 90.52]

    x_demo = np.arange(len(demo_groups))
    w_demo = 0.35

    ax2_c.bar(x_demo - w_demo/2, g_d, w_demo,
              label="Baseline Global Conformal Death Coverage (Unequal)",
              color="#1E3A8A", edgecolor="#0F172A", linewidth=1.0, zorder=3)
    ax2_c.bar(x_demo + w_demo/2, m_d, w_demo,
              label="Mondrian Class-Conditional Death Coverage (Equitable)",
              color="#0D9488", edgecolor="#0F172A", linewidth=1.0, zorder=3)

    ax2_c.axhline(90.0, color="#DC2626", linestyle="--", linewidth=1.5,
                  label="Nominal 90.0% Target Coverage", zorder=2)

    # White percentage numbers placed at safe height (y = 80.0) — ZERO line collisions!
    for i in range(len(demo_groups)):
        diff = m_d[i] - g_d[i]
        ax2_c.text(x_demo[i] - w_demo/2, 80.0, f"{g_d[i]:.1f}%",
                   ha="center", va="center", color="white", fontsize=8.5, fontweight="bold", zorder=5)
        ax2_c.text(x_demo[i] + w_demo/2, 80.0, f"{m_d[i]:.1f}%",
                   ha="center", va="center", color="white", fontsize=8.5, fontweight="bold", zorder=5)

        ax2_c.text(x_demo[i], max(g_d[i], m_d[i]) + 1.4, f"Δ {diff:+.1f} pp",
                   ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0F172A",
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=0.7),
                   zorder=5)

    ax2_c.set_xticks(x_demo)
    ax2_c.set_xticklabels(demo_groups, fontsize=11, fontweight="bold")
    ax2_c.set_ylabel("Class-Conditional Death Coverage (%)", fontsize=11, fontweight="bold")
    ax2_c.set_ylim(73.0, 102.0)
    ax2_c.set_title("C. Restoration of Demographic Parity: All Racial and Payer Subgroups Enforced to 90% Nominal Coverage",
                    fontsize=12, fontweight="bold", pad=10)
    ax2_c.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=True,
                 facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=10, columnspacing=1.8)
    ax2_c.grid(True, axis="y", zorder=0)

    fig2.suptitle(
        "Figure 2: Racial and Socioeconomic Fairness Audit in ICU Conformal Prediction\n"
        "Baseline Disparities in Survivor Coverage and Risk Calibration Restored to Full Nominal Equity via Mondrian Calibration",
        fontsize=13.5, fontweight="bold", y=0.96
    )

    out_fig2 = FIGURES_DIR / "figure2_racial_and_payer_equity.png"
    fig2.savefig(out_fig2, dpi=300, bbox_inches="tight")
    plt.close(fig2)
    print(f"Saved: {out_fig2}")
    print("Master Figures 1 and 2 successfully generated!")


if __name__ == "__main__":
    generate_figures()
