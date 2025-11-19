#!/usr/bin/env python3
"""
So sánh QoS metrics qua các tốc độ khác nhau (0, 5, 10, 20 m/s)
Phân tích riêng cho VoIP và Video traffic
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

# ====== CẤU HÌNH ======
BASE_DIR = "/home/uyen-phuong/ns3-projects/manet-mobility-qos/data"
TXT_DIR = f"{BASE_DIR}/txt"
PLOT_DIR = f"{BASE_DIR}/plots/comparison"
CSV_DIR = f"{BASE_DIR}/csv"

# Tạo thư mục nếu chưa tồn tại
os.makedirs(PLOT_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

# Tìm tất cả file kết quả
pattern = f"{TXT_DIR}/qos_dsr_*node_speed*_*client.txt"
files = sorted(glob.glob(pattern))

if not files:
    print(f"❌ Không tìm thấy file nào trong: {TXT_DIR}")
    print(f"   Pattern: {pattern}")
    exit(1)

print(f"Tìm thấy {len(files)} file kết quả:")
for f in files:
    print(f"   - {os.path.basename(f)}")
print()

# ====== ĐỌC DỮ LIỆU TỪ TẤT CẢ FILES ======
all_data = []

for file_path in files:
    try:
        # Trích xuất tốc độ từ tên file (vd: qos_dsr_20node_speed5_10client.txt)
        basename = os.path.basename(file_path)
        speed_str = basename.split('speed')[1].split('_')[0]
        speed = float(speed_str)
        
        # Đọc file
        df = pd.read_csv(file_path)
        
        # Lọc chỉ lấy dòng Average
        df_avg = df[df["FlowID"] == "Average"].copy()
        
        if not df_avg.empty:
            # Thêm cột Speed
            df_avg["Speed"] = speed
            all_data.append(df_avg)
            print(f"Đã đọc: {basename} (Speed: {speed} m/s)")
        else:
            print(f"⚠️  Không tìm thấy dòng Average trong: {basename}")
            
    except Exception as e:
        print(f"❌ Lỗi khi đọc {file_path}: {e}")

if not all_data:
    print("\n❌ Không có dữ liệu hợp lệ để phân tích!")
    exit(1)

# Gộp tất cả dữ liệu
df_combined = pd.concat(all_data, ignore_index=True)

# Sắp xếp theo Speed và TrafficType
df_combined = df_combined.sort_values(["Speed", "TrafficType"])

print(f"\n📊 Tổng hợp dữ liệu:")
print(df_combined[["Speed", "TrafficType", "Throughput(kbps)", "Delay(ms)", "Jitter(ms)", "Loss(%)"]])

# ====== LƯU FILE CSV TỔNG HỢP ======
output_csv = os.path.join(CSV_DIR, "qos_comparison_all_speeds.csv")
df_combined.to_csv(output_csv, index=False)
print(f"\nĐã lưu CSV tổng hợp: {output_csv}")

# ====== VẼ BIỂU ĐỒ SO SÁNH ======
# Tách dữ liệu theo loại traffic
df_overall = df_combined[df_combined["TrafficType"] == "Overall"]
df_voip = df_combined[df_combined["TrafficType"] == "VoIP"]
df_video = df_combined[df_combined["TrafficType"] == "Video"]

# Tạo figure với 4 subplots
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("QoS Metrics vs Node Speed (DSR Protocol)", fontsize=18, fontweight="bold", y=0.995)

# Màu sắc
colors = {"Overall": "#2E86AB", "VoIP": "#A23B72", "Video": "#0FA3B1"}

# 1️⃣ Throughput vs Speed
ax = axes[0, 0]
for df_type, label, color in [
    (df_overall, "Overall", colors["Overall"]),
    (df_voip, "VoIP", colors["VoIP"]),
    (df_video, "Video", colors["Video"])
]:
    if not df_type.empty:
        ax.plot(df_type["Speed"], df_type["Throughput(kbps)"], 
                marker='o', linewidth=2.5, markersize=8, label=label, color=color)

ax.set_xlabel("Node Speed (m/s)", fontweight="bold", fontsize=12)
ax.set_ylabel("Throughput (kbps)", fontweight="bold", fontsize=12)
ax.set_title("Throughput vs Speed", fontweight="bold", fontsize=14, pad=10)
ax.legend(loc="best", fontsize=10)
ax.grid(alpha=0.3, linestyle="--")
ax.set_ylim(bottom=0)

# 2️⃣ Delay vs Speed
ax = axes[0, 1]
for df_type, label, color in [
    (df_overall, "Overall", colors["Overall"]),
    (df_voip, "VoIP", colors["VoIP"]),
    (df_video, "Video", colors["Video"])
]:
    if not df_type.empty:
        ax.plot(df_type["Speed"], df_type["Delay(ms)"], 
                marker='s', linewidth=2.5, markersize=8, label=label, color=color)

ax.set_xlabel("Node Speed (m/s)", fontweight="bold", fontsize=12)
ax.set_ylabel("Average Delay (ms)", fontweight="bold", fontsize=12)
ax.set_title("Delay vs Speed", fontweight="bold", fontsize=14, pad=10)
ax.legend(loc="best", fontsize=10)
ax.grid(alpha=0.3, linestyle="--")
ax.set_ylim(bottom=0)

# 3️⃣ Jitter vs Speed
ax = axes[1, 0]
for df_type, label, color in [
    (df_overall, "Overall", colors["Overall"]),
    (df_voip, "VoIP", colors["VoIP"]),
    (df_video, "Video", colors["Video"])
]:
    if not df_type.empty:
        ax.plot(df_type["Speed"], df_type["Jitter(ms)"], 
                marker='D', linewidth=2.5, markersize=8, label=label, color=color)

ax.set_xlabel("Node Speed (m/s)", fontweight="bold", fontsize=12)
ax.set_ylabel("Average Jitter (ms)", fontweight="bold", fontsize=12)
ax.set_title("Jitter vs Speed", fontweight="bold", fontsize=14, pad=10)
ax.legend(loc="best", fontsize=10)
ax.grid(alpha=0.3, linestyle="--")
ax.set_ylim(bottom=0)

# 4️⃣ Packet Loss vs Speed
ax = axes[1, 1]
for df_type, label, color in [
    (df_overall, "Overall", colors["Overall"]),
    (df_voip, "VoIP", colors["VoIP"]),
    (df_video, "Video", colors["Video"])
]:
    if not df_type.empty:
        ax.plot(df_type["Speed"], df_type["Loss(%)"], 
                marker='^', linewidth=2.5, markersize=8, label=label, color=color)

ax.set_xlabel("Node Speed (m/s)", fontweight="bold", fontsize=12)
ax.set_ylabel("Packet Loss (%)", fontweight="bold", fontsize=12)
ax.set_title("Packet Loss vs Speed", fontweight="bold", fontsize=14, pad=10)
ax.legend(loc="best", fontsize=10)
ax.grid(alpha=0.3, linestyle="--")
ax.set_ylim(bottom=0)

# Điều chỉnh layout
plt.tight_layout()

# Lưu ảnh
output_plot = os.path.join(PLOT_DIR, "qos_comparison_all_speeds.png")
plt.savefig(output_plot, dpi=300, bbox_inches='tight')
print(f"Đã lưu biểu đồ so sánh: {output_plot}")

# Hiển thị
try:
    plt.show()
except:
    plt.close()

# ====== IN PHÂN TÍCH ======
print("\n" + "="*60)
print("📈 PHÂN TÍCH ẢNH HƯỞNG CỦA TỐC ĐỘ")
print("="*60)

if not df_overall.empty:
    print("\nOVERALL (Tất cả flows):")
    for metric in ["Throughput(kbps)", "Delay(ms)", "Jitter(ms)", "Loss(%)"]:
        min_speed = df_overall.loc[df_overall[metric].idxmin(), "Speed"]
        max_speed = df_overall.loc[df_overall[metric].idxmax(), "Speed"]
        min_val = df_overall[metric].min()
        max_val = df_overall[metric].max()
        
        if metric == "Throughput(kbps)":
            print(f"   • {metric}: Cao nhất ở {max_speed} m/s ({max_val:.2f}), thấp nhất ở {min_speed} m/s ({min_val:.2f})")
        else:
            print(f"   • {metric}: Thấp nhất ở {min_speed} m/s ({min_val:.2f}), cao nhất ở {max_speed} m/s ({max_val:.2f})")

if not df_voip.empty:
    print("\nVoIP Traffic:")
    for metric in ["Throughput(kbps)", "Delay(ms)", "Jitter(ms)"]:
        min_speed = df_voip.loc[df_voip[metric].idxmin(), "Speed"]
        max_speed = df_voip.loc[df_voip[metric].idxmax(), "Speed"]
        min_val = df_voip[metric].min()
        max_val = df_voip[metric].max()
        
        if metric == "Throughput(kbps)":
            print(f"   • {metric}: Cao nhất ở {max_speed} m/s ({max_val:.2f}), thấp nhất ở {min_speed} m/s ({min_val:.2f})")
        else:
            print(f"   • {metric}: Thấp nhất ở {min_speed} m/s ({min_val:.2f}), cao nhất ở {max_speed} m/s ({max_val:.2f})")

if not df_video.empty:
    print("\nVideo Traffic:")
    for metric in ["Throughput(kbps)", "Delay(ms)", "Jitter(ms)"]:
        min_speed = df_video.loc[df_video[metric].idxmin(), "Speed"]
        max_speed = df_video.loc[df_video[metric].idxmax(), "Speed"]
        min_val = df_video[metric].min()
        max_val = df_video[metric].max()
        
        if metric == "Throughput(kbps)":
            print(f"   • {metric}: Cao nhất ở {max_speed} m/s ({max_val:.2f}), thấp nhất ở {min_speed} m/s ({min_val:.2f})")
        else:
            print(f"   • {metric}: Thấp nhất ở {min_speed} m/s ({min_val:.2f}), cao nhất ở {max_speed} m/s ({max_val:.2f})")

print("\n" + "="*60)
print("✨ Phân tích hoàn tất!")
print("="*60)
