"""
02_gear_segmentation.py
Savonius BIWT 风力发电实验 — 挡位分割 & 统计
功能：自动检测风力启动点，按30s分割三挡，计算各挡稳定相的平均电压/电流/功率，以及爬坡响应时间

用法：
    python 02_gear_segmentation.py --input_dir ./cleaned --output gear_stats.csv

参数可调：
    --voltage_thresh    启动检测电压阈值（默认1.0V）
    --gear_duration     每挡持续时间（默认30s）
    --ramp_skip         每挡开头跳过的爬坡时间（默认5s）
    --tail_skip         每挡末尾跳过的时间（默认2s）
    --ramp_target       爬坡响应判定比例（默认0.8，即达到稳态80%）
"""

import os
import argparse
import pandas as pd
import numpy as np


def detect_start(df: pd.DataFrame, voltage_thresh: float = 1.0, window: int = 50) -> float:
    """
    检测风力启动时间点：
    用滚动平均电压首次超过阈值的时刻
    """
    v_smooth = df['voltage_V'].rolling(window, center=True, min_periods=1).mean()
    mask = v_smooth > voltage_thresh
    if mask.any():
        return df.loc[mask.idxmax(), 't_relative']
    return 0.0


def segment_gears(df: pd.DataFrame, t_start: float,
                  gear_duration: float = 30.0, n_gears: int = 3,
                  ramp_skip: float = 5.0, tail_skip: float = 2.0) -> dict:
    """
    按挡位分割数据，返回每挡的统计信息
    
    返回结构：
    {
        'start': float,
        'G1': { 'full': (t0, t1), 'stable': (t0+ramp, t1-tail), 'V': float, 'A': float, 'W': float },
        'G2': { ... },
        'G3': { ... },
    }
    """
    result = {'start': t_start}

    for g in range(1, n_gears + 1):
        t0 = t_start + (g - 1) * gear_duration
        t1 = t_start + g * gear_duration
        t_stable_start = t0 + ramp_skip
        t_stable_end = t1 - tail_skip

        # 全挡数据
        mask_full = (df['t_relative'] >= t0) & (df['t_relative'] < t1)
        # 稳定相数据（去除爬坡和尾部）
        mask_stable = (df['t_relative'] >= t_stable_start) & (df['t_relative'] < t_stable_end)

        sub_stable = df[mask_stable]

        gear_info = {
            'full_range': (t0, t1),
            'stable_range': (t_stable_start, t_stable_end),
            'n_samples': len(sub_stable),
        }

        if len(sub_stable) > 10:
            gear_info['V_mean'] = sub_stable['voltage_V'].mean()
            gear_info['A_mean'] = sub_stable['current_A'].mean()
            gear_info['W_mean'] = sub_stable['power_W'].mean()
            gear_info['V_std'] = sub_stable['voltage_V'].std()
            gear_info['A_std'] = sub_stable['current_A'].std()
            gear_info['W_std'] = sub_stable['power_W'].std()
        else:
            for k in ['V_mean', 'A_mean', 'W_mean', 'V_std', 'A_std', 'W_std']:
                gear_info[k] = np.nan

        result[f'G{g}'] = gear_info

    return result


def compute_ramp_time(df: pd.DataFrame, t_transition: float,
                      stable_power: float, target_ratio: float = 0.8,
                      max_window: float = 15.0, smooth_window: int = 30) -> float:
    """
    计算爬坡响应时间：从挡位切换时刻到功率达到稳态 target_ratio 比例所需的时间
    """
    if stable_power <= 0.0001 or np.isnan(stable_power):
        return np.nan

    target = stable_power * target_ratio
    mask = (df['t_relative'] >= t_transition) & (df['t_relative'] < t_transition + max_window)
    sub = df[mask].copy()

    if len(sub) < smooth_window:
        return np.nan

    sub['p_smooth'] = sub['power_W'].rolling(smooth_window, center=True, min_periods=1).mean()
    reached = sub[sub['p_smooth'] >= target]

    if len(reached) > 0:
        return reached.iloc[0]['t_relative'] - t_transition
    return float('inf')


