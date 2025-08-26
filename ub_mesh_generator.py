#!/usr/bin/env python3
"""
UB Mesh Topology Generator

This script generates UB mesh topology files for GPU clusters with the following characteristics:
- GPUs organized into servers with fully connected intra-server links
- Index-based inter-server connections (GPU i in server A connects to GPU i in all other servers)
- No switches - pure GPU-to-GPU mesh topology
- Configurable bandwidth and latency parameters
"""

import argparse
import math

def generate_ub_mesh_topology(total_gpus, gpus_per_server, output_file, 
                             intra_bandwidth="900Gbps", intra_latency="0.000025ms",
                             inter_bandwidth="350Gbps", inter_latency="0.0005ms",
                             switch_bandwidth="300Gbps", switch_latency="0.0005ms",
                             gpu_type="H100", use_switches=False, gpus_per_rack=64):
    """
    Generate UB mesh topology file
    
    Args:
        total_gpus: Total number of GPUs in the cluster
        gpus_per_server: Number of GPUs per server
        output_file: Output file path
        intra_bandwidth: Bandwidth for intra-server links (GPU-GPU on board, default: 900Gbps)
        intra_latency: Latency for intra-server links
        inter_bandwidth: Bandwidth for inter-server/GPU-to-switch links (default: 350Gbps)
        inter_latency: Latency for inter-server/GPU-to-switch links
        switch_bandwidth: Bandwidth for switch-to-switch links (default: 300Gbps)
        switch_latency: Latency for switch-to-switch links
        gpu_type: Type of GPU (e.g., H100, A100)
        use_switches: Whether to use switches for inter-rack communication
        gpus_per_rack: Number of GPUs per rack (only used when use_switches=True)
    """
    
    # Calculate topology parameters
    if total_gpus % gpus_per_server != 0:
        raise ValueError(f"Total GPUs ({total_gpus}) must be divisible by GPUs per server ({gpus_per_server})")
    
    servers = total_gpus // gpus_per_server
    
    if use_switches:
        if total_gpus % gpus_per_rack != 0:
            raise ValueError(f"Total GPUs ({total_gpus}) must be divisible by GPUs per rack ({gpus_per_rack})")
        if gpus_per_rack % gpus_per_server != 0:
            raise ValueError(f"GPUs per rack ({gpus_per_rack}) must be divisible by GPUs per server ({gpus_per_server})")
        
        racks = total_gpus // gpus_per_rack
        servers_per_rack = gpus_per_rack // gpus_per_server
        switches = racks  # One switch per rack
        
        print(f"Generating UB mesh topology with switches:")
        print(f"  Total GPUs: {total_gpus}")
        print(f"  Racks: {racks}")
        print(f"  GPUs per rack: {gpus_per_rack}")
        print(f"  Servers per rack: {servers_per_rack}")
        print(f"  Total servers: {servers}")
        print(f"  GPUs per server: {gpus_per_server}")
        print(f"  Switches: {switches}")
    else:
        print(f"Generating UB mesh topology:")
        print(f"  Total GPUs: {total_gpus}")
        print(f"  Servers: {servers}")
        print(f"  GPUs per server: {gpus_per_server}")
    
    # Calculate link counts
    intra_server_links_per_server = (gpus_per_server * (gpus_per_server - 1)) // 2
    total_intra_server_links = servers * intra_server_links_per_server
    
    if use_switches:
        # For switched topology: only intra-rack UB mesh connections + switch connections
        racks = total_gpus // gpus_per_rack
        servers_per_rack = gpus_per_rack // gpus_per_server
        switches = racks
        
        # Intra-rack links (UB mesh within each rack)
        intra_rack_inter_server_links_per_rack = 0
        for gpu_index in range(gpus_per_server):
            # Each GPU index connects to same index in other servers within the rack
            connections_per_gpu_index = servers_per_rack * (servers_per_rack - 1) // 2
            intra_rack_inter_server_links_per_rack += connections_per_gpu_index
        
        total_intra_rack_inter_server_links = racks * intra_rack_inter_server_links_per_rack
        
        # Switch connections
        # All GPUs from last server in each rack connect to their rack's switch
        gpu_to_switch_links = racks * gpus_per_server  # Each rack: 8 GPUs from server 7
        
        # Inter-switch connections (all switches in full mesh)
        inter_switch_links = switches * (switches - 1) // 2
        
        total_links = total_intra_server_links + total_intra_rack_inter_server_links + gpu_to_switch_links + inter_switch_links
        
        print(f"  Intra-server links per server: {intra_server_links_per_server}")
        print(f"  Total intra-server links: {total_intra_server_links}")
        print(f"  Intra-rack inter-server links per rack: {intra_rack_inter_server_links_per_rack}")
        print(f"  Total intra-rack inter-server links: {total_intra_rack_inter_server_links}")
        print(f"  GPU-to-switch links: {gpu_to_switch_links}")
        print(f"  Inter-switch links: {inter_switch_links}")
        print(f"  Total links: {total_links}")
    else:
        # For non-switched topology: original UB mesh logic
        inter_server_links_per_gpu_index = servers * (servers - 1) // 2
        total_inter_server_links = gpus_per_server * inter_server_links_per_gpu_index
        
        total_links = total_intra_server_links + total_inter_server_links
        
        print(f"  Intra-server links per server: {intra_server_links_per_server}")
        print(f"  Total intra-server links: {total_intra_server_links}")
        print(f"  Inter-server links per GPU index: {inter_server_links_per_gpu_index}")
        print(f"  Total inter-server links: {total_inter_server_links}")
        print(f"  Total links: {total_links}")
    
    # Generate topology file
    with open(output_file, 'w') as f:
        # Write header: total_nodes gpus_per_server nvswitch_count switch_count total_links gpu_type
        if use_switches:
            switches = total_gpus // gpus_per_rack
            total_nodes = total_gpus + 0 + switches  # GPUs + NVSwitches + Switches
            f.write(f"{total_nodes} {gpus_per_server} 0 {switches} {total_links} {gpu_type}\n")
            
            # Write switch IDs on the second line
            switch_node_start = total_gpus
            switch_ids = [str(switch_node_start + i) for i in range(switches)]
            f.write(f"{' '.join(switch_ids)}\n")
        else:
            f.write(f"{total_gpus} {gpus_per_server} 0 0 {total_links} {gpu_type}\n")
        
        # Generate intra-server links
        print("  Generating intra-server links...")
        for server in range(servers):
            server_start = server * gpus_per_server
            server_end = server_start + gpus_per_server
            
            # Fully connect all GPUs within this server
            for i in range(server_start, server_end):
                for j in range(i + 1, server_end):
                    f.write(f"{i} {j} {intra_bandwidth} {intra_latency} 0\n")
        
        if use_switches:
            # Generate intra-rack inter-server links
            print("  Generating intra-rack inter-server links...")
            racks = total_gpus // gpus_per_rack
            servers_per_rack = gpus_per_rack // gpus_per_server
            
            for rack in range(racks):
                rack_start_server = rack * servers_per_rack
                rack_end_server = rack_start_server + servers_per_rack
                
                for gpu_index in range(gpus_per_server):
                    # For each GPU index, connect across servers within this rack
                    gpu_nodes = []
                    for server in range(rack_start_server, rack_end_server):
                        gpu_nodes.append(server * gpus_per_server + gpu_index)
                    
                    # Connect each GPU to all others with the same index within the rack
                    for i in range(len(gpu_nodes)):
                        for j in range(i + 1, len(gpu_nodes)):
                            f.write(f"{gpu_nodes[i]} {gpu_nodes[j]} {inter_bandwidth} {inter_latency} 0\n")
            
            # Generate GPU-to-switch links
            print("  Generating GPU-to-switch links...")
            switch_node_start = total_gpus  # Switches start after GPU nodes
            
            for rack in range(racks):
                switch_id = switch_node_start + rack
                last_server_in_rack = (rack + 1) * servers_per_rack - 1  # Server 7 in each rack
                last_server_gpu_start = last_server_in_rack * gpus_per_server
                
                # Connect all GPUs from the last server in this rack to the rack's switch
                for gpu_offset in range(gpus_per_server):
                    gpu_id = last_server_gpu_start + gpu_offset
                    f.write(f"{gpu_id} {switch_id} {inter_bandwidth} {inter_latency} 0\n")
            
            # Generate inter-switch links
            print("  Generating inter-switch links...")
            switches = racks
            for i in range(switches):
                for j in range(i + 1, switches):
                    switch_i = switch_node_start + i
                    switch_j = switch_node_start + j
                    f.write(f"{switch_i} {switch_j} {switch_bandwidth} {switch_latency} 0\n")
        else:
            # Generate inter-server links (original logic)
            print("  Generating inter-server links...")
            for gpu_index in range(gpus_per_server):
                # For each GPU index, connect across all servers
                gpu_nodes = []
                for server in range(servers):
                    gpu_nodes.append(server * gpus_per_server + gpu_index)
                
                # Connect each GPU to all others with the same index
                for i in range(len(gpu_nodes)):
                    for j in range(i + 1, len(gpu_nodes)):
                        f.write(f"{gpu_nodes[i]} {gpu_nodes[j]} {inter_bandwidth} {inter_latency} 0\n")
    
    print(f"  Topology file written to: {output_file}")
    
    if use_switches:
        return {
            'total_gpus': total_gpus,
            'total_nodes': total_gpus + switches,  # GPUs + Switches
            'servers': servers,
            'gpus_per_server': gpus_per_server,
            'total_links': total_links,
            'intra_server_links': total_intra_server_links,
            'intra_rack_inter_server_links': total_intra_rack_inter_server_links,
            'gpu_to_switch_links': gpu_to_switch_links,
            'inter_switch_links': inter_switch_links,
            'switches': switches,
            'racks': racks
        }
    else:
        return {
            'total_gpus': total_gpus,
            'total_nodes': total_gpus,  # Only GPUs
            'servers': servers,
            'gpus_per_server': gpus_per_server,
            'total_links': total_links,
            'intra_server_links': total_intra_server_links,
            'inter_server_links': total_inter_server_links
        }

