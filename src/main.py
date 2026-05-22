"""Preprocessing orchestration entrypoint for member A."""

from __future__ import annotations

import argparse
import runpy
from pathlib import Path

from src.common.config_loader import load_config


STEPS = {
    "preprocess": ("src/preprocess/00_preprocess_all.py", "preprocess_all"),
    "unordered": ("src/models/01_unordered_charging.py", "run"),
    "aggregate":("src/models/02_ev_aggregate.py", "run"),
    "dispatch":("src/models/03_ems_dispatch.py", "run"),
    "sensitivity":("src/models/04_penetration_sensitivity.py", "run"),
    "plots_dispatch":("src/analysis/05_plot_dispatch_results.py", "run"),
}

DEFAULT_ORDER = [
    "preprocess",
    "unordered",
    "aggregate",
    "dispatch",
    "sensitivity",
    "plots_dispatch",
]


def _run_step(step: str, config: dict) -> dict[str, str]:
    script, func = STEPS[step]
    namespace = runpy.run_path(str(Path(script)))
    result = namespace[func](config)
    print(f"[{step}]")
    if isinstance(result, dict):
        for key, path in result.items():
            print(f"  {key}: {path}")
        return result
    return {}


def run_pipeline(steps: list[str] | None = None, config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    selected = steps or DEFAULT_ORDER
    outputs: dict[str, str] = {}
    for step in selected:
        if step not in STEPS:
            raise ValueError(f"Unknown step: {step}. Available: {', '.join(STEPS)}")
        outputs.update(_run_step(step, cfg))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Wind-EV dispatch project pipeline.")
    parser.add_argument("--step", action="append", choices=sorted(STEPS), help="Run one or more selected steps.")
    args = parser.parse_args()
    run_pipeline(args.step)


if __name__ == "__main__":
    main()
