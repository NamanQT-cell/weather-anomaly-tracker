"""
Data fetch layer. Ships with a synthetic generator so the pipeline runs
end-to-end with no credentials. Each real-data function is a stub with the
exact call you'd make once you have access.
"""
import numpy as np


def generate_synthetic_ensemble(n_members=20, grid_h=91, grid_w=180,
                                 lead_times=8, seed=0,
                                 center_lat=30.7333, center_lon=76.7794):
    """Stand-in for a NEPS-G/GEFS pull: [members, lead_times, H, W] field
    (e.g. 10m wind speed) with an injected anomaly so the tracker has
    something real to find. Defaults to Chandigarh (30.7333N, 76.7794E)
    as the sample anomaly location -- pass your own center_lat/center_lon
    for a different region."""
    rng = np.random.default_rng(seed)
    lats = np.linspace(-90, 90, grid_h)
    lons = np.linspace(-180, 180, grid_w, endpoint=False)

    base = rng.normal(loc=8.0, scale=2.0, size=(n_members, lead_times, grid_h, grid_w))

    # inject a moving anomaly across lead times, starting at the given center
    drift_lat, drift_lon = -0.15, 0.35
    for t in range(lead_times):
        clat = center_lat + drift_lat * t
        clon = center_lon + drift_lon * t
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                d = np.hypot(lat - clat, lon - clon)
                bump = 35.0 * np.exp(-(d ** 2) / (2 * 3.0 ** 2))
                base[:, t, i, j] += bump * rng.normal(1.0, 0.15, n_members)

    return {"field": base, "lats": lats, "lons": lons,
            "variable": "wind_speed_10m", "lead_times_days": np.arange(1, lead_times + 1)}


def generate_synthetic_climatology(grid_h=91, grid_w=180, n_years=30, seed=1):
    rng = np.random.default_rng(seed)
    return rng.normal(loc=8.0, scale=2.0, size=(n_years, grid_h, grid_w))


# ---- Real-data stubs -------------------------------------------------

def fetch_gefs_ensemble(run_date: str, cycle: str = "00"):
    """Pull NCEP GEFS (public GEFS as a global-ensemble stand-in for
    NEPS-G) from AWS Open Data / NOMADS.
    Example: https://noaa-gefs-pds.s3.amazonaws.com/gefs.{run_date}/{cycle}/...
    Parse GRIB2 with xarray + cfgrib once downloaded.
    """
    raise NotImplementedError("Wire this to the NOMADS/AWS GEFS bucket or NCMRWF NEPS-G feed.")


def fetch_era5_baseline(variable: str, lat_range, lon_range, years):
    """Pull ERA5 climatology via the Copernicus CDS API.

    import cdsapi
    c = cdsapi.Client()
    c.retrieve('reanalysis-era5-single-levels', {...}, 'era5.nc')
    """
    raise NotImplementedError("Requires a free CDS API key: https://cds.climate.copernicus.eu")
