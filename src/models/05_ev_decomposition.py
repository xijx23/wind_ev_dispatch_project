"""Decompose aggregate EV dispatch schedules to individual vehicles.

The dispatcher from member C optimizes only aggregate EV charging/discharging.
This module maps that aggregate schedule back to per-vehicle trajectories while
respecting each vehicle's online window, power limits, battery limits, and
departure energy target.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config_loader import load_config, output_path
from src.common.constants import MAIN_PERIODS
from src.common.io_utils import require_columns, write_csv


SCENARIOS = ("ordered", "v2g")
POWER_TOL_MW = 1e-7
ENERGY_TOL_KWH = 1e-6


def _mode_params(mode_params: pd.DataFrame, scenario: str) -> pd.Series:
    match = mode_params.loc[mode_params["scenario"] == scenario]
    if match.empty:
        raise ValueError(f"ev_mode_params.csv missing scenario={scenario!r}")
    return match.iloc[0]


def _allocate_by_order(
    amount_kwh: float,
    capacities_kwh: np.ndarray,
    ordered_indices: np.ndarray,
) -> tuple[np.ndarray, float]:
    allocation = np.zeros_like(capacities_kwh, dtype=float)
    remaining = max(float(amount_kwh), 0.0)
    for idx in ordered_indices:
        if remaining <= ENERGY_TOL_KWH:
            break
        cap = float(capacities_kwh[idx])
        if cap <= ENERGY_TOL_KWH:
            continue
        take = min(cap, remaining)
        allocation[idx] = take
        remaining -= take
    return allocation, max(remaining, 0.0)


def _repair_dispatch_targets(
    p_ch_mw: np.ndarray,
    p_dis_mw: np.ndarray,
    bounds: pd.DataFrame,
    total_required_mwh: float,
    eta_ch: float,
    eta_dis: float,
    dt_h: float,
    scenario: str,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """Clip numerical residues and repair tiny final-energy mismatch."""
    cleaned_ch = np.where(p_ch_mw > POWER_TOL_MW, p_ch_mw, 0.0).astype(float)
    cleaned_dis = np.where(p_dis_mw > POWER_TOL_MW, p_dis_mw, 0.0).astype(float)
    if scenario == "ordered":
        cleaned_dis[:] = 0.0

    raw_final = float(np.sum(cleaned_ch * eta_ch - cleaned_dis / eta_dis) * dt_h)
    delta_mwh = total_required_mwh - raw_final
    added_ch_mwh = 0.0
    reduced_ch_mwh = 0.0
    added_dis_mwh = 0.0

    if delta_mwh > 1e-8:
        remaining = delta_mwh
        p_ch_max = bounds["p_ch_max_mw"].to_numpy(dtype=float)
        for t in range(MAIN_PERIODS - 1, -1, -1):
            headroom_mw = max(p_ch_max[t] - cleaned_ch[t], 0.0)
            add_mw = min(headroom_mw, remaining / (eta_ch * dt_h))
            cleaned_ch[t] += add_mw
            added = add_mw * eta_ch * dt_h
            added_ch_mwh += added
            remaining -= added
            if remaining <= 1e-8:
                break
    elif delta_mwh < -1e-8:
        surplus = -delta_mwh
        for t in range(MAIN_PERIODS - 1, -1, -1):
            reduce_mw = min(cleaned_ch[t], surplus / (eta_ch * dt_h))
            cleaned_ch[t] -= reduce_mw
            reduced = reduce_mw * eta_ch * dt_h
            reduced_ch_mwh += reduced
            surplus -= reduced
            if surplus <= 1e-8:
                break
        if surplus > 1e-8 and scenario == "v2g":
            p_dis_max = bounds["p_dis_max_mw"].to_numpy(dtype=float)
            for t in range(MAIN_PERIODS - 1, -1, -1):
                headroom_mw = max(p_dis_max[t] - cleaned_dis[t], 0.0)
                add_mw = min(headroom_mw, surplus * eta_dis / dt_h)
                cleaned_dis[t] += add_mw
                added = add_mw / eta_dis * dt_h
                added_dis_mwh += added
                surplus -= added
                if surplus <= 1e-8:
                    break

    repaired_final = float(np.sum(cleaned_ch * eta_ch - cleaned_dis / eta_dis) * dt_h)
    stats = {
        "raw_final_energy_mwh_after_clip": raw_final,
        "target_final_energy_mwh": float(total_required_mwh),
        "final_repair_delta_mwh": float(repaired_final - raw_final),
        "added_charge_battery_mwh": added_ch_mwh,
        "reduced_charge_battery_mwh": reduced_ch_mwh,
        "added_discharge_battery_mwh": added_dis_mwh,
    }
    return cleaned_ch, cleaned_dis, stats


def _build_plan_dataframe(
    scenario: str,
    ev_info: pd.DataFrame,
    time_slots: pd.DataFrame,
    availability: np.ndarray,
    p_ch_kw: np.ndarray,
    p_dis_kw: np.ndarray,
    energy_kwh: np.ndarray,
    initial_energy_kwh: float,
    target_energy_kwh: float,
    battery_capacity_kwh: float,
) -> pd.DataFrame:
    n_ev = len(ev_info)
    ev_repeated = np.repeat(ev_info["ev_id"].to_numpy(), MAIN_PERIODS)
    t_tiled = np.tile(np.arange(MAIN_PERIODS), n_ev)
    time_labels = time_slots["time_label"].to_numpy()

    return pd.DataFrame(
        {
            "scenario": scenario,
            "ev_id": ev_repeated,
            "t": t_tiled,
            "time_label": time_labels[t_tiled],
            "is_online": availability.reshape(-1).astype(int),
            "arrival_slot": np.repeat(ev_info["arrival_slot"].to_numpy(dtype=int), MAIN_PERIODS),
            "departure_slot_exclusive": np.repeat(
                ev_info["departure_slot_exclusive"].to_numpy(dtype=int), MAIN_PERIODS
            ),
            "p_ch_kw": p_ch_kw.reshape(-1),
            "p_dis_kw": p_dis_kw.reshape(-1),
            "p_net_kw": (p_ch_kw - p_dis_kw).reshape(-1),
            "battery_energy_kwh": energy_kwh.reshape(-1),
            "delta_energy_kwh": (energy_kwh - initial_energy_kwh).reshape(-1),
            "soc": (energy_kwh / battery_capacity_kwh).reshape(-1),
            "target_energy_kwh": target_energy_kwh,
            "is_departure_slot": (
                t_tiled
                == np.repeat(ev_info["departure_slot_exclusive"].to_numpy(dtype=int), MAIN_PERIODS) - 1
            ).astype(int),
        }
    )


def decompose_dispatch(scenario: str, config: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return per-vehicle plan and time-slot decomposition diagnostics."""
    cfg = config or load_config()
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of {SCENARIOS}, got {scenario!r}")

    dt_h = float(cfg["time"]["dt_h"])
    ev_info = pd.read_csv(output_path("ev_info", cfg))
    require_columns(ev_info, ["ev_id", "arrival_slot", "departure_slot_exclusive"], "ev_info")
    availability = np.load(output_path("ev_availability_56", cfg))["availability"].astype(bool)
    time_slots = pd.read_csv(output_path("time_slots_56", cfg))
    mode = _mode_params(pd.read_csv(output_path("ev_mode_params", cfg)), scenario)
    bounds = pd.read_csv(output_path(f"ev_agg_bounds_{scenario}_56", cfg))
    dispatch = pd.read_csv(output_path(f"dispatch_{scenario}", cfg))
    require_columns(dispatch, ["t", "time_label", "p_ev_ch_mw", "p_ev_dis_mw"], f"dispatch_{scenario}")

    n_ev = len(ev_info)
    arrival = ev_info["arrival_slot"].to_numpy(dtype=int)
    departure = ev_info["departure_slot_exclusive"].to_numpy(dtype=int)

    p_ch_max_kw = float(mode["p_ch_max_kw"])
    p_dis_max_kw = float(mode["p_dis_max_kw"])
    eta_ch = float(mode["eta_ch"])
    eta_dis = float(mode["eta_dis"])
    charge_need_kwh = float(mode["charge_need_kwh"])
    initial_energy_kwh = float(mode["initial_energy_kwh"])
    minimum_energy_kwh = float(mode["energy_min_kwh"])
    battery_capacity_kwh = float(mode["battery_capacity_kwh"])
    target_energy_kwh = initial_energy_kwh + charge_need_kwh
    total_required_mwh = float(bounds["total_required_energy_mwh"].iloc[0])

    min_delta_kwh = minimum_energy_kwh - initial_energy_kwh
    max_delta_kwh = battery_capacity_kwh - initial_energy_kwh
    ch_slot_kwh = p_ch_max_kw * eta_ch * dt_h
    dis_slot_kwh = p_dis_max_kw / eta_dis * dt_h if p_dis_max_kw > 0 else 0.0

    target_ch_mw_raw = dispatch["p_ev_ch_mw"].to_numpy(dtype=float)
    target_dis_mw_raw = dispatch["p_ev_dis_mw"].to_numpy(dtype=float)
    target_ch_mw, target_dis_mw, repair_stats = _repair_dispatch_targets(
        target_ch_mw_raw,
        target_dis_mw_raw,
        bounds,
        total_required_mwh,
        eta_ch,
        eta_dis,
        dt_h,
        scenario,
    )

    battery_delta = np.zeros(n_ev, dtype=float)
    p_ch_matrix = np.zeros((n_ev, MAIN_PERIODS), dtype=float)
    p_dis_matrix = np.zeros((n_ev, MAIN_PERIODS), dtype=float)
    energy_matrix = np.zeros((n_ev, MAIN_PERIODS), dtype=float)
    errors: list[dict[str, float | int | str]] = []

    for t in range(MAIN_PERIODS):
        active = availability[:, t]
        active_idx = np.flatnonzero(active)

        target_dis_batt_kwh = target_dis_mw[t] * 1000.0 * dt_h / eta_dis
        unallocated_dis_kwh = 0.0
        if (target_dis_batt_kwh > ENERGY_TOL_KWH or scenario == "v2g") and len(active_idx) > 0:
            future_slots = np.clip(departure[active_idx] - (t + 1), 0, None)
            lower_after = np.maximum(min_delta_kwh, charge_need_kwh - ch_slot_kwh * future_slots)
            dis_capacity = np.minimum(dis_slot_kwh, battery_delta[active_idx] - lower_after)
            dis_capacity = np.clip(dis_capacity, 0.0, None)
            upper_after = np.minimum(max_delta_kwh, charge_need_kwh + dis_slot_kwh * future_slots)
            required_dis_now = np.minimum(dis_capacity, np.maximum(0.0, battery_delta[active_idx] - upper_after))
            desired_dis_batt_kwh = max(target_dis_batt_kwh, float(required_dis_now.sum()))

            required_order = np.argsort(-required_dis_now)
            dis_alloc, remaining_dis = _allocate_by_order(
                desired_dis_batt_kwh,
                required_dis_now,
                required_order,
            )
            if remaining_dis > ENERGY_TOL_KWH:
                remaining_capacity = np.clip(dis_capacity - dis_alloc, 0.0, None)
                slack_order = np.argsort(-remaining_capacity)
                flex_dis, unallocated_dis_kwh = _allocate_by_order(
                    remaining_dis,
                    remaining_capacity,
                    slack_order,
                )
                dis_alloc += flex_dis
            battery_delta[active_idx] -= dis_alloc
            p_dis_matrix[active_idx, t] = dis_alloc * eta_dis / dt_h

        target_ch_batt_kwh = target_ch_mw[t] * 1000.0 * eta_ch * dt_h
        unallocated_ch_kwh = 0.0
        if len(active_idx) > 0:
            future_slots = np.clip(departure[active_idx] - (t + 1), 0, None)
            if scenario == "v2g":
                upper_after = np.minimum(max_delta_kwh, charge_need_kwh + dis_slot_kwh * future_slots)
            else:
                upper_after = np.full(len(active_idx), charge_need_kwh)
            charge_capacity = np.minimum(ch_slot_kwh, upper_after - battery_delta[active_idx])
            charge_capacity = np.clip(charge_capacity, 0.0, None)

            required_now = np.maximum(0.0, charge_need_kwh - battery_delta[active_idx] - ch_slot_kwh * future_slots)
            desired_ch_batt_kwh = max(target_ch_batt_kwh, float(np.minimum(charge_capacity, required_now).sum()))
            urgent_capacity = np.minimum(charge_capacity, required_now)
            urgent_order = np.lexsort((battery_delta[active_idx], departure[active_idx]))
            ch_alloc, remaining = _allocate_by_order(desired_ch_batt_kwh, urgent_capacity, urgent_order)

            if remaining > ENERGY_TOL_KWH:
                remaining_capacity = np.clip(charge_capacity - ch_alloc, 0.0, None)
                # Concentrate non-urgent energy instead of spreading it thinly.
                # This preserves future slot-wise charging headroom.
                flexible_order = np.lexsort((-battery_delta[active_idx], departure[active_idx]))
                flex_alloc, unallocated_ch_kwh = _allocate_by_order(remaining, remaining_capacity, flexible_order)
                ch_alloc += flex_alloc
            else:
                unallocated_ch_kwh = 0.0

            battery_delta[active_idx] += ch_alloc
            p_ch_matrix[active_idx, t] = ch_alloc / (eta_ch * dt_h)

        energy_matrix[:, t] = initial_energy_kwh + battery_delta

        departure_idx = np.flatnonzero(departure == t + 1)
        departure_shortfall = np.maximum(charge_need_kwh - battery_delta[departure_idx], 0.0)
        departure_surplus = np.maximum(battery_delta[departure_idx] - charge_need_kwh, 0.0)

        allocated_ch_mw = p_ch_matrix[:, t].sum() / 1000.0
        allocated_dis_mw = p_dis_matrix[:, t].sum() / 1000.0
        allocated_energy_mwh = battery_delta.sum() / 1000.0
        dispatch_energy_mwh = (
            dispatch["ev_battery_energy_mwh"].iloc[t]
            if "ev_battery_energy_mwh" in dispatch.columns
            else np.nan
        )

        errors.append(
            {
                "scenario": scenario,
                "t": int(t),
                "time_label": str(time_slots["time_label"].iloc[t]),
                "target_p_ev_ch_mw_raw": float(target_ch_mw_raw[t]),
                "target_p_ev_dis_mw_raw": float(target_dis_mw_raw[t]),
                "target_p_ev_ch_mw": float(target_ch_mw[t]),
                "target_p_ev_dis_mw": float(target_dis_mw[t]),
                "allocated_p_ev_ch_mw": float(allocated_ch_mw),
                "allocated_p_ev_dis_mw": float(allocated_dis_mw),
                "ch_error_mw": float(allocated_ch_mw - target_ch_mw[t]),
                "dis_error_mw": float(allocated_dis_mw - target_dis_mw[t]),
                "net_error_mw": float((allocated_ch_mw - allocated_dis_mw) - (target_ch_mw[t] - target_dis_mw[t])),
                "dispatch_energy_mwh": float(dispatch_energy_mwh),
                "allocated_energy_mwh": float(allocated_energy_mwh),
                "energy_error_vs_dispatch_mwh": float(allocated_energy_mwh - dispatch_energy_mwh)
                if not np.isnan(dispatch_energy_mwh)
                else np.nan,
                "unallocated_ch_mwh": float(unallocated_ch_kwh / 1000.0),
                "unallocated_dis_mwh": float(unallocated_dis_kwh / 1000.0),
                "offline_power_violation_count": int(
                    np.count_nonzero((~active) & ((p_ch_matrix[:, t] > 1e-6) | (p_dis_matrix[:, t] > 1e-6)))
                ),
                "power_violation_count": int(
                    np.count_nonzero(p_ch_matrix[:, t] - p_ch_max_kw > 1e-6)
                    + np.count_nonzero(p_dis_matrix[:, t] - p_dis_max_kw > 1e-6)
                ),
                "energy_min_violation_count": int(
                    np.count_nonzero(energy_matrix[:, t] < minimum_energy_kwh - 1e-6)
                ),
                "energy_max_violation_count": int(
                    np.count_nonzero(energy_matrix[:, t] > battery_capacity_kwh + 1e-6)
                ),
                "departure_vehicle_count": int(len(departure_idx)),
                "departure_shortfall_kwh": float(departure_shortfall.sum()),
                "max_departure_shortfall_kwh": float(departure_shortfall.max() if len(departure_shortfall) else 0.0),
                "departure_surplus_kwh": float(departure_surplus.sum()),
                **repair_stats,
            }
        )

    plan = _build_plan_dataframe(
        scenario,
        ev_info,
        time_slots,
        availability,
        p_ch_matrix,
        p_dis_matrix,
        energy_matrix,
        initial_energy_kwh,
        target_energy_kwh,
        battery_capacity_kwh,
    )
    error = pd.DataFrame(errors)
    return plan, error


