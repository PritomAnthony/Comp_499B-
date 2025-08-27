#!/usr/bin/env python3
"""
Custom Fat Tree Generator for 64 GPUs
Creates a fat tree with specific switch configuration:
- 8 edge switches
- 4 aggregate switches  
- 2 core switches
- 8 NVSwitches (1 per server)
"""

def generate_custom_fat_tree_64():
    # Configuration
    G = 64  # Total GPUs
    G_P_S = 8  # GPUs per server
    servers = G // G_P_S  # 8 servers
    
    # Switch configuration
    nv_switch_num = 8  # 1 per server
    edge_switches = 8
    agg_switches = 4
    core_switches = 2
    
    # Node ID assignment
    # GPUs: 0-63
    # NVSwitches: 64-71
    # Edge switches: 72-79
    # Aggregate switches: 80-83
    # Core switches: 84-85
    
    nv_start = G
    nv_ids = list(range(nv_start, nv_start + nv_switch_num))
    
    edge_start = nv_start + nv_switch_num
    edge_ids = list(range(edge_start, edge_start + edge_switches))
    
    agg_start = edge_start + edge_switches
    agg_ids = list(range(agg_start, agg_start + agg_switches))
    
    core_start = agg_start + agg_switches
    core_ids = list(range(core_start, core_start + core_switches))
    
    links = []
    
    # 1) GPU -> NVSwitch connections (intra-server)
    for srv in range(servers):
        base_gpu = srv * G_P_S
        nv_switch = nv_ids[srv]
        for g in range(base_gpu, base_gpu + G_P_S):
            links.append((g, nv_switch, "2880Gbps", "0.000025ms", "0"))
    
    # 2) NVSwitch -> Edge switch connections
    # Each NVSwitch connects to corresponding edge switch
    for i, nv in enumerate(nv_ids):
        edge_sw = edge_ids[i % edge_switches]
        links.append((nv, edge_sw, "400Gbps", "0.0005ms", "0"))
    
    # 3) GPU -> Edge switch direct connections (NIC ports)
    # Each GPU also has a direct NIC connection to an edge switch
    for g in range(G):
        edge_sw = edge_ids[g % edge_switches]
        links.append((g, edge_sw, "400Gbps", "0.0005ms", "0"))
    
    # 4) Edge -> Aggregate connections
    # Each edge switch connects to 2 aggregate switches for redundancy
    for i, edge_sw in enumerate(edge_ids):
        # Connect to 2 aggregate switches
        agg1 = agg_ids[i % agg_switches]
        agg2 = agg_ids[(i + 1) % agg_switches]
        links.append((edge_sw, agg1, "400Gbps", "0.0005ms", "0"))
        links.append((edge_sw, agg2, "400Gbps", "0.0005ms", "0"))
    
    # 5) Aggregate -> Core connections
    # Each aggregate switch connects to all core switches
    for agg_sw in agg_ids:
        for core_sw in core_ids:
            links.append((agg_sw, core_sw, "400Gbps", "0.0005ms", "0"))
    
    # Calculate totals
    total_nodes = G + nv_switch_num + edge_switches + agg_switches + core_switches
    total_switches = nv_switch_num + edge_switches + agg_switches + core_switches
    fabric_switches = edge_switches + agg_switches + core_switches
    total_links = len(links)
    
    # Write topology file
    filename = "fat_tree_custom_64g_8e_4a_2c_H100"
    with open(filename, 'w') as f:
        # Header: total_nodes gpus_per_server nv_switches fabric_switches total_links gpu_type
        f.write(f"{total_nodes} {G_P_S} {nv_switch_num} {fabric_switches} {total_links} H100\n")
        
        # Switch IDs line: NVSwitches + Edge + Aggregate + Core
        all_switch_ids = nv_ids + edge_ids + agg_ids + core_ids
        f.write(' '.join(str(sw) for sw in all_switch_ids) + "\n")
        
        # Write all links
        for src, dst, bw, lat, err in links:
            f.write(f"{src} {dst} {bw} {lat} {err}\n")
    
    print(f"Generated custom fat tree topology: {filename}")
    print(f"Total nodes: {total_nodes}")
    print(f"  GPUs: {G}")
    print(f"  NVSwitches: {nv_switch_num}")
    print(f"  Edge switches: {edge_switches}")
    print(f"  Aggregate switches: {agg_switches}")
    print(f"  Core switches: {core_switches}")
    print(f"Total links: {total_links}")
    
    # Breakdown of links
    gpu_nv_links = servers * G_P_S  # 64
    nv_edge_links = nv_switch_num  # 8
    gpu_edge_links = G  # 64
    edge_agg_links = edge_switches * 2  # 16 (each edge to 2 agg)
    agg_core_links = agg_switches * core_switches  # 8
    
    print(f"\nLink breakdown:")
    print(f"  GPU -> NVSwitch: {gpu_nv_links}")
    print(f"  NVSwitch -> Edge: {nv_edge_links}")
    print(f"  GPU -> Edge (NIC): {gpu_edge_links}")
    print(f"  Edge -> Aggregate: {edge_agg_links}")
    print(f"  Aggregate -> Core: {agg_core_links}")
    print(f"  Total: {gpu_nv_links + nv_edge_links + gpu_edge_links + edge_agg_links + agg_core_links}")

if __name__ == "__main__":
    generate_custom_fat_tree_64()
