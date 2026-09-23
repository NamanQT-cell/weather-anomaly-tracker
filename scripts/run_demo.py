"""
End-to-end demo: synthetic ensemble -> mesh -> EFI -> GNN tracker
-> bounding box -> diffusion downscaler -> alerts.geojson

Runs on CPU with small settings so it finishes in a couple of minutes
without a GPU. This is the script to run live in front of judges.
"""
import os
import sys
import json
import numpy as np
import torch

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from data_pipeline.fetch_data import generate_synthetic_ensemble, generate_synthetic_climatology
from data_pipeline.mesh import build_icosphere, xyz_to_latlon, resample_grid_to_mesh
from data_pipeline.efi import compute_efi
from models.gnn_tracker import AnomalyTrackerGNN, cluster_and_box
from models.diffusion_downscaler import ConditionalDownscaler
from api.main import build_geojson

# Punjab/Chandigarh-area reference points, used only to label the demo's
# synthetic zones with a plausible place name -- this is nearest-neighbour
# lookup against a small hardcoded list, not real reverse geocoding.
REGION_LOOKUP = [
    ("Chandigarh", 30.7333, 76.7794),
    ("Mohali", 30.7046, 76.7179),
    ("Panchkula", 30.6942, 76.8606),
    ("Ludhiana", 30.9010, 75.8573),
    ("Jalandhar", 31.3260, 75.5762),
    ("Patiala", 30.3398, 76.3869),
    ("Amritsar", 31.6340, 74.8723),
    ("Bathinda", 30.2110, 74.9455),
]


def nearest_region(lat, lon):
    name, _, _ = min(REGION_LOOKUP, key=lambda r: (r[1] - lat) ** 2 + (r[2] - lon) ** 2)
    return name


def classify_event(wind_speed_kmh, rainfall_mm):
    """Pick the dominant hazard label for display, based on which signal
    is furthest into its own extreme range. A real system would use the
    GNN's per-hazard-class output instead of this ratio heuristic."""
    wind_frac = wind_speed_kmh / 90.0
    rain_frac = rainfall_mm / 100.0
    return "Extreme Rainfall" if rain_frac >= wind_frac else "Extreme Wind"


