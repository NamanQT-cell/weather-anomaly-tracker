# AI-Driven Spatio-Temporal Tracking of Extreme Weather Anomalies

Two-stage hybrid AI pipeline: a GNN tracks extreme-weather anomalies on a spherical
mesh over a 3–10 day ensemble forecast, then a conditional diffusion model
downscales the tracked region from 12km to 5km without smoothing out extremes.
Output is served through a FastAPI alerting API and a Leaflet dashboard.

```
data_pipeline/  -> load NWP ensemble data, build icosahedral mesh, compute EFI
models/         -> GNN anomaly tracker, diffusion downscaler, physics loss
api/            -> FastAPI alert service (GeoJSON out)
dashboard/      -> single-file Leaflet map dashboard
scripts/        -> end-to-end demo runner + training entrypoints
```

## Quickstart (synthetic-data demo — no credentials needed)

```bash
pip install -r requirements.txt
python scripts/run_demo.py
```

This generates a synthetic ensemble field standing in for a NEPS-G/GEFS run,
runs it through the GNN tracker, crops the detected anomaly, runs it through
the diffusion downscaler, and writes `output/alerts.geojson`. Open
`dashboard/index.html` in a browser (it loads that GeoJSON) to see the result.

## Plugging in real data

- **Global ensemble (12km)**: swap `data_pipeline/fetch_data.py`'s synthetic
  generator for a NOMADS/AWS Open Data GEFS pull, or NCMRWF's NEPS-G feed once
  you have MoES data-sharing access.
- **Climatological baseline for EFI**: pull ERA5 via the Copernicus CDS API
  (`cdsapi` package, free registration) — see `fetch_era5_baseline()` stub.
- **Validation truth**: NASA IMERG precipitation via GES DISC.
- **Topography conditioning for downscaling**: Copernicus DEM / SRTM tiles.

Each of these needs an account/API key that can't be provisioned from this
environment — the code paths are structured so you drop in real fetch calls
without touching the model code.

## Training

```bash
python scripts/train_gnn.py --epochs 20        # anomaly tracker
python scripts/train_diffusion.py --epochs 50  # downscaler
```

Both scripts default to synthetic data; point `--data-dir` at real
NEPS-G/ERA5-derived tensors once you have them (see `data_pipeline/`).

## API

```bash
uvicorn api.main:app --reload
# POST /forecast  { "run_id": "demo" } -> GeoJSON alert zones
```
