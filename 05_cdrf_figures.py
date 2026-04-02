"""
05_cdrf_figures.py
Savonius BIWT — CDRF论文配图生成
生成以下图表：
  - fig_bar_power_by_gear.png     分组柱状图：9个模型×3挡功率对比
  - fig_main_effects.png          主效应图：TR / AR / TA
  - fig_interaction_plots.png     交互效应图：TR×AR, TR×TA
  - fig_pareto_effects.png        Pareto图：因子效应绝对值排名
  - fig_timeseries_combined.png   三合一时序图：电压/电流/功率

用法：
    python 05_cdrf_figures.py --stats gear_stats.csv --raw_dir ./raw --output_dir ./figures
"""

import os, argparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d

FACTOR_CODING = {
    1:{'TR':-1,'AR':-1,'TA':-1}, 2:{'TR':-1,'AR':-1,'TA':1},
    3:{'TR':-1,'AR':1,'TA':-1},  4:{'TR':-1,'AR':1,'TA':1},
    5:{'TR':1,'AR':-1,'TA':-1},  6:{'TR':1,'AR':1,'TA':-1},
    7:{'TR':1,'AR':-1,'TA':1},   8:{'TR':1,'AR':1,'TA':1},
}

COLORS = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00',
          '#a65628','#f781bf','#999999','#66c2a5']

FULL_LABELS = [
    'Ctrl\nTR=1.0\nAR=1.0\nTA=0°',
    'V1\nTR=0.5\nAR=0.8\nTA=45°',
    'V2\nTR=0.5\nAR=0.8\nTA=90°',
    'V3\nTR=0.5\nAR=1.4\nTA=45°',
    'V4\nTR=0.5\nAR=1.4\nTA=90°',
    'V5\nTR=1.2\nAR=0.8\nTA=45°',
    'V6\nTR=1.2\nAR=1.4\nTA=45°',
    'V7\nTR=1.2\nAR=0.8\nTA=90°',
    'V8\nTR=1.2\nAR=1.4\nTA=90°',
]


def setup_style():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial','DejaVu Sans'],
        'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 11,
        'xtick.labelsize': 9, 'ytick.labelsize': 9,
        'legend.fontsize': 8, 'figure.dpi': 200,
    })


def load_gear_stats(path):
    """从 02 脚本输出的 gear_stats.csv 读取各挡功率"""
    df = pd.read_csv(path)
    gear_power = {'G1':{}, 'G2':{}, 'G3':{}}
    avg_power = {}
    for _, row in df.iterrows():
        m = int(row['model'])
        gear_power['G1'][m] = row['G1_W_mW']
        gear_power['G2'][m] = row['G2_W_mW']
        gear_power['G3'][m] = row['G3_W_mW']
        avg_power[m] = row['avg_power_mW']
    return gear_power, avg_power


def detect_start(df, thresh=1.0, window=50):
    v_smooth = df['voltage_V'].rolling(window, center=True, min_periods=1).mean()
    mask = v_smooth > thresh
    return df.loc[mask.idxmax(), 't'] if mask.any() else 0.0


def plot_bar_power(gear_power, outdir):
    """分组柱状图：9个模型×3挡功率"""
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(9)
    w = 0.25
    gear_colors = ['#5B9BD5','#ED7D31','#A5A5A5']
    for g_idx, (gear, color) in enumerate(zip(['G1','G2','G3'], gear_colors)):
        vals = [gear_power[gear][i] for i in range(9)]
        ax.bar(x + (g_idx-1)*w, vals, w, label=f'Gear {g_idx+1}', color=color, edgecolor='white', linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(FULL_LABELS, fontsize=7, linespacing=1.1)
    ax.set_ylabel('Mean Power Output (mW)')
    ax.legend(title='Wind Speed Level')
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 350)
    plt.tight_layout()
    plt.savefig(f'{outdir}/fig_bar_power_by_gear.png', dpi=200, bbox_inches='tight')
    plt.close()


def plot_main_effects(avg_power, outdir):
    """主效应图"""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    factor_meta = {
        'TR': ('Taper Ratio', ['0.5 (Low)','1.2 (High)']),
        'AR': ('Aspect Ratio', ['0.8 (Low)','1.4 (High)']),
        'TA': ('Twist Angle',  ['45° (Low)','90° (High)']),
    }
    for ax, factor in zip(axes, ['TR','AR','TA']):
        fname, xlabs = factor_meta[factor]
        high = np.mean([avg_power[i] for i in range(1,9) if FACTOR_CODING[i][factor]==1])
        low  = np.mean([avg_power[i] for i in range(1,9) if FACTOR_CODING[i][factor]==-1])
        effect = high - low
        ax.plot([0,1], [low,high], 'o-', color='#2F5496', linewidth=2, markersize=8)
        ax.set_xticks([0,1]); ax.set_xticklabels(xlabs)
        ax.set_title(f'{fname}\nEffect = {effect:+.1f} mW', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.annotate(f'{low:.1f}', (0,low), textcoords="offset points", xytext=(10,-15), fontsize=9, color='#666')
        ax.annotate(f'{high:.1f}', (1,high), textcoords="offset points", xytext=(-35,10), fontsize=9, color='#666')
    axes[0].set_ylabel('Mean Power Output (mW)')
    plt.tight_layout()
    plt.savefig(f'{outdir}/fig_main_effects.png', dpi=200, bbox_inches='tight')
    plt.close()


def plot_interactions(avg_power, outdir):
    """两因子交互效应图"""
    factor_meta = {'TR':'Taper Ratio', 'AR':'Aspect Ratio', 'TA':'Twist Angle'}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=True)
    for ax, (f1,f2) in zip(axes, [('TR','AR'),('TR','TA')]):
        for level2, ls, mk, color in [(-1,'--','s','#ED7D31'), (1,'-','o','#2F5496')]:
            y = []
            for level1 in [-1, 1]:
                vals = [avg_power[i] for i in range(1,9)
                        if FACTOR_CODING[i][f1]==level1 and FACTOR_CODING[i][f2]==level2]
                y.append(np.mean(vals))
            ax.plot([0,1], y, f'{mk}{ls}', color=color, linewidth=2, markersize=7,
                    label=f'{factor_meta[f2]} = {"High" if level2==1 else "Low"}')
        ax.set_xticks([0,1]); ax.set_xticklabels([f'{factor_meta[f1]}\nLow', f'{factor_meta[f1]}\nHigh'])
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
        ax.set_title(f'{f1} × {f2} Interaction')
    axes[0].set_ylabel('Mean Power Output (mW)')
    plt.tight_layout()
    plt.savefig(f'{outdir}/fig_interaction_plots.png', dpi=200, bbox_inches='tight')
    plt.close()


