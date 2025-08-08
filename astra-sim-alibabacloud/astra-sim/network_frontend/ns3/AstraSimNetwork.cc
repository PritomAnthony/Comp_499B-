/* 
*Copyright (c) 2024, Alibaba Group;
*Licensed under the Apache License, Version 2.0 (the "License");
*you may not use this file except in compliance with the License.
*You may obtain a copy of the License at

*   http://www.apache.org/licenses/LICENSE-2.0

*Unless required by applicable law or agreed to in writing, software
*distributed under the License is distributed on an "AS IS" BASIS,
*WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*See the License for the specific language governing permissions and
*limitations under the License.
*/

#include "astra-sim/system/AstraNetworkAPI.hh"
#include "astra-sim/system/Sys.hh"
#include "astra-sim/system/RecvPacketEventHadndlerData.hh"
#include "astra-sim/system/Common.hh"
#include "astra-sim/system/MockNcclLog.h"
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/csma-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "entry.h"
#include <execinfo.h>
#include <fstream>
#include <iostream>
#include <queue>
#include <stdio.h>
#include <string>
#include <thread>
#include <unistd.h>
#include <vector>
#ifdef NS3_MTP
#include "ns3/mtp-interface.h"
#endif
#ifdef NS3_MPI
#include "ns3/mpi-interface.h"
#include <mpi.h>
#endif

#define RESULT_PATH "./ncclFlowModel_"

using namespace std;
using namespace ns3;

extern std::map<std::pair<std::pair<int, int>,int>, AstraSim::ncclFlowTag> receiver_pending_queue;
extern uint32_t node_num, switch_num, link_num, trace_num, nvswitch_num, gpus_per_server;
extern GPUType gpu_type;
extern std::vector<int>NVswitchs;

struct sim_event {
  void *buffer;
  uint64_t count;
  int type;
  int dst;
  int tag;
  string fnType;
};

