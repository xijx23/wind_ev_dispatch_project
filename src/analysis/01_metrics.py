"""Metric helpers for dispatch and price results."""

from __future__ import annotations

import pandas as pd


def dispatch_summary(dispatch: pd.DataFrame, dt_h: float) -> pd.DataFrame:
    rows = []
    for scenario, group in dispatch.groupby("scenario", sort=False):
        rows.append(
            {
                "scenario": scenario,
                "wind_forecast_mwh": float((group["wind_forecast_mw"] * dt_h).sum()),
                "wind_used_mwh": float((group["wind_used_mw"] * dt_h).sum()),
                "wind_curtail_mwh": float((group["wind_curtail_mw"] * dt_h).sum()),
                "ev_charge_mwh": float((group["p_ev_ch_mw"] * dt_h).sum()),
                "ev_discharge_mwh": float((group["p_ev_dis_mw"] * dt_h).sum()),
                "thermal_energy_mwh": float((group["thermal_total_mw"] * dt_h).sum()),
                "system_cost_usd": float(group["system_cost_usd"].sum()),
            }
        )
    return pd.DataFrame(rows)
