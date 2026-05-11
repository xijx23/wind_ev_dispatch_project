"""Build EV aggregate boundary tables for ordered and V2G scenarios."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config_loader import load_config, output_path
from src.common.constants import MAIN_PERIODS
from src.common.io_utils import write_csv


def _mode_row(mode_params: pd.DataFrame, scenario: str) -> pd.Series:
    match = mode_params.loc[mode_params["scenario"] == scenario]
    if match.empty:
        raise ValueError(f"Missing EV mode params for scenario={scenario}")
    return match.iloc[0]


def build_aggregate_bounds(scenario: str, config: dict | None = None) -> pd.DataFrame:
    cfg = config or load_config()
    time_slots = pd.read_csv(output_path("time_slots_56", cfg))[["t", "time_label"]]
    ev_info = pd.read_csv(output_path("ev_info", cfg))
    availability = np.load(output_path("ev_availability_56", cfg))["availability"].astype(bool)
    mode_params = pd.read_csv(output_path("ev_mode_params", cfg))
    mode = _mode_row(mode_params, scenario)

    online_count = availability.sum(axis=0).astype(int)
    dt_h = float(cfg["time"]["dt_h"])
    p_ch_max_mw = online_count * float(mode["p_ch_max_kw"]) / 1000.0
    p_dis_max_mw = online_count * float(mode["p_dis_max_kw"]) / 1000.0

    ev_cfg = cfg["ev"]
    total_initial_mwh = len(ev_info) * float(ev_cfg["initial_energy_kwh"]) / 1000.0
    total_target_mwh = len(ev_info) * float(ev_cfg["target_energy_kwh"]) / 1000.0
    total_min_mwh = len(ev_info) * float(ev_cfg["minimum_energy_kwh"]) / 1000.0
    total_max_mwh = len(ev_info) * float(ev_cfg["battery_capacity_kwh"]) / 1000.0

    df = time_slots.copy()
    df["scenario"] = scenario
    df["online_count"] = online_count
    df["p_ch_max_mw"] = p_ch_max_mw
    df["p_dis_max_mw"] = p_dis_max_mw
    df["e_initial_total_mwh"] = total_initial_mwh
    df["e_target_total_mwh"] = total_target_mwh
    df["e_min_total_mwh"] = total_min_mwh
    df["e_max_total_mwh"] = total_max_mwh
    df["cumulative_ch_energy_cap_mwh"] = np.cumsum(p_ch_max_mw * dt_h * float(mode["eta_ch"]))
    df["cumulative_dis_energy_cap_mwh"] = np.cumsum(p_dis_max_mw * dt_h / max(float(mode["eta_dis"]), 1e-9))
    df["remaining_charge_need_mwh"] = max(total_target_mwh - total_initial_mwh, 0.0)
    return df


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    ordered = build_aggregate_bounds("ordered", cfg)
    v2g = build_aggregate_bounds("v2g", cfg)
    return {
        "ev_agg_bounds_ordered_56": str(write_csv(ordered, output_path("ev_agg_bounds_ordered_56", cfg))),
        "ev_agg_bounds_v2g_56": str(write_csv(v2g, output_path("ev_agg_bounds_v2g_56", cfg))),
    }


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
