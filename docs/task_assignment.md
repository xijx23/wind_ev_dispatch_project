# 组员 A 当前任务

当前只实现数据预处理和无序充电基准，不实现其他组员的模型内容。

## 负责文件

- `config.yaml`
- `environment.yml`
- `requirements.txt`
- `README.md`
- `src/common/*`
- `src/preprocess/*`
- `src/models/01_unordered_charging.py`
- `docs/variable_dictionary.md`
- `docs/code_interface.md`
- `docs/modeling_notes.md`
- `docs/task_assignment.md`

## 输出

- `data/processed/time_slots_56.csv`
- `data/processed/time_slots_96.csv`
- `data/processed/ev_info.csv`
- `data/processed/ev_availability_56.npz`
- `data/processed/ev_online_summary_56.csv`
- `data/processed/load_wind_56.csv`
- `data/processed/load_wind_96_for_price.csv`
- `data/processed/tou_price_96.csv`
- `data/processed/thermal_params.csv`
- `data/processed/ev_mode_params.csv`
- `data/processed/preprocess_report.json`
- `results/dispatch/dispatch_unordered.csv`
- `results/figures/fig_02_unordered_ev_load.png`
- `results/figures/fig_03_ev_online_summary.png`
