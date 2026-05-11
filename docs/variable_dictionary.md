# 变量字典

## 时间

| 变量 | 含义 | 单位/范围 |
| --- | --- | --- |
| `t` | 主任务时段编号 | `0..55`，18:00-08:00 |
| `t_day` | 拓展任务全天时段编号 | `0..95`，00:00-24:00 |
| `time_label` | 时段文本 | 如 `18:00-18:15` |
| `start_minute` | 时段开始分钟 | 从 00:00 起算 |
| `end_minute` | 时段结束分钟 | 从 00:00 起算 |
| `dt_h` | 时间步长 | h，固定 `0.25` |

## EV 原始与标准化信息

| 变量 | 含义 | 单位 |
| --- | --- | --- |
| `ev_id` | 车辆编号 | - |
| `arrival_period_raw` | 附件 1 原始到达时间段 | 1 基编号 |
| `departure_period_raw` | 附件 1 原始离开时间段 | 1 基编号 |
| `arrival_slot` | 标准化到达时段 | 0 基，主任务 |
| `departure_slot` | 标准化离开时段 | 0 基，主任务 |
| `departure_slot_exclusive` | 标准化离开时段右开端点 | 0 基，主任务 |
| `available_periods` | 在线时段数 | 个 |
| `online_count` | 每时段在线车辆数 | 辆 |

## EV 参数

| 变量 | 含义 | 单位 |
| --- | --- | --- |
| `scenario` | EV 模式名 | `unordered`、`ordered`、`v2g` |
| `p_ch_max_kw` / `p_ch_min_kw` | 单车充电功率上下限 | kW |
| `p_dis_max_kw` / `p_dis_min_kw` | 单车放电功率上下限 | kW |
| `charge_need_kwh` | 单车需补能量 | kWh |
| `battery_capacity_kwh` | 单车电池容量 | kWh |
| `energy_min_kwh` | 单车最小电量 | kWh |
| `initial_energy_kwh` | 单车初始电量 | kWh |
| `eta_ch` / `eta_dis` | 充/放电效率 | p.u. |
| `charge_fee_usd_per_kwh` | 充电费用参数 | $/kWh |
| `discharge_fee_usd_per_kwh` | 放电费用参数 | $/kWh |

## 负荷、风电、热电与价格

| 变量 | 含义 | 单位 |
| --- | --- | --- |
| `load_mw` | 普通负荷预测 | MW |
| `wind_forecast_mw` | 风电预测出力 | MW |
| `price_cny_per_kwh` | 分时电价 | 元/kWh |
| `unit_id` | 热电机组编号 | - |
| `p_min_mw` / `p_max_mw` | 单台热电机组出力上下限 | MW |
| `ramp_down_mw_per_min` / `ramp_up_mw_per_min` | 爬坡约束 | MW/min |
| `cost_a_usd_per_mw2h` | 二次成本系数 | $/(MW²h) |
| `cost_b_usd_per_mwh` | 一次成本系数 | $/MWh |
| `cost_c_usd_per_h` | 固定成本系数 | $/h |
