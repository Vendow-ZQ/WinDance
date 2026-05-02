import pandas as pd
import matplotlib.pyplot as plt

# ===============================
# 1. Read CSV
# ===============================
file_path = "D:\\Tsinghua\\Design Studio\\data\\003.csv"   # 修改为你的实际路径
df = pd.read_csv(file_path)

time_s = df["Time_ms"] / 1000.0
voltage = df["Voltage_V"]
current = df["Current_mA"]
power   = df["Power_mW"]

v_mean = voltage.mean()
i_mean = current.mean()
p_mean = power.mean()

# ===============================
# 2. Nature-style global settings
# ===============================
plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 8,
    "axes.linewidth": 0.8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "figure.dpi": 300
})

# ===============================
# 3. Layout: taller figure
# ===============================
fig, axes = plt.subplots(
    3, 1,
    figsize=(6.5, 7.8),   # ⬅ 关键：增加高度
    sharex=True
)

# Common line style
main_lw = 0.9
mean_lw = 0.8

# ---------- Voltage ----------
axes[0].plot(time_s, voltage, lw=main_lw, color="#1f77b4")
axes[0].axhline(v_mean, ls="--", lw=mean_lw, color="#1f77b4")
axes[0].set_ylabel("Voltage (V)")
axes[0].set_title("Electrical Performance at High Wind Speed", pad=8)

axes[0].text(
    0.02, 1.15,
    f"Mean = {v_mean:.2f} V",
    transform=axes[0].transAxes,
    ha="left",
    va="top"
)

# ---------- Current ----------
axes[1].plot(time_s, current, lw=main_lw, color="#2ca02c")
axes[1].axhline(i_mean, ls="--", lw=mean_lw, color="#2ca02c")
axes[1].set_ylabel("Current (mA)")

axes[1].text(
    0.02, 1.15,
    f"Mean = {i_mean:.2f} mA",
    transform=axes[1].transAxes,
    ha="left",
    va="top"
)

# ---------- Power ----------
axes[2].plot(time_s, power, lw=main_lw, color="#d62728")
axes[2].axhline(p_mean, ls="--", lw=mean_lw, color="#d62728")
axes[2].set_ylabel("Power (mW)")
axes[2].set_xlabel("Time (s)")

axes[2].text(
    0.02 , 1.15,
    f"Mean = {p_mean:.2f} mW",
    transform=axes[2].transAxes,
    ha="left",
    va="top"
)

# ===============================
# 4. Clean spines (Nature style)
# ===============================
for ax in axes:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.8)

plt.tight_layout(h_pad=1.2)   # ⬅ 增加子图垂直间距
plt.show()
