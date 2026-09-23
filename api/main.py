"""
Alerting API: turns the pipeline's output boxes/centroids into
categorized (low/moderate/severe) GeoJSON alert zones with a 5km radius,
ready for a map frontend or downstream SMS/push integration.
"""
import json
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Extreme Weather Anomaly Alert API")

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "alerts.geojson")


class ForecastRequest(BaseModel):
    run_id: str = "demo"


def severity_from_intensity(value: float) -> str:
    if value >= 0.85:
        return "severe"
    if value >= 0.65:
        return "moderate"
    return "low"


@app.post("/forecast")
def get_forecast(req: ForecastRequest):
    """Returns the most recently generated alert GeoJSON. In production
    this triggers/reads a fresh pipeline run keyed by run_id; for the
    demo it serves the file written by scripts/run_demo.py."""
    if not os.path.exists(OUTPUT_PATH):
        return {"error": "No pipeline output yet. Run scripts/run_demo.py first."}
    with open(OUTPUT_PATH) as f:
        return json.load(f)


@app.get("/health")
def health():
    return {"status": "ok"}


def build_geojson(alert_zones: list) -> dict:
    """alert_zones: list of dicts with centroid [lat, lon], radius_km,
    intensity (0-1), lead_time_days, plus whatever downscaled met
    variables are available (wind_speed_kmh, rainfall_mm, humidity_pct,
    temperature_c, pressure_hpa) -> standard GeoJSON FeatureCollection.
    Any variable not present on a zone is simply omitted from its
    properties -- the frontend handles missing fields gracefully."""
    features = []
    for zone in alert_zones:
        lat, lon = zone["centroid"]
        props = {
            "severity": severity_from_intensity(zone["intensity"]),
            "radius_km": zone.get("radius_km", 5),
            "lead_time_days": zone.get("lead_time_days"),
            "intensity": zone["intensity"],
        }
        for key in ("wind_speed_kmh", "rainfall_mm", "humidity_pct",
                    "temperature_c", "pressure_hpa", "region_name", "event_type"):
            if key in zone:
                props[key] = zone[key]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}
