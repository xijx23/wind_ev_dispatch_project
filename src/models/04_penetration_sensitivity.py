"""EV penetration sensitivity analysis for member C."""

from __future__ import annotations

import pandas as pd
from pathlib import Path
import os

from src.common.config_loader import load_config, output_path
from src.common.io_utils import write_csv
import importlib
ems_module = importlib.import_module("src.models.03_ems_dispatch")
solve_ems_dispatch = ems_module.solve_ems_dispatch


def run_sensitivity(config: dict | None = None) -> pd.DataFrame:
    cfg = config or load_config()
    
    # Penetration scales to test (0% to 200% of base EV count)
    scales = [0.0, 0.2, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
    scenarios = ["unordered", "ordered", "v2g"]
    
    results = []
    
    for scale in scales:
        for scenario in scenarios:
            try:
                # Solve dispatch
                res = solve_ems_dispatch(scenario, cfg, penetration_scale=scale)
                
                # Calculate metrics
                total_cost = res["thermal_cost_usd"].sum()
                curtailment = res["p_wind_curtailed_mw"].sum() * cfg["time"]["dt_h"]
                wind_used = res["p_wind_used_mw"].sum() * cfg["time"]["dt_h"]
                
                # EV charging metrics
                ev_ch_energy = res["p_ev_ch_mw"].sum() * cfg["time"]["dt_h"] if "p_ev_ch_mw" in res else 0.0
                ev_dis_energy = res["p_ev_dis_mw"].sum() * cfg["time"]["dt_h"] if "p_ev_dis_mw" in res else 0.0
                
                results.append({
                    "penetration_scale": scale,
                    "scenario": scenario,
                    "total_thermal_cost_usd": total_cost,
                    "total_wind_curtailed_mwh": curtailment,
                    "total_wind_used_mwh": wind_used,
                    "total_ev_ch_mwh": ev_ch_energy,
                    "total_ev_dis_mwh": ev_dis_energy
                })
                print(f"Solved {scenario} at scale {scale}")
            except Exception as e:
                print(f"Failed to solve {scenario} at scale {scale}: {e}")
                
    df = pd.DataFrame(results)
    return df

def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    df = run_sensitivity(cfg)
    
    # Ensure directory exists
    sens_dir = Path(cfg["paths"]["results_dir"]) / "sensitivity"
    sens_dir.mkdir(parents=True, exist_ok=True)
    
    path = sens_dir / "penetration_sensitivity.csv"
    write_csv(df, str(path))
    
    return {"penetration_sensitivity": str(path)}

def main() -> None:
    for k, v in run().items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
