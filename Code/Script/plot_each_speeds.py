#!/usr/bin/env python3
"""
Vẽ biểu đồ QoS chi tiết cho TỪNG tốc độ (per-flow analysis)
Tự động xử lý tất cả file TXT đã generate
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

# ====== CẤU HÌNH ======
BASE_DIR = "/home/uyen-phuong/ns3-projects/manet-mobility-qos/data"
TXT_DIR = f"{BASE_DIR}/txt"
PLOT_DIR = f"{BASE_DIR}/plots/per_speed"
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

print(f"✅ Tìm thấy {len(files)} file kết quả")
print("="*60)

# ====== XỬLÝ TỪNG FILE ======
for file_path in files:
    try:
        basename = os.path.basename(file_path)
        base_name = os.path.splitext(basename)[0]
        
        # Trích xuất thông tin từ tên file
        speed_str = basename.split('speed')[1].split('_')[0]
        speed = float(speed_str)
        
        print(f"\n📊 Đang xử lý: {basename}")
        print(f"   Tốc độ: {speed} m/s")
        
        # ====== ĐỌC FILE TXT ======
        df = pd.read_csv(file_path)
        
        # Bỏ dòng Average riêng ra
        df_flows = df[df["FlowID"] != "Average"].copy()
        df_avg = df[df["FlowID"] == "Average"].copy()
        
        if df_flows.empty:
            print(f"   ⚠️  Không có dữ liệu flows!")
            continue
        
        # Ép kiểu dữ liệu
        df_flows["FlowID"] = df_flows["FlowID"].astype(int)
        df_flows["Throughput(kbps)"] = df_flows["Throughput(kbps)"].astype(float)
        df_flows["Delay(ms)"] = df_flows["Delay(ms)"].astype(float)
        df_flows["Jitter(ms)"] = df_flows["Jitter(ms)"].astype(float)
        df_flows["Loss(%)"] = df_flows["Loss(%)"].astype(float)
        
        # Tách VoIP và Video flows
        df_voip = df_flows[df_flows["TrafficType"] == "VoIP"].copy()
        df_video = df_flows[df_flows["TrafficType"] == "Video"].copy()
        
        # ====== LƯU FILE CSV ======
        csv_path = os.path.join(CSV_DIR, f"{base_name}_flows.csv")
        df_flows.to_csv(csv_path, index=False)
        print(f"   ✅ Đã lưu CSV: {csv_path}")
        
        # ====== VẼ BIỂU ĐỒ ======
        fig = plt.figure(figsize=(16, 12))
        plt.subplots_adjust(hspace=0.35, wspace=0.3, top=0.94)
        
        fig.suptitle(f"QoS Metrics per Flow - Speed {speed} m/s (DSR Protocol)",
                     fontsize=18, fontweight="bold")
        
        # Màu sắc
        voip_color = "#A23B72"
        video_color = "#0FA3B1"
        
        # 1️⃣ Throughput
        ax1 = plt.subplot(2, 2, 1)
        if not df_voip.empty:
            ax1.plot(df_voip["FlowID"], df_voip["Throughput(kbps)"], 
                    marker='o', linewidth=2, markersize=6, label="VoIP", color=voip_color)
        if not df_video.empty:
            ax1.plot(df_video["FlowID"], df_video["Throughput(kbps)"], 
                    marker='s', linewidth=2, markersize=6, label="Video", color=video_color)
        
        ax1.set_title("Throughput per Flow", fontweight="bold", fontsize=14, pad=10)
        ax1.set_xlabel("Flow ID", fontweight="bold")
        ax1.set_ylabel("Throughput (kbps)", fontweight="bold")
        ax1.legend(loc="best")
        ax1.grid(alpha=0.3, linestyle="--")
        ax1.set_ylim(bottom=0)
        
        # 2️⃣ Delay
        ax2 = plt.subplot(2, 2, 2)
        if not df_voip.empty:
            ax2.plot(df_voip["FlowID"], df_voip["Delay(ms)"], 
                    marker='o', linewidth=2, markersize=6, label="VoIP", color=voip_color)
        if not df_video.empty:
            ax2.plot(df_video["FlowID"], df_video["Delay(ms)"], 
                    marker='s', linewidth=2, markersize=6, label="Video", color=video_color)
        
        ax2.set_title("Delay per Flow", fontweight="bold", fontsize=14, pad=10)
        ax2.set_xlabel("Flow ID", fontweight="bold")
        ax2.set_ylabel("Average Delay (ms)", fontweight="bold")
        ax2.legend(loc="best")
        ax2.grid(alpha=0.3, linestyle="--")
        ax2.set_ylim(bottom=0)
        
        # 3️⃣ Jitter
        ax3 = plt.subplot(2, 2, 3)
        if not df_voip.empty:
            ax3.plot(df_voip["FlowID"], df_voip["Jitter(ms)"], 
                    marker='o', linewidth=2, markersize=6, label="VoIP", color=voip_color)
        if not df_video.empty:
            ax3.plot(df_video["FlowID"], df_video["Jitter(ms)"], 
                    marker='s', linewidth=2, markersize=6, label="Video", color=video_color)
        
        ax3.set_title("Jitter per Flow", fontweight="bold", fontsize=14, pad=10)
        ax3.set_xlabel("Flow ID", fontweight="bold")
        ax3.set_ylabel("Average Jitter (ms)", fontweight="bold")
        ax3.legend(loc="best")
        ax3.grid(alpha=0.3, linestyle="--")
        ax3.set_ylim(bottom=0)
        
        # 4️⃣ Packet Loss
        ax4 = plt.subplot(2, 2, 4)
        if not df_voip.empty:
            ax4.plot(df_voip["FlowID"], df_voip["Loss(%)"], 
                    marker='o', linewidth=2, markersize=6, label="VoIP", color=voip_color)
        if not df_video.empty:
            ax4.plot(df_video["FlowID"], df_video["Loss(%)"], 
                    marker='s', linewidth=2, markersize=6, label="Video", color=video_color)
        
        ax4.set_title("Packet Loss per Flow", fontweight="bold", fontsize=14, pad=10)
        ax4.set_xlabel("Flow ID", fontweight="bold")
        ax4.set_ylabel("Loss (%)", fontweight="bold")
        ax4.legend(loc="best")
        ax4.grid(alpha=0.3, linestyle="--")
        ax4.set_ylim(bottom=0)
        
        # ====== LƯU ẢNH ======
        plot_path = os.path.join(PLOT_DIR, f"{base_name}_per_flow.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ Đã lưu biểu đồ: {plot_path}")
        
        plt.close()
        
        # ====== IN THÔNG TIN TRUNG BÌNH ======
        if not df_avg.empty:
            print(f"\n   📊 SUMMARY (Speed {speed} m/s):")
            for _, row in df_avg.iterrows():
                traffic_type = row["TrafficType"]
                thpt = row["Throughput(kbps)"]
                delay = row["Delay(ms)"]
                jitter = row["Jitter(ms)"]
                loss = row["Loss(%)"]
                
                print(f"      {traffic_type:8s}: Thpt={thpt:7.2f} kbps, "
                      f"Delay={delay:5.2f} ms, Jitter={jitter:5.2f} ms, Loss={loss:5.2f}%")
        
        print(f"   ✅ Hoàn tất xử lý!")
        
    except Exception as e:
        print(f"   ❌ Lỗi khi xử lý {basename}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("✨ ĐÃ HOÀN TẤT TẤT CẢ!")
print("="*60)
print(f"\n📁 Kết quả:")
print(f"   - Biểu đồ per-flow: {PLOT_DIR}/")
print(f"   - CSV chi tiết: {CSV_DIR}/")
print(f"\n💡 Tiếp theo: Chạy compare_speeds.py để so sánh cross-speed!")