class ASTRASimNetwork : public AstraSim::AstraNetworkAPI {
private:
  int npu_offset;

public:
  queue<sim_event> sim_event_queue;
  ASTRASimNetwork(int rank, int npu_offset) : AstraNetworkAPI(rank) {
    this->npu_offset = npu_offset;
  }
  ~ASTRASimNetwork() {}
  int sim_comm_size(AstraSim::sim_comm comm, int *size) { return 0; }
  int sim_finish() {
    std::cout << "Debug: Entering sim_finish()" << std::endl;
    for (auto it = nodeHash.begin(); it != nodeHash.end(); it++) {
      pair<int, int> p = it->first;
      if (p.second == 0) {
        std::cout << "sim_finish on sent, " << " Thread id: " << pthread_self() << std::endl;
        cout << "All data sent from node " << p.first << " is " << it->second
             << "\n";
      } else {
        std::cout << "sim_finish on received, " << " Thread id: " << pthread_self() << std::endl;
        cout << "All data received by node " << p.first << " is " << it->second
             << "\n";
      }
    }
    std::cout << "Debug: Completed processing in sim_finish(), about to exit" << std::endl;
    exit(0);
    return 0;
  }
  double sim_time_resolution() { return 1e-9; }  // 1 nanosecond resolution
  int sim_init(AstraSim::AstraMemoryAPI *MEM) { return 0; }
  AstraSim::timespec_t sim_get_time() {
    AstraSim::timespec_t timeSpec;
    timeSpec.time_val = Simulator::Now().GetNanoSeconds();
    return timeSpec;
  }
  virtual void sim_schedule(AstraSim::timespec_t delta,
                            void (*fun_ptr)(void *fun_arg), void *fun_arg) {
    task1 t;
    t.type = 2;
    t.fun_arg = fun_arg;
    t.msg_handler = fun_ptr;
    t.schTime = delta.time_val;
    Simulator::Schedule(NanoSeconds(t.schTime), t.msg_handler, t.fun_arg);
    return;
  }
  virtual int sim_send(void *buffer,   
                       uint64_t count, 
                       int type,       
                       int dst,
                       int tag,                       
                       AstraSim::sim_request *request, 
                       void (*msg_handler)(void *fun_arg), void *fun_arg) {
    dst += npu_offset;
    task1 t;
    t.src = rank;
    t.dest = dst;
    t.count = count;
    t.type = 0;
    t.fun_arg = fun_arg;
    t.msg_handler = msg_handler;
    {
      #ifdef NS3_MTP
      MtpInterface::explicitCriticalSection cs;
      #endif
      sentHash[make_pair(tag, make_pair(t.src, t.dest))] = t;
      #ifdef NS3_MTP
      cs.ExitSection();
      #endif
    }
    SendFlow(rank, dst, count, msg_handler, fun_arg, tag, request);
    return 0;
  }
  virtual int sim_recv(void *buffer, uint64_t count, int type, int src, int tag,
                       AstraSim::sim_request *request,
                       void (*msg_handler)(void *fun_arg), void *fun_arg) {
    #ifdef NS3_MTP
    MtpInterface::explicitCriticalSection cs;
    #endif
    MockNcclLog* NcclLog = MockNcclLog::getInstance();
    AstraSim::ncclFlowTag flowTag = request->flowTag;
    src += npu_offset;
    task1 t;
    t.src = src;
    t.dest = rank;
    t.count = count;
    t.type = 1;
    t.fun_arg = fun_arg;
    t.msg_handler = msg_handler;
    AstraSim::RecvPacketEventHadndlerData* ehd = (AstraSim::RecvPacketEventHadndlerData*) t.fun_arg;
    AstraSim::EventType event = ehd->event;
    tag = ehd->flowTag.tag_id;
    NcclLog->writeLog(NcclLogLevel::DEBUG,"[Receive event registration] src %d sim_recv on rank %d tag_id %d channdl id %d",src,rank,tag,ehd->flowTag.channel_id);
    
    if (recvHash.find(make_pair(tag, make_pair(t.src, t.dest))) !=
        recvHash.end()) {
      uint64_t count = recvHash[make_pair(tag, make_pair(t.src, t.dest))];
      if (count == t.count) {
        recvHash.erase(make_pair(tag, make_pair(t.src, t.dest)));
        assert(ehd->flowTag.child_flow_id == -1 && ehd->flowTag.current_flow_id == -1);
        if(receiver_pending_queue.count(std::make_pair(std::make_pair(rank, src),tag))!= 0) {
          AstraSim::ncclFlowTag pending_tag = receiver_pending_queue[std::make_pair(std::make_pair(rank, src),tag)];
          receiver_pending_queue.erase(std::make_pair(std::make_pair(rank,src),tag));
          ehd->flowTag = pending_tag;
        } 
        #ifdef NS3_MTP
        cs.ExitSection();
        #endif
        t.msg_handler(t.fun_arg);
        goto sim_recv_end_section;
      } else if (count > t.count) {
        recvHash[make_pair(tag, make_pair(t.src, t.dest))] = count - t.count;
        assert(ehd->flowTag.child_flow_id == -1 && ehd->flowTag.current_flow_id == -1);
        if(receiver_pending_queue.count(std::make_pair(std::make_pair(rank, src),tag))!= 0) {
          AstraSim::ncclFlowTag pending_tag = receiver_pending_queue[std::make_pair(std::make_pair(rank, src),tag)];
          receiver_pending_queue.erase(std::make_pair(std::make_pair(rank,src),tag));
          ehd->flowTag = pending_tag;
        } 
        #ifdef NS3_MTP
        cs.ExitSection();
        #endif
        t.msg_handler(t.fun_arg);
        goto sim_recv_end_section;
      } else {
        recvHash.erase(make_pair(tag, make_pair(t.src, t.dest)));
        t.count -= count;
        expeRecvHash[make_pair(tag, make_pair(t.src, t.dest))] = t;
      }
    } else {
      if (expeRecvHash.find(make_pair(tag, make_pair(t.src, t.dest))) ==
          expeRecvHash.end()) {
        expeRecvHash[make_pair(tag, make_pair(t.src, t.dest))] = t;
          NcclLog->writeLog(NcclLogLevel::DEBUG," [Packet arrived late, registering first] recvHash do not find expeRecvHash.new make src  %d dest  %d t.count:  %llu channel_id  %d current_flow_id  %d",t.src,t.dest,t.count,tag,flowTag.current_flow_id);
          
      } else {
        uint64_t expecount =
            expeRecvHash[make_pair(tag, make_pair(t.src, t.dest))].count;
          NcclLog->writeLog(NcclLogLevel::DEBUG," [Packet arrived late, re-registering] recvHash do not find expeRecvHash.add make src  %d dest  %d expecount:  %d t.count:  %d tag_id  %d current_flow_id  %d",t.src,t.dest,expecount,t.count,tag,flowTag.current_flow_id);
          
      }
    }
    #ifdef NS3_MTP
    cs.ExitSection();
    #endif

sim_recv_end_section:    
    return 0;
  }
  void handleEvent(int dst, int cnt) {
  }

  // Add validation for CSV data before writing
  bool validateCSVData() {
    for (auto it = nodeHash.begin(); it != nodeHash.end(); it++) {
      if (it->first.first < 0 || it->second < 0) {
        std::cout << "Invalid data detected in nodeHash" << std::endl;
        return false;
      }
    }
    return true;
  }
};

struct user_param {
  int thread;
  string workload;
  string network_topo;
  string network_conf;
  user_param() {
    thread = 1;
    workload = "";
    network_topo = "";
    network_conf = "";
  };
  ~user_param(){};
};

static int user_param_prase(int argc,char * argv[],struct user_param* user_param){
  int opt;
  while ((opt = getopt(argc,argv,"ht:w:g:s:n:c:"))!=-1){
    switch (opt)
    {
    case 'h':
      /* code */
      std::cout<<"-t    number of threads,default 1"<<std::endl;
      std::cout<<"-w    workloads default none "<<std::endl;
      std::cout<<"-n    network topo"<<std::endl;
      std::cout<<"-c    network_conf"<<std::endl;
      return 1;
      break;
    case 't':
      user_param->thread = stoi(optarg);
      break;
    case 'w':
      user_param->workload = optarg;
      break;
    case 'n':
      user_param->network_topo = optarg;
      break;
    case 'c':
      user_param->network_conf = optarg;
      break;
    default:
      std::cerr<<"-h    help message"<<std::endl;
      return 1;
    }
  }
  return 0 ;
}

