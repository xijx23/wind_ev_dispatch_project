"""
负责：
- 写入最终输出CSV（固定、分时、推荐新电价、局部搜索结果）到 results/price/
- 绘制图表（共8张）：
  1. fig_12_price_curves.png - 电价曲线（所有β）
  2. fig_13_price_response.png - 充电曲线（所有β）
  3. fig_14_wind_charging_matching.png - 风电与推荐充电匹配
  4. fig_15_price_response_for_discomfort_cost.png - alpha扫描对比
  5. fig_16_price_response_3d.png - 三维曲面
  6. fig_17_extra_price_local_search.png - 局部搜索电价对比
  7. fig_18_extra_price_response_local_search.png - 局部搜索充电曲线对比
  8. fig_19_charging_comparison.png - 不同准则充电方案对比
"""

import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJ_ROOT))

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import importlib
from mpl_toolkits.mplot3d import Axes3D

# 设置中文字体（解决中文显示问题）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

model = importlib.import_module('src.models.06_price_response')

PRICE_DIR = PROJ_ROOT / "results/price"
FIG_DIR = PROJ_ROOT / "results/figures"
PRICE_DIR.mkdir(exist_ok=True, parents=True)
FIG_DIR.mkdir(exist_ok=True, parents=True)

DT_H = 0.25
x = np.arange(96) * DT_H

