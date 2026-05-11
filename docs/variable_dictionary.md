# 变量字典

## 时间

| 变量 | 含义 | 单位/范围 |
| --- | --- | --- |
| `t` | 主任务时段编号 | `0..55`，18:00-08:00 |
| `t_day` | 拓展任务全天时段编号 | `0..95`，00:00-24:00 |
| `time_label` | 时段文本 | 如 `18:00-18:15` |
| `dt_h` | 时间步长 | h，固定 `0.25` |

## EV

| 变量 | 含义 | 单位 |
| --- | --- | --- |
| `ev_id` | 车辆编号 | - |
| `arrival_period_raw` | 附件 1 原始到达时间段 | 1 基编号 |
| `departure_period_raw` | 附件 1 原始离开时间段 | 1 基编号 |
| `arrival_slot` | 标准化到达时段 | 0 基，主任务 |
| `departure_slot_exclusive` | 标准化离开时段右开端点 | 0 基，主任务 |
| `online_count` | 在线车辆数 | 辆 |
| `p_ev_ch_mw` | EV 集群充电功率 | MW |
| `p_ev_dis_mw` | EV 集群放电功率 | MW |
| `p_ev_net_mw` | EV 集群净功率，充电为正 | MW |
| `charge_need_kwh` | 单车需补能量 | kWh |
| `battery_capacity_kwh` | 单车电池容量 | kWh |
| `eta_ch` / `eta_dis` | 充/放电效率 | p.u. |

## 负荷、风电、热电

| 变量 | 含义 | 单位 |
| --- | --- | --- |
| `load_mw` | 普通负荷预测 | MW |
| `wind_forecast_mw` | 风电预测出力 | MW |
| `wind_used_mw` | 风电消纳功率 | MW |
| `wind_curtail_mw` | 弃风功率 | MW |
| `thermal_total_mw` | 热电机组总出力 | MW |
| `p_min_mw` / `p_max_mw` | 单台热电机组出力上下限 | MW |
| `ramp_down_mw_per_min` / `ramp_up_mw_per_min` | 爬坡约束 | MW/min |
| `cost_a_usd_per_mw2h` | 二次成本系数 | $/(MW²h) |
| `cost_b_usd_per_mwh` | 一次成本系数 | $/MWh |
| `cost_c_usd_per_h` | 固定成本系数 | $/h |

## 价格拓展

| 变量 | 含义 | 单位 |
| --- | --- | --- |
| `price_cny_per_kwh` | 电价 | 元/kWh |
| `price_type` | 电价机制 | `fixed`、`tou`、`wind_guided` |
| `energy_cost_cny` | 用户电费 | 元 |
| `discomfort_cost` | 偏离参考充电曲线的不适成本指标 | 标幺化指标 |
| `wind_charging_corr` | 风电与充电功率相关系数 | - |

## 场景

| 场景 | 含义 |
| --- | --- |
| `unordered` | 无序充电 |
| `ordered` | 有序充电 |
| `v2g` | 有序充放电 |
