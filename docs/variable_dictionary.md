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
| `charging_count` | 无序充电中正在充电的车辆数 | 辆 |
| `p_ev_ch_mw` | EV 集群充电功率 | MW |
| `p_ev_dis_mw` | EV 集群放电功率 | MW |
| `p_ev_net_mw` | EV 集群净功率，充电为正 | MW |
| `system_load_with_unordered_ev_mw` | 普通负荷叠加无序充电后的系统负荷 | MW |
| `grid_energy_mwh` | EV 从电网侧吸收的电量 | MWh |
| `battery_energy_mwh` | 计入充电效率后的电池侧补能量 | MWh |
| `remaining_battery_need_mwh` | 剩余未满足电池侧补能量 | MWh |
| `p_ch_max_mw` | 当前时段 EV 集群最大可充电功率，电网侧 | MW |
| `p_dis_max_mw` | 当前时段 EV 集群最大可放电功率，电网侧 | MW |
| `p_net_min_mw` / `p_net_max_mw` | EV 集群净功率上下限，充电为正 | MW |
| `energy_min_mwh` / `energy_max_mwh` | 时段结束时 EV 集群累计电池侧净补能上下限 | MWh |
| `departed_target_energy_mwh` | 截至当前时段结束，已离开车辆累计应满足补能量 | MWh |
| `feasibility_gap_mwh` | 聚合边界不可行缺口，正常应为 0 | MWh |
| `total_required_energy_mwh` | 全部 EV 最终累计应补电池侧能量 | MWh |
| `battery_energy_kwh` | 单车当前时段结束后的电池电量 | kWh |
| `delta_energy_kwh` | 单车相对初始电量的净变化 | kWh |
| `soc` | 单车荷电状态，`battery_energy_kwh / battery_capacity_kwh` | p.u. |
| `is_online` | 单车当前时段是否在线 | 0/1 |
| `is_departure_slot` | 当前时段是否为该车离开前最后一个可用时段 | 0/1 |
| `target_p_ev_ch_mw` / `target_p_ev_dis_mw` | EMS 输出并经数值残差清理后的集群充/放电功率目标 | MW |
| `allocated_p_ev_ch_mw` / `allocated_p_ev_dis_mw` | 单车计划重新聚合后的集群充/放电功率 | MW |
| `ch_error_mw` / `dis_error_mw` / `net_error_mw` | 单车分解相对 EMS 集群目标的功率误差 | MW |
| `departure_shortfall_kwh` / `departure_surplus_kwh` | 离开车辆相对目标电量的总缺口/盈余 | kWh |

| `departure_shortfall_kwh` / `departure_surplus_kwh` | 离开车辆相对目标电量的总缺口/盈余 | kWh |
| `departure_shift_slots` / `departure_shift_minutes` | 离开时间相对原始数据整体平移量 | 时段 / min |
| `infeasible_vehicle_count` | 离开时间平移后未达到目标电量的车辆数 | 辆 |
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
