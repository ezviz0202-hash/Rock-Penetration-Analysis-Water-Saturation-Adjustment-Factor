import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MultipleLocator
import seaborn as sns
from scipy.stats import f_oneway

from src.data_generator import generate_dataset, SATURATION_LEVELS, IMPACT_ENERGIES, ROCK_PARAMS
from src.signal_processing import smooth_force_signal, detect_peaks
from src.statistical_analysis import (
    run_anova_by_saturation,
    compute_pearson_correlation,
    group_means_by_saturation,
    build_correlation_matrix,
)
from src.adjustment_factor import (
    compute_adjustment_factors,
    fit_all_models,
    select_best_model,
    MODELS,
)

os.makedirs("figures", exist_ok=True)
os.makedirs("data", exist_ok=True)

PALETTE_SW = {
    0.00: "#1a1a2e",
    0.25: "#16213e",
    0.50: "#0f3460",
    0.75: "#2b6cb0",
    1.00: "#63b3ed",
}
ROCK_COLORS = {"andesite": "#c0392b", "tuff": "#2980b9"}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "--",
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
})

df, ft_curves = generate_dataset(seed=42)
df.to_csv("data/experimental_data.csv", index=False)


def fig1_force_time_curves():
    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    fig.suptitle("Force–Time Curves at Varying Water Saturation Levels", fontsize=13, fontweight="bold", y=1.01)
    for col, energy in enumerate(IMPACT_ENERGIES):
        for row, rock in enumerate(["andesite", "tuff"]):
            ax = axes[row][col]
            for sw in SATURATION_LEVELS:
                t, force = ft_curves[(rock, sw, energy)]
                dt = t[1] - t[0]
                force_smooth = smooth_force_signal(force, dt)
                label = f"Sw={int(sw*100)}%"
                ax.plot(t * 1000, force_smooth, color=PALETTE_SW[sw], lw=1.6, label=label, alpha=0.9)
            ax.set_xlabel("Time (ms)", fontsize=9)
            ax.set_ylabel("Impact Force (kN)", fontsize=9)
            ax.set_title(f"{rock.capitalize()} | E={energy} J", fontsize=9, fontweight="bold")
            if row == 0 and col == 2:
                ax.legend(fontsize=7, loc="upper right", framealpha=0.7)
    plt.tight_layout()
    plt.savefig("figures/fig1_force_time_curves.png")
    plt.close()
    print("[fig1] saved")


def fig2_penetration_depth():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Penetration Depth vs Water Saturation", fontsize=13, fontweight="bold")
    for ax, rock in zip(axes, ["andesite", "tuff"]):
        for energy in IMPACT_ENERGIES:
            summary = group_means_by_saturation(df, "penetration_mm", rock_type=rock, energy=energy)
            sw = summary["water_saturation"].values * 100
            ax.errorbar(
                sw, summary["mean"].values, yerr=summary["std"].values,
                marker="o", capsize=4, lw=1.8, markersize=6,
                label=f"E={energy} J", alpha=0.9,
            )
        ax.set_xlabel("Water Saturation (%)", fontsize=10)
        ax.set_ylabel("Penetration Depth (mm)", fontsize=10)
        ax.set_title(f"{rock.capitalize()}", fontsize=11, fontweight="bold")
        ax.legend(fontsize=9)
        ax.set_xticks([0, 25, 50, 75, 100])
    plt.tight_layout()
    plt.savefig("figures/fig2_penetration_depth.png")
    plt.close()
    print("[fig2] saved")


