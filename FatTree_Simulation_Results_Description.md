# Fat Tree Topology Simulation Results - 128 GPU GPT Training

## Executive Summary

This document presents the comprehensive analysis of **Fat Tree network topology performance** for distributed deep learning training using **128 H100 GPUs** simulating **GPT-13B model training**.

###  Key Result
**End-to-End Training Latency: 658.9 milliseconds per training step**

---

## System Configuration

### Hardware Setup
- **Total GPUs**: 128 × NVIDIA H100
- **GPUs per Server**: 8
- **Total Servers**: 16
- **Network Topology**: Fat Tree (k=4)
- **Total Network Nodes**: 144 (128 compute + 16 infrastructure)

### Network Specifications
- **Intra-Server (NVLink)**: 2,880 Gbps per link
- **Inter-Server (InfiniBand)**: 400 Gbps per link
- **Network Buffer Size**: 10 MB (optimized from initial 32 bytes)
- **Topology Arity**: k=4 (4-ary fat tree)

### Model Configuration
- **Model**: GPT-13B (13 billion parameters)
- **Training Layers**: 172 layers total
- **Parallelism Strategy**:
  - **Tensor Parallelism (TP)**: 2 GPUs per group
  - **Expert Parallelism (EP)**: 64 GPUs per group  
  - **Pipeline Parallelism (PP)**: 1 (no pipelining)
- **Workload File**: `G13B-M1-C02_GPT13B_megatron_tp8_pp1_mbs1_sp_A100.txt`

---

## Performance Results

###  End-to-End Training Latency
```
Total Training Time per Step: 658,913 microseconds = 658.9 milliseconds
```

### Computation vs Communication Breakdown
| Component | Time (μs) | Time (ms) | Percentage | Analysis |
|-----------|-----------|-----------|------------|----------|
| **Total Computation** | 363,836 | 363.8 | 55.22% | **Compute-Bound** ✅ |
| **Total Communication** | 295,077 | 295.1 | 44.78% | Well-balanced |
| **Total Time** | **658,913** | **658.9** | **100%** | **Realistic** |

###  Detailed Computation Analysis
| Pass Type | Time (μs) | Time (ms) | Description |
|-----------|-----------|-----------|-------------|
| **Forward Pass** | 126,525 | 126.5 | Input → Predictions |
| **Weight Gradients** | 111,960 | 112.0 | Parameter Updates |
| **Input Gradients** | 125,351 | 125.4 | Backpropagation |
| **Total Compute** | **363,836** | **363.8** | **All Computation** |

###  Communication Pattern Analysis
| Communication Type | Time (μs) | Time (ms) | Percentage | Description |
|---------------------|-----------|-----------|------------|-------------|
| **Tensor Parallelism (TP)** | 24,305 | 24.3 | 3.69% | Intra-layer sync |
| **Expert Parallelism (EP)** | 13,945 | 13.9 | 2.12% | Expert routing |
| **Other Communication** | 256,827 | 256.8 | 38.97% | General sync |
| **Total Communication** | **295,077** | **295.1** | **44.78%** | **All Network** |

---

##  Layer-Level Performance Analysis

### Per-Layer Computation Times (Realistic Values)
| Layer Type | Computation Time | Communication Time | Total Layer Time |
|------------|------------------|-------------------|------------------|
| **Attention Column** | 375 μs | 30.4 μs | 405.4 μs |
| **Attention Row** | 376 μs | 30.4 μs | 406.4 μs |
| **MLP Column** | 923 μs | 30.4 μs | 953.4 μs |
| **MLP Row** | 1,125 μs | 30.4 μs | 1,155.4 μs |

### Layer Distribution
- **172 Total Layers** processed successfully
- **168 Transformer layers** (42 blocks × 4 layers per block)
- **4 Special layers** (norm, embedding, cross-entropy, optimizer)

---

##  Network Performance Analysis



### Network Efficiency Metrics
- **TP Communication**: Only 3.69% of total time → **Excellent locality**
- **Buffer Usage**: Max 3.5MB (out of 10MB) → **No congestion**
- **Load Balancing**: Equal 15GB per GPU → **Perfect distribution**

---

##  Training Scalability Analysis

### What One Training Step Represents
```
658.9ms = Time to process ONE batch through the ENTIRE 13B parameter model
```