def main():
    parser = argparse.ArgumentParser(description='Generate UB mesh topology files for GPU clusters')
    
    parser.add_argument('total_gpus', type=int, 
                       help='Total number of GPUs in the cluster')
    parser.add_argument('gpus_per_server', type=int,
                       help='Number of GPUs per server')
    parser.add_argument('-o', '--output', type=str, required=True,
                       help='Output topology file path')
    
    # Bandwidth and latency options
    parser.add_argument('--intra-bandwidth', type=str, default='900Gbps',
                       help='Bandwidth for intra-server links (GPU-GPU on board, default: 900Gbps)')
    parser.add_argument('--intra-latency', type=str, default='0.000025ms',
                       help='Latency for intra-server links (default: 0.000025ms)')
    parser.add_argument('--inter-bandwidth', type=str, default='350Gbps',
                       help='Bandwidth for inter-server/GPU-to-switch links (default: 350Gbps)')
    parser.add_argument('--inter-latency', type=str, default='0.0005ms',
                       help='Latency for inter-server/GPU-to-switch links (default: 0.0005ms)')
    parser.add_argument('--switch-bandwidth', type=str, default='300Gbps',
                       help='Bandwidth for switch-to-switch links (default: 300Gbps)')
    parser.add_argument('--switch-latency', type=str, default='0.0005ms',
                       help='Latency for switch-to-switch links (default: 0.0005ms)')
    parser.add_argument('--gpu-type', type=str, default='H100',
                       help='GPU type (default: H100)')
    
    # Validation options
    parser.add_argument('--validate', action='store_true',
                       help='Validate the generated topology file')
    
    # Switch topology options
    parser.add_argument('--use-switches', action='store_true',
                       help='Use switches for inter-rack communication')
    parser.add_argument('--gpus-per-rack', type=int, default=64,
                       help='Number of GPUs per rack (default: 64, only used with --use-switches)')
    
    args = parser.parse_args()
    
    try:
        stats = generate_ub_mesh_topology(
            total_gpus=args.total_gpus,
            gpus_per_server=args.gpus_per_server,
            output_file=args.output,
            intra_bandwidth=args.intra_bandwidth,
            intra_latency=args.intra_latency,
            inter_bandwidth=args.inter_bandwidth,
            inter_latency=args.inter_latency,
            switch_bandwidth=args.switch_bandwidth,
            switch_latency=args.switch_latency,
            gpu_type=args.gpu_type,
            use_switches=args.use_switches,
            gpus_per_rack=args.gpus_per_rack
        )
        
        if args.validate:
            validate_topology_file(args.output, stats)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

