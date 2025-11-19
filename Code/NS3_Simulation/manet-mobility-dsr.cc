
// ./ns3 build manet-mobility-dsr
// ./ns3 run "scratch/manet-mobility-dsr --nNodes=30  --nodeSpeed=5 --numClients=20"

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/wifi-module.h"
#include "ns3/internet-module.h"
#include "ns3/applications-module.h"
#include "ns3/dsr-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("ManetDsrQoS");

struct FlowStats {
    uint32_t txPackets = 0;
    uint32_t rxPackets = 0;
    uint64_t txBytes = 0;
    uint64_t rxBytes = 0;
    Time firstTxTime;
    Time lastRxTime;
    Time totalDelay;
    uint32_t delayCount = 0;

    // ✅ Thêm thông tin Jitter
    double lastDelayMs = 0.0;
    double totalJitter = 0.0;
    uint32_t jitterCount = 0;
    
    // ✅ Thêm loại traffic
    std::string trafficType = "Unknown";
};

std::map<uint32_t, FlowStats> g_flowStats;
std::map<uint64_t, Time> g_packetSentTime; // UID -> TxTime

// ===== CALLBACKS =====
void TxCallback(uint32_t flowId, Ptr<const Packet> packet) {
    if (g_flowStats.find(flowId) == g_flowStats.end()) {
        g_flowStats[flowId].firstTxTime = Simulator::Now();
    }
    g_flowStats[flowId].txPackets++;
    g_flowStats[flowId].txBytes += packet->GetSize();
    g_packetSentTime[packet->GetUid()] = Simulator::Now();
}

void RxCallback(uint32_t flowId, Ptr<const Packet> packet, const Address &address) {
    g_flowStats[flowId].rxPackets++;
    g_flowStats[flowId].rxBytes += packet->GetSize();
    g_flowStats[flowId].lastRxTime = Simulator::Now();

    auto it = g_packetSentTime.find(packet->GetUid());
    if (it != g_packetSentTime.end()) {
        Time delay = Simulator::Now() - it->second;
        double delayMs = delay.GetMilliSeconds();

        // ✅ Cập nhật delay
        g_flowStats[flowId].totalDelay += delay;
        g_flowStats[flowId].delayCount++;

        // ✅ Tính jitter giữa 2 gói liên tiếp
        if (g_flowStats[flowId].delayCount > 1) {
            double jitter = std::abs(delayMs - g_flowStats[flowId].lastDelayMs);
            g_flowStats[flowId].totalJitter += jitter;
            g_flowStats[flowId].jitterCount++;
        }
        g_flowStats[flowId].lastDelayMs = delayMs;

        g_packetSentTime.erase(it);
    }
}

