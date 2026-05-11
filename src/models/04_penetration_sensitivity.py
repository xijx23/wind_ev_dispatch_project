"""Simple EV penetration sensitivity based on the baseline dispatch profile."""

from __future__ import annotations

import pandas as pd

from src.common.config_loader import load_config, project_path
from src.common.io_utils import write_csv


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    base = pd.read_csv(project_path(cfg["paths"]["dispatch_dir"], "dispatch_ordered.csv"))
    rows = []
    for ratio in [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5]:
        ev_net = base["p_ev_net_mw"] * ratio
        residual_curtail = (base["wind_forecast_mw"] - (base["load_mw"] + ev_net - base["thermal_total_mw"]).clip(lower=0)).clip(lower=0)
        rows.append(
            {
                "penetration_ratio": ratio,
                "ev_energy_mwh": float((ev_net.clip(lower=0) * cfg["time"]["dt_h"]).sum()),
                "wind_curtailment_mwh": float((residual_curtail * cfg["time"]["dt_h"]).sum()),
            }
        )
    path = project_path(cfg["paths"]["sensitivity_dir"], "penetration_sensitivity.csv")
    return {"penetration_sensitivity": str(write_csv(pd.DataFrame(rows), path))}


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
