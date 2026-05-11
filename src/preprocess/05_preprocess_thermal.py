"""Create thermal-unit parameter table."""

from __future__ import annotations

import pandas as pd

from src.common.config_loader import load_config, output_path, raw_path
from src.common.io_utils import write_csv


def build_thermal_params(config: dict | None = None) -> pd.DataFrame:
    cfg = config or load_config()
    manual_path = raw_path("thermal_params_manual", cfg)
    if manual_path.exists() and manual_path.stat().st_size > 0:
        manual = pd.read_csv(manual_path)
        canonical = [
            "unit_id",
            "p_min_mw",
            "p_max_mw",
            "ramp_down_mw_per_min",
            "ramp_up_mw_per_min",
            "cost_a_usd_per_mw2h",
            "cost_b_usd_per_mwh",
            "cost_c_usd_per_h",
        ]
        if set(canonical).issubset(manual.columns):
            return manual[canonical]
        # Accept the copied appendix format with a descriptive first header row and
        # a second units row. Keep only numeric unit rows and assign canonical names.
        compact = manual.iloc[:, :8].copy()
        compact.columns = canonical
        compact = compact[pd.to_numeric(compact["unit_id"], errors="coerce").notna()]
        for col in canonical:
            compact[col] = pd.to_numeric(compact[col], errors="raise")
        compact["unit_id"] = compact["unit_id"].astype(int)
        return compact
    return pd.DataFrame(cfg["thermal_units"])


def preprocess_thermal(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    thermal = build_thermal_params(cfg)
    return {"thermal_params": str(write_csv(thermal, output_path("thermal_params", cfg)))}


def main() -> None:
    for name, path in preprocess_thermal().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
