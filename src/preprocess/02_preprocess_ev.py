"""Preprocess EV arrival/departure data and mode parameters."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config_loader import load_config, output_path, raw_path
from src.common.constants import MAIN_PERIODS
from src.common.io_utils import write_csv, write_npz
from src.common.validators import validate_availability_matrix, validate_ev_info


def _read_ev_raw(config: dict) -> pd.DataFrame:
    path = raw_path("ev_arrive_leave", config)
    raw = pd.read_excel(path, sheet_name="EV_arrive_leave")
    raw = raw.iloc[:, :3].copy()
    raw.columns = ["ev_id", "arrival_period_raw", "departure_period_raw"]
    raw = raw.dropna(how="all")
    for col in raw.columns:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    raw = raw.dropna(subset=["ev_id", "arrival_period_raw", "departure_period_raw"])
    return raw.astype({"ev_id": int, "arrival_period_raw": int, "departure_period_raw": int})


def build_ev_info(config: dict | None = None) -> pd.DataFrame:
    cfg = config or load_config()
    raw = _read_ev_raw(cfg)

    # Attachment period 2 maps to 18:00-18:15 (t=0); period 57 maps to 07:45-08:00 (t=55).
    ev = raw.copy()
    ev["arrival_slot"] = (ev["arrival_period_raw"] - 2).clip(lower=0, upper=MAIN_PERIODS - 1)
    ev["departure_slot"] = (ev["departure_period_raw"] - 2).clip(lower=0, upper=MAIN_PERIODS - 1)
    ev["departure_slot_exclusive"] = (ev["departure_slot"] + 1).clip(lower=1, upper=MAIN_PERIODS)
    ev["available_periods"] = ev["departure_slot_exclusive"] - ev["arrival_slot"]
    ev = ev[
        [
            "ev_id",
            "arrival_period_raw",
            "departure_period_raw",
            "arrival_slot",
            "departure_slot",
            "departure_slot_exclusive",
            "available_periods",
        ]
    ]
    validate_ev_info(ev)
    return ev


def build_availability_matrix(ev_info: pd.DataFrame) -> np.ndarray:
    slots = np.arange(MAIN_PERIODS)
    start = ev_info["arrival_slot"].to_numpy()[:, None]
    end = ev_info["departure_slot_exclusive"].to_numpy()[:, None]
    availability = (slots[None, :] >= start) & (slots[None, :] < end)
    validate_availability_matrix(availability, len(ev_info))
    return availability


def build_online_summary(availability: np.ndarray, config: dict) -> pd.DataFrame:
    ev_cfg = config["ev"]
    online_count = availability.sum(axis=0).astype(int)
    return pd.DataFrame(
        {
            "t": range(MAIN_PERIODS),
            "online_count": online_count,
            "p_ch_max_unordered_mw": online_count * ev_cfg["default_charge_power_kw"] / 1000.0,
            "p_ch_max_ordered_mw": online_count * ev_cfg["default_charge_power_kw"] / 1000.0,
            "p_dis_max_v2g_mw": online_count * ev_cfg["default_discharge_power_kw"] / 1000.0,
        }
    )


def build_ev_mode_params(config: dict | None = None) -> pd.DataFrame:
    cfg = config or load_config()
    ev = cfg["ev"]
    rows = [
        {
            "scenario": "unordered",
            "p_ch_max_kw": ev["default_charge_power_kw"],
            "p_ch_min_kw": ev["default_charge_power_kw"],
            "p_dis_max_kw": 0.0,
            "p_dis_min_kw": 0.0,
            "charge_fee_usd_per_kwh": ev["unordered_charge_fee_usd_per_kwh"],
            "discharge_fee_usd_per_kwh": 0.0,
        },
        {
            "scenario": "ordered",
            "p_ch_max_kw": ev["default_charge_power_kw"],
            "p_ch_min_kw": 0.0,
            "p_dis_max_kw": 0.0,
            "p_dis_min_kw": 0.0,
            "charge_fee_usd_per_kwh": ev["ordered_charge_fee_usd_per_kwh"],
            "discharge_fee_usd_per_kwh": 0.0,
        },
        {
            "scenario": "v2g",
            "p_ch_max_kw": ev["default_charge_power_kw"],
            "p_ch_min_kw": 0.0,
            "p_dis_max_kw": ev["default_discharge_power_kw"],
            "p_dis_min_kw": 0.0,
            "charge_fee_usd_per_kwh": ev["v2g_charge_fee_usd_per_kwh"],
            "discharge_fee_usd_per_kwh": ev["v2g_discharge_fee_usd_per_kwh"],
        },
    ]
    df = pd.DataFrame(rows)
    for col, value in {
        "charge_need_kwh": ev["charge_need_kwh"],
        "battery_capacity_kwh": ev["battery_capacity_kwh"],
        "energy_min_kwh": ev["minimum_energy_kwh"],
        "initial_energy_kwh": ev["initial_energy_kwh"],
        "eta_ch": ev["charge_efficiency"],
        "eta_dis": ev["discharge_efficiency"],
    }.items():
        df[col] = value
    return df[
        [
            "scenario",
            "p_ch_max_kw",
            "p_ch_min_kw",
            "p_dis_max_kw",
            "p_dis_min_kw",
            "charge_need_kwh",
            "battery_capacity_kwh",
            "energy_min_kwh",
            "initial_energy_kwh",
            "eta_ch",
            "eta_dis",
            "charge_fee_usd_per_kwh",
            "discharge_fee_usd_per_kwh",
        ]
    ]


def preprocess_ev(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    ev_info = build_ev_info(cfg)
    availability = build_availability_matrix(ev_info)
    online_summary = build_online_summary(availability, cfg)
    mode_params = build_ev_mode_params(cfg)

    outputs = {
        "ev_info": write_csv(ev_info, output_path("ev_info", cfg)),
        "ev_availability_56": write_npz(
            output_path("ev_availability_56", cfg),
            availability=availability.astype(np.uint8),
            ev_id=ev_info["ev_id"].to_numpy(),
            t=np.arange(MAIN_PERIODS),
        ),
        "ev_online_summary_56": write_csv(online_summary, output_path("ev_online_summary_56", cfg)),
        "ev_mode_params": write_csv(mode_params, output_path("ev_mode_params", cfg)),
    }
    return {key: str(path) for key, path in outputs.items()}


def main() -> None:
    for name, path in preprocess_ev().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
