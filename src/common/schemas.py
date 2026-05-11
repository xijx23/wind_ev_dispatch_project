"""Canonical table schemas.

The schemas are intentionally lightweight: they document required columns and
are used by validators without imposing a heavy data-model dependency.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.common.constants import (
    EV_INFO_COLUMNS,
    EV_MODE_COLUMNS,
    LOAD_WIND_COLUMNS,
    PRICE_COLUMNS,
    THERMAL_COLUMNS,
)


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: tuple[str, ...]
    primary_key: tuple[str, ...] = ()


TIME_SLOTS_56 = TableSchema("time_slots_56", ("t", "time_label", "start_minute", "end_minute", "dt_h"), ("t",))
TIME_SLOTS_96 = TableSchema("time_slots_96", ("t_day", "time_label", "start_minute", "end_minute", "dt_h"), ("t_day",))
EV_INFO = TableSchema("ev_info", tuple(EV_INFO_COLUMNS), ("ev_id",))
LOAD_WIND_56 = TableSchema("load_wind_56", tuple(LOAD_WIND_COLUMNS), ("t",))
TOU_PRICE_96 = TableSchema("tou_price_96", tuple(PRICE_COLUMNS), ("t_day",))
EV_MODE_PARAMS = TableSchema("ev_mode_params", tuple(EV_MODE_COLUMNS), ("scenario",))
THERMAL_PARAMS = TableSchema("thermal_params", tuple(THERMAL_COLUMNS), ("unit_id",))


SCHEMAS = {
    schema.name: schema
    for schema in [
        TIME_SLOTS_56,
        TIME_SLOTS_96,
        EV_INFO,
        LOAD_WIND_56,
        TOU_PRICE_96,
        EV_MODE_PARAMS,
        THERMAL_PARAMS,
    ]
}
