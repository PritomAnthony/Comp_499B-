# Generate a clean, minimalist topology diagram for H100 64-GPU fat tree cluster
import matplotlib.pyplot as plt

# ---------- Layout (layered) ----------
pos = {}

# Eight groups horizontally for 64 GPUs
x_gap = 1.6
anchors = [i * x_gap for i in range(8)]

# GPUs: 0-63 (8 groups of 8)
for g in range(64):
    group = g // 8
    idx = g % 8
    x = anchors[group] - 0.5 + idx * (1.0 / 7)
    y = 0.0
    pos[g] = (x, y)

# NVSwitch: 64-71 (one per group)
for i in range(8):
    node = 64 + i
    pos[node] = (anchors[i], 0.9)

# Edge: 72-79 (aligned with groups)
for i in range(8):
    node = 72 + i
    pos[node] = (anchors[i], 1.8)

# Aggregation: 80-83 (spread across middle)
agg_x_positions = [anchors[1] + 0.8, anchors[2] + 0.8, anchors[4] + 0.8, anchors[5] + 0.8]
for i in range(4):
    pos[80 + i] = (agg_x_positions[i], 2.7)

# TWO Cores: 84-85 (top center)
pos[84] = (anchors[3] - 0.4, 3.6)
pos[85] = (anchors[4] + 0.4, 3.6)

# ---------- Edge sets ----------
edges_gpu_nvsw = []     # GPU -> NVSwitch
edges_nvsw_edge = []    # NVSwitch -> Edge
edges_edge_agg = []     # Edge -> Agg
edges_agg_core = []     # Agg -> both cores (84,85)
edges_gpu_edge = []     # GPU -> Edge (NIC), dashed

# GPU -> NVSwitch (grouped by 8)
for g in range(64):
    nvsw = 64 + (g // 8)
    edges_gpu_nvsw.append((g, nvsw))

# NVSwitch -> its Edge
for i in range(8):
    edges_nvsw_edge.append((64 + i, 72 + i))

# Edge -> Agg (based on your fat tree file pattern)
# From the file: edges 72-79 connect to aggs 80-83 in specific pattern
edge_to_agg_mapping = {
    72: [80, 81],  # Edge 0 -> Agg 0,1
    73: [81, 82],  # Edge 1 -> Agg 1,2  
    74: [82, 83],  # Edge 2 -> Agg 2,3
    75: [83, 80],  # Edge 3 -> Agg 3,0
    76: [80, 81],  # Edge 4 -> Agg 0,1
    77: [81, 82],  # Edge 5 -> Agg 1,2
    78: [82, 83],  # Edge 6 -> Agg 2,3
    79: [83, 80],  # Edge 7 -> Agg 3,0
}

for edge, aggs in edge_to_agg_mapping.items():
    for agg in aggs:
        edges_edge_agg.append((edge, agg))

# Agg -> both Cores (84,85)
for a in range(80, 84):
    edges_agg_core.append((a, 84))
    edges_agg_core.append((a, 85))

# GPU -> Edge (NIC): connect each GPU to corresponding edge (round-robin pattern)
for g in range(64):
    e = 72 + (g % 8)
    edges_gpu_edge.append((g, e))

# ---------- Drawing helpers ----------
def draw_nodes(node_ids, marker, size, label_prefix):
    xs = [pos[n][0] for n in node_ids]
    ys = [pos[n][1] for n in node_ids]
    plt.scatter(xs, ys, s=size, marker=marker, c='white', edgecolors='black', linewidths=1.5, zorder=3)
    # Only draw labels if label_prefix is provided and not empty
    if label_prefix:
        for n, x, y in zip(node_ids, xs, ys):
            plt.text(x+0.15, y+0.15, f"{label_prefix}{n}", ha='center', va='top', fontsize=7, zorder=4)

def draw_edges(edges, style='-', width=1.0, alpha=0.9, colors=None):
    for u,v in edges:
        x1,y1 = pos[u]
        x2,y2 = pos[v]
        if colors:
            plt.plot([x1,x2], [y1,y2], linestyle=style, linewidth=width, alpha=alpha, color=colors, zorder=1)
        else:
            plt.plot([x1,x2], [y1,y2], linestyle=style, linewidth=width, alpha=alpha, zorder=1)

# ---------- Compose figure ----------
plt.figure(figsize=(16, 8), dpi=150)

# Draw edges with better colors and ordering (draw first so they appear behind nodes)
draw_edges(edges_gpu_edge, style='--', width=0.8, alpha=0.3, colors='#888888')   # GPU->Edge (NIC) - light gray dashed
draw_edges(edges_gpu_nvsw, style='-',  width=1.2, alpha=0.7, colors='#1f77b4')  # GPU->NVSwitch - blue
draw_edges(edges_nvsw_edge, style='-', width=1.2, alpha=0.7, colors='#2ca02c')  # NVSwitch->Edge - green
draw_edges(edges_edge_agg, style='-',  width=1.2, alpha=0.7, colors='#ff7f0e')  # Edge->Agg - orange
draw_edges(edges_agg_core, style='-',  width=1.2, alpha=0.7, colors='#d62728')  # Agg->Core - red

# Draw nodes with clean styling
draw_nodes(range(64),        marker='o', size=15, label_prefix='')     # GPUs (smaller for 64)
draw_nodes(range(64,72),     marker='s', size=40, label_prefix='N')    # NVSwitch
draw_nodes(range(72,80),     marker='D', size=40, label_prefix='E')    # Edge
draw_nodes(range(80,84),     marker='p', size=50, label_prefix='A')    # Agg
draw_nodes([84,85],          marker='*', size=70, label_prefix='C')    # Cores

# Simple group labels for 8 groups
group_labels = ["GPUs 0–7", "GPUs 8–15", "GPUs 16–23", "GPUs 24–31", 
                "GPUs 32–39", "GPUs 40–47", "GPUs 48–55", "GPUs 56–63"]
for i, label in enumerate(group_labels):
    x = anchors[i]
    plt.text(x, -0.25, label, ha='center', va='top', fontsize=8)

plt.title("H100 64-GPU Fat Tree Topology", fontsize=16, pad=15)
plt.axis('off')
plt.tight_layout()

out_path = "h100_64gpu_topology_minimalist.png"
plt.savefig(out_path, bbox_inches='tight', dpi=150)
print(f"64-GPU Fat Tree topology diagram saved as: {out_path}")