def analyze_departure_shift_feasibility(
    plan: pd.DataFrame,
    shifts: tuple[int, ...] = (-4, -2, -1, 0, 1, 2, 4),
) -> pd.DataFrame:
    """Check whether earlier/later departure assumptions keep the plan feasible."""
    ev_static = (
        plan[["ev_id", "arrival_slot", "departure_slot_exclusive", "target_energy_kwh", "scenario"]]
        .drop_duplicates("ev_id")
        .sort_values("ev_id")
        .reset_index(drop=True)
    )
    n_ev = len(ev_static)
    energy = plan.sort_values(["ev_id", "t"])["battery_energy_kwh"].to_numpy().reshape(n_ev, MAIN_PERIODS)
    rows: list[dict[str, float | int | str | bool]] = []

    for shift in shifts:
        new_departure = np.clip(
            ev_static["departure_slot_exclusive"].to_numpy(dtype=int) + shift,
            ev_static["arrival_slot"].to_numpy(dtype=int) + 1,
            MAIN_PERIODS,
        )
        check_t = new_departure - 1
        final_energy = energy[np.arange(n_ev), check_t]
        target = ev_static["target_energy_kwh"].to_numpy(dtype=float)
        shortfall = np.maximum(target - final_energy, 0.0)
        surplus = np.maximum(final_energy - target, 0.0)
        rows.append(
            {
                "scenario": str(ev_static["scenario"].iloc[0]),
                "departure_shift_slots": int(shift),
                "departure_shift_minutes": int(shift * 15),
                "infeasible_vehicle_count": int(np.count_nonzero(shortfall > 1e-6)),
                "total_shortfall_kwh": float(shortfall.sum()),
                "max_shortfall_kwh": float(shortfall.max()),
                "total_surplus_kwh": float(surplus.sum()),
                "is_feasible": bool(np.all(shortfall <= 1e-6)),
            }
        )
    return pd.DataFrame(rows)


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    outputs: dict[str, str] = {}
    shift_tables: list[pd.DataFrame] = []
    for scenario in SCENARIOS:
        plan, error = decompose_dispatch(scenario, cfg)
        shift_tables.append(analyze_departure_shift_feasibility(plan))
        plan_key = f"ev_plan_{scenario}"
        error_key = f"decomposition_error_{scenario}"
        outputs[plan_key] = str(write_csv(plan, output_path(plan_key, cfg)))
        outputs[error_key] = str(write_csv(error, output_path(error_key, cfg)))
    outputs["departure_shift_feasibility"] = str(
        write_csv(pd.concat(shift_tables, ignore_index=True), output_path("departure_shift_feasibility", cfg))
    )
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
