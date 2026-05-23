"""
生成汇总表格（写入组长预留的表格文件）
- table_price_summary.csv：固定、分时、推荐、局部搜索对比
- 其他表格（成本、弃风等）由主任务负责，本模块不覆盖
"""

import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJ_ROOT))

import pandas as pd
import numpy as np
import importlib

model = importlib.import_module('src.models.06_price_response')

TABLE_DIR = PROJ_ROOT / "results/tables"
TABLE_DIR.mkdir(exist_ok=True, parents=True)

def generate_tables():
    # 加载模型结果
    res = model.main()
    
    # 使用主体 alpha=3.0 的数据
    scan_results = res['scan_alpha3.0']
    _, _, m_fixed = res['fixed']
    _, _, m_tou = res['tou']
    best_price_ls, best_p_ch_ls, best_metrics_ls, start_beta, _ = res['local_search']
    
    # 推荐新电价（电费非负下加权风电最大的β）
    feasible = [r for r in scan_results if r['metrics']['elec_cost_kyuan'] >= 0]
    if feasible:
        best_rec = max(feasible, key=lambda x: x['metrics']['weighted_wind_mw'])
        rec_beta = best_rec['beta']
        rec_metrics = best_rec['metrics']
    else:
        best_rec = max(scan_results, key=lambda x: x['metrics']['weighted_wind_mw'])
        rec_beta = best_rec['beta']
        rec_metrics = best_rec['metrics']
    
    # 写入 table_price_summary.csv（组长预留）
    data = {
        'Scenario': ['Fixed price', 'Time-of-Use', f'Recommended (β={rec_beta:.2f})', f'Local search (from β={start_beta})'],
        'Weighted Wind (MW)': [m_fixed['weighted_wind_mw'], m_tou['weighted_wind_mw'], rec_metrics['weighted_wind_mw'], best_metrics_ls['weighted_wind_mw']],
        'Electricity Cost (kYuan)': [m_fixed['elec_cost_kyuan'], m_tou['elec_cost_kyuan'], rec_metrics['elec_cost_kyuan'], best_metrics_ls['elec_cost_kyuan']],
        'Wind Correlation': [m_fixed['wind_corr'], m_tou['wind_corr'], rec_metrics['wind_corr'], best_metrics_ls['wind_corr']],
        'Discomfort Cost (kYuan)': [m_fixed['discomfort_kyuan'], m_tou['discomfort_kyuan'], rec_metrics['discomfort_kyuan'], best_metrics_ls['discomfort_kyuan']],
        'Total Cost (kYuan)': [m_fixed['total_cost_kyuan'], m_tou['total_cost_kyuan'], rec_metrics['total_cost_kyuan'], best_metrics_ls['total_cost_kyuan']]
    }
    df = pd.DataFrame(data)
    for col in df.columns:
        if col != 'Scenario':
            df[col] = df[col].round(4)
    
    # 写入组长预留的表格文件
    out_path = TABLE_DIR / "table_price_summary.csv"
    df.to_csv(out_path, index=False)
    print(f"价格汇总表已保存到 {out_path}")
    print(df.to_string(index=False))
    
    # 注意：其他表格（table_cost_summary.csv, table_dispatch_summary.csv 等）
    # 由主任务（A/B/C）负责，本模块不覆盖，保持组长预留的空文件或原有内容

if __name__ == "__main__":
    generate_tables()