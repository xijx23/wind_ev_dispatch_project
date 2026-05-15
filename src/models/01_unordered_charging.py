"""Simulate the unordered EV charging baseline for member A."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config_loader import load_config, output_path
from src.common.constants import MAIN_PERIODS
from src.common.io_utils import write_csv


def _unordered_mode(mode_params: pd.DataFrame) -> pd.Series:
    match = mode_params.loc[mode_params["scenario"] == "unordered"]
    if match.empty:
        raise ValueError("ev_mode_params.csv missing scenario='unordered'")
    return match.iloc[0]


def simulate_unordered_charging(config: dict | None = None) -> pd.DataFrame:
    """Return the 56-slot unordered charging load curve.

    Unordered charging is modeled as immediate charging after arrival. A vehicle
    charges in every available slot until its battery-side energy demand is met.
    The last charging slot may use a partial grid power to avoid overcharging.
    """
    cfg = config or load_config()
    dt_h = float(cfg["time"]["dt_h"])

    ev_info = pd.read_csv(output_path("ev_info", cfg))
    availability = np.load(output_path("ev_availability_56", cfg))["availability"].astype(bool)
    load_wind = pd.read_csv(output_path("load_wind_56", cfg))
    online_summary = pd.read_csv(output_path("ev_online_summary_56", cfg))
    mode_params = pd.read_csv(output_path("ev_mode_params", cfg))
    mode = _unordered_mode(mode_params)

    p_ch_kw = float(mode["p_ch_max_kw"])
    eta_ch = float(mode["eta_ch"])
    charge_need_kwh = float(mode["charge_need_kwh"])

    remaining_battery_need_kwh = np.full(len(ev_info), charge_need_kwh, dtype=float)
    p_ev_matrix_kw = np.zeros((len(ev_info), MAIN_PERIODS), dtype=float)

    for t in range(MAIN_PERIODS):
        can_charge = availability[:, t] & (remaining_battery_need_kwh > 1e-9)
        if not np.any(can_charge):
            continue
        full_slot_battery_kwh = p_ch_kw * eta_ch * dt_h
        p_this_kw = np.minimum(p_ch_kw, remaining_battery_need_kwh / (eta_ch * dt_h))
        p_ev_matrix_kw[can_charge, t] = p_this_kw[can_charge]
        remaining_battery_need_kwh[can_charge] -= np.minimum(
            remaining_battery_need_kwh[can_charge],
            full_slot_battery_kwh,
        )

    p_ev_ch_mw = p_ev_matrix_kw.sum(axis=0) / 1000.0
    battery_energy_mwh = p_ev_ch_mw * eta_ch * dt_h
    result = load_wind[["t", "time_label", "load_mw", "wind_forecast_mw"]].copy()
    result["online_count"] = online_summary["online_count"].to_numpy(dtype=int)
    result["charging_count"] = (p_ev_matrix_kw > 1e-9).sum(axis=0).astype(int)
    result["p_ev_ch_mw"] = p_ev_ch_mw
    result["p_ev_dis_mw"] = 0.0
    result["p_ev_net_mw"] = result["p_ev_ch_mw"]
    result["system_load_with_unordered_ev_mw"] = result["load_mw"] + result["p_ev_ch_mw"]
    result["grid_energy_mwh"] = result["p_ev_ch_mw"] * dt_h
    result["battery_energy_mwh"] = battery_energy_mwh
    result["cumulative_battery_energy_mwh"] = battery_energy_mwh.cumsum()
    total_need_mwh = charge_need_kwh * len(ev_info) / 1000.0
    result["remaining_battery_need_mwh"] = np.maximum(total_need_mwh - np.cumsum(battery_energy_mwh), 0.0)
    result["unserved_battery_need_mwh_at_end"] = remaining_battery_need_kwh.sum() / 1000.0
    return result


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    result = simulate_unordered_charging(cfg)
    return {"dispatch_unordered": str(write_csv(result, output_path("dispatch_unordered", cfg)))}


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