def plot_pareto(outdir):
    """Pareto图：效应绝对值排名"""
    data = sorted([
        ('TR',183.29), ('TR×AR',30.82), ('TA',25.69),
        ('TR×TA',22.08), ('AR×TA',10.04), ('AR',2.99), ('TR×AR×TA',1.31),
    ], key=lambda x: x[1])
    fig, ax = plt.subplots(figsize=(8, 4))
    names, vals = zip(*data)
    colors_bar = ['#2F5496' if v>20 else '#A5A5A5' for v in vals]
    bars = ax.barh(names, vals, color=colors_bar, edgecolor='white')
    ax.set_xlabel('|Effect| on Mean Power (mW)')
    for bar, v in zip(bars, vals):
        ax.text(bar.get_width()+2, bar.get_y()+bar.get_height()/2, f'{v:.1f}', va='center', fontsize=9, color='#333')
    ax.set_xlim(0, 210); ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{outdir}/fig_pareto_effects.png', dpi=200, bbox_inches='tight')
    plt.close()


def plot_timeseries(raw_dir, outdir, models=range(9), voltage_thresh=1.0):
    """三合一时序图"""
    t_grid = np.arange(0, 90.01, 0.1)
    aligned = {}
    for i in models:
        df = pd.read_csv(f'{raw_dir}/{i}.csv')
        df['t'] = df['time_s'] - df['time_s'].min()
        df['power_W'] = df['power_W'].clip(lower=0)
        df['current_A'] = df['current_A'].clip(lower=0)
        t_start = detect_start(df, voltage_thresh)
        t_al = df['t'].values - t_start
        mask = (t_al >= -1) & (t_al <= 91)
        v = uniform_filter1d(np.interp(t_grid, t_al[mask], df['voltage_V'].values[mask]), 20)
        a = uniform_filter1d(np.interp(t_grid, t_al[mask], df['current_A'].values[mask]), 20)*1000
        p = uniform_filter1d(np.interp(t_grid, t_al[mask], df['power_W'].values[mask]), 20)*1000
        aligned[i] = {'V':v, 'A':a, 'P':p}

    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    for ax, (key, ylabel) in zip(axes, [('V','Voltage (V)'),('A','Current (mA)'),('P','Power (mW)')]):
        for i in models:
            ax.plot(t_grid, aligned[i][key], color=COLORS[i], label=f'Model {i}', linewidth=1.0, alpha=0.85)
        ax.axvline(30, color='#555', ls='--', lw=0.8, alpha=0.4)
        ax.axvline(60, color='#555', ls='--', lw=0.8, alpha=0.4)
        ax.set_xlim(0, 90); ax.set_ylabel(ylabel); ax.grid(True, alpha=0.2)
        ylim = ax.get_ylim()
        for g, cx in enumerate([15,45,75], 1):
            ax.text(cx, ylim[0]+(ylim[1]-ylim[0])*0.02, f'Gear {g}', ha='center', fontsize=10, color='#888', fontweight='bold')
    axes[0].legend(loc='center left', bbox_to_anchor=(1.01,0.5), fontsize=8)
    axes[-1].set_xlabel('Time since wind onset (s)')
    plt.tight_layout()
    plt.savefig(f'{outdir}/fig_timeseries_combined.png', dpi=200, bbox_inches='tight')
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='CDRF论文配图生成')
    parser.add_argument('--stats', default='./gear_stats.csv', help='挡位统计CSV')
    parser.add_argument('--raw_dir', default='.', help='原始CSV目录')
    parser.add_argument('--output_dir', default='./figures', help='输出目录')
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    setup_style()

    gear_power, avg_power = load_gear_stats(args.stats)

    print("Generating figures...")
    plot_bar_power(gear_power, args.output_dir);      print("  ✓ fig_bar_power_by_gear.png")
    plot_main_effects(avg_power, args.output_dir);     print("  ✓ fig_main_effects.png")
    plot_interactions(avg_power, args.output_dir);      print("  ✓ fig_interaction_plots.png")
    plot_pareto(args.output_dir);                       print("  ✓ fig_pareto_effects.png")
    plot_timeseries(args.raw_dir, args.output_dir);     print("  ✓ fig_timeseries_combined.png")
    print(f"Done! All figures in {args.output_dir}/")


if __name__ == '__main__':
    main()
