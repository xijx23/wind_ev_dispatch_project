"""Generate summary tables for dispatch, penetration, wind curtailment, and price response."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config_loader import load_config, output_path
from src.common.io_utils import write_csv


SCENARIOS = ("unordered", "ordered", "v2g")
SCENARIO_LABELS = {"unordered": "Unordered", "ordered": "Ordered", "v2g": "V2G"}


def _table_dir(cfg: dict) -> Path:
    path = Path(cfg["paths"]["results_dir"]) / "tables"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _dispatch_path(cfg: dict, scenario: str) -> Path:
    if scenario == "unordered":
        return output_path("dispatch_unordered", cfg)
    return Path(cfg["paths"]["results_dir"]) / "dispatch" / f"dispatch_{scenario}.csv"


def _load_dispatches(cfg: dict) -> dict[str, pd.DataFrame]:
    dispatches: dict[str, pd.DataFrame] = {}
    for scenario in SCENARIOS:
        path = _dispatch_path(cfg, scenario)
        if path.exists() and path.stat().st_size > 0:
            dispatches[scenario] = pd.read_csv(path)
    return dispatches


def generate_dispatch_tables(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    dt_h = float(cfg["time"]["dt_h"])
    tables = _table_dir(cfg)
    dispatches = _load_dispatches(cfg)

    rows: list[dict[str, float | str]] = []
    curtail_rows: list[dict[str, float | str]] = []
    cost_rows: list[dict[str, float | str]] = []
    for scenario, df in dispatches.items():
        ev_ch_mwh = float((df["p_ev_ch_mw"] * dt_h).sum())
        ev_dis_mwh = float((df["p_ev_dis_mw"] * dt_h).sum())
        wind_used_mwh = float((df["p_wind_used_mw"] * dt_h).sum())
        wind_curtail_mwh = float((df["p_wind_curtailed_mw"] * dt_h).sum())
        total_cost_usd = float(df["total_cost_usd"].sum())
        thermal_energy_mwh = float((df["p_th_total_mw"] * dt_h).sum())
        rows.append(
            {
                "scenario": scenario,
                "scenario_label": SCENARIO_LABELS[scenario],
                "ev_charge_mwh": ev_ch_mwh,
                "ev_discharge_mwh": ev_dis_mwh,
                "ev_net_mwh": ev_ch_mwh - ev_dis_mwh,
                "thermal_energy_mwh": thermal_energy_mwh,
                "wind_used_mwh": wind_used_mwh,
                "wind_curtailed_mwh": wind_curtail_mwh,
                "total_cost_usd": total_cost_usd,
            }
        )
        curtail_rows.append(
            {
                "scenario": scenario,
                "wind_used_mwh": wind_used_mwh,
                "wind_curtailed_mwh": wind_curtail_mwh,
                "wind_available_mwh": wind_used_mwh + wind_curtail_mwh,
                "curtailment_rate": wind_curtail_mwh / (wind_used_mwh + wind_curtail_mwh)
                if wind_used_mwh + wind_curtail_mwh > 0
                else 0.0,
            }
        )
        cost_rows.append(
            {
                "scenario": scenario,
                "total_cost_usd": total_cost_usd,
                "thermal_energy_mwh": thermal_energy_mwh,
                "average_cost_usd_per_mwh": total_cost_usd / thermal_energy_mwh
                if thermal_energy_mwh > 0
                else 0.0,
            }
        )

    outputs = {
        "table_dispatch_summary": str(write_csv(pd.DataFrame(rows), tables / "table_dispatch_summary.csv")),
        "table_wind_curtailment_summary": str(
            write_csv(pd.DataFrame(curtail_rows), tables / "table_wind_curtailment_summary.csv")
        ),
        "table_cost_summary": str(write_csv(pd.DataFrame(cost_rows), tables / "table_cost_summary.csv")),
    }
    return outputs


def generate_penetration_table(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    tables = _table_dir(cfg)
    src = Path(cfg["paths"]["results_dir"]) / "sensitivity" / "penetration_sensitivity.csv"
    if not src.exists() or src.stat().st_size == 0:
        df = pd.DataFrame()
    else:
        df = pd.read_csv(src)
        df = df.sort_values(["scenario", "penetration_scale"]).reset_index(drop=True)
    path = tables / "table_penetration_summary.csv"
    return {"table_penetration_summary": str(write_csv(df, path))}


def generate_price_table(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    tables = _table_dir(cfg)
    src = Path(cfg["paths"]["results_dir"]) / "price" / "price_response_summary.csv"
    if not src.exists() or src.stat().st_size == 0:
        df = pd.DataFrame()
    else:
        df = pd.read_csv(src)
        df = df.rename(
            columns={
                "scenario": "Scenario",
                "weighted_wind_mw": "Weighted Wind (MW)",
                "elec_cost_kyuan": "Electricity Cost (kYuan)",
                "wind_corr": "Wind Correlation",
                "discomfort_kyuan": "Discomfort Cost (kYuan)",
                "total_cost_kyuan": "Total Cost (kYuan)",
            }
        )
    path = tables / "table_price_summary.csv"
    return {"table_price_summary": str(write_csv(df, path))}


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    outputs: dict[str, str] = {}
    outputs.update(generate_dispatch_tables(cfg))
    outputs.update(generate_penetration_table(cfg))
    outputs.update(generate_price_table(cfg))
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
