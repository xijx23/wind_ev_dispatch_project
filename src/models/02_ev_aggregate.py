"""Build aggregate EV flexibility bounds for ordered and V2G scenarios.

The output files are the interface from member B to member C.  Power columns are
slot-wise grid-side limits, while energy columns are cumulative battery-side net
energy limits at the end of each 15-minute slot.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config_loader import load_config, output_path
from src.common.constants import MAIN_PERIODS
from src.common.io_utils import require_columns, write_csv


SCENARIOS = ("ordered", "v2g")


def _mode_params(mode_params: pd.DataFrame, scenario: str) -> pd.Series:
    match = mode_params.loc[mode_params["scenario"] == scenario]
    if match.empty:
        raise ValueError(f"ev_mode_params.csv missing scenario={scenario!r}")
    return match.iloc[0]


def _load_inputs(config: dict) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ev_info = pd.read_csv(output_path("ev_info", config))
    require_columns(
        ev_info,
        ["ev_id", "arrival_slot", "departure_slot_exclusive", "available_periods"],
        "ev_info",
    )

    availability_file = np.load(output_path("ev_availability_56", config))
    availability = availability_file["availability"].astype(bool)
    if availability.shape != (len(ev_info), MAIN_PERIODS):
        raise ValueError(
            "ev_availability_56.npz availability shape mismatch: "
            f"expected {(len(ev_info), MAIN_PERIODS)}, got {availability.shape}"
        )

    online_summary = pd.read_csv(output_path("ev_online_summary_56", config))
    require_columns(online_summary, ["t", "online_count"], "ev_online_summary_56")

    mode_params = pd.read_csv(output_path("ev_mode_params", config))
    time_slots = pd.read_csv(output_path("time_slots_56", config))
    require_columns(time_slots, ["t", "time_label"], "time_slots_56")
    return ev_info, availability, online_summary, mode_params, time_slots


def _energy_bounds_kwh(
    ev_info: pd.DataFrame,
    mode: pd.Series,
    scenario: str,
    dt_h: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return aggregate lower/upper cumulative energy bounds in kWh.

    Boundary index ``k`` means the end of slot ``k - 1``. The returned arrays
    have length 56 and correspond to k = 1..56 for direct joining with t = 0..55.
    """
    arrival = ev_info["arrival_slot"].to_numpy(dtype=int)
    departure = ev_info["departure_slot_exclusive"].to_numpy(dtype=int)

    p_ch_kw = float(mode["p_ch_max_kw"])
    p_dis_kw = float(mode["p_dis_max_kw"])
    eta_ch = float(mode["eta_ch"])
    eta_dis = float(mode["eta_dis"])
    need_kwh = float(mode["charge_need_kwh"])
    initial_kwh = float(mode["initial_energy_kwh"])
    energy_min_kwh = float(mode["energy_min_kwh"])
    battery_capacity_kwh = float(mode["battery_capacity_kwh"])

    ch_per_slot_kwh = p_ch_kw * eta_ch * dt_h
    dis_per_slot_kwh = p_dis_kw / eta_dis * dt_h if p_dis_kw > 0 else 0.0

    if scenario == "ordered":
        min_delta_kwh = 0.0
        max_delta_kwh = need_kwh
        dis_per_slot_kwh = 0.0
    elif scenario == "v2g":
        min_delta_kwh = energy_min_kwh - initial_kwh
        max_delta_kwh = battery_capacity_kwh - initial_kwh
    else:
        raise ValueError(f"Unsupported EV aggregate scenario: {scenario}")

    energy_min = np.zeros(MAIN_PERIODS, dtype=float)
    energy_max = np.zeros(MAIN_PERIODS, dtype=float)
    departed_target = np.zeros(MAIN_PERIODS, dtype=float)
    feasibility_gap = np.zeros(MAIN_PERIODS, dtype=float)

    for idx, k in enumerate(range(1, MAIN_PERIODS + 1)):
        elapsed = np.clip(np.minimum(k, departure) - arrival, 0, None)
        remaining = np.clip(departure - np.maximum(k, arrival), 0, None)

        lower = np.maximum(min_delta_kwh, need_kwh - ch_per_slot_kwh * remaining)
        upper = np.minimum(max_delta_kwh, ch_per_slot_kwh * elapsed)

        if scenario == "v2g":
            lower = np.maximum(lower, -dis_per_slot_kwh * elapsed)
            upper = np.minimum(upper, need_kwh + dis_per_slot_kwh * remaining)

        before_arrival = k <= arrival
        after_departure = k >= departure
        lower = np.where(before_arrival, 0.0, lower)
        upper = np.where(before_arrival, 0.0, upper)
        lower = np.where(after_departure, need_kwh, lower)
        upper = np.where(after_departure, need_kwh, upper)

        gap = np.maximum(lower - upper, 0.0)
        energy_min[idx] = lower.sum()
        energy_max[idx] = upper.sum()
        departed_target[idx] = np.where(after_departure, need_kwh, 0.0).sum()
        feasibility_gap[idx] = gap.sum()

    return energy_min, energy_max, departed_target, feasibility_gap


