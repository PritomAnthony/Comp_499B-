#!/usr/bin/env python3
"""
Topology Validation Script for UB_Mesh_128g_8gps_LRS16_H100
Validates the 128-GPU UB-Mesh topology with 16 inter-rack switches
Perfect UB mesh topology requirements:
- Intra-server GPU-to-GPU: 7200Gbps, 0.000025ms
- Inter-server GPU-to-GPU: 2800Gbps, 0.0005ms  
- GPU-to-Switch: 2800Gbps, 0.0005ms
- Switch-to-Switch: 1600Gbps, 0.0001ms
"""

def parse_topology_file(filename):
    """Parse the 128-GPU UB mesh topology file and extract connections"""
    connections = []
    header = None
    switch_list = []
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    line_count = 0
    for line in lines:
        line = line.strip()
        line_count += 1
        
        if not line or line.startswith('#'):
            continue
            
        parts = line.split()
        
        if header is None and len(parts) >= 6:  # Header line: nodes servers switches unknown links device
            header = {
                'total_nodes': int(parts[0]),
                'gpus_per_server': int(parts[1]),
                'nvswitch_num': int(parts[2]),
                'switch_num': int(parts[3]),
                'total_links': int(parts[4]),
                'device': parts[5] if len(parts) > 5 else 'Unknown'
            }
        elif switch_list == [] and len(parts) >= 16 and all(p.isdigit() for p in parts):  # Switch ID list
            switch_list = [int(x) for x in parts]
        elif len(parts) >= 5:  # Connection line: src dst bandwidth latency type
            try:
                src = int(parts[0])
                dst = int(parts[1])
                bandwidth = parts[2]
                latency = parts[3]
                connection_type = int(parts[4])
                
                connections.append({
                    'src': src,
                    'dst': dst,
                    'bandwidth': bandwidth,
                    'latency': latency,
                    'type': connection_type
                })
            except ValueError:
                continue  # Skip malformed lines
    
    return header, connections, switch_list

