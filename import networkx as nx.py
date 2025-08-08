import networkx as nx

G = nx.Graph()
with open("UB_AI_32g_8gps_200Gbps_A100") as f:
    for line in f:
        if line.strip() and line[0].isdigit():
            src, dst, *_ = line.strip().split()
            G.add_edge(int(src), int(dst))

print("Connected:", nx.is_connected(G))