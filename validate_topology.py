#!/usr/bin/env python3
"""
Topology Validation Script for UB_32_new
Validates the UB-Mesh topology against research paper requirements
"""

def parse_topology_file(filename):
    """Parse the topology file and extract connections"""
    connections = []
    header = None
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        parts = line.split()
        if header is None and len(parts) >= 5:  # Header line (first non-comment line)
            header = {
                'nodes': int(parts[0]),
                'servers': int(parts[1]),
                'switches': int(parts[2]),
                'unknown': int(parts[3]),
                'total_links': int(parts[4]),
                'device': parts[5] if len(parts) > 5 else 'Unknown'
            }
        elif header is not None and len(parts) >= 5:  # Connection line
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
    
    return header, connections

def validate_topology(header, connections):
    """Validate the topology against UB-Mesh requirements"""
    print("=== TOPOLOGY VALIDATION REPORT ===\n")
    
    # Basic header validation
    print(f"Header Info:")
    print(f"  Nodes: {header['nodes']}")
    print(f"  Servers: {header['servers']}")
    print(f"  Expected total links: {header['total_links']}")
    print(f"  Actual connections found: {len(connections)}")
    print(f"  Device: {header.get('device', 'Unknown')}")
    print()
    
    # Check if we have the right number of connections
    expected_connections = 32 * 31 // 2  # Full mesh: C(32,2) = 496
    if len(connections) == expected_connections:
        print(f"✅ Connection count CORRECT: {len(connections)} = C(32,2)")
    else:
        print(f"❌ Connection count WRONG: {len(connections)} != {expected_connections}")
    print()
    
    # Analyze server layout (8 GPUs per server, 4 servers)
    servers = {
        0: list(range(0, 8)),    # Server 0: GPUs 0-7
        1: list(range(8, 16)),   # Server 1: GPUs 8-15
        2: list(range(16, 24)),  # Server 2: GPUs 16-23
        3: list(range(24, 32))   # Server 3: GPUs 24-31
    }
    
    # Categorize connections
    intra_server_connections = []
    inter_server_connections = []
    
    for conn in connections:
        src, dst = conn['src'], conn['dst']
        
        # Find which servers the GPUs belong to
        src_server = None
        dst_server = None
        for server_id, gpus in servers.items():
            if src in gpus:
                src_server = server_id
            if dst in gpus:
                dst_server = server_id
        
        if src_server == dst_server:
            intra_server_connections.append(conn)
        else:
            inter_server_connections.append(conn)
    
    print(f"Connection Analysis:")
    print(f"  Intra-server connections: {len(intra_server_connections)}")
    print(f"  Inter-server connections: {len(inter_server_connections)}")
    
    # Expected counts
    # Intra-server: 4 servers × C(8,2) = 4 × 28 = 112
    # Inter-server: Total - Intra = 496 - 112 = 384
    expected_intra = 4 * (8 * 7 // 2)  # 4 servers × C(8,2)
    expected_inter = expected_connections - expected_intra
    
    if len(intra_server_connections) == expected_intra:
        print(f"  ✅ Intra-server count CORRECT: {len(intra_server_connections)} = 4×C(8,2)")
    else:
        print(f"  ❌ Intra-server count WRONG: {len(intra_server_connections)} != {expected_intra}")
        
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
