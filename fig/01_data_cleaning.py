"""
01_data_cleaning.py
Savonius BIWT 风力发电实验 — 数据清洗
功能：读取原始CSV，去除噪声/负值，平滑处理，归一化时间轴，输出清洗后的数据

用法：
    python 01_data_cleaning.py --input_dir ./raw --output_dir ./cleaned
    
输入：0.csv ~ 8.csv（每个文件含 time_s, voltage_V, current_A, power_W, energy_Wh）
输出：cleaned_0.csv ~ cleaned_8.csv（增加 t_relative 列，时间从0开始）
"""

import os
import argparse
import pandas as pd
import numpy as np


def load_raw(filepath: str) -> pd.DataFrame:
    """读取原始CSV，自动检测编码"""
    for enc in ['utf-8', 'gbk', 'cp1252']:
        try:
            return pd.read_csv(filepath, encoding=enc)
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    raise FileNotFoundError(f"无法读取: {filepath}")


def clean_single_model(df: pd.DataFrame, model_id: int, verbose: bool = True) -> pd.DataFrame:
    """
    清洗单个模型的数据：
    1. 去除重复时间戳
    2. 按时间排序
    3. 将负功率钳位到0（传感器噪声）
    4. 将负电流钳位到0
    5. 添加相对时间列（从0开始）
    6. 添加平滑列（rolling均值，用于后续分析）
    """
    df = df.copy()
    n_before = len(df)

    # 去重 & 排序
    df = df.drop_duplicates(subset=['time_s']).sort_values('time_s').reset_index(drop=True)

    # 钳位负值（传感器噪声）
    df['power_W'] = df['power_W'].clip(lower=0)
    df['current_A'] = df['current_A'].clip(lower=0)

    # 相对时间
    df['t_relative'] = df['time_s'] - df['time_s'].iloc[0]

    # 平滑列（窗口=20个采样点，约0.2s）
    smooth_window = 20
    df['voltage_smooth'] = df['voltage_V'].rolling(smooth_window, center=True, min_periods=1).mean()
    df['current_smooth'] = df['current_A'].rolling(smooth_window, center=True, min_periods=1).mean()
    df['power_smooth'] = df['power_W'].rolling(smooth_window, center=True, min_periods=1).mean()

    if verbose:
        n_after = len(df)
        duration = df['t_relative'].iloc[-1]
        print(f"  Model {model_id}: {n_before}→{n_after} rows, duration={duration:.1f}s, "
              f"V=[{df['voltage_V'].min():.3f}, {df['voltage_V'].max():.3f}], "
              f"P=[{df['power_W'].min():.4f}, {df['power_W'].max():.4f}]")

    return df


def main():
    parser = argparse.ArgumentParser(description='Savonius BIWT 数据清洗')
    parser.add_argument('--input_dir', default='.', help='原始CSV所在目录')
    parser.add_argument('--output_dir', default='./cleaned', help='清洗后输出目录')
    parser.add_argument('--models', default='0,1,2,3,4,5,6,7,8', help='模型编号，逗号分隔')
    parser.add_argument('--smooth_window', type=int, default=20, help='平滑窗口大小')
    args = parser.parse_args()

    model_ids = [int(x) for x in args.models.split(',')]
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"输入目录: {args.input_dir}")
    print(f"输出目录: {args.output_dir}")
    print(f"模型列表: {model_ids}")
    print("-" * 60)

    for mid in model_ids:
        filepath = os.path.join(args.input_dir, f'{mid}.csv')
        df = load_raw(filepath)
        df_clean = clean_single_model(df, mid)
        out_path = os.path.join(args.output_dir, f'cleaned_{mid}.csv')
        df_clean.to_csv(out_path, index=False)

    print("-" * 60)
    print(f"完成！共清洗 {len(model_ids)} 个模型，输出到 {args.output_dir}/")


if __name__ == '__main__':
    main()
