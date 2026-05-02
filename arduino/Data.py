import math
import pandas as pd
import itertools

def generate_savonius_params():
    # ================= 配置参数 =================
    # 扫风面积 (mm^2)
    S_fixed = 10000 
    # 重叠率
    OR = 0.25 
    # 3D打印机最大尺寸限制 (mm)
    PRINT_LIMIT = 200.0
    
    # 实验变量
    TR_list = [0.5, 1.0, 1.2, 1.5]  # Taper Ratio
    AR_list = [0.8, 1.0, 1.2, 1.5]  # Aspect Ratio
    TA_list = [0, 30, 60, 90]       # Twist Angle (度)

    results = []

    # 使用笛卡尔积生成所有组合 (TR x AR x TA)
    # 注意：TA(扭转角)其实不影响H和Rd的计算，但在实验列表中需要列出
    combinations = list(itertools.product(TR_list, AR_list, TA_list))

    print(f"正在计算 {len(combinations)} 组参数...\n")

    for tr, ar, ta in combinations:
        # 1. 根据 S 和 AR 计算 H 和 L
        # 公式推导：
        # S = H * L
        # AR = H / L  ->  H = AR * L
        # 代入第一式: S = (AR * L) * L = AR * L^2
        # L = sqrt(S / AR)
        
        L = math.sqrt(S_fixed / ar)
        H = ar * L
        
        # 2. 根据 TR 和 L 计算 Rd 和 Re
        # 规则: L = 2 * Max(Rd, Re)
        # 且 Re = TR * Rd
        
        if tr <= 1.0:
            # 此时 Rd >= Re (或者相等)
            # Max(Rd, Re) = Rd
            # L = 2 * Rd
            rd = L / 2.0
            re = rd * tr
        else:
            # 此时 Re > Rd
            # Max(Rd, Re) = Re
            # L = 2 * Re
            re = L / 2.0
            rd = re / tr

        # 3. 计算重叠部分和模型总宽
        l_in = 2 * rd * OR
        l_max = (2 * L) - l_in

        # 4. 检查约束条件
        valid_h = H < PRINT_LIMIT
        valid_l_max = l_max < PRINT_LIMIT
        is_printable = valid_h and valid_l_max

        # 5. 存储数据
        results.append({
            "TR (收分率)": tr,
            "AR (展径比)": ar,
            "TA (扭转角)": ta,
            "H (高度 mm)": round(H, 2),
            "L (单叶直径 mm)": round(L, 2),
            "Rd (端部半径 mm)": round(rd, 2),
            "Re (赤道半径 mm)": round(re, 2),
            "L_in (重叠宽 mm)": round(l_in, 2),
            "L_Max (总模型宽 mm)": round(l_max, 2),
            "S (扫风面积)": round(H * L, 1), # 验证用
            "符合打印要求": "✅" if is_printable else "❌ (超限)"
        })

    # 转换为 DataFrame
    df = pd.DataFrame(results)
    return df

if __name__ == "__main__":
    df_results = generate_savonius_params()
    
    # 显示所有数据
    print("--- 生成结果预览 ---")
    print(df_results)
    
    # 筛选出符合打印要求的数据
    valid_df = df_results[df_results["符合打印要求"] == "✅"]
    
    print(f"\n总组合数: {len(df_results)}")
    print(f"符合打印要求的组合数: {len(valid_df)}")
    
    # 检查哪些参数导致了超限
    invalid_df = df_results[df_results["符合打印要求"] != "✅"]
    if not invalid_df.empty:
        print("\n--- 以下组合超出 200mm 限制 (主要是 L_Max 超限) ---")
        # 只显示不重复的几何尺寸组合（去掉TA重复项）
        print(invalid_df.drop_duplicates(subset=['TR', 'AR'])[['TR', 'AR', 'H', 'L_Max']].to_string(index=False))
    
    # 导出到 Excel (如果需要，取消下面注释)
    df_results.to_excel("Savonius_Params.xlsx", index=False)