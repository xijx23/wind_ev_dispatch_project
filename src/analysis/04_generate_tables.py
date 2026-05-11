"""Generate summary tables for the report."""

from __future__ import annotations

import runpy

import pandas as pd

from src.common.config_loader import load_config, project_path
from src.common.io_utils import write_csv


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    metrics_ns = runpy.run_path(str(project_path("src/analysis/01_metrics.py")))
    dispatch_summary = metrics_ns["dispatch_summary"]

    dispatch = pd.concat(
        [pd.read_csv(project_path(cfg["paths"]["dispatch_dir"], f"dispatch_{s}.csv")) for s in ["unordered", "ordered", "v2g"]],
        ignore_index=True,
    )
    summary = dispatch_summary(dispatch, float(cfg["time"]["dt_h"]))
    path = project_path(cfg["paths"]["tables_dir"], "table_dispatch_summary.csv")
    outputs = {"table_dispatch_summary": str(write_csv(summary, path))}

    price_summary = pd.read_csv(project_path(cfg["paths"]["price_dir"], "price_response_summary.csv"))
    outputs["table_price_summary"] = str(
        write_csv(price_summary, project_path(cfg["paths"]["tables_dir"], "table_price_summary.csv"))
    )
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