def validate_topology(header, connections, switch_list):
    """Validate the 128-GPU UB mesh topology against perfect specifications"""
    print(f"Validating 128-GPU UB mesh topology with {header['total_nodes']} total nodes")
    print(f"Expected: 16 servers × 8 GPUs = 128 GPUs + 16 switches = 144 total nodes")
    print(f"Switch IDs: {switch_list}")
    
    # Expected specifications for perfect UB mesh
    expected_total_nodes = 144  # 128 GPUs + 16 switches
    expected_gpus_per_server = 8
    expected_servers = 16
    expected_switches = 16
    
    # Bandwidth specifications in Gbps
    expected_bandwidths = {
        'intra_server': '7200Gbps',     # Intra-server GPU-to-GPU
        'inter_server': '2800Gbps',     # Inter-server GPU-to-GPU  
        'gpu_to_switch': '2800Gbps',    # GPU-to-Switch
        'switch_to_switch': '1600Gbps'  # Switch-to-Switch
    }
    
    # Latency specifications
    expected_latencies = {
        'intra_server': '0.000025ms',
        'inter_server': '0.0005ms', 
        'gpu_to_switch': '0.0005ms',
        'switch_to_switch': '0.0001ms'
    }
    
    # Validate header information
    errors = []
    
    if header['total_nodes'] != expected_total_nodes:
        errors.append(f"Total nodes mismatch: expected {expected_total_nodes}, got {header['total_nodes']}")
    
    if header['gpus_per_server'] != expected_gpus_per_server:
        errors.append(f"GPUs per server mismatch: expected {expected_gpus_per_server}, got {header['gpus_per_server']}")
    
    if header['switch_num'] != expected_switches:
        errors.append(f"Switch count mismatch: expected {expected_switches}, got {header['switch_num']}")
    
    if len(switch_list) != expected_switches:
        errors.append(f"Switch list length mismatch: expected {expected_switches}, got {len(switch_list)}")
    
    # Analyze connections by type and bandwidth
    bandwidth_counts = {}
    latency_counts = {}
    connection_types = {0: 'unknown', 1: 'intra_server', 2: 'inter_server', 3: 'gpu_to_switch', 4: 'switch_to_switch'}
    
    for conn in connections:
        bw = conn['bandwidth']
        lat = conn['latency']
        conn_type = conn['type']
        
        if bw not in bandwidth_counts:
            bandwidth_counts[bw] = 0
        bandwidth_counts[bw] += 1
        
        if lat not in latency_counts:
            latency_counts[lat] = 0
        latency_counts[lat] += 1
    
    # Print bandwidth and latency distribution
    print("\nBandwidth Distribution:")
    for bw, count in sorted(bandwidth_counts.items()):
        print(f"  {bw}: {count} connections")
    
    print("\nLatency Distribution:")  
    for lat, count in sorted(latency_counts.items()):
        print(f"  {lat}: {count} connections")
    
    # Validate bandwidth specifications
    expected_counts = {
        '7200Gbps': 448,    # Intra-server connections (8 servers × 8 GPUs × 7 connections each)
        '2800Gbps': 3712,   # GPU-to-switch + inter-server (128×16 + 2560)  
        '1600Gbps': 120     # Switch-to-switch connections (16×15/2×2)
    }
    
    for bw, expected_count in expected_counts.items():
        actual_count = bandwidth_counts.get(bw, 0)
        if actual_count != expected_count:
            errors.append(f"Bandwidth {bw} count mismatch: expected {expected_count}, got {actual_count}")
    
    # Check for GPU node ranges (0-127) and switch node ranges  
    gpu_nodes = set()
    switch_nodes = set(switch_list)
    
    for conn in connections:
        if conn['src'] < 128:
            gpu_nodes.add(conn['src'])
        if conn['dst'] < 128:
            gpu_nodes.add(conn['dst'])
    
    if len(gpu_nodes) != 128:
        errors.append(f"GPU node count mismatch: expected 128, found {len(gpu_nodes)}")
    
    if len(switch_nodes) != 16:
        errors.append(f"Switch node count mismatch: expected 16, found {len(switch_nodes)}")
    
    # Validate server grouping (GPUs 0-7 in server 0, 8-15 in server 1, etc.)
    intra_server_connections = [conn for conn in connections if conn['bandwidth'] == '7200Gbps']
    server_validation_errors = []
    
    for conn in intra_server_connections:
        src_server = conn['src'] // 8
        dst_server = conn['dst'] // 8
        if src_server != dst_server:
            server_validation_errors.append(f"Intra-server connection spans servers: GPU {conn['src']} (server {src_server}) <-> GPU {conn['dst']} (server {dst_server})")
    
    if server_validation_errors:
        errors.extend(server_validation_errors[:5])  # Limit to first 5 errors
        if len(server_validation_errors) > 5:
            errors.append(f"... and {len(server_validation_errors) - 5} more server grouping errors")
    
    # Report results
    if errors:
        print(f"\n❌ Topology validation FAILED with {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print(f"\n✅ Topology validation PASSED! Perfect UB mesh topology confirmed.")
        print(f"  - {header['total_nodes']} total nodes (128 GPUs + 16 switches)")
        print(f"  - {len(connections)} total connections")
        print(f"  - Correct bandwidth hierarchy: 7200Gbps, 2800Gbps, 1600Gbps")
        print(f"  - Proper server grouping (16 servers × 8 GPUs each)")
        return True
        
    if len(inter_server_connections) == expected_inter:
        print(f"  ✅ Inter-server count CORRECT: {len(inter_server_connections)} = {expected_inter}")
    else:
        print(f"  ❌ Inter-server count WRONG: {len(inter_server_connections)} != {expected_inter}")
    print()
    
    # Validate bandwidth and latency settings
    print("Bandwidth & Latency Validation:")
    
    # Check intra-server connections (should be 7200Gbps, 0.000025ms)
    intra_bandwidth_correct = 0
    intra_latency_correct = 0
    for conn in intra_server_connections:
        if conn['bandwidth'] == '7200Gbps':
            intra_bandwidth_correct += 1
        if conn['latency'] == '0.000025ms':
            intra_latency_correct += 1
    
    print(f"  Intra-server (900 GB/s = 7200Gbps, 0.000025ms):")
    print(f"    Bandwidth correct: {intra_bandwidth_correct}/{len(intra_server_connections)}")
    print(f"    Latency correct: {intra_latency_correct}/{len(intra_server_connections)}")
    
    # Check inter-server connections (should be 2800Gbps, 0.0005ms)
    inter_bandwidth_correct = 0
    inter_latency_correct = 0
    for conn in inter_server_connections:
        if conn['bandwidth'] == '2800Gbps':
            inter_bandwidth_correct += 1
        if conn['latency'] == '0.0005ms':
            inter_latency_correct += 1
    
    print(f"  Inter-server (350 GB/s = 2800Gbps, 0.0005ms):")
    print(f"    Bandwidth correct: {inter_bandwidth_correct}/{len(inter_server_connections)}")
    print(f"    Latency correct: {inter_latency_correct}/{len(inter_server_connections)}")
    print()
    
    # Check for full mesh connectivity
    print("Mesh Connectivity Check:")
    all_nodes = set(range(32))
    connection_matrix = {}
    
    for node in all_nodes:
        connection_matrix[node] = set()
    
    for conn in connections:
        src, dst = conn['src'], conn['dst']
        connection_matrix[src].add(dst)
        connection_matrix[dst].add(src)  # Undirected graph
    
    # Check if every node connects to every other node
    full_mesh = True
    for node in all_nodes:
        expected_connections_set = all_nodes - {node}  # All nodes except itself
        if connection_matrix[node] != expected_connections_set:
            print(f"  ❌ Node {node} missing connections to: {expected_connections_set - connection_matrix[node]}")
            full_mesh = False
    
    if full_mesh:
        print("  ✅ Full mesh connectivity VERIFIED")
    else:
        print("  ❌ Full mesh connectivity FAILED")
    print()
    
    # Check for duplicate connections
    print("Duplicate Check:")
    seen_connections = set()
    duplicates = []
    
    for conn in connections:
        src, dst = conn['src'], conn['dst']
        # Normalize connection (smaller node first)
        edge = (min(src, dst), max(src, dst))
        if edge in seen_connections:
            duplicates.append(edge)
        seen_connections.add(edge)
    
    if duplicates:
        print(f"  ❌ Found {len(duplicates)} duplicate connections: {duplicates}")
    else:
        print("  ✅ No duplicate connections found")
    print()
    
    # Summary
    print("=== VALIDATION SUMMARY ===")
    checks = [
        (len(connections) == expected_connections, f"Total connections: {len(connections)} == {expected_connections}"),
        (len(intra_server_connections) == expected_intra, f"Intra-server count: {len(intra_server_connections)} == {expected_intra}"),
        (len(inter_server_connections) == expected_inter, f"Inter-server count: {len(inter_server_connections)} == {expected_inter}"),
        (intra_bandwidth_correct == len(intra_server_connections), f"Intra-server bandwidth: {intra_bandwidth_correct}/{len(intra_server_connections)}"),
        (intra_latency_correct == len(intra_server_connections), f"Intra-server latency: {intra_latency_correct}/{len(intra_server_connections)}"),
        (inter_bandwidth_correct == len(inter_server_connections), f"Inter-server bandwidth: {inter_bandwidth_correct}/{len(inter_server_connections)}"),
        (inter_latency_correct == len(inter_server_connections), f"Inter-server latency: {inter_latency_correct}/{len(inter_server_connections)}"),
        (full_mesh, "Full mesh connectivity"),
        (len(duplicates) == 0, f"No duplicates: {len(duplicates)} == 0")
    ]
    
    passed_checks = 0
    for check_passed, description in checks:
        status = "✅" if check_passed else "❌"
        print(f"  {status} {description}")
        if check_passed:
            passed_checks += 1
    
    total_checks = len(checks)
    
    if passed_checks == total_checks:
        print(f"🎉 ALL CHECKS PASSED ({passed_checks}/{total_checks})")
        print("✅ Topology is VALID for UB-Mesh simulation!")
    else:
        print(f"⚠️  {passed_checks}/{total_checks} checks passed")
        print("❌ Topology needs fixes before simulation")

def main():
    """Main validation function"""
    filename = "UB_32_new"
    
    try:
        print(f"Validating topology file: {filename}")
        print("=" * 50)
        
        header, connections = parse_topology_file(filename)
        validate_topology(header, connections)
        
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found!")
    except Exception as e:
        print(f"❌ Error parsing file: {e}")

if __name__ == "__main__":
    main()
