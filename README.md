# Changes I made 


## GPU-to-GPU Direct Routing Implementation

**Key Enhancement:** Implemented enhanced UB mesh routing algorithm that enables direct GPU-to-GPU communication while supporting inter-rack switches, resulting in 1.75x overall speedup and 21.7x communication speedup compared to Fat Tree topology.

### Modified Files:

**Core Network Routing:**
- `astra-sim-alibabacloud/astra-sim/network_frontend/ns3/common.h` - Added `CalculateUBMeshRoute()` function for direct GPU routing, UB mesh topology detection, and routing path debug functionality
- `ns-3-alibabacloud/simulation/src/point-to-point/model/rdma-hw.h` - Added UB mesh enable flag and method declarations
- `ns-3-alibabacloud/simulation/src/point-to-point/model/rdma-hw.cc` - Implemented UB mesh topology enable/disable methods and routing logic

**System Integration:**
- `astra-sim-alibabacloud/astra-sim/system/MockNcclGroup.h` - Added static UB mesh flag to skip NVSwitch grouping
- `astra-sim-alibabacloud/astra-sim/system/MockNcclGroup.cc` - Implemented UB mesh-aware constructor logic
- `astra-sim-alibabacloud/astra-sim/system/Sys.cc` - Added UB mesh topology detection and configuration

**Application Entry:**
- `astra-sim-alibabacloud/astra-sim/network_frontend/ns3/AstraSimNetwork.cc` - Integrated UB mesh enablement with system initialization

### Key Technical Implementation Details:

#### 1. UB Mesh Topology Detection (common.h)
```cpp
// Automatic UB mesh detection based on topology characteristics
bool is_ub_mesh = (nvswitch_num == 0 && link_num > node_num * 2);
is_ub_mesh_topology = is_ub_mesh;
if (is_ub_mesh) {
    std::cout << "[UB_MESH_DEBUG] Detected UB mesh topology with " << switch_num 
              << " inter-rack switches and " << link_num << " mesh links" << std::endl;
}
```

#### 2. Enhanced UB Mesh Routing Algorithm (common.h)
```cpp
void CalculateUBMeshRoute(Ptr<Node> host, NodeContainer &n) {
    // BFS-based routing with GPU-to-GPU path preference
    for (auto it = nbr2if[now].begin(); it != nbr2if[now].end(); it++) {
        // Prefer direct GPU-to-GPU paths over switch paths
        bool current_via_switch = false;
        bool new_via_switch = (now->GetNodeType() == 1);
        
        // If current path uses switches but new path is direct, replace it
        if (current_via_switch && !new_via_switch) {
            nextHop[next][host].clear();
            nextHop[next][host].push_back(now);
        }
    }
}
```

#### 3. Bandwidth Efficiency Modeling (common.h)
```cpp
// Apply UB mesh bandwidth modeling for collective communication
if (host_server != target_server) {
    // Inter-rack: bandwidth reduced due to switch contention
    effective_bw = effective_bw / 4; // 25% due to inter-rack contention
} else {
    // Intra-rack: high efficiency for direct GPU connections
    effective_bw = effective_bw * 0.9; // 90% efficiency for intra-rack
}
```

#### 4. UB Mesh Integration (AstraSimNetwork.cc)
```cpp
// Enable UB mesh topology for RDMA hardware
Ptr<RdmaDriver> rdma = n.Get(i)->GetObject<RdmaDriver>();
rdma->enable_ub_mesh_topology();

// System-level UB mesh configuration
if (enable_ub_mesh) {
    MockNccl::MockNcclGroup::enable_ub_mesh = true;
    std::cout << "[UB_MESH] UB mesh topology enabled for enhanced GPU-to-GPU routing" << std::endl;
}
```

#### 5. Debug Path Tracing (common.h)
```cpp
void PrintPathDebug() {
    for (auto i = nextHop.begin(); i != nextHop.end(); i++) {
        // Trace complete routing paths
        vector<uint32_t> path;
        Ptr<Node> current = src;
        path.push_back(current->GetId());
        
        while (current->GetId() != dst->GetId()) {
            current = nextHop[current][dst][0]; // Take first next hop
            path.push_back(current->GetId());
        }
        
        std::cout << "[PATH_DEBUG] Host " << src->GetId() << " -> Host " << dst->GetId() 
                  << " (hops: " << (path.size() - 1) << ") Path: ";
        for (size_t p = 0; p < path.size(); p++) {
            std::cout << path[p];
            if (p < path.size() - 1) std::cout << " -> ";
        }
    }
}
```

#### 6. RDMA Hardware UB Mesh Support (rdma-hw.h/cc)
```cpp
// Header declaration
class RdmaHw {
    uint32_t enable_ub_mesh;  // Per-instance UB mesh flag
    void enable_ub_mesh_topology();
    void disable_ub_mesh_topology();
};

// Implementation
void RdmaHw::enable_ub_mesh_topology() {
    enable_ub_mesh = 1;
    std::cout << "[RDMA_UB_MESH] UB mesh topology enabled for direct GPU routing" << std::endl;
}
```

### Performance Impact Analysis:

