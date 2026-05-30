"""Visualization for member A baseline outputs."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from src.common.config_loader import load_config, output_path, project_path


def _format_time_axis(ax, df: pd.DataFrame) -> None:
    ticks = list(range(0, len(df), 8))
    if len(df) - 1 not in ticks:
        ticks.append(len(df) - 1)
    ax.set_xticks(ticks)
    ax.set_xticklabels(df.loc[ticks, "time_label"], rotation=30, ha="right")
    ax.grid(True, alpha=0.25)


def plot_unordered_ev_load(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    unordered = pd.read_csv(output_path("dispatch_unordered", cfg))
    load_wind = pd.read_csv(output_path("load_wind_56", cfg))
    if "load_mw" not in unordered.columns:
        unordered = unordered.merge(load_wind[["t", "load_mw"]], on="t", how="left")
    system_load = (
        unordered["system_load_with_unordered_ev_mw"]
        if "system_load_with_unordered_ev_mw" in unordered.columns
        else unordered.get("system_load_mw", unordered["load_mw"] + unordered["p_ev_ch_mw"])
    )

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(unordered["t"], unordered["load_mw"], label="Base load", linewidth=1.8)
    ax.plot(unordered["t"], system_load, label="Load + unordered EV", linewidth=1.8)
    ax.bar(
        unordered["t"],
        unordered["p_ev_ch_mw"],
        label="Unordered EV charging",
        alpha=0.35,
        width=0.8,
    )
    ax.set_xlabel("Time")
    ax.set_ylabel("Power (MW)")
    ax.set_title("Unordered EV Charging Load")
    _format_time_axis(ax, unordered)
    ax.legend()
    fig.tight_layout()
    fig_path = output_path("fig_unordered_ev_load", cfg)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)
    return {"fig_unordered_ev_load": str(fig_path)}


def plot_load_wind(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    load_wind = pd.read_csv(output_path("load_wind_56", cfg))

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(load_wind["t"], load_wind["load_mw"], label="Base load", linewidth=1.8)
    ax.plot(load_wind["t"], load_wind["wind_forecast_mw"], label="Wind forecast", linewidth=1.8)
    ax.set_xlabel("Time")
    ax.set_ylabel("Power (MW)")
    ax.set_title("Load and Wind Forecast")
    _format_time_axis(ax, load_wind)
    ax.legend()
    fig.tight_layout()
    fig_path = project_path("results/figures/fig_01_load_wind.png", config=cfg)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)
    return {"fig_load_wind": str(fig_path)}


def plot_ev_online_summary(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    unordered = pd.read_csv(output_path("dispatch_unordered", cfg))
    online = pd.read_csv(output_path("ev_online_summary_56", cfg))
    if "online_count" not in unordered.columns:
        unordered = unordered.merge(online[["t", "online_count"]], on="t", how="left")
    if "charging_count" not in unordered.columns:
        unordered["charging_count"] = (unordered["p_ev_ch_mw"] > 1e-9).astype(int) * unordered["online_count"]

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(unordered["t"], unordered["online_count"], label="Online EVs", linewidth=1.8)
    ax.plot(unordered["t"], unordered["charging_count"], label="Charging EVs", linewidth=1.8)
    ax.set_xlabel("Time")
    ax.set_ylabel("Vehicle count")
    ax.set_title("EV Online and Charging Counts")
    _format_time_axis(ax, unordered)
    ax.legend()
    fig.tight_layout()
    fig_path = output_path("fig_ev_online_summary", cfg)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)
    return {"fig_ev_online_summary": str(fig_path)}


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    outputs = {}
    outputs.update(plot_load_wind(cfg))
    outputs.update(plot_unordered_ev_load(cfg))
    outputs.update(plot_ev_online_summary(cfg))
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
