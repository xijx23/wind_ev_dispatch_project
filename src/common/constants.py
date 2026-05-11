"""Project-wide constants and canonical names."""

from __future__ import annotations

from enum import StrEnum


DT_H = 0.25
MAIN_PERIODS = 56
DAY_PERIODS = 96
MAIN_START_HOUR = 18

KW_PER_MW = 1000.0
KWH_PER_MWH = 1000.0
MINUTES_PER_HOUR = 60.0


class Scenario(StrEnum):
    UNORDERED = "unordered"
    ORDERED = "ordered"
    V2G = "v2g"


SCENARIOS = tuple(item.value for item in Scenario)

EV_INFO_COLUMNS = [
    "ev_id",
    "arrival_period_raw",
    "departure_period_raw",
    "arrival_slot",
    "departure_slot",
    "departure_slot_exclusive",
    "available_periods",
]

LOAD_WIND_COLUMNS = ["t", "time_label", "load_mw", "wind_forecast_mw"]

PRICE_COLUMNS = ["t_day", "time_label", "price_cny_per_kwh"]

EV_MODE_COLUMNS = [
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

THERMAL_COLUMNS = [
    "unit_id",
    "p_min_mw",
    "p_max_mw",
    "ramp_down_mw_per_min",
    "ramp_up_mw_per_min",
    "cost_a_usd_per_mw2h",
    "cost_b_usd_per_mwh",
    "cost_c_usd_per_h",
]

DISPATCH_COLUMNS = [
    "t",
    "time_label",
    "scenario",
    "load_mw",
    "wind_forecast_mw",
    "wind_used_mw",
    "wind_curtail_mw",
    "thermal_total_mw",
    "p_ev_ch_mw",
    "p_ev_dis_mw",
    "p_ev_net_mw",
    "system_cost_usd",
]