**Routing Efficiency Improvements:**
- **Direct GPU Paths:** Eliminates unnecessary switch hops for intra-rack communication
- **Bandwidth Modeling:** Realistic efficiency factors (90% intra-rack vs 25% inter-rack)
- **Path Selection:** Prioritizes direct connections while maintaining switch fallback for inter-rack

**Measured Performance Gains:**
- **Overall Speedup:** 1.75x improvement in total simulation time
- **Communication Speedup:** 21.7x improvement in communication latency
- **Switch Utilization:** Reduced bottlenecks by bypassing switches for intra-rack traffic

**Algorithm Features:**
- Prefers direct GPU-to-GPU paths over switch-based routing
- Applies bandwidth efficiency modeling (90% intra-rack, 25% inter-rack)
- Automatically detects UB mesh topology (nvswitch_num=0, high link density)
- Supports debug path tracing with `PrintPathDebug()` function





## Simulation Result files and location
```bash 
# workload files:

  # 32 Gpus simulation workload file, communicat# My Understanding:
./workload/None-None-world_size32-tp2-pp1-ep16-gbs64-mbs1-seq4096-MOE-True-GEMM-True-flash_attn-False.txt


# 128 gpus simulation workload file
./workload/G13B-M1-C02_GPT13B_megatron_tp8_pp1_mbs1_sp_A100.txt



# Fat tree 32gpus topolgy, simulation detailed information, log file

  # topolgy:

      fat_tree_server_32g_New

  # Simulation detailed information

    FatTree_32_final_ncclFlowModel_EndToEnd.csv

  # Simulation log file

    FatTree_32_final_output.log



# Fat tree 128gpus topolgy, simulation detailed information, log file

  # topolgy:

      fat_tree_server_128g_8gps_nvs16_k4_400Gbps_H100

  # Simulation detailed information

    fatTree_128_final_End_to _end.csv

  # Simulation log file

    FatTree_128_TP2_output.log





# UB Mesh 32gpus topolgy, simulation detailed information, log file

  # topolgy:

      UB_32_new

  # Simulation detailed information

    UB_32_final_ncclFlowModel_EndToEnd.csv

  # Simulation log file

    UB_32_latest_final_output.log




# UB Mesh 128gpus topolgy, simulation detailed information, log file

  # topolgy:

      UB_Mesh_128g_8gps_LRS16_H100

  # Simulation detailed information

      UB_128_latest_final_ncclFlowModel_EndToEnd.csv

  # Simulation log file

      UB_128_latest_01_output.log
  

```












# Quick Start

Here are some simple examples, SimAI full tutorials can be found here: [**SimAI@Tutorial**](./docs/Tutorial.md), [**aicb@Tutorial**](https://github.com/aliyun/aicb/blob/master/training/tutorial.md), [SimCCL@Tutorial], [ns-3-alibabacloud@Tutorial]

## Setup

You can follow the instrucitons below to quickly set up the environtments and run SimAI

### From Source Code

The following code has been successfully tested on GCC/G++ 9.4.0, python 3.8.10 in Ubuntu 20.04

You can use the official Ubuntu 20.04 image, and do not install ninja.

(For generation workloads, it's recommended to leverage NGC container images directly.)

```bash
# Clone the repository
$ git clone https://github.com/aliyun/SimAI.git
$ cd ./SimAI/

# Clone submodules
$ git submodule update --init --recursive
# Make sure use the newest commit
$ git submodule update --remote

# Compile SimAI-Analytical
$ ./scripts/build.sh -c analytical

# Compile SimAI-Simulation (ns3)
$ ./scripts/build.sh -c ns3

```

## Use SimAI-Analytical

```bash
$  ./bin/SimAI_analytical -w example/workload_analytical.txt -g 9216 -g_p_s 8 -r test- -busbw example/busbw.yaml
```

For calculating bus bandwidth autolly, please try the following command:
```bash
$  ./bin/SimAI_analytical -w ./example/workload_analytical.txt -g 9216  -nv 360 -nic 48.5 -n_p_s 8 -g_p_s 8 -r example-
```

## Use SimAI-Simulation

```bash
# Create network topo
$ python3 ./astra-sim-alibabacloud/inputs/topo/gen_Topo_Template.py -topo Spectrum-X -g 128 -gt A100 -bw 100Gbps -nvbw 2400Gbps

# Running
$ AS_SEND_LAT=3 AS_NVLS_ENABLE=1 ./bin/SimAI_simulator -t 16 -w ./example/microAllReduce.txt -n ./Spectrum-X_128g_8gps_100Gbps_A100 -c astra-sim-alibabacloud/inputs/config/SimAI.conf

```

# Contact us

Please email Gang Lu (yunding.lg@alibaba-inc.com) or Qingxu Li (qingxu.lqx@alibaba-inc.com) if you have any questions.

Welcome to join the SimAI community chat groups, with the DingTalk group on the left and the WeChat group on the right.

<div style="display: flex; justify-content: flex-start; align-items: center; gap: 20px; margin-left: 20px;">
    <img src="./docs/images/simai_dingtalk.jpg" alt="SimAI DingTalk" style="width: 300px; height: auto;">
    <img src="./docs/images/simai_wechat.jpg" alt="SimAI WeChat" style="width: 300px; height: auto;">
</div>

<br/>
