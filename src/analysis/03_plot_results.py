"""Generate core figures for quick inspection."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from src.common.config_loader import load_config, project_path


def _save_line(df: pd.DataFrame, y_cols: list[str], title: str, path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    for col in y_cols:
        ax.plot(df.iloc[:, 0], df[col], label=col, linewidth=1.8)
    ax.set_title(title)
    ax.set_xlabel(df.columns[0])
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    fig_dir = project_path(cfg["paths"]["figures_dir"])
    outputs = {}
    load_wind = pd.read_csv(project_path("data/processed/load_wind_56.csv"))
    _save_line(load_wind, ["load_mw", "wind_forecast_mw"], "Load and Wind Forecast", fig_dir / "fig_01_load_wind.png")
    outputs["fig_01_load_wind"] = str(fig_dir / "fig_01_load_wind.png")

    unordered = pd.read_csv(project_path("data/processed/unordered_ev_load_56.csv"))
    _save_line(unordered, ["p_ev_ch_mw"], "Unordered EV Charging", fig_dir / "fig_02_unordered_ev_load.png")
    outputs["fig_02_unordered_ev_load"] = str(fig_dir / "fig_02_unordered_ev_load.png")

    dispatch = pd.concat(
        [pd.read_csv(project_path(cfg["paths"]["dispatch_dir"], f"dispatch_{s}.csv")) for s in ["unordered", "ordered", "v2g"]],
        ignore_index=True,
    )
    pivot = dispatch.pivot(index="t", columns="scenario", values="wind_curtail_mw").reset_index()
    _save_line(pivot, ["unordered", "ordered", "v2g"], "Wind Curtailment by Scenario", fig_dir / "fig_06_wind_curtailment_comparison.png")
    outputs["fig_06_wind_curtailment_comparison"] = str(fig_dir / "fig_06_wind_curtailment_comparison.png")
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
