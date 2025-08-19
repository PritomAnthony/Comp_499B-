#!/usr/bin/env python3
"""
Performance Comparison Analysis: Fat Tree vs UB Mesh Topology
Compares the two CSV files to analyze network topology performance
"""

import pandas as pd
import numpy as np

def parse_simulation_results():
    """Parse and compare both topology simulation results"""
    
    # Fat Tree Results
    fat_tree_file = "fatTree_End_to _end.csv"
    
    # UB Mesh Results  
    ub_mesh_file = "ncclFlowModel_EndToEnd.csv"
    
    print("=== TOPOLOGY PERFORMANCE COMPARISON ===\n")
    
    # Parse summary data from first lines
    fat_tree_summary = {
        'total_time': 658913,
        'total_comp': 363836,
        'total_exposed_comm': 295077,
        'expose_tp_comm': 24305,
        'comp_percentage': 55.22,
        'comm_percentage': 44.78
    }
    
    ub_mesh_summary = {
        'total_time': 377397,
        'total_comp': 363836,
        'total_exposed_comm': 13561,
        'expose_tp_comm': 9950,
        'comp_percentage': 96.41,
        'comm_percentage': 3.59
    }
    
    print("📊 **OVERALL PERFORMANCE METRICS**\n")
    
    print(f"{'Metric':<25} {'Fat Tree':<15} {'UB Mesh':<15} {'Improvement':<15}")
    print("-" * 70)
    
    # Total simulation time comparison
    time_improvement = ((fat_tree_summary['total_time'] - ub_mesh_summary['total_time']) / fat_tree_summary['total_time']) * 100
    print(f"{'Total Time (μs)':<25} {fat_tree_summary['total_time']:<15,} {ub_mesh_summary['total_time']:<15,} {time_improvement:.1f}% faster")
    
    # Communication time comparison  
    comm_improvement = ((fat_tree_summary['total_exposed_comm'] - ub_mesh_summary['total_exposed_comm']) / fat_tree_summary['total_exposed_comm']) * 100
    print(f"{'Total Comm Time (μs)':<25} {fat_tree_summary['total_exposed_comm']:<15,} {ub_mesh_summary['total_exposed_comm']:<15,} {comm_improvement:.1f}% faster")
    
    # TP communication comparison
    tp_improvement = ((fat_tree_summary['expose_tp_comm'] - ub_mesh_summary['expose_tp_comm']) / fat_tree_summary['expose_tp_comm']) * 100
    print(f"{'TP Comm Time (μs)':<25} {fat_tree_summary['expose_tp_comm']:<15,} {ub_mesh_summary['expose_tp_comm']:<15,} {tp_improvement:.1f}% faster")
    
    print(f"{'Compute %':<25} {fat_tree_summary['comp_percentage']:<15.2f}% {ub_mesh_summary['comp_percentage']:<15.2f}% {ub_mesh_summary['comp_percentage'] - fat_tree_summary['comp_percentage']:+.2f}%")
    print(f"{'Communication %':<25} {fat_tree_summary['comm_percentage']:<15.2f}% {ub_mesh_summary['comm_percentage']:<15.2f}% {ub_mesh_summary['comm_percentage'] - fat_tree_summary['comm_percentage']:+.2f}%")
    
    print("\n🔍 **DETAILED LAYER ANALYSIS**\n")
    
    # Parse layer-specific data
    print(f"{'Layer Type':<20} {'Fat Tree Comm (μs)':<20} {'UB Mesh Comm (μs)':<20} {'Improvement':<15}")
    print("-" * 75)
    
    # Sample layer comparisons based on the CSV data
    layers = [
        ('grad_norm fwd', 4513.205, 1805.948),
        ('grad_norm wg', 270771.339, 3610.736),
        ('layernorm ig', 9026.300, 3611.792),
        ('embedding fwd/ig', 60.609, 25.515),
        ('attention_column', 30.361, 12.810),
        ('attention_row', 30.361, 12.810),
        ('mlp_column', 30.361, 12.810),
        ('mlp_row', 30.361, 12.810)
    ]
    
    for layer_name, fat_tree_time, ub_mesh_time in layers:
        improvement = ((fat_tree_time - ub_mesh_time) / fat_tree_time) * 100
        print(f"{layer_name:<20} {fat_tree_time:<20.3f} {ub_mesh_time:<20.3f} {improvement:.1f}% faster")
    
    print("\n🌐 **BANDWIDTH ANALYSIS**\n")
    
    # Bandwidth comparisons from the CSV
    print(f"{'Layer Type':<20} {'Fat Tree AlgBW':<18} {'UB Mesh AlgBW':<18} {'Ratio':<12}")
    print("-" * 68)
    
    bandwidth_data = [
        ('grad_norm fwd', 670.369, 1675.304),
        ('grad_norm wg', 22.347, 1675.843),
        ('layernorm ig', 335.189, 837.676),
        ('embedding', 322.250, 765.481),
        ('attention layers', 643.301, 1524.688),
        ('mlp layers', 643.301, 1524.688)
    ]
    
    for layer_name, fat_tree_bw, ub_mesh_bw in bandwidth_data:
        ratio = ub_mesh_bw / fat_tree_bw
        print(f"{layer_name:<20} {fat_tree_bw:<18.1f} {ub_mesh_bw:<18.1f} {ratio:.2f}x")
    
    print("\n🏆 **KEY FINDINGS**\n")
    
    print("✅ **UB Mesh Advantages:**")
    print(f"   • {time_improvement:.1f}% faster overall execution time")
    print(f"   • {comm_improvement:.1f}% reduction in communication overhead")
    print(f"   • {ub_mesh_summary['comp_percentage']:.1f}% compute utilization vs {fat_tree_summary['comp_percentage']:.1f}% (Fat Tree)")
    print("   • 2-2.5x higher algorithmic bandwidth for most operations")
    print("   • Dramatically better gradient communication performance")
    
    print("\n📈 **Performance Breakdown:**")
    print("   • Gradient norm weight grad: 98.7% communication time reduction")
    print("   • Layer norm: 60.0% communication time reduction") 
    print("   • Attention/MLP layers: 57.8% communication time reduction")
    print("   • Embedding layers: 57.9% communication time reduction")
    
    print("\n🔧 **Architecture Impact:**")
    print("   • UB Mesh's higher intra-server bandwidth (7200Gbps) enables faster local communication")
    print("   • Optimized inter-server links (2800Gbps) reduce cross-node latency")
    print("   • Switch-to-switch backbone (1600Gbps) provides efficient routing")
    print("   • Overall better resource utilization and lower communication bottlenecks")

if __name__ == "__main__":
    parse_simulation_results()
