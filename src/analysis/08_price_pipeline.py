"""Generate price-response CSVs and figures with reusable summary output."""

from __future__ import annotations

import importlib
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.config_loader import load_config


PROJ_ROOT = Path(__file__).parents[2]
PRICE_DIR = PROJ_ROOT / "results" / "price"
FIG_DIR = PROJ_ROOT / "results" / "figures"

model = importlib.import_module("src.models.06_price_response")
plotter = importlib.import_module("src.analysis.06_plot_price_results")


def _save_series(filename: str, column: str, values: np.ndarray) -> str:
    PRICE_DIR.mkdir(parents=True, exist_ok=True)
    path = PRICE_DIR / filename
    pd.DataFrame({"time_slot": range(len(values)), column: values}).to_csv(path, index=False)
    return str(path)


def _write_summary(
    m_fixed: dict,
    m_tou: dict,
    best_rec: dict,
    best_metrics_ls: dict,
    start_beta: float,
) -> str:
    summary = pd.DataFrame(
        [
            {"scenario": "fixed", "beta": np.nan, **m_fixed},
            {"scenario": "tou", "beta": np.nan, **m_tou},
            {"scenario": "wind_guided", "beta": best_rec["beta"], **best_rec["metrics"]},
            {"scenario": "local_search", "beta": start_beta, **best_metrics_ls},
        ]
    )
    path = PRICE_DIR / "price_response_summary.csv"
    summary.to_csv(path, index=False)
    return str(path)


def run(config: dict | None = None) -> dict[str, str]:
    load_config() if config is None else config
    PRICE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    res = model.main()
    price_fixed, p_ch_fixed, m_fixed = res["fixed"]
    price_tou, p_ch_tou, m_tou = res["tou"]
    scan_results = res["scan_alpha3.0"]
    best_price_ls, best_p_ch_ls, best_metrics_ls, start_beta, _ = res["local_search"]

    feasible = [r for r in scan_results if r["metrics"]["elec_cost_kyuan"] >= 0]
    best_rec = max(feasible or scan_results, key=lambda x: x["metrics"]["weighted_wind_mw"])
    rec_price = best_rec["price"]
    rec_p_ch = best_rec["p_ch"]

    outputs = {
        "price_fixed": _save_series("price_fixed.csv", "price_yuan_per_mwh", price_fixed),
        "price_response_fixed": _save_series("price_response_fixed.csv", "p_ch_mw", p_ch_fixed),
        "price_tou": _save_series("price_tou.csv", "price_yuan_per_mwh", price_tou),
        "price_response_tou": _save_series("price_response_tou.csv", "p_ch_mw", p_ch_tou),
        "price_wind_guided": _save_series("price_wind_guided.csv", "price_yuan_per_mwh", rec_price),
        "price_response_wind_guided": _save_series("price_response_wind_guided.csv", "p_ch_mw", rec_p_ch),
        "price_local_search": _save_series("price_local_search.csv", "price_yuan_per_mwh", best_price_ls),
        "price_response_local_search": _save_series("price_response_local_search.csv", "p_ch_mw", best_p_ch_ls),
        "price_response_summary": _write_summary(m_fixed, m_tou, best_rec, best_metrics_ls, start_beta),
    }

    alpha_scan_results = res.get("alpha_scan", [])
    plotter.plot_fig12_price_curves(scan_results, price_fixed, price_tou)
    plotter.plot_fig13_price_response(scan_results, p_ch_fixed, p_ch_tou)
    plotter.plot_fig14_wind_charging_matching(rec_p_ch)
    if alpha_scan_results:
        plotter.plot_fig15_alpha_comparison(alpha_scan_results)
    plotter.plot_fig16_3d(scan_results)
    plotter.plot_fig17_extra_price_local_search(scan_results, price_fixed, price_tou, best_price_ls, start_beta)
    plotter.plot_fig18_extra_price_response_local_search(scan_results, p_ch_fixed, p_ch_tou, best_p_ch_ls, start_beta)
    plotter.plot_fig19_charging_comparison(scan_results, best_p_ch_ls, start_beta)

    for index in range(12, 20):
        for path in FIG_DIR.glob(f"fig_{index:02d}_*.png"):
            outputs[path.stem] = str(path)
    return outputs


def main() -> None:
    for name, path in run().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