int main(int argc, char *argv[]) {
  struct user_param user_param;
  MockNcclLog::set_log_name("SimAI.log");
  MockNcclLog* NcclLog = MockNcclLog::getInstance();
  NcclLog->writeLog(NcclLogLevel::INFO," init SimAI.log ");
  if(user_param_prase(argc,argv,&user_param)){
    return 0;
  }
  #ifdef NS3_MTP
  MtpInterface::Enable(user_param.thread);
  #endif
  
  main1(user_param.network_topo,user_param.network_conf);
  int nodes_num = node_num - switch_num;
  int gpu_num = node_num - nvswitch_num - switch_num;

  std::map<int, int> node2nvswitch;
  std::map<int, std::vector<int>> tp_groups;
  
  // Setup topology for tensor parallel groups
  for(int i = 0; i < gpu_num; ++i) {
    int group_id = i / 2;  // Group ID for tensor parallelism
    node2nvswitch[i] = group_id;  // Map each GPU to its group
    
    // Add GPU to its tensor parallel group
    if (tp_groups.find(group_id) == tp_groups.end()) {
      tp_groups[group_id] = std::vector<int>();
    }
    tp_groups[group_id].push_back(i);
    
    // Create virtual switches for each tensor parallel group
    if (i % 2 == 0) {
      int switch_id = gpu_num + group_id;
      NVswitchs.push_back(switch_id);
    }
  }
  
  // Configure cross-group communication paths
  for (auto& group : tp_groups) {
    int group_id = group.first;
    auto& gpus = group.second;
    
    // Ensure all GPUs in the group can communicate
    for (int i = 0; i < gpus.size(); i++) {
      for (int j = i + 1; j < gpus.size(); j++) {
        // Set up bidirectional communication
        int gpu1 = gpus[i];
        int gpu2 = gpus[j];
        node2nvswitch[gpu1] = group_id;
        node2nvswitch[gpu2] = group_id;
      }
    }
  }

  LogComponentEnable("OnOffApplication", LOG_LEVEL_INFO);
  LogComponentEnable("PacketSink", LOG_LEVEL_INFO);
  LogComponentEnable("GENERIC_SIMULATION", LOG_LEVEL_INFO);

  std::vector<ASTRASimNetwork *> networks(nodes_num, nullptr);
  std::vector<AstraSim::Sys *> systems(nodes_num, nullptr);

  // Enable UB mesh topology with proper switch handling
  // Enable UB mesh topology routing 
  RdmaHw::enable_ub_mesh = true;
  
  // Create virtual switches for UB mesh topology
  std::vector<int> virtual_switches;
  for (int i = 0; i < gpu_num; i++) {
    virtual_switches.push_back(gpu_num + i);  // Virtual switches start after GPUs
  }
  
  for (int j = 0; j < nodes_num; j++) {
    networks[j] = new ASTRASimNetwork(j, 0);
    
    // Calculate the group ID for this node
    int group_id = j / 2;
    int group_size = 2;  // Size of tensor parallel groups
    
    systems[j] = new AstraSim::Sys(
        networks[j],
        nullptr,
        j,
        group_id,  // Pass group_id for tensor parallel awareness
        1,
        {group_size},  // Tensor parallel size is 2 (tp2)
        {gpu_num/group_size},  // Number of TP groups
        "",
        user_param.workload,
        1,
        1,
        1,
        1,
        0,
        RESULT_PATH,
        "test1",
        true,
        enable_ub_mesh,
        gpu_type,
        {gpu_num},  // Total number of GPUs
        NVswitchs,  // Virtual switches for TP groups
        gpu_num
    );
    
    // Set up routing information
    systems[j]->nvswitch_id = node2nvswitch[j];
    systems[j]->num_gpus = gpu_num;
    
    // UB mesh specific parameters are handled through topology configuration
    if (enable_ub_mesh) {
        // The topology file and virtual switches handle the mesh configuration
        NcclLog->writeLog(NcclLogLevel::INFO, "Setting up UB mesh configuration for node %d in group %d", j, group_id);
    }
  }
  std::cout << "Debug: Before firing workloads" << std::endl;
  for (int i = 0; i < nodes_num; i++) {
    std::cout << "Debug: Firing workload for system " << i << std::endl;
    systems[i]->workload->fire();
  }
  std::cout << "Debug: All workloads fired, starting simulator" << std::endl;

  Simulator::Run();
  std::cout << "Debug: Simulator::Run() completed" << std::endl;
  
  Simulator::Stop(Seconds(2000000000));
  std::cout << "Debug: Simulator stopped" << std::endl;
  
  Simulator::Destroy();
  std::cout << "Debug: Simulator destroyed" << std::endl;
  
  #ifdef NS3_MPI
  MpiInterface::Disable ();
  #endif
  return 0;
}