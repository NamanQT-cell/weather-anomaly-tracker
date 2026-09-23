"""
Trains AnomalyTrackerGNN on labeled mesh snapshots (node features ->
anomaly flag + displacement). Point --data-dir at real NEPS-G/ERA5-derived
tensors; defaults to synthetic data for a runnable demo.
"""
import argparse
import os
import sys
import numpy as np
import torch
import torch.nn.functional as F

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from data_pipeline.fetch_data import generate_synthetic_ensemble, generate_synthetic_climatology
from data_pipeline.mesh import build_icosphere, xyz_to_latlon, resample_grid_to_mesh
from data_pipeline.efi import compute_efi, flag_anomalies
from models.gnn_tracker import AnomalyTrackerGNN


def build_synthetic_dataset(n_samples=20):
    verts, edges = build_icosphere(subdivisions=3)
    lat, lon = xyz_to_latlon(verts)
    edge_index = torch.tensor(edges.T, dtype=torch.long)

    samples = []
    for s in range(n_samples):
        ens = generate_synthetic_ensemble(n_members=10, grid_h=45, grid_w=90, lead_times=1, seed=s)
        clim = generate_synthetic_climatology(grid_h=45, grid_w=90, seed=s + 100)
        field = ens["field"][:, 0]
        mesh_ens = np.stack([resample_grid_to_mesh(field[m], ens["lats"], ens["lons"], verts)
                              for m in range(field.shape[0])])
        mesh_clim = np.stack([resample_grid_to_mesh(clim[y], ens["lats"], ens["lons"], verts)
                               for y in range(clim.shape[0])])
        efi = compute_efi(mesh_ens, mesh_clim)
        labels = flag_anomalies(efi).astype(np.float32)

        feats = np.stack([mesh_ens.mean(0), mesh_ens.std(0), efi], axis=-1).astype(np.float32)
        samples.append((torch.tensor(feats), torch.tensor(labels)))

    return samples, edge_index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--data-dir", type=str, default=None, help="Real data dir (unused by synthetic path)")
    args = ap.parse_args()

    samples, edge_index = build_synthetic_dataset()
    model = AnomalyTrackerGNN(in_features=3, hidden_dim=32, n_layers=3)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    for epoch in range(args.epochs):
        total_loss = 0.0
        for feats, labels in samples:
            opt.zero_grad()
            pred, _ = model(feats, edge_index)
            loss = F.binary_cross_entropy(pred, labels)
            loss.backward()
            opt.step()
            total_loss += loss.item()
        print(f"epoch {epoch+1}/{args.epochs}  loss={total_loss/len(samples):.4f}")

    os.makedirs("checkpoints", exist_ok=True)
    torch.save(model.state_dict(), "checkpoints/gnn_tracker.pt")
    print("Saved checkpoints/gnn_tracker.pt")


if __name__ == "__main__":
    main()
