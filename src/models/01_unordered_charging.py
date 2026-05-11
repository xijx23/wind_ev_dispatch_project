"""Baseline unordered EV charging simulation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config_loader import load_config, output_path
from src.common.constants import MAIN_PERIODS
from src.common.io_utils import write_csv


def simulate_unordered_charging(config: dict | None = None) -> pd.DataFrame:
    cfg = config or load_config()
    ev_info = pd.read_csv(output_path("ev_info", cfg))
    time_slots = pd.read_csv(output_path("time_slots_56", cfg))[["t", "time_label"]]
    availability = np.load(output_path("ev_availability_56", cfg))["availability"].astype(bool)

    ev_cfg = cfg["ev"]
    dt_h = cfg["time"]["dt_h"]
    p_kw = float(ev_cfg["default_charge_power_kw"])
    eta_ch = float(ev_cfg["charge_efficiency"])
    charge_need_kwh = float(ev_cfg["charge_need_kwh"])

    remaining = np.full(len(ev_info), charge_need_kwh, dtype=float)
    p_matrix_kw = np.zeros_like(availability, dtype=float)

    for t in range(MAIN_PERIODS):
        can_charge = availability[:, t] & (remaining > 1e-9)
        delivered_if_full = p_kw * eta_ch * dt_h
        p_this = np.minimum(p_kw, remaining / (eta_ch * dt_h))
        p_matrix_kw[can_charge, t] = p_this[can_charge]
        remaining[can_charge] -= np.minimum(remaining[can_charge], delivered_if_full)

    p_ch_mw = p_matrix_kw.sum(axis=0) / 1000.0
    result = time_slots.copy()
    result["p_ev_ch_mw"] = p_ch_mw
    result["p_ev_dis_mw"] = 0.0
    result["p_ev_net_mw"] = result["p_ev_ch_mw"]
    result["ev_count_charging"] = (p_matrix_kw > 0).sum(axis=0).astype(int)
    result["charged_energy_mwh"] = result["p_ev_ch_mw"] * dt_h * eta_ch
    result["unserved_energy_mwh"] = remaining.sum() / 1000.0
    return result


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    result = simulate_unordered_charging(cfg)
    return {"unordered_ev_load_56": str(write_csv(result, output_path("unordered_ev_load_56", cfg)))}


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
