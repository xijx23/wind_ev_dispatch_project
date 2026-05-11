"""Preprocess the 96-slot time-of-use price file."""

from __future__ import annotations

import pandas as pd

from src.common.config_loader import load_config, output_path, raw_path
from src.common.constants import DAY_PERIODS
from src.common.io_utils import write_csv
from src.common.time_utils import build_day_time_slots


def build_tou_price_96(config: dict | None = None) -> pd.DataFrame:
    cfg = config or load_config()
    raw = pd.read_excel(raw_path("tou_price", cfg), sheet_name="Sheet1")
    values = raw.iloc[0, 1 : DAY_PERIODS + 1].astype(float).to_list()
    if len(values) != DAY_PERIODS:
        raise ValueError(f"Expected {DAY_PERIODS} price values, got {len(values)}")
    slots = build_day_time_slots()[["t_day", "time_label"]]
    slots["price_cny_per_kwh"] = values
    return slots


def preprocess_price(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    price = build_tou_price_96(cfg)
    return {"tou_price_96": str(write_csv(price, output_path("tou_price_96", cfg)))}


def main() -> None:
    for name, path in preprocess_price().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