def validate_topology_file(file_path, expected_stats):
    """Validate the generated topology file"""
    print(f"\nValidating topology file: {file_path}")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Parse header: total_nodes gpus_per_server nvswitch_count switch_count total_links gpu_type
    header = lines[0].strip().split()
    actual_nodes = int(header[0])
    actual_gpus_per_server = int(header[1])
    actual_nvswitch_count = int(header[2])
    actual_switch_count = int(header[3])
    actual_links = int(header[4])
    actual_gpu_type = header[5]
    
    # Check if there are switches (switch IDs on second line)
    has_switches = actual_switch_count > 0
    link_start_line = 2 if has_switches else 1
    
    # Count actual links in file
    link_lines = len(lines) - link_start_line
    
    print(f"  Expected total nodes: {expected_stats['total_nodes']}, Actual: {actual_nodes}")
    print(f"  Expected GPUs: {expected_stats['total_gpus']}")
    print(f"  Expected GPUs per server: {expected_stats['gpus_per_server']}, Actual: {actual_gpus_per_server}")
    if has_switches:
        print(f"  Switch count: {actual_switch_count}")
        print(f"  Switch IDs: {lines[1].strip()}")
    print(f"  Expected links: {expected_stats['total_links']}, Actual (header): {actual_links}")
    print(f"  Actual link lines: {link_lines}")
    
    if actual_nodes != expected_stats['total_nodes']:
        print(f"  ❌ Total node count mismatch!")
        return False
    
    if actual_gpus_per_server != expected_stats['gpus_per_server']:
        print(f"  ❌ GPUs per server mismatch!")
        return False
    
    if actual_links != expected_stats['total_links']:
        print(f"  ❌ Link count mismatch in header!")
        return False
        
    if link_lines != expected_stats['total_links']:
        print(f"  ❌ Actual link lines don't match expected!")
        return False
    
    print(f"  ✅ Topology file validation passed!")
    return True

