#!/usr/bin/env python3
"""
Test script to generate workload that forces inter-server communication
"""

def generate_inter_server_workload():
    """Generate a workload file that forces communication between servers"""
    num_servers = 8
    gpus_per_server = 8
    total_gpus = num_servers * gpus_per_server
    
    workload_lines = []
    workload_lines.append("# Inter-server communication test workload")
    workload_lines.append(f"# {num_servers} servers, {gpus_per_server} GPUs per server")
    workload_lines.append("")
    
    # Layer 1: All-to-All between server representatives
    workload_lines.append("# Layer 1: Inter-server All-to-All (server representatives)")
    layer_id = 1
    data_size = 1024 * 1024 * 100  # 100MB per communication
    
    # Each server's first GPU communicates with all other servers' first GPUs
    for src_server in range(num_servers):
        for dst_server in range(num_servers):
            if src_server != dst_server:
                src_gpu = src_server * gpus_per_server  # First GPU of source server
                dst_gpu = dst_server * gpus_per_server  # First GPU of destination server
                workload_lines.append(f"{layer_id} {src_gpu} {dst_gpu} {data_size} ALL_REDUCE")
    
    # Layer 2: Ring across servers (node 0 -> node 8 -> node 16 -> ... -> node 56 -> node 0)
    workload_lines.append("")
    workload_lines.append("# Layer 2: Cross-server ring communication")
    layer_id = 2
    for i in range(num_servers):
        src_gpu = i * gpus_per_server
        dst_gpu = ((i + 1) % num_servers) * gpus_per_server
        workload_lines.append(f"{layer_id} {src_gpu} {dst_gpu} {data_size} ALL_REDUCE")
    
    # Layer 3: Butterfly pattern across servers
    workload_lines.append("")
    workload_lines.append("# Layer 3: Butterfly pattern across servers")
    layer_id = 3
    for distance in [1, 2, 4]:  # Powers of 2 for butterfly
        for src_server in range(num_servers):
            dst_server = src_server ^ distance  # XOR for butterfly pattern
            if dst_server < num_servers:
                src_gpu = src_server * gpus_per_server
                dst_gpu = dst_server * gpus_per_server
                workload_lines.append(f"{layer_id} {src_gpu} {dst_gpu} {data_size} ALL_REDUCE")
    
    return "\n".join(workload_lines)

def generate_simple_ping_test():
    """Generate a simple ping test between adjacent servers"""
    workload_lines = []
    workload_lines.append("# Simple ping test between adjacent servers")
    
    # Test communication between server 0 and server 1
    layer_id = 1
    data_size = 1024 * 1024  # 1MB
    
    # Node 0 (server 0) -> Node 8 (server 1)
    workload_lines.append(f"{layer_id} 0 8 {data_size} ALL_REDUCE")
    # Node 8 (server 1) -> Node 0 (server 0)  
    workload_lines.append(f"{layer_id} 8 0 {data_size} ALL_REDUCE")
    
    return "\n".join(workload_lines)

if __name__ == "__main__":
    print("=== Inter-Server Communication Test Workloads ===")
    print("\n1. Full Inter-Server Workload:")
    print(generate_inter_server_workload())
    
    print("\n\n2. Simple Ping Test:")
    print(generate_simple_ping_test())
    
    # Save the workloads to files
    with open("/home/parozario/newSimAI/Comp_499B-/inter_server_workload.txt", "w") as f:
        f.write(generate_inter_server_workload())
    
    with open("/home/parozario/newSimAI/Comp_499B-/ping_test_workload.txt", "w") as f:
        f.write(generate_simple_ping_test())
    
    print("\n\nWorkload files saved:")
    print("- inter_server_workload.txt")
    print("- ping_test_workload.txt")
