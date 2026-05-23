"""
指标计算模块（价格机制拓展专用）
提供电费、不适成本、风电匹配度等计算函数
"""

import numpy as np

def calculate_price_response_metrics(p_ch_mw, price_yuan_per_mwh, discomfort_penalty_per_mwh, dt_h=0.25):
    """
    计算价格响应场景下的经济指标
    
    参数:
        p_ch_mw: 96时段充电功率 (MW)
        price_yuan_per_mwh: 96时段电价 (元/MWh)
        discomfort_penalty_per_mwh: 96时段不适成本系数 (元/MWh)
        dt_h: 时段时长 (小时), 默认0.25
    
    返回:
        dict: 包含总能量(MWh)、电费(千元)、不适成本(千元)、总成本(千元)、平均电价(元/MWh)
    """
    energy_mwh = p_ch_mw * dt_h
    total_energy = np.sum(energy_mwh)
    electricity_cost = np.sum(p_ch_mw * price_yuan_per_mwh * dt_h) / 1000   # 千元
    discomfort_cost = np.sum(p_ch_mw * discomfort_penalty_per_mwh * dt_h) / 1000
    total_cost = electricity_cost + discomfort_cost
    avg_price = (electricity_cost * 1000) / total_energy if total_energy > 0 else 0
    
    return {
        'total_energy_mwh': total_energy,
        'electricity_cost_k_yuan': electricity_cost,
        'discomfort_cost_k_yuan': discomfort_cost,
        'total_cost_k_yuan': total_cost,
        'avg_price_yuan_per_mwh': avg_price
    }

def calculate_wind_matching(p_ch_mw, wind_mw):
    """
    计算充电功率与风电的匹配度
    
    参数:
        p_ch_mw: 96时段充电功率 (MW)
        wind_mw: 96时段风电功率 (MW)
    
    返回:
        dict: 包含相关系数和加权平均风电
    """
    if np.sum(p_ch_mw) == 0 or np.std(p_ch_mw) == 0 or np.std(wind_mw) == 0:
        return {'correlation': 0.0, 'weighted_wind': 0.0}
    corr = np.corrcoef(p_ch_mw, wind_mw)[0, 1]
    if np.isnan(corr):
        corr = 0.0
    weighted_wind = np.sum(p_ch_mw * wind_mw) / np.sum(p_ch_mw) if np.sum(p_ch_mw) > 0 else 0
    return {'correlation': corr, 'weighted_wind': weighted_wind}

def discomfort_penalty_from_preference(preference_hours, penalty_value=300.0, dt_h=0.25):
    """
    根据偏好时段生成不适成本系数数组
    
    参数:
        preference_hours: 列表，每个元素为 (start_hour, end_hour)，如 [(18, 24), (0, 6)]
        penalty_value: 非偏好时段的单位不适成本 (元/MWh)
        dt_h: 时段时长 (小时)
    
    返回:
        penalty: 96长度数组，单位元/MWh
    """
    n = int(24 / dt_h)
    penalty = np.full(n, penalty_value)
    for start, end in preference_hours:
        start_idx = int(start / dt_h)
        end_idx = int(end / dt_h)
        penalty[start_idx:end_idx] = 0.0
    return penalty