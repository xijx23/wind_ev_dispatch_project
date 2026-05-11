# 数据预处理接口

本阶段只定义组员 A 的预处理输入输出。后续模型组应通过这些标准文件读取数据，不直接读取预处理脚本中的中间变量。

## 运行入口

```bash
python run_all.py
python run_all.py --step preprocess
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
