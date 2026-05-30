"""Plot EMS dispatch and sensitivity results."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.common.config_loader import load_config, output_path


plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

SCENARIOS = ("unordered", "ordered", "v2g")
SCENARIO_LABELS = {"unordered": "Unordered", "ordered": "Ordered", "v2g": "V2G"}


def _dispatch_path(cfg: dict, scenario: str) -> Path:
    if scenario == "unordered":
        return output_path("dispatch_unordered", cfg)
    return Path(cfg["paths"]["results_dir"]) / "dispatch" / f"dispatch_{scenario}.csv"


def _load_dispatches(cfg: dict) -> dict[str, pd.DataFrame]:
    dispatches: dict[str, pd.DataFrame] = {}
    for scenario in SCENARIOS:
        path = _dispatch_path(cfg, scenario)
        if path.exists():
            dispatches[scenario] = pd.read_csv(path)
    return dispatches


def _format_time_axis(ax, df: pd.DataFrame) -> None:
    ticks = list(range(0, len(df), 8))
    if len(df) - 1 not in ticks:
        ticks.append(len(df) - 1)
    ax.set_xticks(ticks)
    if "time_label" in df.columns:
        ax.set_xticklabels(df.loc[ticks, "time_label"], rotation=30, ha="right")
    ax.grid(True, alpha=0.25)


def _save(fig: plt.Figure, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return str(path)


def plot_dispatch_curves(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    fig_dir = Path(cfg["paths"]["figures_dir"])
    dispatches = _load_dispatches(cfg)
    if not dispatches:
        return {}

    outputs: dict[str, str] = {}
    first = next(iter(dispatches.values()))

    fig, ax = plt.subplots(figsize=(10, 5))
    for scenario, df in dispatches.items():
        ax.plot(df["t"], df["p_ev_net_mw"], label=SCENARIO_LABELS[scenario], linewidth=1.7)
    ax.set_title("EV Net Charging Power by Scenario")
    ax.set_xlabel("Time")
    ax.set_ylabel("Power (MW)")
    _format_time_axis(ax, first)
    ax.legend()
    outputs["dispatch_ev_net_power"] = _save(fig, fig_dir / "dispatch_ev_net_power.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    for scenario, df in dispatches.items():
        ax.plot(df["t"], df["p_wind_curtailed_mw"], label=SCENARIO_LABELS[scenario], linewidth=1.7)
    ax.set_title("Wind Curtailment by Scenario")
    ax.set_xlabel("Time")
    ax.set_ylabel("Curtailment (MW)")
    _format_time_axis(ax, first)
    ax.legend()
    outputs["dispatch_wind_curtailment"] = _save(fig, fig_dir / "dispatch_wind_curtailment.png")

    if "v2g" in dispatches:
        df = dispatches["v2g"]
        thermal_cols = [c for c in df.columns if c.startswith("p_th_") and "total" not in c]
        fig, ax = plt.subplots(figsize=(11, 5.5))
        ax.stackplot(df["t"], *[df[c] for c in thermal_cols], labels=thermal_cols, alpha=0.72)
        ax.plot(df["t"], df["p_wind_used_mw"], label="Wind used", color="green", linewidth=2)
        ax.plot(df["t"], df["system_load_mw"], label="System load incl. EV", color="red", linestyle="--", linewidth=2)
        ax.set_title("V2G Scenario Dispatch Stack")
        ax.set_xlabel("Time")
        ax.set_ylabel("Power (MW)")
        _format_time_axis(ax, df)
        ax.legend(loc="upper left", ncol=2)
        outputs["dispatch_v2g_stacked"] = _save(fig, fig_dir / "dispatch_v2g_stacked.png")

    sens_path = Path(cfg["paths"]["results_dir"]) / "sensitivity" / "penetration_sensitivity.csv"
    if sens_path.exists():
        sens = pd.read_csv(sens_path)
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.lineplot(data=sens, x="penetration_scale", y="total_thermal_cost_usd", hue="scenario", marker="o", ax=ax)
        ax.set_title("Total Thermal Cost vs EV Penetration")
        ax.set_xlabel("Penetration scale")
        ax.set_ylabel("Thermal cost (USD)")
        ax.grid(True, alpha=0.25)
        outputs["dispatch_sensitivity_cost"] = _save(fig, fig_dir / "dispatch_sensitivity_cost.png")

        fig, ax = plt.subplots(figsize=(9, 5))
        sns.lineplot(data=sens, x="penetration_scale", y="total_wind_curtailed_mwh", hue="scenario", marker="o", ax=ax)
        ax.set_title("Total Wind Curtailment vs EV Penetration")
        ax.set_xlabel("Penetration scale")
        ax.set_ylabel("Curtailed wind (MWh)")
        ax.grid(True, alpha=0.25)
        outputs["dispatch_sensitivity_curtailment"] = _save(fig, fig_dir / "dispatch_sensitivity_curtailment.png")

    outputs.update(plot_named_dispatch_figures(cfg, dispatches))
    return outputs


def plot_named_dispatch_figures(cfg: dict, dispatches: dict[str, pd.DataFrame]) -> dict[str, str]:
    fig_dir = Path(cfg["paths"]["figures_dir"])
    outputs: dict[str, str] = {}
    first = next(iter(dispatches.values()))

    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    for scenario, df in dispatches.items():
        ax.plot(df["t"], df["p_ev_ch_mw"], label=f"{SCENARIO_LABELS[scenario]} charge", linewidth=1.6)
        if df["p_ev_dis_mw"].abs().max() > 1e-8:
            ax.plot(df["t"], -df["p_ev_dis_mw"], label=f"{SCENARIO_LABELS[scenario]} discharge", linewidth=1.6, linestyle="--")
    ax.set_title("EV Charging and Discharging Power")
    ax.set_xlabel("Time")
    ax.set_ylabel("Power (MW)")
    _format_time_axis(ax, first)
    ax.legend(ncol=2)
    outputs["fig_05_ev_power_comparison"] = _save(fig, fig_dir / "fig_05_ev_power_comparison.png")

    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    for scenario, df in dispatches.items():
        ax.plot(df["t"], df["p_wind_curtailed_mw"], label=SCENARIO_LABELS[scenario], linewidth=1.7)
    ax.set_title("Wind Curtailment Comparison")
    ax.set_xlabel("Time")
    ax.set_ylabel("Curtailment (MW)")
    _format_time_axis(ax, first)
    ax.legend()
    outputs["fig_06_wind_curtailment_comparison"] = _save(fig, fig_dir / "fig_06_wind_curtailment_comparison.png")

    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    for scenario, df in dispatches.items():
        ax.plot(df["t"], df["p_th_total_mw"], label=SCENARIO_LABELS[scenario], linewidth=1.7)
    ax.set_title("Thermal Output Comparison")
    ax.set_xlabel("Time")
    ax.set_ylabel("Thermal output (MW)")
    _format_time_axis(ax, first)
    ax.legend()
    outputs["fig_07_thermal_output_comparison"] = _save(fig, fig_dir / "fig_07_thermal_output_comparison.png")

    cost_rows = [
        {"scenario": SCENARIO_LABELS[scenario], "thermal_cost_usd": df["thermal_cost_usd"].sum()}
        for scenario, df in dispatches.items()
    ]
    cost_df = pd.DataFrame(cost_rows)
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    ax.bar(cost_df["scenario"], cost_df["thermal_cost_usd"])
    ax.set_title("Total Thermal Cost Comparison")
    ax.set_ylabel("Cost (USD)")
    ax.grid(True, axis="y", alpha=0.25)
    outputs["fig_08_cost_comparison"] = _save(fig, fig_dir / "fig_08_cost_comparison.png")

    sens_path = Path(cfg["paths"]["results_dir"]) / "sensitivity" / "penetration_sensitivity.csv"
    if sens_path.exists():
        sens = pd.read_csv(sens_path)
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
        sns.lineplot(data=sens, x="penetration_scale", y="total_thermal_cost_usd", hue="scenario", marker="o", ax=axes[0])
        axes[0].set_title("Cost Sensitivity")
        axes[0].set_xlabel("EV penetration scale")
        axes[0].set_ylabel("Thermal cost (USD)")
        axes[0].grid(True, alpha=0.25)
        sns.lineplot(data=sens, x="penetration_scale", y="total_wind_curtailed_mwh", hue="scenario", marker="o", ax=axes[1])
        axes[1].set_title("Curtailment Sensitivity")
        axes[1].set_xlabel("EV penetration scale")
        axes[1].set_ylabel("Curtailed wind (MWh)")
        axes[1].grid(True, alpha=0.25)
        outputs["fig_09_penetration_sensitivity"] = _save(fig, fig_dir / "fig_09_penetration_sensitivity.png")
    return outputs


def run(config: dict | None = None) -> dict[str, str]:
    return plot_dispatch_curves(config)


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
