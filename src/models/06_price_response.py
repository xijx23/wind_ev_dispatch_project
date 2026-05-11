"""Baseline price-response model for the extension task."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config_loader import load_config, project_path
from src.common.io_utils import write_csv


def _allocate_by_low_price(price: np.ndarray, total_energy_mwh: float, max_power_mw: float, dt_h: float) -> np.ndarray:
    p = np.zeros_like(price, dtype=float)
    remaining = total_energy_mwh
    for idx in np.argsort(price):
        charge = min(max_power_mw, remaining / dt_h)
        p[idx] = charge
        remaining -= charge * dt_h
        if remaining <= 1e-9:
            break
    return p


def _response_frame(name: str, price: pd.DataFrame, p_mw: np.ndarray, config: dict) -> pd.DataFrame:
    dt_h = float(config["time"]["dt_h"])
    out = price[["t_day", "time_label"]].copy()
    out["price_type"] = name
    out["price_cny_per_kwh"] = price["price_cny_per_kwh"].to_numpy(dtype=float)
    out["p_ev_ch_mw"] = p_mw
    out["energy_mwh"] = p_mw * dt_h
    out["energy_cost_cny"] = out["energy_mwh"] * 1000.0 * out["price_cny_per_kwh"]
    return out


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    price = pd.read_csv(project_path("data/processed/tou_price_96.csv"))
    load_wind = pd.read_csv(project_path("data/processed/load_wind_96_for_price.csv"))
    pr_cfg = cfg["price_response"]
    dt_h = float(cfg["time"]["dt_h"])
    total_energy = float(pr_cfg["total_energy_mwh"])
    max_power = float(pr_cfg["max_charge_power_mw"])

    fixed = price.copy()
    fixed["price_cny_per_kwh"] = float(price["price_cny_per_kwh"].mean())
    tou = price.copy()
    wind_norm = (load_wind["wind_forecast_mw"] - load_wind["wind_forecast_mw"].min()) / (
        load_wind["wind_forecast_mw"].max() - load_wind["wind_forecast_mw"].min()
    )
    wind_guided = price.copy()
    wind_guided["price_cny_per_kwh"] = (
        price["price_cny_per_kwh"] * (1.0 - float(pr_cfg["wind_guided_discount_ratio"]) * wind_norm)
    ).clip(lower=0.1)

    price_tables = {"fixed": fixed, "tou": tou, "wind_guided": wind_guided}
    outputs = {}
    summary_rows = []
    uniform_ref = np.full(len(price), total_energy / (len(price) * dt_h))
    for name, table in price_tables.items():
        p = _allocate_by_low_price(table["price_cny_per_kwh"].to_numpy(dtype=float), total_energy, max_power, dt_h)
        response = _response_frame(name, table, p, cfg)
        outputs[f"price_{name}"] = str(write_csv(table, project_path(cfg["paths"]["price_dir"], f"price_{name}.csv")))
        outputs[f"price_response_{name}"] = str(
            write_csv(response, project_path(cfg["paths"]["price_dir"], f"price_response_{name}.csv"))
        )
        wind_match = float(np.corrcoef(p, load_wind["wind_forecast_mw"].to_numpy(dtype=float))[0, 1])
        discomfort = float(((p - uniform_ref) ** 2).mean() * float(pr_cfg["discomfort_weight"]))
        summary_rows.append(
            {
                "price_type": name,
                "total_energy_mwh": float(response["energy_mwh"].sum()),
                "energy_cost_cny": float(response["energy_cost_cny"].sum()),
                "discomfort_cost": discomfort,
                "wind_charging_corr": wind_match,
            }
        )
    outputs["price_response_summary"] = str(
        write_csv(pd.DataFrame(summary_rows), project_path(cfg["paths"]["price_dir"], "price_response_summary.csv"))
    )
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
