# Wind-EV Dispatch Project

《能源互联网导论》大作业代码框架：系统级风电-电动汽车协同调度，以及价格机制引导 EV 充电与风电消纳。

## 快速运行

```bash
pip install -r requirements.txt
python run_all.py
```

只运行单个步骤：

```bash
python run_all.py --step preprocess
python run_all.py --step dispatch
```

## 当前代码定位

本仓库已补齐基础代码层：

- `config.yaml`：路径、时段、EV、热电机组、价格响应参数的统一配置；
- `src/common/`：统一字段、配置读取、路径 IO、单位换算、校验；
- `src/preprocess/`：将 3 个附件转为标准 CSV/NPZ；
- `src/models/`：可运行的无序充电、聚合边界、EMS 基线调度、价格响应基线；
- `src/analysis/`：一致性检查、基础图表、汇总表。

其中 EMS 调度、V2G 和单车分解目前是稳定接口下的基线实现，便于团队协作和报告前期打通流程；正式报告中的优化模型可在保持输出字段不变的前提下替换对应脚本。

## 统一约定

- 主任务时段：`t = 0..55`，对应 18:00-08:00，步长 `dt_h = 0.25`；
- 拓展任务时段：`t_day = 0..95`，对应 00:00-24:00；
- 单车层单位：`kW/kWh`；
- 集群和系统层单位：`MW/MWh`；
- EV 净功率：`p_ev_net_mw = p_ev_ch_mw - p_ev_dis_mw`；
- 场景名：`unordered`、`ordered`、`v2g`。

详细字段见 `docs/variable_dictionary.md`，模块接口见 `docs/code_interface.md`。
