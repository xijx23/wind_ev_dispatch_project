"""Validation routines for exchanged CSV/NPZ files."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.constants import MAIN_PERIODS
from src.common.io_utils import require_columns
from src.common.schemas import TableSchema


def validate_schema(df: pd.DataFrame, schema: TableSchema) -> None:
    require_columns(df, list(schema.columns), schema.name)
    for key in schema.primary_key:
        if df[key].isna().any():
            raise ValueError(f"{schema.name}.{key} contains missing values")
    if schema.primary_key and df.duplicated(list(schema.primary_key)).any():
        raise ValueError(f"{schema.name} primary key is not unique: {schema.primary_key}")


def validate_time_slots_56(df: pd.DataFrame) -> None:
    require_columns(df, ["t", "dt_h"], "time_slots_56")
    if len(df) != MAIN_PERIODS or set(df["t"]) != set(range(MAIN_PERIODS)):
        raise ValueError("time_slots_56 must contain t=0..55")


def validate_ev_info(df: pd.DataFrame) -> None:
    require_columns(df, ["ev_id", "arrival_slot", "departure_slot_exclusive"], "ev_info")
    if (df["arrival_slot"] < 0).any() or (df["departure_slot_exclusive"] > MAIN_PERIODS).any():
        raise ValueError("EV availability slots out of 56-period range")
    if (df["departure_slot_exclusive"] <= df["arrival_slot"]).any():
        raise ValueError("Some EVs have non-positive available windows")


def validate_availability_matrix(matrix: np.ndarray, ev_count: int | None = None) -> None:
    if matrix.ndim != 2 or matrix.shape[1] != MAIN_PERIODS:
        raise ValueError(f"EV availability matrix must be N x {MAIN_PERIODS}")
    if ev_count is not None and matrix.shape[0] != ev_count:
        raise ValueError(f"EV availability matrix row count {matrix.shape[0]} != {ev_count}")
