import serial
import csv
import os
from datetime import datetime

PORT = "COM6"
BAUDRATE = 9600

# ===== 明确指定保存路径 =====
save_dir = r"D:\Tsinghua\Design Studio\data"
os.makedirs(save_dir, exist_ok=True)

filename = os.path.join(
    save_dir,
    f"ina226_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
)

ser = serial.Serial(PORT, BAUDRATE, timeout=1)

with open(filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    print("Saving to:", filename)
    print("Waiting for data...")

    while True:
        line = ser.readline().decode("utf-8").strip()
        if not line:
            continue

        if "Time_ms" in line:
            writer.writerow(line.split(","))
            print(line)
            continue

        data = line.split(",")
        if len(data) == 4:
            writer.writerow(data)
            print(data)
