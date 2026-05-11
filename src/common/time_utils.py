"""Time-slot utilities for 15-minute dispatch models."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from src.common.constants import DAY_PERIODS, DT_H, MAIN_PERIODS, MAIN_START_HOUR


def _format_clock(total_minutes: int) -> str:
    total_minutes %= 24 * 60
    hour, minute = divmod(total_minutes, 60)
    return f"{hour:02d}:{minute:02d}"


def slot_label(start_minutes: int, slot: int, dt_h: float = DT_H) -> str:
    step = int(round(dt_h * 60))
    begin = start_minutes + slot * step
    end = begin + step
    return f"{_format_clock(begin)}-{_format_clock(end)}"


def build_time_slots(periods: int, start_hour: int = 0, dt_h: float = DT_H) -> pd.DataFrame:
    start_minutes = int(start_hour * 60)
    return pd.DataFrame(
        {
            "t" if periods == MAIN_PERIODS else "t_day": range(periods),
            "time_label": [slot_label(start_minutes, t, dt_h) for t in range(periods)],
            "start_minute": [(start_minutes + t * int(round(dt_h * 60))) % (24 * 60) for t in range(periods)],
            "end_minute": [(start_minutes + (t + 1) * int(round(dt_h * 60))) % (24 * 60) for t in range(periods)],
            "dt_h": dt_h,
        }
    )


def build_main_time_slots() -> pd.DataFrame:
    return build_time_slots(MAIN_PERIODS, MAIN_START_HOUR, DT_H)


def build_day_time_slots() -> pd.DataFrame:
    return build_time_slots(DAY_PERIODS, 0, DT_H)


def main_slot_to_day_slot(t: int) -> int:
    """Map 18:00-08:00 main-task slot index to 00:00-24:00 slot index."""
    return (MAIN_START_HOUR * 4 + t) % DAY_PERIODS


def now_timestamp() -> str:
    return datetime.now().replace(microsecond=0).isoformat()