def analyze_model(df: pd.DataFrame, model_id: int,
                  voltage_thresh: float = 1.0,
                  gear_duration: float = 30.0,
                  ramp_skip: float = 5.0,
                  tail_skip: float = 2.0,
                  ramp_target: float = 0.8) -> dict:
    """完整分析单个模型：启动检测 → 挡位分割 → 爬坡响应"""

    t_start = detect_start(df, voltage_thresh)
    gears = segment_gears(df, t_start, gear_duration, ramp_skip=ramp_skip, tail_skip=tail_skip)

    row = {
        'model': model_id,
        'start_s': t_start,
    }

    for g in range(1, 4):
        gi = gears[f'G{g}']
        row[f'G{g}_V'] = gi['V_mean']
        row[f'G{g}_A_mA'] = gi['A_mean'] * 1000 if not np.isnan(gi['A_mean']) else np.nan
        row[f'G{g}_W_mW'] = gi['W_mean'] * 1000 if not np.isnan(gi['W_mean']) else np.nan

        # 爬坡时间
        t_trans = t_start + (g - 1) * gear_duration
        ramp_t = compute_ramp_time(df, t_trans, gi['W_mean'], ramp_target)
        row[f'ramp_G{g}_s'] = ramp_t

    # 三挡平均功率
    powers = [row.get(f'G{g}_W_mW', np.nan) for g in range(1, 4)]
    row['avg_power_mW'] = np.nanmean(powers)

    return row


def main():
    parser = argparse.ArgumentParser(description='Savonius BIWT 挡位分割与统计')
    parser.add_argument('--input_dir', default='./cleaned', help='清洗后CSV目录')
    parser.add_argument('--output', default='./gear_stats.csv', help='输出统计CSV路径')
    parser.add_argument('--models', default='0,1,2,3,4,5,6,7,8', help='模型编号')
    parser.add_argument('--voltage_thresh', type=float, default=1.0, help='启动检测电压阈值(V)')
    parser.add_argument('--gear_duration', type=float, default=30.0, help='每挡持续时间(s)')
    parser.add_argument('--ramp_skip', type=float, default=5.0, help='每挡跳过的爬坡时间(s)')
    parser.add_argument('--tail_skip', type=float, default=2.0, help='每挡跳过的尾部时间(s)')
    parser.add_argument('--ramp_target', type=float, default=0.8, help='爬坡判定比例')
    args = parser.parse_args()

    model_ids = [int(x) for x in args.models.split(',')]

    print(f"参数: voltage_thresh={args.voltage_thresh}V, gear_duration={args.gear_duration}s, "
          f"ramp_skip={args.ramp_skip}s, tail_skip={args.tail_skip}s, ramp_target={args.ramp_target}")
    print("-" * 80)

    rows = []
    for mid in model_ids:
        filepath = os.path.join(args.input_dir, f'cleaned_{mid}.csv')
        df = pd.read_csv(filepath)
        row = analyze_model(df, mid,
                            voltage_thresh=args.voltage_thresh,
                            gear_duration=args.gear_duration,
                            ramp_skip=args.ramp_skip,
                            tail_skip=args.tail_skip,
                            ramp_target=args.ramp_target)
        rows.append(row)

        print(f"  Model {mid}: start={row['start_s']:.1f}s | "
              f"G1={row['G1_W_mW']:.2f}mW  G2={row['G2_W_mW']:.2f}mW  G3={row['G3_W_mW']:.2f}mW | "
              f"Ramp: {row['ramp_G1_s']:.2f}s / {row['ramp_G2_s']:.2f}s / {row['ramp_G3_s']:.2f}s")

    result_df = pd.DataFrame(rows)
    result_df = result_df.sort_values('avg_power_mW', ascending=False).reset_index(drop=True)
    result_df.to_csv(args.output, index=False)

    print("-" * 80)
    print("功率排名:")
    for _, r in result_df.iterrows():
        print(f"  Model {int(r['model'])}: {r['avg_power_mW']:.2f} mW")

    print(f"\n输出: {args.output}")


if __name__ == '__main__':
    main()