def fig3_specific_energy():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Specific Energy vs Water Saturation", fontsize=13, fontweight="bold")
    for ax, rock in zip(axes, ["andesite", "tuff"]):
        sub = df[df["rock_type"] == rock]
        bp_data = [sub[sub["water_saturation"] == sw]["specific_energy_MJm3"].values for sw in SATURATION_LEVELS]
        bp = ax.boxplot(bp_data, patch_artist=True, widths=0.55,
                        medianprops=dict(color="white", lw=2.5))
        for patch, sw in zip(bp["boxes"], SATURATION_LEVELS):
            patch.set_facecolor(PALETTE_SW[sw])
            patch.set_alpha(0.85)
        ax.set_xticklabels([f"{int(s*100)}%" for s in SATURATION_LEVELS], fontsize=9)
        ax.set_xlabel("Water Saturation (%)", fontsize=10)
        ax.set_ylabel("Specific Energy (MJ/m³)", fontsize=10)
        ax.set_title(f"{rock.capitalize()}", fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig("figures/fig3_specific_energy.png")
    plt.close()
    print("[fig3] saved")


def fig4_correlation_heatmap():
    cols = ["water_saturation", "impact_energy_J", "peak_force_kN",
            "penetration_mm", "specific_energy_MJm3", "impact_efficiency"]
    labels = ["Sw", "Energy", "Peak F", "Pen. D", "Spec. E", "Efficiency"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Pearson Correlation Matrix", fontsize=13, fontweight="bold")
    for ax, rock in zip(axes, ["andesite", "tuff"]):
        sub = df[df["rock_type"] == rock]
        corr = sub[cols].corr(method="pearson")
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        sns.heatmap(
            corr, ax=ax, annot=True, fmt=".2f", cmap="RdBu_r",
            vmin=-1, vmax=1, linewidths=0.5, square=True,
            xticklabels=labels, yticklabels=labels,
            cbar_kws={"shrink": 0.8},
        )
        ax.set_title(f"{rock.capitalize()}", fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig("figures/fig4_correlation_heatmap.png")
    plt.close()
    print("[fig4] saved")


def fig5_adjustment_factor():
    sw_dense = np.linspace(0, 1, 200)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Water-Saturation Adjustment Factor f(Sw) — Model Fitting", fontsize=13, fontweight="bold")
    model_styles = {
        "linear": ("--", "#e74c3c"),
        "quadratic": ("-.", "#8e44ad"),
        "exponential": (":", "#27ae60"),
        "power": ("-", "#e67e22"),
    }
    results_all = {}
    for ax, rock in zip(axes, ["andesite", "tuff"]):
        sub = df[(df["rock_type"] == rock) & (df["impact_energy_J"] == 120)]
        summary = group_means_by_saturation(sub, "penetration_mm")
        sw_pts, f_sw_pts, rop0 = compute_adjustment_factors(summary, "penetration_mm")
        fit_results = fit_all_models(sw_pts, f_sw_pts)
        best = select_best_model(fit_results)
        results_all[rock] = {"fit_results": fit_results, "best": best, "rop0": rop0}
        ax.scatter(sw_pts * 100, f_sw_pts, color="black", s=55, zorder=5, label="Observed", marker="D")
        for name, (ls, color) in model_styles.items():
            res = fit_results.get(name)
            if res is None:
                continue
            func = MODELS[name][0]
            params = list(res["params"].values())
            f_dense = func(sw_dense, *params)
            r2 = res["R2"]
            lbl = f"{name.capitalize()} (R²={r2:.3f})"
            lw = 2.5 if name == best else 1.4
            ax.plot(sw_dense * 100, f_dense, ls=ls, color=color, lw=lw, label=lbl, alpha=0.9)
        ax.axhline(1.0, color="gray", lw=0.8, ls="--", alpha=0.5)
        ax.set_xlabel("Water Saturation (%)", fontsize=10)
        ax.set_ylabel("f(Sw) = ROP / ROP₀", fontsize=10)
        ax.set_title(f"{rock.capitalize()} — Best: {best.capitalize()}", fontsize=11, fontweight="bold")
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.legend(fontsize=8, loc="upper right")
    plt.tight_layout()
    plt.savefig("figures/fig5_adjustment_factor.png")
    plt.close()
    print("[fig5] saved")
    return results_all


def fig6_anova_summary():
    indicators = ["penetration_mm", "specific_energy_MJm3", "peak_force_kN", "impact_efficiency"]
    ind_labels = ["Penetration Depth", "Specific Energy", "Peak Force", "Impact Efficiency"]
    rocks = ["andesite", "tuff"]
    f_vals = np.zeros((len(indicators), len(rocks)))
    p_vals = np.zeros((len(indicators), len(rocks)))
    for i, ind in enumerate(indicators):
        for j, rock in enumerate(rocks):
            res = run_anova_by_saturation(df, ind, rock_type=rock)
            f_vals[i, j] = res["F_statistic"]
            p_vals[i, j] = res["p_value"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("One-Way ANOVA: Effect of Water Saturation on Penetration Indicators", fontsize=12, fontweight="bold")
    for j, (ax, rock) in enumerate(zip(axes, rocks)):
        bars = ax.barh(ind_labels, f_vals[:, j], color=[ROCK_COLORS[rock]] * len(indicators), alpha=0.85, edgecolor="white")
        for bar, pv in zip(bars, p_vals[:, j]):
            sig = "***" if pv < 0.001 else "**" if pv < 0.01 else "*" if pv < 0.05 else "ns"
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    sig, va="center", fontsize=11, fontweight="bold")
        ax.set_xlabel("F-statistic", fontsize=10)
        ax.set_title(f"{rock.capitalize()}", fontsize=11, fontweight="bold")
        ax.set_xlim(0, f_vals.max() * 1.2)
    plt.tight_layout()
    plt.savefig("figures/fig6_anova_summary.png")
    plt.close()
    print("[fig6] saved")


def print_summary_table(results_all):
    print("\n" + "=" * 60)
    print("ADJUSTMENT FACTOR FITTING SUMMARY")
    print("=" * 60)
    for rock, data in results_all.items():
        print(f"\n[{rock.upper()}]  ROP₀ = {data['rop0']:.4f} mm/blow")
        for name, res in data["fit_results"].items():
            if res is None:
                continue
            params_str = ", ".join([f"{k}={v:.4f}" for k, v in res["params"].items()])
            marker = " ← BEST" if name == data["best"] else ""
            print(f"  {name:12s}  R²={res['R2']:.4f}  RMSE={res['RMSE']:.6f}  params: {params_str}{marker}")
    print("=" * 60)


if __name__ == "__main__":
    print("Running analysis pipeline...")
    fig1_force_time_curves()
    fig2_penetration_depth()
    fig3_specific_energy()
    fig4_correlation_heatmap()
    results_all = fig5_adjustment_factor()
    fig6_anova_summary()
    print_summary_table(results_all)
    print("\nAll figures saved to figures/")
    print("Dataset saved to data/experimental_data.csv")
