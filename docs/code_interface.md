# 代码接口

所有模块通过文件交互，不直接依赖其他成员脚本中的中间变量。

## 运行入口

```bash
python run_all.py
python run_all.py --step preprocess
python run_all.py --step dispatch
```

可选步骤：

`preprocess`、`unordered`、`aggregate`、`dispatch`、`sensitivity`、`decomposition`、`price`、`checks`、`plots`、`tables`。

## 预处理输出

| 文件 | 说明 |
| --- | --- |
| `data/processed/time_slots_56.csv` | 主任务 56 时段 |
| `data/processed/time_slots_96.csv` | 拓展任务 96 时段 |
| `data/processed/ev_info.csv` | 标准化 EV 到达/离开数据 |
| `data/processed/ev_availability_56.npz` | EV 在线矩阵，形状 `N x 56` |
| `data/processed/ev_online_summary_56.csv` | 每时段在线数量和功率上限 |
| `data/processed/load_wind_56.csv` | 主任务负荷与风电 |
| `data/processed/load_wind_96_for_price.csv` | 拓展任务全天负荷与风电参考 |
| `data/processed/tou_price_96.csv` | 96 时段分时电价 |
| `data/processed/thermal_params.csv` | 热电厂参数 |
| `data/processed/ev_mode_params.csv` | 三类 EV 模式参数 |

## B → C 接口

| 文件 | 必需字段 |
| --- | --- |
| `data/processed/ev_agg_bounds_ordered_56.csv` | `t`, `p_ch_max_mw`, `p_dis_max_mw`, `e_min_total_mwh`, `e_max_total_mwh` |
| `data/processed/ev_agg_bounds_v2g_56.csv` | `t`, `p_ch_max_mw`, `p_dis_max_mw`, `e_min_total_mwh`, `e_max_total_mwh` |

## C → B 接口

| 文件 | 必需字段 |
| --- | --- |
| `results/dispatch/dispatch_ordered.csv` | `t`, `p_ev_ch_mw`, `p_ev_dis_mw`, `p_ev_net_mw` |
| `results/dispatch/dispatch_v2g.csv` | `t`, `p_ev_ch_mw`, `p_ev_dis_mw`, `p_ev_net_mw` |

## 调度结果标准字段

`t`, `time_label`, `scenario`, `load_mw`, `wind_forecast_mw`, `wind_used_mw`, `wind_curtail_mw`, `thermal_total_mw`, `p_ev_ch_mw`, `p_ev_dis_mw`, `p_ev_net_mw`, `system_cost_usd`。

功率平衡检查使用：

```text
thermal_total_mw + wind_used_mw + p_ev_dis_mw
= load_mw + p_ev_ch_mw
```