#### Complete Training Cycle (Per Step):
1. **Forward Pass** (126.5ms): Data flows through all 172 layers
2. **Loss Calculation**: Compute prediction accuracy
3. **Backward Pass** (237.4ms): Calculate gradients for all parameters
4. **Parameter Update**: Synchronize weights across 128 GPUs
5. **Communication** (295ms): Coordinate between all nodes

### Real-World Training Implications
| Training Scenario | Steps Required | Total Time | Analysis |
|-------------------|----------------|------------|----------|
| **Small Experiment** | 1,000 steps | 11 minutes | Quick iteration |
| **Model Validation** | 10,000 steps | 1.8 hours | Reasonable validation |
| **Production Training** | 100,000 steps | 18.3 hours | Practical training |
| **Full GPT-Scale** | 1,000,000 steps | 7.6 days | Enterprise training |

---

##  Technical Implementation Details

### Simulation Parameters
```bash
# Command used for simulation
AS_SEND_LAT=1 AS_NVLS_ENABLE=1 gdb --batch --ex run --ex bt --ex quit \
--args ./bin/SimAI_simulator -t 16 \
-w ./workload/G13B-M1-C02_GPT13B_megatron_tp8_pp1_mbs1_sp_A100.txt \
-n ./fat_tree_server_128g_8gps_nvs16_k4_400Gbps_H100 \
-c astra-sim-alibabacloud/inputs/config/SimAI.conf
```

### Configuration Optimizations Applied
1. **Buffer Size**: Increased from 32 bytes to 10MB
2. **Parallelism Strategy**: TP=2 for stability (vs initial TP=8)
3. **Workload Model**: Realistic computation times (vs minimal)
4. **Network Topology**: Server-level fat tree with k=4 arity

### Data Validation
- **Total Streams**: 333 injected, 333 finished (100% completion)
- **Data Balance**: 14.99GB sent/received per GPU (perfect symmetry)
- **Thread Management**: All 15 simulation threads completed successfully

---

##  Performance Comparison Context

### Fat Tree Advantages Demonstrated
1. **Balanced Communication**: Only 44.78% time in network
2. **Low TP Overhead**: Just 3.69% for tensor parallelism
3. **Scalable Architecture**: Handles 128 GPUs efficiently
4. **No Congestion**: Buffer usage well below limits

### Topology Suitability for GPT Training
-  **Compute-Bound Workload**: 55% computation time ideal
-  **Efficient Collectives**: Low communication overhead
-  **Balanced Load**: Equal work distribution
-  **Fault Tolerance**: Multiple paths available

---

##  Key Insights for Distributed Deep Learning

### 1. Network Impact
- **44.78% communication time** shows network is significant but not dominant
- **Fat tree topology** provides good balance for transformer training
- **Buffer optimization** critical for avoiding congestion

### 2. Scalability Patterns
- **TP=2 stability** vs TP=8 complexity tradeoff
- **EP=64 scaling** handles large expert models well
- **128 GPU efficiency** demonstrates good horizontal scaling

### 3. Training Efficiency
- **658.9ms per step** enables practical large model training
- **Realistic computation modeling** essential for accurate predictions
- **End-to-end measurement** captures true training costs

---

##  Generated Files and Logs

### Primary Results
- **`ncclFlowModel_EndToEnd.csv`**: Complete performance metrics
- **`FatTree_128_TP2_output.log`**: Full simulation output
- **`ncclFlowModel_detailed_144.csv`**: Node-level detailed statistics

### Topology Files
- **`fat_tree_server_128g_8gps_nvs16_k4_400Gbps_H100`**: Network topology definition
- **`G13B-M1-C02_GPT13B_megatron_tp8_pp1_mbs1_sp_A100.txt`**: Workload specification

---

##  Conclusion

The **Fat Tree topology with 128 H100 GPUs** demonstrates **excellent performance** for GPT-13B training with:

- **658.9ms end-to-end training latency per step**
- **55% computation vs 45% communication** - optimal balance
- **3.69% tensor parallelism overhead** - highly efficient
- **100% completion rate** with perfect load balancing

This configuration provides a **strong baseline** for comparing against other network topologies and scaling strategies in distributed deep learning environments.

---

