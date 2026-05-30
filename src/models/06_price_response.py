"""
价格机制拓展模块（独立于主任务）
- 纯计算模块，不写入任何文件
- 提供价格函数和求解器
- 主函数执行参数扫描并返回结果
- 支持不同的不适成本系数 alpha
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import minimize
from tqdm import tqdm

# ========== 固定参数（任务书） ==========
NUM_EV = 4012
BATTERY_CAP_kWh = 50.0
SOC_REQUIREMENT = 0.4
TOTAL_ENERGY_MWh = NUM_EV * BATTERY_CAP_kWh * SOC_REQUIREMENT / 1000.0   # 80.24 MWh
MAX_POWER_MW = 17.0
DT_H = 0.25
N_TIME = 96

# ========== 路径（仅用于读取输入数据） ==========
PROJ_ROOT = Path(__file__).parents[2]
DATA_DIR = PROJ_ROOT / "data/processed"

# ========== 辅助函数：读取数据 ==========
def load_tou_price():
    path = DATA_DIR / "tou_price_96.csv"
    df = pd.read_csv(path)
    return df['price_cny_per_kwh'].values * 1000.0

def load_wind():
    path = DATA_DIR / "load_wind_96_for_price.csv"
    df = pd.read_csv(path)
    return df['wind_forecast_mw'].values

# ========== 电价生成函数 ==========
def fixed_price():
    return np.full(N_TIME, 500.0)

def tou_price():
    return load_tou_price()

def tou_wind_price(beta):
    price_tou = load_tou_price()
    wind = load_wind()
    avg_wind = np.mean(wind)
    epsilon = 1e-3
    factor = 1 + beta * (avg_wind - wind) / (avg_wind + epsilon)
    return np.clip(price_tou * factor, 0.0, None)

# ========== 参考曲线 ==========
def reference_charging_profile():
    constant_power = TOTAL_ENERGY_MWh / (N_TIME * DT_H)
    return np.full(N_TIME, constant_power)

# ========== 不适成本 ==========
def discomfort_cost(p_ch, p_ref, alpha):
    return alpha * np.sum((p_ch - p_ref) ** 2 * DT_H)

# ========== 充电优化求解器 ==========
def solve_charging(price, alpha=0.3):
    p_ref = reference_charging_profile()
    n = len(price)
    dt = DT_H

    def objective(p):
        p_arr = np.array(p)
        electricity = np.sum(price * p_arr * dt)
        discomfort = alpha * np.sum((p_arr - p_ref) ** 2 * dt)
        return electricity + discomfort

    constraints = [{'type': 'eq', 'fun': lambda p: np.sum(p * dt) - TOTAL_ENERGY_MWh}]
    bounds = [(0, MAX_POWER_MW) for _ in range(n)]
    p0 = np.full(n, TOTAL_ENERGY_MWh / (n * dt))
    p0 = np.clip(p0, 0, MAX_POWER_MW)

    res = minimize(objective, p0, method='SLSQP', bounds=bounds, constraints=constraints,
                   options={'maxiter': 2000, 'ftol': 1e-6, 'disp': False})
    return res.x

# ========== 计算指标 ==========
def compute_metrics(price, p_ch, alpha=0.3):
    p_ref = reference_charging_profile()
    dt = DT_H
    total_energy = np.sum(p_ch * dt)
    elec_cost = np.sum(p_ch * price * dt) / 1000
    discomfort = discomfort_cost(p_ch, p_ref, alpha) / 1000
    total_cost = elec_cost + discomfort
    wind = load_wind()
    if np.std(p_ch) > 0 and np.std(wind) > 0:
        corr = np.corrcoef(p_ch, wind)[0, 1]
    else:
        corr = np.nan
    if total_energy > 0:
        weighted_wind = np.sum(p_ch * wind * dt) / total_energy
    else:
        weighted_wind = np.nan
    return {
        'total_energy_mwh': total_energy,
        'elec_cost_kyuan': elec_cost,
        'discomfort_kyuan': discomfort,
        'total_cost_kyuan': total_cost,
        'wind_corr': corr,
        'weighted_wind_mw': weighted_wind
    }

# ========== 扫描β ==========
def scan_beta(beta_list, alpha=0.3, verbose=True):
    results = []
    for beta in beta_list:
        price = tou_wind_price(beta)
        p_ch = solve_charging(price, alpha)
        metrics = compute_metrics(price, p_ch, alpha)
        results.append({
            'beta': beta,
            'p_ch': p_ch,
            'price': price,
            'metrics': metrics
        })
        if verbose:
            print(f"beta={beta:.2f}: 匹配度={metrics['wind_corr']:.3f}, 加权风电={metrics['weighted_wind_mw']:.1f} MW, "
                  f"电费={metrics['elec_cost_kyuan']:.2f} kYuan, 不适={metrics['discomfort_kyuan']:.2f} kYuan")
    return results

# ========== 局部搜索 ==========
def local_search_from_beta(beta_start, lambda_cost=0.1, alpha=0.3, n_iter=1500, step_init=20.0, anneal=0.995, price_clip=(0, 2000), seed=2026):
    init_price = tou_wind_price(beta_start)
    current_price = init_price.copy()
    rng = np.random.default_rng(seed)
    
    def objective(price):
        p_ch = solve_charging(price, alpha)
        m = compute_metrics(price, p_ch, alpha)
        return m['weighted_wind_mw'] - lambda_cost * m['elec_cost_kyuan']
    
    current_obj = objective(current_price)
    best_price = current_price.copy()
    best_obj = current_obj
    step = step_init
    history = []
    
    for i in tqdm(range(n_iter), desc="Local search"):
        candidate = current_price + rng.normal(0, step, size=N_TIME)
        candidate = np.clip(candidate, price_clip[0], price_clip[1])
        cand_obj = objective(candidate)
        history.append(cand_obj)
        if cand_obj > current_obj:
            current_price = candidate
            current_obj = cand_obj
        if cand_obj > best_obj:
            best_price = candidate.copy()
            best_obj = cand_obj
        step *= anneal
    
    p_ch_best = solve_charging(best_price, alpha)
    metrics_best = compute_metrics(best_price, p_ch_best, alpha)
    return best_price, p_ch_best, metrics_best, history

# ========== 主函数 ==========
def main():
    print("===== 价格机制拓展模型 =====")
    print(f"总充电需求: {TOTAL_ENERGY_MWh:.2f} MWh, 最大功率: {MAX_POWER_MW} MW\n")
    
    # 固定电价（使用主体 alpha=3.0）
    price_fixed = fixed_price()
    p_ch_fixed = solve_charging(price_fixed, alpha=3.0)
    m_fixed = compute_metrics(price_fixed, p_ch_fixed, alpha=3.0)
    print("固定电价 (alpha=3.0):")
    print(f"  电量={m_fixed['total_energy_mwh']:.2f} MWh, 电费={m_fixed['elec_cost_kyuan']:.2f} kYuan, "
          f"不适={m_fixed['discomfort_kyuan']:.2f} kYuan, 匹配度={m_fixed['wind_corr']:.3f}, 加权风电={m_fixed['weighted_wind_mw']:.1f} MW\n")
    
    # 分时电价（使用主体 alpha=3.0）
    price_tou = tou_price()
    p_ch_tou = solve_charging(price_tou, alpha=3.0)
    m_tou = compute_metrics(price_tou, p_ch_tou, alpha=3.0)
    print("分时电价 (alpha=3.0):")
    print(f"  电量={m_tou['total_energy_mwh']:.2f} MWh, 电费={m_tou['elec_cost_kyuan']:.2f} kYuan, "
          f"不适={m_tou['discomfort_kyuan']:.2f} kYuan, 匹配度={m_tou['wind_corr']:.3f}, 加权风电={m_tou['weighted_wind_mw']:.1f} MW\n")
    
    # 扫描β（主体 alpha=3.0，补充 alpha=0.3）
    beta_list = [0.0, 0.08, 0.16, 0.2, 0.24, 0.32, 0.4, 0.48, 0.56, 0.6, 0.64, 0.72, 0.8]
    print("--- 新电价扫描 (alpha=3.0，主体) ---")
    scan_results_30 = scan_beta(beta_list, alpha=3.0)
    
    print("\n--- 新电价扫描 (alpha=0.3，补充对比) ---")
    scan_results_03 = scan_beta(beta_list, alpha=0.3)
    
    # 局部搜索（使用主体 alpha=3.0）
    start_beta = 0.8
    print(f"\n--- 局部搜索 (alpha=3.0，从 β={start_beta} 出发) ---")
    best_price_ls, best_p_ch_ls, best_metrics_ls, ls_history = local_search_from_beta(start_beta, lambda_cost=0.1, alpha=3.0, n_iter=60)
    print(f"局部搜索最优结果:")
    print(f"  加权风电={best_metrics_ls['weighted_wind_mw']:.1f} MW, 电费={best_metrics_ls['elec_cost_kyuan']:.2f} kYuan, "
          f"匹配度={best_metrics_ls['wind_corr']:.3f}, 不适={best_metrics_ls['discomfort_kyuan']:.2f} kYuan")
    
    # 添加 alpha 扫描（固定 β=0.4）
    alpha_list = [0.3, 0.8, 1.5, 2.0, 2.5, 3.0]
    print("\n--- Alpha 扫描 (固定 β=0.4) ---")
    alpha_scan_results = scan_alpha(alpha_list, beta_fixed=0.4)

    return {
        'fixed': (price_fixed, p_ch_fixed, m_fixed),
        'tou': (price_tou, p_ch_tou, m_tou),
        'scan_alpha3.0': scan_results_30,   # 主体
        'scan_alpha0.3': scan_results_03,   # 补充
        'local_search': (best_price_ls, best_p_ch_ls, best_metrics_ls, start_beta, ls_history),
        'alpha_scan': alpha_scan_results
    }
 

def scan_alpha(alpha_list, beta_fixed=0.4, verbose=True):
    """扫描不同alpha对充电曲线的影响（固定β）"""
    results = []
    price = tou_wind_price(beta_fixed)
    for alpha in alpha_list:
        p_ch = solve_charging(price, alpha)
        metrics = compute_metrics(price, p_ch, alpha)
        results.append({
            'alpha': alpha,
            'p_ch': p_ch,
            'metrics': metrics
        })
        if verbose:
            print(f"alpha={alpha:.1f}: 加权风电={metrics['weighted_wind_mw']:.1f} MW, "
                  f"电费={metrics['elec_cost_kyuan']:.2f} kYuan, 不适={metrics['discomfort_kyuan']:.2f} kYuan")
    return results

if __name__ == "__main__":
    main()
