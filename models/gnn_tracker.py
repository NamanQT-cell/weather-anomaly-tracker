"""
Stage 1: Spatio-Temporal GNN anomaly tracker.

Message-passing network over the icosahedral mesh. Per node it predicts:
  - anomaly probability (is this node part of an extreme-weather feature)
  - a 2D displacement vector (where the anomaly is heading next lead time)

Kept small (3 message-passing layers) so it trains in minutes on a laptop
GPU/CPU for a hackathon demo; scale layers/hidden dim up for production.
"""
import torch
import torch.nn as nn
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops


class MeshConv(MessagePassing):
    def __init__(self, in_dim, out_dim):
        super().__init__(aggr="mean")
        self.lin = nn.Linear(in_dim * 2, out_dim)
        self.act = nn.SiLU()

    def forward(self, x, edge_index):
        edge_index, _ = add_self_loops(edge_index, num_nodes=x.size(0))
        return self.propagate(edge_index, x=x)

    def message(self, x_i, x_j):
        return self.act(self.lin(torch.cat([x_i, x_j], dim=-1)))


class AnomalyTrackerGNN(nn.Module):
    def __init__(self, in_features: int, hidden_dim: int = 64, n_layers: int = 3):
        super().__init__()
        self.encoder = nn.Linear(in_features, hidden_dim)
        self.convs = nn.ModuleList([
            MeshConv(hidden_dim, hidden_dim) for _ in range(n_layers)
        ])
        self.anomaly_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2), nn.SiLU(),
            nn.Linear(hidden_dim // 2, 1),
        )
        self.trajectory_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2), nn.SiLU(),
            nn.Linear(hidden_dim // 2, 2),  # displacement in (lat, lon) degrees
        )

    def forward(self, x, edge_index):
        h = self.encoder(x)
        for conv in self.convs:
            h = h + conv(h, edge_index)  # residual message passing
        anomaly_logit = self.anomaly_head(h).squeeze(-1)
        displacement = self.trajectory_head(h)
        return torch.sigmoid(anomaly_logit), displacement


def cluster_and_box(mesh_verts_latlon, anomaly_prob, threshold=0.5, eps_deg=4.0, min_samples=5):
    """Turn per-node anomaly probabilities into a macro-scale bounding
    box (lat/lon min/max) around each detected cluster, using DBSCAN on
    the flagged nodes' lat/lon coordinates."""
    import numpy as np
    from sklearn.cluster import DBSCAN

    flagged = anomaly_prob >= threshold
    if flagged.sum() == 0:
        return []

    coords = mesh_verts_latlon[flagged]
    labels = DBSCAN(eps=eps_deg, min_samples=min_samples).fit_predict(coords)

    boxes = []
    for lab in set(labels):
        if lab == -1:
            continue
        pts = coords[labels == lab]
        boxes.append({
            "lat_min": float(pts[:, 0].min()), "lat_max": float(pts[:, 0].max()),
            "lon_min": float(pts[:, 1].min()), "lon_max": float(pts[:, 1].max()),
            "centroid": [float(pts[:, 0].mean()), float(pts[:, 1].mean())],
            "n_nodes": int(len(pts)),
        })
    return boxes
