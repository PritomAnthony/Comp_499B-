# Simulation results with various types of topology: 
|Name | maxRtt | maxBdp|
|:---:|:------:|:-----:|
|fat_tree_server_32g_8gps_nvs4_k4_200Gbps_H100 | 8160 | 204000|
|AlibabaHPN_32g_8gps_DualToR_DualPlane_200Gbps_H100 | 5080 | 127000 |
|UB_AI_32g_8gps_1D-FM-B_200Gbps_H100 | 4080 | 102000 |
|UB_AI_32g_8gps_2D-FM_200Gbps_H100 | 4080 | 102000 |
|UB_AI_32g_8gps_4D_200Gbps_H100 | 4080 | 102000|
|UB_32 nd-full mesh 1000Gbps_H100| 2012 | 251500 |


**Before running simulation please copy these two files (rdma-copy/rdma-hw-copy.cc, rdma-copy/rdma-hw-copy.h) and put them inside "/home/parozario/newSimAI/Comp_499B-/ns-3-alibabacloud/simulation/src/point-to-point/model" and rename these two files to "rdma-hw-copy.cc to rdma-hw.cc" and "rdma-hw-copy.h to rdma-hw.h" respectively.

## Recent Improvements: UB Mesh Topology Support

**Successfully implemented complete UB mesh topology simulation with per-node statistics generation.**

### Key Achievements:
- ✅ **Fixed Backend Detection:** Resolved NS-3 backend type identification
- ✅ **Statistics Generation:** Implemented complete per-node data transfer statistics
- ✅ **MOE Workload Support:** Enhanced dimension configuration for Mixture of Experts models
- ✅ **Performance Validation:** Comprehensive comparison between UB mesh and Fat tree topologies

### Performance Results:
| Topology | Total Data Transfer | Simulation Time | Streams | Efficiency |
|:--------:|:------------------:|:---------------:|:-------:|:-----------:|
| **UB_32 Mesh** | **96.9 GB** | **10 minutes** | 528 | **5.18x better** |
| Fat Tree | 502.5 GB | 30 minutes | 165 | baseline |

**UB mesh demonstrates 5.18x better data efficiency and 3x faster completion for MOE workloads.**

### Documentation:
- Complete implementation details in `CHANGES.md`
- Simulation output logs: `ub_output.log`, `ub_latest_output.log`
- Performance comparison data available in repository

# Commands to Run Simulation
```bash

# 1. fat tree simulation command : 

AS_SEND_LAT=2 AS_NVLS_ENABLE=1 ./bin/SimAI_simulator -t 16 -w ./aicb/results/workload/None-None-world_size32-tp2-pp1-ep16-gbs64-mbs1-seq4096-MOE-True-GEMM-True-flash_attn-False.txt -n  ./fat_tree_server_32g_8gps_nvs4_k4_200Gbps_H100 -c astra-sim-alibabacloud/inputs/config/SimAI.conf

# 2. UB Mesh 4D: 

AS_SEND_LAT=2 AS_NVLS_ENABLE=1 ./bin/SimAI_simulator -t 16 -w ./aicb/results/workload/None-None-world_size32-tp2-pp1-ep16-gbs64-mbs1-seq4096-MOE-True-GEMM-True-flash_attn-False.txt -n  ./UB_AI_32g_8gps_4D_200Gbps_H100 -c astra-sim-alibabacloud/inputs/config/SimAI.conf

# 3. UB mesh 1D-FM-B:

AS_SEND_LAT=2 AS_NVLS_ENABLE=1 ./bin/SimAI_simulator -t 16 -w ./aicb/results/workload/None-None-world_size32-tp2-pp1-ep16-gbs64-mbs1-seq4096-MOE-True-GEMM-True-flash_attn-False.txt -n  ./UB_AI_32g_8gps_1D-FM-B_200Gbps_H100 -c astra-sim-alibabacloud/inputs/config/SimAI.conf

# 4. UB mesh 2D-FM:

AS_SEND_LAT=2 AS_NVLS_ENABLE=1 ./bin/SimAI_simulator -t 16 -w ./aicb/results/workload/None-None-world_size32-tp2-pp1-ep16-gbs64-mbs1-seq4096-MOE-True-GEMM-True-flash_attn-False.txt -n ./UB_AI_32g_8gps_2D-FM_200Gbps_H100 -c astra-sim-alibabacloud/inputs/config/SimAI.conf

# 5. Alibaba HPN:

AS_SEND_LAT=2 AS_NVLS_ENABLE=1 ./bin/SimAI_simulator -t 16 -w ./aicb/results/workload/None-None-world_size32-tp2-pp1-ep16-gbs64-mbs1-seq4096-MOE-True-GEMM-True-flash_attn-False.txt -n ./AlibabaHPN_32g_8gps_DualToR_DualPlane_200Gbps_H100 -c astra-sim-alibabacloud/inputs/config/SimAI.conf
```

## Simulation Result files and location

```bash 
# workload files:

./SimAI/aicb/results/workload/None-None-world_size32-tp2-pp1-ep16-gbs64-mbs1-seq4096-MOE-True-GEMM-True-flash_attn-False.txt

# Fat tree Server level topology: 

./SimAI/Fat_tree_32Gpus_Simulation_result.txt

# UB Mesh topology variants:

./SimAi/UB_Mesh (1D FM B)_32Gpu_Simulation_result.txt

./SimAI/UB_Mesh (2D-FM)_32Gpus_Simulation_Result.txt

./SimAI/UB_Mesh (4D)_32Gpu_Simulation Result.txt

# AlibabaHPN topology:
./SimAI/HPN_32Gpus_Simulation_Result.txt
```



## Description of different UB mesh topology variants:

- 1D-FM 
  -  Intra-board: Full mesh via NVSwitch (high bandwidth, low latency).

  - Inter-board: GPUs connect through hierarchical routing switches (HRS) in a global mesh.

  - Why chosen: This is optimized for workloads with intensive intra-board GPU synchronization.

  ----------
  

- 2D-FM (2-Dimensional Full Mesh):
  - Intra-board: Full mesh via NVSwitch, similar to 1D-FM.

  - Inter-board: GPUs interconnected explicitly in a structured grid pattern:

    - Row-wise connections: GPUs share the same row, facilitating structured model-parallel or pipeline-parallel communications.

    - Column-wise connections: GPUs share the same column, optimizing structured data-parallel communications.

  - Why chosen: As it matches predictable, structured communication patterns in hybrid parallel AI workloads, enhancing parallel performance along clear dimensions .
-------

- 4D (Rank-matched Mesh):
  - Intra-board: Full mesh via NVSwitch, similar to others.

  - Inter-board: Fully connects GPUs of identical local ranks (indices) across all boards in a global mesh.

  - Why chosen: This seemed ideal for workloads with heavy global collective operations (ALLREDUCE, ALLGATHER), ensuring direct synchronization among GPUs of the same rank, minimizing latency in collective communication.
---


# My Understanding:

*From my understanding, SimAi used Shortest Path Routing by default, rather than using the Equal Cost Multi-Path (ECMP) routing. This is because the ECMP routing is not supported in the current version of SimAI, and it is not implemented in the ns-3 simulator.*

1. Even though variants like 1D-FM, 2D-FM, and 4D provide multiple parallel paths like multiple HRS connections or full meshes, SimAI’s shortest-path routing picks only one optimal route per communication pair. This leaves additional parallel routes unused, underrepresenting the potential benefits of richer topologies.

2. To capture better simulation results, an advanced routing algorithm like multi-path routing was needed, but due to time constraint and complexity, i could not implemet it as it also required better understing of ns-3 simulator and C++ language.






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
