"""Unit conversion helpers."""

from __future__ import annotations

from src.common.constants import KWH_PER_MWH, KW_PER_MW


def kw_to_mw(value: float) -> float:
    return value / KW_PER_MW


def mw_to_kw(value: float) -> float:
    return value * KW_PER_MW


def kwh_to_mwh(value: float) -> float:
    return value / KWH_PER_MWH


def mwh_to_kwh(value: float) -> float:
    return value * KWH_PER_MWH
