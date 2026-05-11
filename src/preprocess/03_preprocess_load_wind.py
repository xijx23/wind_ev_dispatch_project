"""Preprocess load and wind forecast data."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config_loader import load_config, output_path, raw_path
from src.common.constants import DAY_PERIODS, MAIN_PERIODS
from src.common.io_utils import write_csv
from src.common.time_utils import build_day_time_slots, main_slot_to_day_slot


def build_load_wind_56(config: dict | None = None) -> pd.DataFrame:
    cfg = config or load_config()
    raw = pd.read_excel(raw_path("load_wind", cfg), sheet_name="load_wind_data")
    df = raw.iloc[:, :3].copy()
    df.columns = ["time_label", "load_mw", "wind_forecast_mw"]
    df = df.dropna(how="all")
    df["t"] = range(len(df))
    df = df[["t", "time_label", "load_mw", "wind_forecast_mw"]]
    if len(df) != MAIN_PERIODS:
        raise ValueError(f"Expected {MAIN_PERIODS} load/wind rows, got {len(df)}")
    return df


def build_load_wind_96(load_wind_56: pd.DataFrame) -> pd.DataFrame:
    day = build_day_time_slots()[["t_day", "time_label"]].copy()
    day["load_mw"] = np.nan
    day["wind_forecast_mw"] = np.nan
    for _, row in load_wind_56.iterrows():
        t_day = main_slot_to_day_slot(int(row["t"]))
        day.loc[day["t_day"] == t_day, ["load_mw", "wind_forecast_mw"]] = [row["load_mw"], row["wind_forecast_mw"]]

    # The source only covers 18:00-08:00. Fill the daytime gap smoothly so price-response
    # experiments have a complete 96-slot reference without inventing another raw file.
    for col in ["load_mw", "wind_forecast_mw"]:
        day[col] = day[col].interpolate(method="linear", limit_direction="both")
    return day


def preprocess_load_wind(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    load_wind_56 = build_load_wind_56(cfg)
    load_wind_96 = build_load_wind_96(load_wind_56)
    return {
        "load_wind_56": str(write_csv(load_wind_56, output_path("load_wind_56", cfg))),
        "load_wind_96_for_price": str(write_csv(load_wind_96, output_path("load_wind_96_for_price", cfg))),
    }


def main() -> None:
    for name, path in preprocess_load_wind().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