def main():
    print("1/6  Generating synthetic ensemble (stand-in for NEPS-G/GEFS run)...")
    ens = generate_synthetic_ensemble(n_members=12, grid_h=45, grid_w=90, lead_times=4)
    clim = generate_synthetic_climatology(grid_h=45, grid_w=90)

    print("2/6  Building icosahedral mesh...")
    verts, edges = build_icosphere(subdivisions=3)  # ~642 nodes, fast for demo
    lat, lon = xyz_to_latlon(verts)
    mesh_latlon = np.stack([lat, lon], axis=-1)

    print("3/6  Resampling ensemble + climatology onto mesh, computing EFI...")
    lead_t = 0
    field_t = ens["field"][:, lead_t]  # [members, H, W]
    mesh_ensemble = np.stack([
        resample_grid_to_mesh(field_t[m], ens["lats"], ens["lons"], verts)
        for m in range(field_t.shape[0])
    ])
    mesh_clim = np.stack([
        resample_grid_to_mesh(clim[y], ens["lats"], ens["lons"], verts)
        for y in range(clim.shape[0])
    ])
    efi_scores = compute_efi(mesh_ensemble, mesh_clim)

    print("4/6  Running GNN anomaly tracker...")
    node_features = np.stack([
        mesh_ensemble.mean(axis=0),   # ensemble mean field
        mesh_ensemble.std(axis=0),    # ensemble spread
        efi_scores,                   # extremity signal
    ], axis=-1).astype(np.float32)

    edge_index = torch.tensor(edges.T, dtype=torch.long)
    x = torch.tensor(node_features)
    model = AnomalyTrackerGNN(in_features=3, hidden_dim=32, n_layers=3)

    ckpt_path = os.path.join("checkpoints", "gnn_tracker.pt")
    if os.path.exists(ckpt_path):
        print("     loading trained checkpoint...")
        model.load_state_dict(torch.load(ckpt_path))
    else:
        # A freshly-initialized (random-weight) GNN has no learned notion
        # of "anomaly" yet, so its output isn't spatially correlated with
        # the injected vortex and clustering finds nothing. Run a short
        # supervised warm-up on EFI-derived labels (same signal used for
        # real training in scripts/train_gnn.py) so the demo shows the
        # tracker actually working. For a real run, use a properly
        # trained checkpoint instead of this shortcut.
        print("     no checkpoint found -- running a quick warm-up fit"
              " (use scripts/train_gnn.py for a real training run)...")
        from data_pipeline.efi import flag_anomalies
        labels = torch.tensor(flag_anomalies(efi_scores, threshold=0.5).astype(np.float32))
        opt = torch.optim.Adam(model.parameters(), lr=5e-3)
        model.train()
        for _ in range(60):
            opt.zero_grad()
            pred, _ = model(x, edge_index)
            loss = torch.nn.functional.binary_cross_entropy(pred, labels)
            loss.backward()
            opt.step()

    model.eval()
    with torch.no_grad():
        anomaly_prob, displacement = model(x, edge_index)
    anomaly_prob = anomaly_prob.numpy()

    print("5/6  Clustering into bounding boxes / trajectory...")
    # eps_deg is generous because the demo mesh (subdivisions=3, ~642
    # nodes over the whole sphere) is coarse -- neighbouring flagged
    # nodes can be >10 degrees apart. Tighten this as mesh resolution
    # increases (more subdivisions -> denser nodes -> smaller eps_deg).
    threshold = max(0.5, float(np.quantile(anomaly_prob, 0.85)))
    boxes = cluster_and_box(mesh_latlon, anomaly_prob, threshold=threshold,
                             eps_deg=15.0, min_samples=3)
    print(f"     found {len(boxes)} candidate anomaly region(s)"
          f" (threshold={threshold:.2f})")

    if not boxes:
        # Fall back to the single highest-probability node so the rest of
        # the pipeline (downscaling, alerting) still has something to run
        # on -- keeps the demo runnable end-to-end even in edge cases.
        top = int(anomaly_prob.argmax())
        boxes = [{
            "lat_min": float(mesh_latlon[top, 0]), "lat_max": float(mesh_latlon[top, 0]),
            "lon_min": float(mesh_latlon[top, 1]), "lon_max": float(mesh_latlon[top, 1]),
            "centroid": [float(mesh_latlon[top, 0]), float(mesh_latlon[top, 1])],
            "n_nodes": 1,
        }]
        print("     (using top-probability node as fallback region)")

    print("6/6  Running diffusion downscaler on top region + writing alerts...")
    # out_channels=5: wind_u, wind_v, rainfall, temperature, humidity at
    # 5km resolution. A trained model outputs these in physical units
    # directly (that's the point of the diffusion downscaler); this demo
    # uses an untrained network, so we rescale its raw output into
    # plausible physical ranges purely for the dashboard to display --
    # replace with the real output of a trained checkpoint for production.
    downscaler = ConditionalDownscaler(out_channels=5, cond_channels=2, image_size=32, base_channels=16)
    downscaler.eval()
    zones = []
    for box in boxes[:3]:
        cond = torch.randn(1, 2, 32, 32)  # stand-in: upsampled coarse field + topography
        with torch.no_grad():
            hi_res = downscaler.sample(cond, out_channels=5, num_inference_steps=10)

        u, v, rain_raw, temp_raw, hum_raw = [hi_res[0, c] for c in range(5)]
        wind_speed_kmh = float(torch.hypot(u, v).mean()) * 20 + 15       # ~15-90 km/h range
        rainfall_mm = float(torch.relu(rain_raw).mean()) * 40             # ~0-100mm range
        temperature_c = float(torch.tanh(temp_raw.mean())) * 8 + 27       # ~19-35C range
        humidity_pct = float(torch.sigmoid(hum_raw.mean())) * 40 + 55     # ~55-95% range
        pressure_hpa = 1013 - wind_speed_kmh * 0.6                        # rough wind/pressure coupling
        intensity = float(np.clip(wind_speed_kmh / 90 * 0.5 + rainfall_mm / 100 * 0.5, 0, 1))

        zones.append({
            "centroid": box["centroid"],
            "radius_km": 5,
            "lead_time_days": int(ens["lead_times_days"][lead_t]),
            "intensity": intensity,
            "wind_speed_kmh": round(wind_speed_kmh, 1),
            "rainfall_mm": round(rainfall_mm, 1),
            "temperature_c": round(temperature_c, 1),
            "humidity_pct": round(humidity_pct, 1),
            "pressure_hpa": round(pressure_hpa, 1),
            "region_name": nearest_region(*box["centroid"]),
            "event_type": classify_event(wind_speed_kmh, rainfall_mm),
        })

    geojson = build_geojson(zones)
    os.makedirs("output", exist_ok=True)
    with open("output/alerts.geojson", "w") as f:
        json.dump(geojson, f, indent=2)

    print(f"Done. Wrote output/alerts.geojson with {len(zones)} alert zone(s).")
    print("Open dashboard/index.html in a browser to visualize.")


if __name__ == "__main__":
    main()
