"""Plot EV decomposition diagnostics for member B."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from src.common.config_loader import load_config, output_path


SCENARIOS = ("ordered", "v2g")
SCENARIO_LABELS = {"ordered": "Ordered", "v2g": "V2G"}


def _format_time_axis(ax, df: pd.DataFrame) -> None:
    ticks = list(range(0, len(df), 8))
    if len(df) - 1 not in ticks:
        ticks.append(len(df) - 1)
    ax.set_xticks(ticks)
    ax.set_xticklabels(df.loc[ticks, "time_label"], rotation=30, ha="right")
    ax.grid(True, alpha=0.25)


def plot_decomposition_error(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 7.0), sharex=True)

    last_df: pd.DataFrame | None = None
    for scenario in SCENARIOS:
        df = pd.read_csv(output_path(f"decomposition_error_{scenario}", cfg))
        last_df = df
        label = SCENARIO_LABELS[scenario]
        axes[0].plot(df["t"], df["ch_error_mw"], label=f"{label} charge", linewidth=1.6)
        axes[0].plot(df["t"], df["dis_error_mw"], label=f"{label} discharge", linewidth=1.6, linestyle="--")
        axes[1].plot(df["t"], df["net_error_mw"], label=label, linewidth=1.7)

    axes[0].set_title("Per-Vehicle Decomposition Power Error")
    axes[0].set_ylabel("Power error (MW)")
    axes[0].legend(ncol=2)
    axes[1].set_ylabel("Net power error (MW)")
    axes[1].set_xlabel("Time")
    axes[1].legend()
    if last_df is not None:
        _format_time_axis(axes[1], last_df)
    axes[0].grid(True, alpha=0.25)
    fig.tight_layout()
    fig_path = output_path("fig_decomposition_error", cfg)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)
    return {"fig_decomposition_error": str(fig_path)}


def _sample_ev_ids(plan: pd.DataFrame, count: int = 5) -> list[int]:
    ev_windows = (
        plan[["ev_id", "departure_slot_exclusive"]]
        .drop_duplicates()
        .sort_values(["departure_slot_exclusive", "ev_id"])
    )
    if len(ev_windows) <= count:
        return ev_windows["ev_id"].astype(int).tolist()
    positions = [round(i * (len(ev_windows) - 1) / (count - 1)) for i in range(count)]
    return ev_windows.iloc[positions]["ev_id"].astype(int).tolist()


def plot_ev_soc_examples(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 7.0), sharex=True)

    last_df: pd.DataFrame | None = None
    for ax, scenario in zip(axes, SCENARIOS, strict=True):
        plan = pd.read_csv(output_path(f"ev_plan_{scenario}", cfg))
        last_df = plan.drop_duplicates("t")[["t", "time_label"]]
        for ev_id in _sample_ev_ids(plan):
            one = plan.loc[plan["ev_id"] == ev_id]
            ax.plot(one["t"], one["soc"], linewidth=1.4, label=f"EV {ev_id}")
        ax.set_title(f"{SCENARIO_LABELS[scenario]} EV SOC Examples")
        ax.set_ylabel("SOC")
        ax.set_ylim(0.15, 1.02)
        ax.legend(ncol=5, fontsize=8)
        ax.grid(True, alpha=0.25)

    axes[-1].set_xlabel("Time")
    if last_df is not None:
        _format_time_axis(axes[-1], last_df.reset_index(drop=True))
    fig.tight_layout()
    fig_path = output_path("fig_ev_soc_examples", cfg)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)
    return {"fig_ev_soc_examples": str(fig_path)}


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    outputs = {}
    outputs.update(plot_decomposition_error(cfg))
    outputs.update(plot_ev_soc_examples(cfg))
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
