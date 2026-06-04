"""EMS dispatch optimization model for member C."""

from __future__ import annotations

import numpy as np
import pandas as pd
import cvxpy as cp
import os

from src.common.config_loader import load_config, output_path
from src.common.constants import MAIN_PERIODS
from src.common.io_utils import write_csv


def solve_ems_dispatch(scenario: str, config: dict | None = None, penetration_scale: float = 1.0) -> pd.DataFrame:
    """Solve the EMS dispatch optimization for a given scenario and EV penetration scale."""
    cfg = config or load_config()
    dt_h = float(cfg["time"]["dt_h"])

    # Load data
    load_wind = pd.read_csv(output_path("load_wind_56", cfg))
    thermal_params = pd.read_csv(output_path("thermal_params", cfg))
    ev_mode_params = pd.read_csv(output_path("ev_mode_params", cfg))
    
    mode = ev_mode_params[ev_mode_params["scenario"] == scenario]
    if mode.empty:
        raise ValueError(f"ev_mode_params.csv missing scenario={scenario!r}")
    mode = mode.iloc[0]
    fee_ch_usd_per_kwh = float(mode["charge_fee_usd_per_kwh"])
    fee_dis_usd_per_kwh = float(mode["discharge_fee_usd_per_kwh"])

    if scenario == "unordered":
        # Ensure unordered charging baseline exists
        dispatch_unord_path = output_path("dispatch_unordered", cfg)
        if not os.path.exists(dispatch_unord_path):
            raise FileNotFoundError(f"Missing {dispatch_unord_path}. Run unordered charging first.")
        ev_data = pd.read_csv(dispatch_unord_path)
        p_ev_net_mw = ev_data["p_ev_net_mw"].to_numpy() * penetration_scale
    else:
        bounds_key = f"ev_agg_bounds_{scenario}_56"
        ev_bounds = pd.read_csv(output_path(bounds_key, cfg))

    # Thermal params
    p_min = thermal_params["p_min_mw"].to_numpy()
    p_max = thermal_params["p_max_mw"].to_numpy()
    ramp_down = thermal_params["ramp_down_mw_per_min"].to_numpy()
    ramp_up = thermal_params["ramp_up_mw_per_min"].to_numpy()
    cost_a = thermal_params["cost_a_usd_per_mw2h"].to_numpy()
    cost_b = thermal_params["cost_b_usd_per_mwh"].to_numpy()
    cost_c = thermal_params["cost_c_usd_per_h"].to_numpy()
    n_units = len(thermal_params)

    # Load and wind
    load_mw = load_wind["load_mw"].to_numpy()
    wind_forecast = load_wind["wind_forecast_mw"].to_numpy()
    
    # CVXPY variables
    p_th = cp.Variable((n_units, MAIN_PERIODS))
    p_wind_used = cp.Variable(MAIN_PERIODS)
    
    if scenario == "unordered":
        p_ev_ch = cp.Constant(np.maximum(p_ev_net_mw, 0))
        p_ev_dis = cp.Constant(np.maximum(-p_ev_net_mw, 0))
        p_ev_net_val = p_ev_net_mw
    else:
        p_ev_ch = cp.Variable(MAIN_PERIODS)
        p_ev_dis = cp.Variable(MAIN_PERIODS)
        p_ev_net_val = p_ev_ch - p_ev_dis

    # Constraints
    constraints = []
    
    # Thermal limits
    constraints.append(p_th >= p_min[:, None])
    constraints.append(p_th <= p_max[:, None])
    
    # Ramp limits
    ramp_limit_down = ramp_down * 60 * dt_h
    ramp_limit_up = ramp_up * 60 * dt_h
    for t in range(1, MAIN_PERIODS):
        constraints.append(p_th[:, t] - p_th[:, t - 1] >= ramp_limit_down)
        constraints.append(p_th[:, t] - p_th[:, t - 1] <= ramp_limit_up)
        
    # Wind limits
    constraints.append(p_wind_used >= 0)
    constraints.append(p_wind_used <= wind_forecast)
    
    # Power balance
    constraints.append(cp.sum(p_th, axis=0) + p_wind_used == load_mw + p_ev_net_val)
    
    # EV constraints for ordered and v2g
    if scenario != "unordered":
        p_ch_max = ev_bounds["p_ch_max_mw"].to_numpy() * penetration_scale
        p_dis_max = ev_bounds["p_dis_max_mw"].to_numpy() * penetration_scale
        energy_min = ev_bounds["energy_min_mwh"].to_numpy() * penetration_scale
        energy_max = ev_bounds["energy_max_mwh"].to_numpy() * penetration_scale
        eta_ch = ev_bounds["eta_ch"].iloc[0]
        eta_dis = ev_bounds["eta_dis"].iloc[0]
        total_required_energy = ev_bounds["total_required_energy_mwh"].iloc[0] * penetration_scale
        
        constraints.append(p_ev_ch >= 0)
        constraints.append(p_ev_ch <= p_ch_max)
        constraints.append(p_ev_dis >= 0)
        constraints.append(p_ev_dis <= p_dis_max)
        
        # Cumulative energy
        energy_cum = cp.cumsum(p_ev_ch * eta_ch - p_ev_dis / eta_dis) * dt_h
        constraints.append(energy_cum >= energy_min)
        constraints.append(energy_cum <= energy_max)
        constraints.append(energy_cum[-1] == total_required_energy)
        
        # Only v2g can discharge
        # (Note: Mutual exclusion of charging and discharging is naturally satisfied
        # because simultaneous charging and discharging increases total cost)
        if scenario == "ordered":
            constraints.append(p_ev_dis == 0)

    # Objective
    cost = 0
    for i in range(n_units):
        cost += cp.sum(cost_a[i] * cp.square(p_th[i, :]) + cost_b[i] * p_th[i, :] + cost_c[i]) * dt_h
        
    ev_cost = cp.sum(p_ev_dis * fee_dis_usd_per_kwh * 1000 * dt_h) - cp.sum(p_ev_ch * fee_ch_usd_per_kwh * 1000 * dt_h)
        
    # Objective is to minimize total operational cost.
    prob = cp.Problem(cp.Minimize(cost + ev_cost), constraints)
    for solver in ("CLARABEL", "OSQP", "SCIPY"):
        if solver not in cp.installed_solvers():
            continue
        try:
            prob.solve(solver=solver)
        except cp.SolverError:
            continue
        if prob.status in ["optimal", "optimal_inaccurate"]:
            break
    
    if prob.status not in ["optimal", "optimal_inaccurate"]:
        raise ValueError(f"EMS optimization failed for {scenario} with status {prob.status}")
        
    # Build output
    result = load_wind[["t", "time_label"]].copy()
    result["scenario"] = scenario
    result["penetration_scale"] = penetration_scale
    
    p_th_val = p_th.value
    for i in range(n_units):
        result[f"p_th_{i+1}_mw"] = p_th_val[i, :]
    
    result["p_th_total_mw"] = p_th_val.sum(axis=0)
    result["p_wind_used_mw"] = p_wind_used.value
    result["p_wind_curtailed_mw"] = wind_forecast - p_wind_used.value
    
    if scenario == "unordered":
        result["p_ev_ch_mw"] = p_ev_ch.value
        result["p_ev_dis_mw"] = p_ev_dis.value
        result["p_ev_net_mw"] = p_ev_net_val
    else:
        result["p_ev_ch_mw"] = p_ev_ch.value
        result["p_ev_dis_mw"] = p_ev_dis.value
        result["p_ev_net_mw"] = p_ev_ch.value - p_ev_dis.value
        result["ev_battery_energy_mwh"] = energy_cum.value
        
    result["system_load_mw"] = load_mw + result["p_ev_net_mw"]
    
    # Calculate costs
    total_cost_usd = np.zeros(MAIN_PERIODS)
    for i in range(n_units):
        c_i = (cost_a[i] * p_th_val[i, :]**2 + cost_b[i] * p_th_val[i, :] + cost_c[i]) * dt_h
        total_cost_usd += c_i
    result["thermal_cost_usd"] = total_cost_usd
    
    ev_ch_val = result["p_ev_ch_mw"].to_numpy() if isinstance(result["p_ev_ch_mw"], pd.Series) else result["p_ev_ch_mw"]
    ev_dis_val = result["p_ev_dis_mw"].to_numpy() if isinstance(result["p_ev_dis_mw"], pd.Series) else result["p_ev_dis_mw"]
    
    ev_cost_usd = (ev_dis_val * fee_dis_usd_per_kwh * 1000 * dt_h) - (ev_ch_val * fee_ch_usd_per_kwh * 1000 * dt_h)
    result["ev_cost_usd"] = ev_cost_usd
    result["total_cost_usd"] = total_cost_usd + ev_cost_usd
    
    return result

def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    outputs = {}
    for scenario in ["unordered", "ordered", "v2g"]:
        try:
            res = solve_ems_dispatch(scenario, cfg)
            if scenario == "unordered":
                path = output_path("dispatch_unordered", cfg)
            else:
                path = f"{cfg['paths']['results_dir']}/dispatch/dispatch_{scenario}.csv"
            outputs[f"dispatch_{scenario}"] = str(write_csv(res, path))
        except Exception as e:
            print(f"Error in {scenario}: {e}")
    return outputs

def main() -> None:
    for k, v in run().items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