// ===== PRINT + SAVE RESULTS =====
void PrintQoSResults(std::string routingProtocol, double nodeSpeed, double totalTime, uint32_t numClients, uint32_t nNodes) {
    std::cout << "\n=== QoS ANALYSIS RESULTS ===" << std::endl;

    double totalThroughput = 0.0;
    double totalDelay = 0.0;
    double totalJitter = 0.0;
    uint32_t totalRxPackets = 0;
    uint32_t totalTxPackets = 0;
    uint32_t flowCount = 0;

    // 🔥 Stats riêng cho VoIP và Video
    double voipThroughput = 0.0, voipDelay = 0.0, voipJitter = 0.0;
    double videoThroughput = 0.0, videoDelay = 0.0, videoJitter = 0.0;
    uint32_t voipCount = 0, videoCount = 0;

    // 🔥 Tạo tên file theo tốc độ node
    std::ostringstream filename;
    filename << "/home/uyen-phuong/ns3-projects/manet-mobility-qos/data/txt/qos_dsr_"<<nNodes<<"node_speed"<< nodeSpeed <<"_"<<numClients<<"client.txt";
    std::ofstream out(filename.str(), std::ios::out);

    // Ghi tiêu đề (thêm cột TrafficType)
    out << "Routing,Speed,TrafficType,FlowID,TxPackets,RxPackets,Throughput(kbps),Delay(ms),Jitter(ms),Loss(%)\n";

    for (auto &pair : g_flowStats) {
        uint32_t flowId = pair.first;
        FlowStats &s = pair.second;
        totalTxPackets += s.txPackets;
        totalRxPackets += s.rxPackets;

        if (s.rxPackets > 0) {
            double duration = (s.lastRxTime - s.firstTxTime).GetSeconds();
            if (duration <= 0) duration = totalTime;

            double throughput = (s.rxBytes * 8.0) / duration / 1000.0; // kbps
            double avgDelay = (s.delayCount > 0) ? s.totalDelay.GetMilliSeconds() / s.delayCount : 0;
            double avgJitter = (s.jitterCount > 0) ? s.totalJitter / s.jitterCount : 0;
            double loss = (s.txPackets > 0) ? ((s.txPackets - s.rxPackets) * 100.0 / s.txPackets) : 0;

            totalThroughput += throughput;
            totalDelay += avgDelay;
            totalJitter += avgJitter;
            flowCount++;

            // ✅ Tính riêng cho từng loại traffic
            if (s.trafficType == "VoIP") {
                voipThroughput += throughput;
                voipDelay += avgDelay;
                voipJitter += avgJitter;
                voipCount++;
            } else if (s.trafficType == "Video") {
                videoThroughput += throughput;
                videoDelay += avgDelay;
                videoJitter += avgJitter;
                videoCount++;
            }

            std::cout << "Flow " << flowId << " [" << s.trafficType << "]"
                      << ": Tx=" << s.txPackets
                      << ", Rx=" << s.rxPackets
                      << ", Thpt=" << throughput << " kbps"
                      << ", Delay=" << avgDelay << " ms"
                      << ", Jitter=" << avgJitter << " ms"
                      << ", Loss=" << loss << " %" << std::endl;

            // 🔹 Ghi chi tiết flow vào file
            out << routingProtocol << "," << nodeSpeed << "," << s.trafficType << ","
                << flowId << "," << s.txPackets << "," << s.rxPackets << ","
                << throughput << "," << avgDelay << "," << avgJitter << "," << loss << "\n";
        }
    }

    if (flowCount > 0) {
        double avgThroughput = totalThroughput / flowCount;
        double avgDelayAll = totalDelay / flowCount;
        double avgJitterAll = totalJitter / flowCount;
        double pdr = (totalRxPackets * 100.0) / totalTxPackets;

        std::cout << "\n=== OVERALL QoS SUMMARY ===" << std::endl;
        std::cout << "Flows: " << flowCount << std::endl;
        std::cout << "Avg Throughput: " << avgThroughput << " kbps" << std::endl;
        std::cout << "Avg Delay: " << avgDelayAll << " ms" << std::endl;
        std::cout << "Avg Jitter: " << avgJitterAll << " ms" << std::endl;
        std::cout << "PDR: " << pdr << " %" << std::endl;

        // ✅ In thống kê riêng cho VoIP
        if (voipCount > 0) {
            std::cout << "\n=== VoIP QoS ===" << std::endl;
            std::cout << "Avg Throughput: " << voipThroughput/voipCount << " kbps" << std::endl;
            std::cout << "Avg Delay: " << voipDelay/voipCount << " ms" << std::endl;
            std::cout << "Avg Jitter: " << voipJitter/voipCount << " ms" << std::endl;
        }

        // ✅ In thống kê riêng cho Video
        if (videoCount > 0) {
            std::cout << "\n=== Video QoS ===" << std::endl;
            std::cout << "Avg Throughput: " << videoThroughput/videoCount << " kbps" << std::endl;
            std::cout << "Avg Delay: " << videoDelay/videoCount << " ms" << std::endl;
            std::cout << "Avg Jitter: " << videoJitter/videoCount << " ms" << std::endl;
        }

        // 🔹 Ghi dòng Average tổng thể
        out << routingProtocol << "," << nodeSpeed << ",Overall,Average,,,"
            << avgThroughput << "," << avgDelayAll << "," << avgJitterAll << "," << (100.0 - pdr) << "\n";

        // 🔹 Ghi dòng Average cho VoIP (tính Loss riêng)
        if (voipCount > 0) {
            uint32_t voipTx = 0, voipRx = 0;
            for (auto &pair : g_flowStats) {
                if (pair.second.trafficType == "VoIP" && pair.second.rxPackets > 0) {
                    voipTx += pair.second.txPackets;
                    voipRx += pair.second.rxPackets;
                }
            }
            double voipLoss = (voipTx > 0) ? ((voipTx - voipRx) * 100.0 / voipTx) : 0;
            
            out << routingProtocol << "," << nodeSpeed << ",VoIP,Average,,,"
                << voipThroughput/voipCount << "," << voipDelay/voipCount << ","
                << voipJitter/voipCount << "," << voipLoss << "\n";
        }

        // 🔹 Ghi dòng Average cho Video (tính Loss riêng)
        if (videoCount > 0) {
            uint32_t videoTx = 0, videoRx = 0;
            for (auto &pair : g_flowStats) {
                if (pair.second.trafficType == "Video" && pair.second.rxPackets > 0) {
                    videoTx += pair.second.txPackets;
                    videoRx += pair.second.rxPackets;
                }
            }
            double videoLoss = (videoTx > 0) ? ((videoTx - videoRx) * 100.0 / videoTx) : 0;
            
            out << routingProtocol << "," << nodeSpeed << ",Video,Average,,,"
                << videoThroughput/videoCount << "," << videoDelay/videoCount << ","
                << videoJitter/videoCount << "," << videoLoss << "\n";
        }
    } else {
        std::cout << "\n⚠️ No valid flows found!" << std::endl;
    }

    out.close();
    std::cout << "\n✅ Saved detailed results to: " << filename.str() << std::endl;
}

