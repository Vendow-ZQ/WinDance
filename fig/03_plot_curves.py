"""
03_plot_curves.py
Savonius BIWT 风力发电实验 — 绘制对齐折线图
功能：读取清洗后的数据，对齐启动时间，绘制电压/电流/功率三张折线图（0-90s）

用法：
    python 03_plot_curves.py --input_dir ./cleaned --output_dir ./figures
    
参数可调：
    --voltage_thresh    启动检测阈值（与02脚本一致）
    --smooth_size       绘图平滑窗口
    --dpi               输出分辨率
    --format            输出格式（png/svg/pdf）
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d


# ---- 颜色方案（色盲友好，9个模型） ----
COLORS = [
    '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
    '#a65628', '#f781bf', '#999999', '#66c2a5'
]

MODEL_LABELS = [
    '0 (Baseline)',
    '1 (TR↓ AR↓ TA↓)',
    '2 (TR↓ AR↓ TA↑)',
    '3 (TR↓ AR↑ TA↓)',
    '4 (TR↓ AR↑ TA↑)',
    '5 (TR↑ AR↓ TA↓)',
    '6 (TR↑ AR↑ TA↓)',
    '7 (TR↑ AR↓ TA↑)',
    '8 (TR↑ AR↑ TA↑)',
]


def detect_start(df: pd.DataFrame, voltage_thresh: float = 1.0, window: int = 50) -> float:
    """与02脚本一致的启动检测"""
    v_smooth = df['voltage_V'].rolling(window, center=True, min_periods=1).mean()
    mask = v_smooth > voltage_thresh
    if mask.any():
        return df.loc[mask.idxmax(), 't_relative']
    return 0.0


def interpolate_aligned(df: pd.DataFrame, t_start: float,
                        total_duration: float = 90.0,
                        dt: float = 0.1,
                        smooth_size: int = 20) -> dict:
    """
    将数据对齐到 t_start，插值到均匀时间网格，平滑处理
    返回: { 't': array, 'V': array, 'A_mA': array, 'P_mW': array }
    """
    t_grid = np.arange(0, total_duration + dt, dt)
    t_aligned = df['t_relative'].values - t_start

    # 只取有效范围
    mask = (t_aligned >= -1) & (t_aligned <= total_duration + 1)
    t_sub = t_aligned[mask]

    v = np.interp(t_grid, t_sub, df['voltage_V'].values[mask])
    a = np.interp(t_grid, t_sub, df['current_A'].values[mask])
    p = np.interp(t_grid, t_sub, df['power_W'].values[mask])

    return {
        't': t_grid,
        'V': uniform_filter1d(v, size=smooth_size),
        'A_mA': uniform_filter1d(a, size=smooth_size) * 1000,
        'P_mW': uniform_filter1d(p, size=smooth_size) * 1000,
    }


def plot_single_metric(ax, t_grid, data_dict, metric_key, ylabel, title,
                       gear_duration=30.0, n_gears=3):
    """在给定ax上绘制一个指标的所有模型曲线"""
    for i in sorted(data_dict.keys()):
        ax.plot(t_grid, data_dict[i][metric_key],
                color=COLORS[i], label=MODEL_LABELS[i],
                linewidth=1.3, alpha=0.9)

    # 挡位分界线
    for g in range(1, n_gears):
        ax.axvline(g * gear_duration, color='#555', ls='--', lw=1, alpha=0.5)

    # 挡位标签
    ylim = ax.get_ylim()
    for g in range(n_gears):
        cx = (g + 0.5) * gear_duration
        ax.text(cx, ylim[0] + (ylim[1] - ylim[0]) * 0.03,
                f'Gear {g + 1}', ha='center', fontsize=11, color='#777', fontweight='bold')

    ax.set_xlim(0, n_gears * gear_duration)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=9)
    ax.grid(True, alpha=0.3)


def main():
    parser = argparse.ArgumentParser(description='Savonius BIWT 折线图绘制')
    parser.add_argument('--input_dir', default='./cleaned', help='清洗后CSV目录')
    parser.add_argument('--output_dir', default='./figures', help='图表输出目录')
    parser.add_argument('--models', default='0,1,2,3,4,5,6,7,8', help='模型编号')
    parser.add_argument('--voltage_thresh', type=float, default=1.0, help='启动检测阈值(V)')
    parser.add_argument('--smooth_size', type=int, default=20, help='绘图平滑窗口')
    parser.add_argument('--gear_duration', type=float, default=30.0, help='每挡时长(s)')
    parser.add_argument('--dpi', type=int, default=150, help='输出DPI')
    parser.add_argument('--format', default='png', choices=['png', 'svg', 'pdf'], help='输出格式')
    args = parser.parse_args()

    model_ids = [int(x) for x in args.models.split(',')]
    os.makedirs(args.output_dir, exist_ok=True)
    total_duration = args.gear_duration * 3

    # ---- 加载数据并对齐 ----
    aligned = {}
    for mid in model_ids:
        filepath = os.path.join(args.input_dir, f'cleaned_{mid}.csv')
        df = pd.read_csv(filepath)
        t_start = detect_start(df, args.voltage_thresh)
        aligned[mid] = interpolate_aligned(df, t_start, total_duration, smooth_size=args.smooth_size)
        print(f"  Model {mid}: start={t_start:.1f}s")

    t_grid = aligned[model_ids[0]]['t']

    # ---- 绘制三张图 ----
    plot_configs = [
        ('V',    'Voltage (V)',  'Voltage vs Time — Savonius BIWT Variants',  'chart_voltage'),
        ('A_mA', 'Current (mA)', 'Current vs Time — Savonius BIWT Variants',  'chart_current'),
        ('P_mW', 'Power (mW)',   'Power vs Time — Savonius BIWT Variants',    'chart_power'),
    ]

    for metric_key, ylabel, title, filename in plot_configs:
        fig, ax = plt.subplots(figsize=(16, 6), dpi=args.dpi)
        plot_single_metric(ax, t_grid, aligned, metric_key, ylabel, title, args.gear_duration)
        ax.set_xlabel('Time since start (s)', fontsize=12)
        plt.tight_layout()

        out_path = os.path.join(args.output_dir, f'{filename}.{args.format}')
        plt.savefig(out_path, dpi=args.dpi, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {out_path}")

    # ---- 额外：三合一图 ----
    fig, axes = plt.subplots(3, 1, figsize=(16, 16), dpi=args.dpi)
    for ax, (metric_key, ylabel, title, _) in zip(axes, plot_configs):
        plot_single_metric(ax, t_grid, aligned, metric_key, ylabel, title, args.gear_duration)
    axes[-1].set_xlabel('Time since start (s)', fontsize=12)
    plt.tight_layout()
    combined_path = os.path.join(args.output_dir, f'chart_combined.{args.format}')
    plt.savefig(combined_path, dpi=args.dpi, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {combined_path}")

    print(f"\n完成！共 {len(plot_configs)+1} 张图输出到 {args.output_dir}/")


if __name__ == '__main__':
    main()
