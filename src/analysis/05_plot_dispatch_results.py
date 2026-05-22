"""Plot EMS dispatch results for member C."""

from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

from src.common.config_loader import load_config, output_path
from src.common.constants import MAIN_PERIODS

# Enable Chinese font if possible
plt.rcParams['font.sans-serif'] = ['SimHei'] # or other Chinese fonts
plt.rcParams['axes.unicode_minus'] = False


def plot_dispatch_curves(config: dict | None = None) -> None:
    cfg = config or load_config()
    fig_dir = Path(cfg["paths"]["figures_dir"])
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    scenarios = ["unordered", "ordered", "v2g"]
    scenario_labels = {"unordered": "无序充电", "ordered": "有序充电", "v2g": "V2G"}
    
    # 1. Compare EV net power across scenarios
    plt.figure(figsize=(10, 6))
    for sc in scenarios:
        try:
            if sc == "unordered":
                path = output_path("dispatch_unordered", cfg)
            else:
                path = f"{cfg['paths']['results_dir']}/dispatch/dispatch_{sc}.csv"
            df = pd.read_csv(path)
            plt.plot(df.index, df["p_ev_net_mw"], label=scenario_labels[sc])
        except Exception as e:
            print(f"Skipping {sc} EV plot: {e}")
            
    plt.title("EV Net Charging Power by Scenario")
    plt.xlabel("Time Slot")
    plt.ylabel("Power (MW)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir / "dispatch_ev_net_power.png")
    plt.close()

    # 2. Compare Wind Curtailment across scenarios
    plt.figure(figsize=(10, 6))
    for sc in scenarios:
        try:
            if sc == "unordered":
                path = output_path("dispatch_unordered", cfg)
            else:
                path = f"{cfg['paths']['results_dir']}/dispatch/dispatch_{sc}.csv"
            df = pd.read_csv(path)
            plt.plot(df.index, df["p_wind_curtailed_mw"], label=scenario_labels[sc])
        except Exception as e:
            print(f"Skipping {sc} Wind Curtailment plot: {e}")
            
    plt.title("Wind Curtailment by Scenario")
    plt.xlabel("Time Slot")
    plt.ylabel("Curtailment (MW)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir / "dispatch_wind_curtailment.png")
    plt.close()
    
    # 3. Stacked Area Chart for V2G (Example)
    try:
        path = f"{cfg['paths']['results_dir']}/dispatch/dispatch_v2g.csv"
        if os.path.exists(path):
            df = pd.read_csv(path)
            plt.figure(figsize=(12, 6))
            
            # Stacked thermal
            thermal_cols = [c for c in df.columns if c.startswith("p_th_") and "total" not in c]
            plt.stackplot(df.index, *[df[c] for c in thermal_cols], labels=thermal_cols, alpha=0.7)
            plt.plot(df.index, df["p_wind_used_mw"], label="Wind Used", color="green", linewidth=2)
            plt.plot(df.index, df["system_load_mw"], label="System Load (incl EV)", color="red", linestyle="--", linewidth=2)
            
            plt.title("V2G Scenario Dispatch")
            plt.xlabel("Time Slot")
            plt.ylabel("Power (MW)")
            plt.legend(loc="upper left")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(fig_dir / "dispatch_v2g_stacked.png")
            plt.close()
    except Exception as e:
        print(f"Skipping V2G stacked plot: {e}")

    # 4. Penetration Sensitivity
    try:
        sens_path = Path(cfg["paths"]["results_dir"]) / "sensitivity" / "penetration_sensitivity.csv"
        if sens_path.exists():
            df_sens = pd.read_csv(sens_path)
            plt.figure(figsize=(10, 6))
            sns.lineplot(data=df_sens, x="penetration_scale", y="total_thermal_cost_usd", hue="scenario", marker="o")
            plt.title("Total Thermal Cost vs EV Penetration")
            plt.xlabel("Penetration Scale (1.0 = Base)")
            plt.ylabel("Cost (USD)")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(fig_dir / "dispatch_sensitivity_cost.png")
            plt.close()
            
            plt.figure(figsize=(10, 6))
            sns.lineplot(data=df_sens, x="penetration_scale", y="total_wind_curtailed_mwh", hue="scenario", marker="o")
            plt.title("Total Wind Curtailment vs EV Penetration")
            plt.xlabel("Penetration Scale (1.0 = Base)")
            plt.ylabel("Curtailed Energy (MWh)")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(fig_dir / "dispatch_sensitivity_curtailment.png")
            plt.close()
    except Exception as e:
        print(f"Skipping Sensitivity plot: {e}")

def run(config: dict | None = None) -> dict[str, str]:
    plot_dispatch_curves(config)
    return {"status": "Success"}

def main() -> None:
    run()

if __name__ == "__main__":
    main()