# ========== 绘图函数 ==========
def plot_fig12_price_curves(scan_results, price_fixed, price_tou):
    """fig_12_price_curves.png: 电价曲线（固定、分时、所有β曲线）"""
    wind = model.load_wind()
    
    fig, ax1 = plt.subplots(figsize=(14,6))
    ax1.plot(x, price_fixed, label='Fixed price', linewidth=2, color='blue')
    ax1.plot(x, price_tou, label='ToU price', linewidth=2, color='orange')
    cmap = plt.cm.viridis
    colors = cmap(np.linspace(0, 1, len(scan_results)))
    for r, color in zip(scan_results, colors):
        ax1.plot(x, r['price'], label=f"β={r['beta']:.2f}", color=color, alpha=0.8, linewidth=1.2)
    ax1.set_xlabel('Hour of day')
    ax1.set_ylabel('Price (yuan/MWh)', color='black')
    ax1.legend(loc='upper left', ncol=2, fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(x, wind, label='Wind power (MW)', linewidth=2, color='purple', linestyle='--')
    ax2.set_ylabel('Wind power (MW)', color='purple')
    ax2.legend(loc='upper right')
    plt.title('Electricity price curves under different β (alpha=3.0)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'fig_12_price_curves.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("fig_12_price_curves.png 已保存")

def plot_fig13_price_response(scan_results, p_ch_fixed, p_ch_tou):
    """fig_13_price_response.png: 充电曲线（固定、分时、所有β曲线）"""
    wind = model.load_wind()
    
    fig, ax1 = plt.subplots(figsize=(14,6))
    ax1.plot(x, p_ch_fixed, label='Fixed price', linewidth=2, color='blue')
    ax1.plot(x, p_ch_tou, label='ToU price', linewidth=2, color='orange')
    cmap = plt.cm.viridis
    colors = cmap(np.linspace(0, 1, len(scan_results)))
    for r, color in zip(scan_results, colors):
        ax1.plot(x, r['p_ch'], label=f"β={r['beta']:.2f}", color=color, alpha=0.8, linewidth=1.2)
    ax1.set_xlabel('Hour of day')
    ax1.set_ylabel('Charging power (MW)', color='black')
    ax1.legend(loc='upper left', ncol=2, fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(x, wind, label='Wind power (MW)', linewidth=2, color='purple', linestyle='--')
    ax2.set_ylabel('Wind power (MW)', color='purple')
    ax2.legend(loc='upper right')
    plt.title('EV charging power under different β (alpha=3.0)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'fig_13_price_response.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("fig_13_price_response.png 已保存")

def plot_fig14_wind_charging_matching(rec_p_ch):
    """fig_14_wind_charging_matching.png: 风电与推荐充电功率叠加（双纵轴）"""
    wind = model.load_wind()
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.plot(x, rec_p_ch, label='EV charging (recommended)', linewidth=2, color='green')
    ax1.set_xlabel('Hour of day')
    ax1.set_ylabel('Charging power (MW)', color='green')
    ax1.tick_params(axis='y', labelcolor='green')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(x, wind, label='Wind power (MW)', linewidth=2, color='purple')
    ax2.set_ylabel('Wind power (MW)', color='purple')
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2.legend(loc='upper right')
    plt.title('Wind power and recommended EV charging profile (alpha=3.0)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'fig_14_wind_charging_matching.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("fig_14_wind_charging_matching.png 已保存")

def plot_fig15_alpha_comparison(alpha_scan_results):
    """fig_15_price_response_for_discomfort_cost.png: 不同alpha下充电曲线对比（β=0.4）"""
    plt.figure(figsize=(12,6))
    cmap = plt.cm.plasma
    alphas = [r['alpha'] for r in alpha_scan_results]
    colors = cmap(np.linspace(0, 1, len(alphas)))
    for r, color in zip(alpha_scan_results, colors):
        plt.plot(x, r['p_ch'], label=f"alpha={r['alpha']:.1f}", linewidth=2, color=color)
    plt.xlabel('Hour of day')
    plt.ylabel('Charging power (MW)')
    plt.title(f'Effect of discomfort cost on charging profile (β=0.4)')
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.3)
    plt.savefig(FIG_DIR / 'fig_15_price_response_for_discomfort_cost.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("fig_15_price_response_for_discomfort_cost.png 已保存")

def plot_fig16_3d(scan_results):
    """fig_16_price_response_3d.png: 三维曲面图"""
    beta_list = [r['beta'] for r in scan_results]
    p_ch_all = np.array([r['p_ch'] for r in scan_results])
    X, Y = np.meshgrid(x, beta_list)
    fig = plt.figure(figsize=(12,8))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(X, Y, p_ch_all, cmap='viridis', edgecolor='none')
    ax.set_xlabel('Hour')
    ax.set_ylabel('β')
    ax.set_zlabel('Charging power (MW)')
    ax.set_title('EV charging power vs time and β (alpha=3.0)')
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
    plt.savefig(FIG_DIR / 'fig_16_price_response_3d.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("fig_16_price_response_3d.png 已保存")

def plot_fig17_extra_price_local_search(scan_results, price_fixed, price_tou, best_price_ls, start_beta):
    """fig_17_extra_price_local_search.png: 局部搜索电价对比"""
    wind = model.load_wind()
    beta_display = [0.2, 0.4, 0.6, 0.8]
    price_beta_display = {}
    for beta in beta_display:
        for r in scan_results:
            if abs(r['beta'] - beta) < 1e-6:
                price_beta_display[beta] = r['price']
                break
    
    fig, ax1 = plt.subplots(figsize=(14,6))
    ax1.plot(x, price_fixed, label='Fixed price', linewidth=2, color='blue')
    ax1.plot(x, price_tou, label='ToU price', linewidth=2, color='orange')
    for beta in beta_display:
        if beta in price_beta_display:
            ax1.plot(x, price_beta_display[beta], label=f'β={beta}', linewidth=1.5, alpha=0.8)
    ax1.plot(x, best_price_ls, label=f'Local search (from β={start_beta})', linewidth=2.5, color='red', linestyle='--')
    ax1.set_xlabel('Hour of day')
    ax1.set_ylabel('Price (yuan/MWh)', color='black')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(x, wind, label='Wind power (MW)', linewidth=2, color='purple', linestyle=':')
    ax2.set_ylabel('Wind power (MW)', color='purple')
    ax2.legend(loc='upper right')
    plt.title('Electricity price curves with local search optimal (alpha=3.0)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'fig_17_extra_price_local_search.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("fig_17_extra_price_local_search.png 已保存")

def plot_fig18_extra_price_response_local_search(scan_results, p_ch_fixed, p_ch_tou, best_p_ch_ls, start_beta):
    """fig_18_extra_price_response_local_search.png: 局部搜索充电曲线对比（图例合并到右上角）"""
    wind = model.load_wind()
    
    fig, ax1 = plt.subplots(figsize=(14,6))
    # 左轴：充电功率
    ax1.plot(x, p_ch_fixed, label='Fixed price', linewidth=2, color='blue')
    ax1.plot(x, p_ch_tou, label='ToU price', linewidth=2, color='orange')
    cmap = plt.cm.viridis
    colors = cmap(np.linspace(0, 1, len(scan_results)))
    for r, color in zip(scan_results, colors):
        ax1.plot(x, r['p_ch'], color=color, alpha=0.5, linewidth=0.8)
    ax1.plot(x, best_p_ch_ls, label=f'Local search (from β={start_beta})', linewidth=3, color='red', linestyle='--')
    ax1.set_xlabel('Hour of day')
    ax1.set_ylabel('Charging power (MW)', color='black')
    ax1.grid(True, alpha=0.3)
    
    # 右轴：风电
    ax2 = ax1.twinx()
    ax2.plot(x, wind, label='Wind power (MW)', linewidth=2, color='purple', linestyle=':')
    ax2.set_ylabel('Wind power (MW)', color='purple')
    
    # 合并图例到右上角
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.title('EV charging power under different β with local search optimal (alpha=3.0)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'fig_18_extra_price_response_local_search.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("fig_18_extra_price_response_local_search.png 已保存")

def plot_fig19_charging_comparison(scan_results, best_p_ch_ls, start_beta):
    """fig_19_charging_comparison.png: 不同准则充电方案对比（图例合并到右上角）"""
    wind = model.load_wind()
    metrics_list = [r['metrics'] for r in scan_results]
    
    idx_corr = np.argmax([m['wind_corr'] for m in metrics_list])
    corr_p_ch = scan_results[idx_corr]['p_ch']
    corr_beta = scan_results[idx_corr]['beta']
    corr_value = metrics_list[idx_corr]['wind_corr']
    
    idx_w = np.argmax([m['weighted_wind_mw'] for m in metrics_list])
    w_p_ch = scan_results[idx_w]['p_ch']
    w_beta = scan_results[idx_w]['beta']
    w_value = metrics_list[idx_w]['weighted_wind_mw']
    
    weighted_vals = np.array([m['weighted_wind_mw'] for m in metrics_list])
    elec_vals = np.array([m['elec_cost_kyuan'] for m in metrics_list])
    w_norm = (weighted_vals - weighted_vals.min()) / (weighted_vals.max() - weighted_vals.min())
    c_norm = (elec_vals.max() - elec_vals) / (elec_vals.max() - elec_vals.min())
    composite = 0.6 * w_norm + 0.4 * c_norm
    idx_comp = np.argmax(composite)
    comp_p_ch = scan_results[idx_comp]['p_ch']
    comp_beta = scan_results[idx_comp]['beta']
    comp_score = composite[idx_comp]
    
    fig, ax1 = plt.subplots(figsize=(14,6))
    # 左轴：充电功率
    ax1.plot(x, corr_p_ch, label=f'Max correlation (β={corr_beta:.2f}, ρ={corr_value:.3f})', 
             linewidth=2, color='blue', linestyle='--')
    ax1.plot(x, w_p_ch, label=f'Max weighted wind (β={w_beta:.2f}, W={w_value:.1f} MW)', 
             linewidth=2, color='green', linestyle=':')
    ax1.plot(x, comp_p_ch, label=f'Composite score (β={comp_beta:.2f}, S={comp_score:.3f})', 
             linewidth=2, color='orange', linestyle='-.')
    ax1.plot(x, best_p_ch_ls, label=f'Local search (from β={start_beta})', 
             linewidth=2.5, color='red', linestyle='-')
    ax1.set_xlabel('Hour of day')
    ax1.set_ylabel('Charging power (MW)', color='black')
    ax1.grid(True, alpha=0.3)
    
    # 右轴：风电
    ax2 = ax1.twinx()
    ax2.plot(x, wind, label='Wind power (MW)', linewidth=2, color='purple', linestyle=':')
    ax2.set_ylabel('Wind power (MW)', color='purple')
    
    # 合并图例到右上角
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.title('Comparison of optimal charging strategies under different criteria (alpha=3.0)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'fig_19_charging_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("fig_19_charging_comparison.png 已保存")

# ========== 主函数 ==========
def save_csv_and_plot():
    res = model.main()
    
    price_fixed, p_ch_fixed, m_fixed = res['fixed']
    price_tou, p_ch_tou, m_tou = res['tou']
    scan_results = res['scan_alpha3.0']
    best_price_ls, best_p_ch_ls, best_metrics_ls, start_beta, ls_history = res['local_search']
    
    # 推荐新电价
    feasible = [r for r in scan_results if r['metrics']['elec_cost_kyuan'] >= 0]
    if feasible:
        best_rec = max(feasible, key=lambda x: x['metrics']['weighted_wind_mw'])
        rec_p_ch = best_rec['p_ch']
        rec_price = best_rec['price']
    else:
        best_rec = max(scan_results, key=lambda x: x['metrics']['weighted_wind_mw'])
        rec_p_ch = best_rec['p_ch']
        rec_price = best_rec['price']
    
    # 写入CSV
    pd.DataFrame({'time_slot': range(96), 'price_yuan_per_mwh': price_fixed}).to_csv(PRICE_DIR / "price_fixed.csv", index=False)
    pd.DataFrame({'time_slot': range(96), 'p_ch_mw': p_ch_fixed}).to_csv(PRICE_DIR / "price_response_fixed.csv", index=False)
    pd.DataFrame({'time_slot': range(96), 'price_yuan_per_mwh': price_tou}).to_csv(PRICE_DIR / "price_tou.csv", index=False)
    pd.DataFrame({'time_slot': range(96), 'p_ch_mw': p_ch_tou}).to_csv(PRICE_DIR / "price_response_tou.csv", index=False)
    pd.DataFrame({'time_slot': range(96), 'price_yuan_per_mwh': rec_price}).to_csv(PRICE_DIR / "price_wind_guided.csv", index=False)
    pd.DataFrame({'time_slot': range(96), 'p_ch_mw': rec_p_ch}).to_csv(PRICE_DIR / "price_response_wind_guided.csv", index=False)
    pd.DataFrame({'time_slot': range(96), 'price_yuan_per_mwh': best_price_ls}).to_csv(PRICE_DIR / "price_local_search.csv", index=False)
    pd.DataFrame({'time_slot': range(96), 'p_ch_mw': best_p_ch_ls}).to_csv(PRICE_DIR / "price_response_local_search.csv", index=False)
    print("已写入 CSV 文件到 results/price/")
    
    # 生成所有图表
    plot_fig12_price_curves(scan_results, price_fixed, price_tou)
    plot_fig13_price_response(scan_results, p_ch_fixed, p_ch_tou)
    plot_fig14_wind_charging_matching(rec_p_ch)
    
    alpha_scan_results = res.get('alpha_scan', [])
    if alpha_scan_results:
        plot_fig15_alpha_comparison(alpha_scan_results)
    else:
        print("警告：未找到 alpha 扫描数据")
    
    plot_fig16_3d(scan_results)
    plot_fig17_extra_price_local_search(scan_results, price_fixed, price_tou, best_price_ls, start_beta)
    plot_fig18_extra_price_response_local_search(scan_results, p_ch_fixed, p_ch_tou, best_p_ch_ls, start_beta)
    plot_fig19_charging_comparison(scan_results, best_p_ch_ls, start_beta)
    
    print("所有图表已保存到 results/figures/")

if __name__ == "__main__":
    save_csv_and_plot()