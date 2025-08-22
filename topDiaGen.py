# Generate a clean, minimalist topology diagram for H100 32-GPU cluster
import matplotlib.pyplot as plt

# ---------- Layout (layered) ----------
pos = {}

# Four groups horizontally
x_gap = 2.2
anchors = [i * x_gap for i in range(4)]

# GPUs: 0-31 (4 groups of 8)
for g in range(32):
    group = g // 8
    idx = g % 8
    x = anchors[group] - 0.7 + idx * (1.4 / 7)
    y = 0.0
    pos[g] = (x, y)

# NVSwitch: 32-35 (one per group)
for i in range(4):
    node = 32 + i
    pos[node] = (anchors[i], 0.9)

# Edge: 36-39 (aligned with groups)
for i in range(4):
    node = 36 + i
    pos[node] = (anchors[i], 1.8)

# Aggregation: 40-41 (centered)
pos[40] = (anchors[1], 2.7)
pos[41] = (anchors[2], 2.7)

# TWO Cores: 42-43 (top left / top right)
pos[42] = (anchors[1] - 0.4, 3.6)
pos[43] = (anchors[2] + 0.4, 3.6)

# ---------- Edge sets ----------
edges_gpu_nvsw = []     # GPU -> NVSwitch
edges_nvsw_edge = []    # NVSwitch -> Edge
edges_edge_agg = []     # Edge -> Agg (each edge to both aggs)
edges_agg_core = []     # Agg -> both cores (42,43)
edges_gpu_edge = []     # GPU -> Edge (NIC), dashed

# GPU -> NVSwitch (grouped by 8)
for g in range(32):
    nvsw = 32 + (g // 8)
    edges_gpu_nvsw.append((g, nvsw))

# NVSwitch -> its Edge
for i in range(4):
    edges_nvsw_edge.append((32 + i, 36 + i))

# Edge -> Agg (full bipartite: each edge to both aggs)
for e in range(36, 40):
    edges_edge_agg.append((e, 40))
    edges_edge_agg.append((e, 41))

# Agg -> both Cores
for a in (40, 41):
    edges_agg_core.append((a, 42))
    edges_agg_core.append((a, 43))

# GPU -> Edge (NIC): connect each GPU to one edge (round-robin)
for g in range(32):
    e = 36 + (g % 4)
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
plt.figure(figsize=(12, 6), dpi=150)

# Draw edges with better colors and ordering (draw first so they appear behind nodes)
draw_edges(edges_gpu_edge, style='--', width=0.8, alpha=0.3, colors='#888888')   # GPU->Edge (NIC) - light gray dashed
draw_edges(edges_gpu_nvsw, style='-',  width=1.2, alpha=0.7, colors='#1f77b4')  # GPU->NVSwitch - blue
draw_edges(edges_nvsw_edge, style='-', width=1.2, alpha=0.7, colors='#2ca02c')  # NVSwitch->Edge - green
draw_edges(edges_edge_agg, style='-',  width=1.2, alpha=0.7, colors='#ff7f0e')  # Edge->Agg - orange
draw_edges(edges_agg_core, style='-',  width=1.2, alpha=0.7, colors='#d62728')  # Agg->Core - red

# Draw nodes with clean styling
draw_nodes(range(32),        marker='o', size=20, label_prefix='')     # GPUs
draw_nodes(range(32,36),     marker='s', size=50, label_prefix='N')    # NVSwitch
draw_nodes(range(36,40),     marker='D', size=50, label_prefix='E')    # Edge
draw_nodes([40,41],          marker='p', size=60, label_prefix='A')    # Agg
draw_nodes([42,43],          marker='*', size=80, label_prefix='C')    # Cores

# Simple group labels
for i, label in enumerate(["GPUs 0–7","GPUs 8–15","GPUs 16–23","GPUs 24–31"]):
    x = anchors[i]
    plt.text(x, -0.25, label, ha='center', va='top', fontsize=9)

plt.title("H100 32-GPU Fat Tree Topology", fontsize=14, pad=15)
plt.axis('off')
plt.tight_layout()

out_path = "h100_topology_minimalist.png"
plt.savefig(out_path, bbox_inches='tight', dpi=150)
print(f"Minimalist topology diagram saved as: {out_path}")
