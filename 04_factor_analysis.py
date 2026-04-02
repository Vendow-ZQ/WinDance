"""
04_factor_analysis.py
Savonius BIWT 风力发电实验 — 2^3 全因子分析
功能：读取挡位统计结果和实验设计表，计算主效应、交互效应，输出因子分析报告

用法：
    python 04_factor_analysis.py --stats gear_stats.csv --experiment Experiment_utf8.csv

输入：
    gear_stats.csv       — 02脚本输出的挡位统计
    Experiment_utf8.csv  — 实验设计参数表（UTF-8编码）
"""

import argparse
import pandas as pd
import numpy as np


# ---- 2^3 全因子编码（Model 1~8，排除 Model 0 基准） ----
FACTOR_CODING = {
    1: {'TR': -1, 'AR': -1, 'TA': -1},  # 低低低
    2: {'TR': -1, 'AR': -1, 'TA':  1},  # 低低高
    3: {'TR': -1, 'AR':  1, 'TA': -1},  # 低高低
    4: {'TR': -1, 'AR':  1, 'TA':  1},  # 低高高
    5: {'TR':  1, 'AR': -1, 'TA': -1},  # 高低低
    6: {'TR':  1, 'AR':  1, 'TA': -1},  # 高高低
    7: {'TR':  1, 'AR': -1, 'TA':  1},  # 高低高
    8: {'TR':  1, 'AR':  1, 'TA':  1},  # 高高高
}

FACTOR_NAMES = {
    'TR': '收分率 (Taper Ratio)',
    'AR': '展径比 (Aspect Ratio)',
    'TA': '扭转角 (Twist Angle)',
}


def compute_main_effects(power_dict: dict) -> dict:
    """计算三个因子的主效应"""
    effects = {}
    for factor in ['TR', 'AR', 'TA']:
        high = [power_dict[i] for i in range(1, 9) if FACTOR_CODING[i][factor] == 1]
        low = [power_dict[i] for i in range(1, 9) if FACTOR_CODING[i][factor] == -1]
        effects[factor] = {
            'high_mean': np.mean(high),
            'low_mean': np.mean(low),
            'effect': np.mean(high) - np.mean(low),
            'high_models': [i for i in range(1, 9) if FACTOR_CODING[i][factor] == 1],
            'low_models': [i for i in range(1, 9) if FACTOR_CODING[i][factor] == -1],
        }
    return effects


def compute_two_way_interactions(power_dict: dict) -> dict:
    """计算两因子交互效应"""
    interactions = {}
    for f1, f2 in [('TR', 'AR'), ('TR', 'TA'), ('AR', 'TA')]:
        pp = np.mean([power_dict[i] for i in range(1, 9)
                       if FACTOR_CODING[i][f1] == 1 and FACTOR_CODING[i][f2] == 1])
        pm = np.mean([power_dict[i] for i in range(1, 9)
                       if FACTOR_CODING[i][f1] == 1 and FACTOR_CODING[i][f2] == -1])
        mp = np.mean([power_dict[i] for i in range(1, 9)
                       if FACTOR_CODING[i][f1] == -1 and FACTOR_CODING[i][f2] == 1])
        mm = np.mean([power_dict[i] for i in range(1, 9)
                       if FACTOR_CODING[i][f1] == -1 and FACTOR_CODING[i][f2] == -1])
        interactions[f'{f1}×{f2}'] = {
            '(+,+)': pp, '(+,-)': pm, '(-,+)': mp, '(-,-)': mm,
            'effect': (pp - pm - mp + mm) / 2,
        }
    return interactions


def compute_three_way_interaction(power_dict: dict) -> float:
    """计算三因子交互效应"""
    vals = []
    for i in range(1, 9):
        sign = FACTOR_CODING[i]['TR'] * FACTOR_CODING[i]['AR'] * FACTOR_CODING[i]['TA']
        vals.append(sign * power_dict[i])
    return np.mean(vals)


def main():
    parser = argparse.ArgumentParser(description='Savonius BIWT 全因子分析')
    parser.add_argument('--stats', default='./gear_stats.csv', help='挡位统计CSV')
    parser.add_argument('--experiment', default='./Experiment_utf8.csv', help='实验设计表')
    parser.add_argument('--response', default='avg_power_mW', help='响应变量列名')
    args = parser.parse_args()

    stats = pd.read_csv(args.stats)
    power_dict = dict(zip(stats['model'].astype(int), stats[args.response]))

    print("=" * 70)
    print(f"响应变量: {args.response}")
    print("=" * 70)
    for i in sorted(power_dict.keys()):
        print(f"  Model {i}: {power_dict[i]:.2f}")

    # ---- 主效应 ----
    print("\n" + "=" * 70)
    print("主效应 (Main Effects)")
    print("=" * 70)
    main_effects = compute_main_effects(power_dict)
    for factor, info in main_effects.items():
        name = FACTOR_NAMES[factor]
        print(f"\n  {factor} — {name}:")
        print(f"    高水平 (+1): {info['high_mean']:.2f}  (Models {info['high_models']})")
        print(f"    低水平 (-1): {info['low_mean']:.2f}  (Models {info['low_models']})")
        print(f"    效应 = {info['effect']:+.2f}")
        magnitude = abs(info['effect'])
        if magnitude > 100:
            print(f"    → 主导因子 (DOMINANT)")
        elif magnitude > 20:
            print(f"    → 显著 (Significant)")
        elif magnitude > 5:
            print(f"    → 弱效应 (Weak)")
        else:
            print(f"    → 可忽略 (Negligible)")

    # ---- 两因子交互 ----
    print("\n" + "=" * 70)
    print("两因子交互效应 (Two-Way Interactions)")
    print("=" * 70)
    interactions = compute_two_way_interactions(power_dict)
    for name, info in interactions.items():
        print(f"\n  {name}:")
        print(f"    (+,+)={info['(+,+)']:.1f}  (+,-)={info['(+,-)']:.1f}  "
              f"(-,+)={info['(-,+)']:.1f}  (-,-)={info['(-,-)']:.1f}")
        print(f"    交互效应 = {info['effect']:+.2f}")

    # ---- 三因子交互 ----
    three_way = compute_three_way_interaction(power_dict)
    print(f"\n  TR × AR × TA = {three_way:+.2f}")

    # ---- 效应排名 ----
    print("\n" + "=" * 70)
    print("效应绝对值排名")
    print("=" * 70)
    all_effects = {}
    for f, info in main_effects.items():
        all_effects[f] = abs(info['effect'])
    for name, info in interactions.items():
        all_effects[name] = abs(info['effect'])
    all_effects['TR×AR×TA'] = abs(three_way)

    for rank, (name, val) in enumerate(sorted(all_effects.items(), key=lambda x: x[1], reverse=True), 1):
        bar = '█' * int(val / 5)
        print(f"  #{rank} {name:>10}: {val:>8.2f} {bar}")


if __name__ == '__main__':
    main()
