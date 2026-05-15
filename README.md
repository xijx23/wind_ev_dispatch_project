# Wind-EV Dispatch Project

《能源互联网导论》大作业组员 A 代码框架：数据预处理与无序充电基准。

## 快速运行

```bash
conda env create -f environment.yml
conda activate wind_ev_dispatch
python run_all.py
```

已存在环境时更新依赖：

```bash
conda env update -f environment.yml --prune
```

## 当前代码定位

当前只完成组员 A 的数据底座和无序充电基准：

- `config.yaml`：路径、时段、EV、热电机组等预处理参数；
- `environment.yml` / `requirements.txt`：环境依赖；
- `src/common/`：统一字段、配置读取、路径 IO、单位换算、校验；
- `src/preprocess/`：将附件 1、附件 2、附件 3 和手工参数转为标准 CSV/NPZ。
- `src/models/01_unordered_charging.py`：仿真无序充电负荷曲线。

其他 `src/models/` 和 `src/analysis/` 文件暂不实现，留给对应组员继续完成。

## 项目结构

| 路径 | 作用 |
| --- | --- |
| `config.yaml` | 统一配置预处理路径、时段、EV 参数和热电机组参数 |
| `environment.yml` | Conda 环境文件，组员可据此创建一致的虚拟环境 |
| `requirements.txt` | pip 依赖清单，作为 Conda 环境外的轻量备用安装方式 |
| `run_all.py` | 当前总入口，运行预处理、无序充电基准和基础可视化 |
| `data/raw/` | 原始附件和手工参数表，不在代码中改写 |
| `data/processed/` | 预处理标准输出，供后续模型组读取 |
| `src/common/` | 公共工具：配置、路径、字段、单位、时间和校验 |
| `src/preprocess/` | 数据预处理脚本，将附件转换为标准 CSV/NPZ/JSON |
| `src/models/01_unordered_charging.py` | 组员 A 的无序充电基准仿真 |
| `src/models/` | 其他模型文件预留给 EV 聚合、EMS 调度、分解、价格响应等任务 |
| `src/analysis/` | 预留给结果检查、指标、图表和表格生成 |
| `docs/` | 变量字典、预处理接口和任务范围说明 |
| `results/dispatch/` | 无序充电基准等仿真结果输出目录 |
| `results/figures/` | 基础可视化图表输出目录 |
| `report/` | 预留最终报告材料 |

## 统一约定

- 主任务时段：`t = 0..55`，对应 18:00-08:00，步长 `dt_h = 0.25`；
- 拓展任务时段：`t_day = 0..95`，对应 00:00-24:00；
- 单车层单位：`kW/kWh`；
- 集群和系统层单位：`MW/MWh`；
- 场景名：`unordered`、`ordered`、`v2g`。

详细字段见 `docs/variable_dictionary.md`，预处理接口见 `docs/code_interface.md`。