# Predefined configurations for common setups
PREDEFINED_CONFIGS = {
    'ub64': {'total_gpus': 64, 'gpus_per_server': 8},
    'ub32': {'total_gpus': 32, 'gpus_per_server': 8},
    'ub128': {'total_gpus': 128, 'gpus_per_server': 8},
    'ub128-switch': {'total_gpus': 128, 'gpus_per_server': 8, 'use_switches': True, 'gpus_per_rack': 64},
    'ub256': {'total_gpus': 256, 'gpus_per_server': 8},
}

def list_predefined_configs():
    """List predefined configurations"""
    print("Predefined configurations:")
    for name, config in PREDEFINED_CONFIGS.items():
        servers = config['total_gpus'] // config['gpus_per_server']
        switches_info = ""
        if config.get('use_switches', False):
            racks = config['total_gpus'] // config['gpus_per_rack']
            switches_info = f", {racks} racks with switches"
        print(f"  {name}: {config['total_gpus']} GPUs, {servers} servers, {config['gpus_per_server']} GPUs/server{switches_info}")

if __name__ == "__main__":
    # Check for special commands
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--list-configs':
        list_predefined_configs()
        sys.exit(0)
    
    # Check for predefined config usage
    if len(sys.argv) > 1 and sys.argv[1] in PREDEFINED_CONFIGS:
        config_name = sys.argv[1]
        config = PREDEFINED_CONFIGS[config_name]
        
        # Replace first argument with actual values
        sys.argv[1:2] = [str(config['total_gpus']), str(config['gpus_per_server'])]
        
        # Add switch-related arguments if specified in config
        if config.get('use_switches', False):
            sys.argv.append('--use-switches')
            sys.argv.extend(['--gpus-per-rack', str(config['gpus_per_rack'])])
        
        switches_info = ""
        if config.get('use_switches', False):
            racks = config['total_gpus'] // config['gpus_per_rack']
            switches_info = f", {racks} racks with switches"
        print(f"Using predefined config '{config_name}': {config['total_gpus']} GPUs, {config['gpus_per_server']} GPUs/server{switches_info}")
    
    sys.exit(main())
