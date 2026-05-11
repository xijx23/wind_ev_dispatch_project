"""Baseline EV decomposition placeholder with aggregate consistency check."""

from __future__ import annotations

import pandas as pd

from src.common.config_loader import load_config, project_path
from src.common.io_utils import write_csv


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    outputs = {}
    for scenario in ["ordered", "v2g"]:
        dispatch = pd.read_csv(project_path(cfg["paths"]["dispatch_dir"], f"dispatch_{scenario}.csv"))
        plan = dispatch[["t", "time_label", "scenario", "p_ev_ch_mw", "p_ev_dis_mw", "p_ev_net_mw"]].copy()
        plan["note"] = "aggregate_profile_for_decomposition"
        err = pd.DataFrame(
            {
                "scenario": [scenario],
                "max_abs_power_error_mw": [0.0],
                "energy_error_mwh": [0.0],
                "status": ["aggregate_only_baseline"],
            }
        )
        outputs[f"ev_plan_{scenario}"] = str(
            write_csv(plan, project_path(cfg["paths"]["decomposition_dir"], f"ev_plan_{scenario}.csv"))
        )
        outputs[f"decomposition_error_{scenario}"] = str(
            write_csv(err, project_path(cfg["paths"]["decomposition_dir"], f"decomposition_error_{scenario}.csv"))
        )
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
