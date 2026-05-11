# 团队分工摘要

本文件与根目录 `团队分工文档.md` 保持一致，用于代码开发时快速查阅。

## A：数据底座与报告整合

负责：

- `src/common/*`
- `src/preprocess/*`
- `src/models/01_unordered_charging.py`
- `src/analysis/02_result_checks.py`
- `README.md`
- `config.yaml`

主要输出：预处理数据、无序充电基准、结果一致性检查、最终报告整合。

## B：EV 集群建模与单车分解

负责：

- `src/models/02_ev_aggregate.py`
- `src/models/05_ev_decomposition.py`

主要输出：

- `data/processed/ev_agg_bounds_ordered_56.csv`
- `data/processed/ev_agg_bounds_v2g_56.csv`
- `results/decomposition/ev_plan_ordered.csv`
- `results/decomposition/ev_plan_v2g.csv`

## C：EMS 调度与渗透率分析

负责：

- `src/models/03_ems_dispatch.py`
- `src/models/04_penetration_sensitivity.py`

主要输出：

- `results/dispatch/dispatch_unordered.csv`
- `results/dispatch/dispatch_ordered.csv`
- `results/dispatch/dispatch_v2g.csv`
- `results/sensitivity/penetration_sensitivity.csv`

## D：价格机制拓展

负责：

- `src/models/06_price_response.py`
- `src/analysis/01_metrics.py`
- `src/analysis/04_generate_tables.py`

主要输出：

- `results/price/price_fixed.csv`
- `results/price/price_tou.csv`
- `results/price/price_wind_guided.csv`
- `results/price/price_response_*.csv`
- `results/tables/*.csv`

## 协作要求

- 不修改 `data/raw/` 原始附件；
- 重要参数写入 `config.yaml`；
- 文件字段遵守 `docs/variable_dictionary.md`；
- 模块间只通过 CSV、NPZ、JSON 交互；
- 图表保存到 `results/figures/`，表格保存到 `results/tables/`。