def build_ev_aggregate_bounds(
    scenario: str,
    config: dict | None = None,
) -> pd.DataFrame:
    """Build a 56-slot aggregate EV boundary table for ``ordered`` or ``v2g``."""
    cfg = config or load_config()
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of {SCENARIOS}, got {scenario!r}")

    dt_h = float(cfg["time"]["dt_h"])
    ev_info, availability, online_summary, mode_params, time_slots = _load_inputs(cfg)
    mode = _mode_params(mode_params, scenario)

    online_count = availability.sum(axis=0).astype(int)
    p_ch_max_mw = online_count * float(mode["p_ch_max_kw"]) / 1000.0
    p_dis_max_mw = online_count * float(mode["p_dis_max_kw"]) / 1000.0
    energy_min_kwh, energy_max_kwh, departed_target_kwh, gap_kwh = _energy_bounds_kwh(
        ev_info=ev_info,
        mode=mode,
        scenario=scenario,
        dt_h=dt_h,
    )

    result = time_slots[["t", "time_label"]].copy()
    result["scenario"] = scenario
    result["online_count"] = online_count
    result["p_ch_max_mw"] = p_ch_max_mw
    result["p_dis_max_mw"] = p_dis_max_mw
    result["p_net_min_mw"] = -p_dis_max_mw
    result["p_net_max_mw"] = p_ch_max_mw
    result["energy_min_mwh"] = energy_min_kwh / 1000.0
    result["energy_max_mwh"] = energy_max_kwh / 1000.0
    result["departed_target_energy_mwh"] = departed_target_kwh / 1000.0
    result["feasibility_gap_mwh"] = gap_kwh / 1000.0
    result["is_feasible"] = result["feasibility_gap_mwh"] <= 1e-9
    result["initial_cumulative_energy_mwh"] = 0.0
    result["total_required_energy_mwh"] = (
        len(ev_info) * float(mode["charge_need_kwh"]) / 1000.0
    )
    result["dt_h"] = dt_h
    result["eta_ch"] = float(mode["eta_ch"])
    result["eta_dis"] = float(mode["eta_dis"])
    result["p_ch_max_kw_per_ev"] = float(mode["p_ch_max_kw"])
    result["p_dis_max_kw_per_ev"] = float(mode["p_dis_max_kw"])
    result["charge_need_kwh_per_ev"] = float(mode["charge_need_kwh"])
    return result


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    outputs: dict[str, str] = {}
    for scenario in SCENARIOS:
        bounds = build_ev_aggregate_bounds(scenario, cfg)
        key = f"ev_agg_bounds_{scenario}_56"
        outputs[key] = str(write_csv(bounds, output_path(key, cfg)))
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
