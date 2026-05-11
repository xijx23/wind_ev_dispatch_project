"""Baseline EMS dispatch.

This file provides a deterministic baseline and a stable output schema. It is
not intended to replace a formal MILP/convex optimization model for the report.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config_loader import load_config, output_path, project_path
from src.common.constants import MAIN_PERIODS
from src.common.io_utils import write_csv


def _thermal_cost(total_p_mw: float, thermal: pd.DataFrame, dt_h: float) -> float:
    p_min = thermal["p_min_mw"].to_numpy(dtype=float)
    p_max = thermal["p_max_mw"].to_numpy(dtype=float)
    a = thermal["cost_a_usd_per_mw2h"].to_numpy(dtype=float)
    b = thermal["cost_b_usd_per_mwh"].to_numpy(dtype=float)
    c = thermal["cost_c_usd_per_h"].to_numpy(dtype=float)
    span = p_max - p_min
    if total_p_mw <= p_min.sum():
        p = p_min
    else:
        extra = min(total_p_mw - p_min.sum(), span.sum())
        p = p_min + extra * span / span.sum()
    return float(((a * p**2 + b * p + c) * dt_h).sum())


def _schedule_ordered(bounds: pd.DataFrame, load_wind: pd.DataFrame, total_need_mwh: float, dt_h: float) -> np.ndarray:
    score = load_wind["wind_forecast_mw"] - load_wind["load_mw"]
    order = np.argsort(-score.to_numpy())
    p = np.zeros(MAIN_PERIODS)
    remaining = total_need_mwh
    for idx in order:
        cap = float(bounds.loc[idx, "p_ch_max_mw"])
        charge = min(cap, remaining / dt_h)
        p[idx] = charge
        remaining -= charge * dt_h
        if remaining <= 1e-9:
            break
    return p


def _dispatch_frame(scenario: str, p_ch: np.ndarray, p_dis: np.ndarray, config: dict) -> pd.DataFrame:
    dt_h = float(config["time"]["dt_h"])
    load_wind = pd.read_csv(output_path("load_wind_56", config))
    thermal = pd.read_csv(output_path("thermal_params", config))
    p_min_total = float(thermal["p_min_mw"].sum())
    p_max_total = float(thermal["p_max_mw"].sum())

    rows = []
    for t, row in load_wind.iterrows():
        load = float(row["load_mw"])
        wind = float(row["wind_forecast_mw"])
        demand_after_ev = load + float(p_ch[t]) - float(p_dis[t])
        thermal_total = min(max(demand_after_ev - wind, p_min_total), p_max_total)
        wind_used = min(wind, max(demand_after_ev - thermal_total, 0.0))
        wind_curtail = max(wind - wind_used, 0.0)
        rows.append(
            {
                "t": int(row["t"]),
                "time_label": row["time_label"],
                "scenario": scenario,
                "load_mw": load,
                "wind_forecast_mw": wind,
                "wind_used_mw": wind_used,
                "wind_curtail_mw": wind_curtail,
                "thermal_total_mw": thermal_total,
                "p_ev_ch_mw": float(p_ch[t]),
                "p_ev_dis_mw": float(p_dis[t]),
                "p_ev_net_mw": float(p_ch[t] - p_dis[t]),
                "system_cost_usd": _thermal_cost(thermal_total, thermal, dt_h),
            }
        )
    return pd.DataFrame(rows)


def run_dispatch(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    dt_h = float(cfg["time"]["dt_h"])
    load_wind = pd.read_csv(output_path("load_wind_56", cfg))
    ev_cfg = cfg["ev"]
    ev_count = len(pd.read_csv(output_path("ev_info", cfg)))
    total_need_mwh = ev_count * float(ev_cfg["charge_need_kwh"]) / 1000.0 / float(ev_cfg["charge_efficiency"])

    unordered_load = pd.read_csv(output_path("unordered_ev_load_56", cfg))
    unordered = _dispatch_frame(
        "unordered",
        unordered_load["p_ev_ch_mw"].to_numpy(dtype=float),
        np.zeros(MAIN_PERIODS),
        cfg,
    )

    ordered_bounds = pd.read_csv(output_path("ev_agg_bounds_ordered_56", cfg))
    ordered_p_ch = _schedule_ordered(ordered_bounds, load_wind, total_need_mwh, dt_h)
    ordered = _dispatch_frame("ordered", ordered_p_ch, np.zeros(MAIN_PERIODS), cfg)

    v2g_bounds = pd.read_csv(output_path("ev_agg_bounds_v2g_56", cfg))
    v2g_p_ch = _schedule_ordered(v2g_bounds, load_wind, total_need_mwh * 1.08, dt_h)
    high_load = load_wind["load_mw"].to_numpy() > load_wind["load_mw"].quantile(0.75)
    p_dis = np.where(high_load, np.minimum(v2g_bounds["p_dis_max_mw"].to_numpy() * 0.25, 3.0), 0.0)
    v2g = _dispatch_frame("v2g", v2g_p_ch, p_dis, cfg)

    paths = {
        "dispatch_unordered": project_path(cfg["paths"]["dispatch_dir"], "dispatch_unordered.csv"),
        "dispatch_ordered": project_path(cfg["paths"]["dispatch_dir"], "dispatch_ordered.csv"),
        "dispatch_v2g": project_path(cfg["paths"]["dispatch_dir"], "dispatch_v2g.csv"),
    }
    return {
        "dispatch_unordered": str(write_csv(unordered, paths["dispatch_unordered"])),
        "dispatch_ordered": str(write_csv(ordered, paths["dispatch_ordered"])),
        "dispatch_v2g": str(write_csv(v2g, paths["dispatch_v2g"])),
    }


def main() -> None:
    for name, path in run_dispatch().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