// ===== MAIN =====
int main(int argc, char *argv[]) {
    Time::SetResolution(Time::NS);
    uint32_t nNodes = 20;
    uint32_t numClients = 10; // ✅ Tăng lên để có cả VoIP và Video
    double nodeSpeed = 5.0;
    double totalTime = 50.0;

    CommandLine cmd;
    cmd.AddValue("nNodes", "Number of nodes", nNodes);
    cmd.AddValue("numClients", "Number of client nodes", numClients);
    cmd.AddValue("nodeSpeed", "Speed (m/s)", nodeSpeed);
    cmd.AddValue("totalTime", "Simulation time (s)", totalTime);
    cmd.Parse(argc, argv);

    std::cout << "\n=== MANET DSR MULTIFLOW (VoIP + Video) ===" << std::endl;
    std::cout << "Nodes: " << nNodes << ", Clients: " << numClients
              << ", Speed: " << nodeSpeed << " m/s" << std::endl;

    // ===== NODES =====
    NodeContainer nodes;
    nodes.Create(nNodes);

    // ===== WIFI =====
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211a);
    WifiMacHelper mac;
    mac.SetType("ns3::AdhocWifiMac");
    YansWifiChannelHelper chan;
    chan.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel");
    chan.AddPropagationLoss("ns3::RangePropagationLossModel", "MaxRange", DoubleValue(120.0));
    YansWifiPhyHelper phy;
    phy.SetChannel(chan.Create());
    NetDeviceContainer devs = wifi.Install(phy, mac, nodes);

    // ===== MOBILITY =====
    MobilityHelper mob;
    mob.SetPositionAllocator("ns3::RandomRectanglePositionAllocator",
                             "X", StringValue("ns3::UniformRandomVariable[Min=0.0|Max=200.0]"),
                             "Y", StringValue("ns3::UniformRandomVariable[Min=0.0|Max=200.0]"));
    mob.SetMobilityModel("ns3::RandomWalk2dMobilityModel",
                         "Bounds", RectangleValue(Rectangle(0, 200, 0, 200)),
                         "Speed", StringValue("ns3::ConstantRandomVariable[Constant=" + std::to_string(nodeSpeed) + "]"));
    mob.Install(nodes);

    // ===== DSR STACK =====
    InternetStackHelper internet;
    DsrMainHelper dsrMain;
    DsrHelper dsr;
    internet.Install(nodes);
    dsrMain.Install(dsr, nodes);

    Ipv4AddressHelper ipv4;
    ipv4.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer ifs = ipv4.Assign(devs);

    // ===== MULTI FLOW (VoIP + Video) =====
    uint16_t basePort = 9000;
    
    // ✅ Kiểm tra số clients hợp lệ
    if (numClients >= nNodes) {
        std::cerr << "❌ Error: numClients (" << numClients 
                  << ") must be less than nNodes (" << nNodes << ")" << std::endl;
        std::cerr << "   Reason: Node 0 is reserved as sink (receiver)" << std::endl;
        return 1;
    }

    for (uint32_t i = 0; i < numClients; i++) {
        uint16_t port = basePort + i;
        
        // ✅ 50% VoIP (64 kbps), 50% Video (512 kbps)
        bool isVoIP = (i < numClients / 2);
        std::string trafficType = isVoIP ? "VoIP" : "Video";
        std::string dataRate = isVoIP ? "64kbps" : "512kbps";
        uint32_t packetSize = isVoIP ? 160 : 1024; // VoIP: 160 bytes, Video: 1024 bytes
        
        std::cout << "Flow " << (i+1) << ": " << trafficType 
                  << " @ " << dataRate 
                  << " (Node " << (i+1) << " → Node 0)" << std::endl;
        
        // ✅ Lưu loại traffic vào FlowStats
        g_flowStats[i + 1].trafficType = trafficType;

        Address sinkAddr(InetSocketAddress(ifs.GetAddress(0), port));

        PacketSinkHelper sinkHelper("ns3::UdpSocketFactory",
                                    InetSocketAddress(Ipv4Address::GetAny(), port));
        ApplicationContainer sinkApp = sinkHelper.Install(nodes.Get(0));
        sinkApp.Start(Seconds(5.0));
        sinkApp.Stop(Seconds(totalTime));

        Ptr<PacketSink> sink = DynamicCast<PacketSink>(sinkApp.Get(0));
        sink->TraceConnectWithoutContext("Rx", MakeBoundCallback(&RxCallback, i + 1));

        OnOffHelper onoff("ns3::UdpSocketFactory", sinkAddr);
        onoff.SetAttribute("DataRate", DataRateValue(DataRate(dataRate)));
        onoff.SetAttribute("PacketSize", UintegerValue(packetSize));
        onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1.0]"));
        onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0.0]"));
        ApplicationContainer clientApp = onoff.Install(nodes.Get(i + 1));
        clientApp.Start(Seconds(10.0 + i));
        clientApp.Stop(Seconds(totalTime - 5));

        Ptr<OnOffApplication> app = DynamicCast<OnOffApplication>(clientApp.Get(0));
        app->TraceConnectWithoutContext("Tx", MakeBoundCallback(&TxCallback, i + 1));
    }
    
    std::cout << "\n📊 Network Topology:" << std::endl;
    std::cout << "   - Node 0: Sink (receiver)" << std::endl;
    std::cout << "   - Nodes 1-" << numClients << ": Senders (clients)" << std::endl;
    if (nNodes > numClients + 1) {
        std::cout << "   - Nodes " << (numClients + 1) << "-" << (nNodes - 1) 
                  << ": Relay nodes (routing only)" << std::endl;
    }
    std::cout << std::endl;

    Simulator::Stop(Seconds(totalTime));
    Simulator::Run();

    // ✅ In và lưu kết quả
    PrintQoSResults("DSR", nodeSpeed, totalTime, numClients, nNodes);

    Simulator::Destroy();
    std::cout << "\n✓ Simulation completed successfully!" << std::endl;
}