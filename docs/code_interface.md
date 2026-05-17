# 数据预处理接口

本阶段只定义组员 A 的预处理输入输出。后续模型组应通过这些标准文件读取数据，不直接读取预处理脚本中的中间变量。

## 运行入口

```bash
python run_all.py
python run_all.py --step preprocess
python run_all.py --step unordered
python run_all.py --step aggregate
python run_all.py --step plots
```

## 原始输入

| 文件 | 说明 |
| --- | --- |
| `data/raw/附件1-集群电动汽车到达_离开数据.xlsx` | EV 到达/离开时间段 |
| `data/raw/附件2-风电出力_普通负荷预测数据.xlsx` | 56 时段负荷与风电 |
| `data/raw/附件3-参考单日分时电价_未考虑风电消纳.xlsx` | 96 时段分时电价 |
| `data/raw/thermal_params_manual.csv` | 热电参数手工表，可为空，空时读取 `config.yaml` |
| `data/raw/ev_mode_params_manual.csv` | 预留手工表，目前参数来自 `config.yaml` |

## 标准输出

| 文件 | 主要字段 |
| --- | --- |
| `data/processed/time_slots_56.csv` | `t`, `time_label`, `start_minute`, `end_minute`, `dt_h` |
| `data/processed/time_slots_96.csv` | `t_day`, `time_label`, `start_minute`, `end_minute`, `dt_h` |
| `data/processed/ev_info.csv` | `ev_id`, `arrival_slot`, `departure_slot_exclusive`, `available_periods` |
| `data/processed/ev_availability_56.npz` | `availability`, `ev_id`, `t` |
| `data/processed/ev_online_summary_56.csv` | `t`, `online_count`, `p_ch_max_*_mw`, `p_dis_max_v2g_mw` |
| `data/processed/load_wind_56.csv` | `t`, `time_label`, `load_mw`, `wind_forecast_mw` |
| `data/processed/load_wind_96_for_price.csv` | `t_day`, `time_label`, `load_mw`, `wind_forecast_mw` |
| `data/processed/tou_price_96.csv` | `t_day`, `time_label`, `price_cny_per_kwh` |
| `data/processed/thermal_params.csv` | `unit_id`, `p_min_mw`, `p_max_mw`, `ramp_*`, `cost_*` |
| `data/processed/ev_mode_params.csv` | `scenario`, `p_ch_max_kw`, `p_dis_max_kw`, `eta_*`, `fee_*` |
| `data/processed/preprocess_report.json` | 预处理输出清单和表结构摘要 |

## 无序充电输出

| 文件 | 主要字段/内容 |
| --- | --- |
| `results/dispatch/dispatch_unordered.csv` | `t`, `p_ev_ch_mw`, `system_load_with_unordered_ev_mw`, `charging_count` |
| `results/figures/fig_02_unordered_ev_load.png` | 普通负荷、无序充电负荷、叠加负荷曲线 |
| `results/figures/fig_03_ev_online_summary.png` | 在线车辆数与正在充电车辆数 |

## EV 聚合边界输出

| 文件 | 主要字段/内容 |
| --- | --- |
| `data/processed/ev_agg_bounds_ordered_56.csv` | 有序充电场景的 `p_ch_max_mw`, `p_dis_max_mw`, `energy_min_mwh`, `energy_max_mwh` |
| `data/processed/ev_agg_bounds_v2g_56.csv` | 有序充放电场景的 `p_ch_max_mw`, `p_dis_max_mw`, `energy_min_mwh`, `energy_max_mwh` |

其中 `p_*_mw` 为时段内电网侧功率边界，`energy_*_mwh` 为每个时段结束时的累计电池侧净补能边界。调度模型可使用：

```text
E_ev[t] = E_ev[t-1] + eta_ch * p_ev_ch_mw[t] * dt_h - p_ev_dis_mw[t] * dt_h / eta_dis
energy_min_mwh[t] <= E_ev[t] <= energy_max_mwh[t]
0 <= p_ev_ch_mw[t] <= p_ch_max_mw[t]
0 <= p_ev_dis_mw[t] <= p_dis_max_mw[t]
```
