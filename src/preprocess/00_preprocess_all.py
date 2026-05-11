"""Run all preprocessing steps."""

from __future__ import annotations

import runpy
from pathlib import Path

import pandas as pd

from src.common.config_loader import PROJECT_ROOT, load_config, output_path
from src.common.io_utils import write_json
from src.common.time_utils import now_timestamp
from src.preprocess import (
    _load_module_function,
)


def _call(script_name: str, function_name: str, config: dict) -> dict[str, str]:
    module_path = Path(__file__).with_name(script_name)
    namespace = runpy.run_path(str(module_path))
    return namespace[function_name](config)


def preprocess_all(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    outputs: dict[str, str] = {}
    for script_name, function_name in [
        ("01_build_time_slots.py", "build_time_slot_files"),
        ("02_preprocess_ev.py", "preprocess_ev"),
        ("03_preprocess_load_wind.py", "preprocess_load_wind"),
        ("04_preprocess_price.py", "preprocess_price"),
        ("05_preprocess_thermal.py", "preprocess_thermal"),
    ]:
        outputs.update(_call(script_name, function_name, cfg))

    report = {
        "generated_at": now_timestamp(),
        "project_root": str(PROJECT_ROOT),
        "outputs": outputs,
        "summary": _build_summary(cfg),
    }
    outputs["preprocess_report"] = str(write_json(report, output_path("preprocess_report", cfg)))
    return outputs


def _build_summary(config: dict) -> dict:
    summary = {}
    for key in ["ev_info", "load_wind_56", "tou_price_96", "thermal_params", "ev_mode_params"]:
        path = output_path(key, config)
        if path.exists() and path.stat().st_size > 0:
            df = pd.read_csv(path)
            summary[key] = {"rows": int(len(df)), "columns": list(df.columns)}
    return summary


def main() -> None:
    for name, path in preprocess_all().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
