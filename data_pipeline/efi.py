"""
Extreme Forecast Index (EFI): how far the ensemble forecast distribution
diverges from the 30-year climatological (ERA5) distribution for the same
location/day-of-year, per mesh node. EFI in [-1, 1]; near +/-1 means the
whole ensemble sits in the tail of climatology -- a strong extremity signal.

Formula follows the ECMWF EFI definition (Lalaurette 2003): integrate the
signed difference between forecast CDF and climate CDF, weighted so the
tails count more than the centre of the distribution.
"""
import numpy as np


def compute_efi(ensemble_values: np.ndarray, climatology_values: np.ndarray,
                 n_quantiles: int = 101) -> np.ndarray:
    """
    ensemble_values:     [n_members, n_nodes] forecast ensemble at one lead time
    climatology_values:  [n_hist_years, n_nodes] historical values for that
                          day-of-year window (e.g. +/-15 days over 30 years)
    returns: [n_nodes] EFI score in [-1, 1]
    """
    n_nodes = ensemble_values.shape[1]
    efi = np.zeros(n_nodes)
    qs = np.linspace(0.01, 0.99, n_quantiles)

    for node in range(n_nodes):
        clim_q = np.quantile(climatology_values[:, node], qs)
        fcst_cdf = np.array([
            (ensemble_values[:, node] <= v).mean() for v in clim_q
        ])
        # weight tails more heavily than the centre
        weight = 1.0 / np.sqrt(qs * (1 - qs))
        weight /= weight.sum()
        efi[node] = np.sum(weight * (qs - fcst_cdf))

    return np.clip(efi, -1, 1)


def flag_anomalies(efi_scores: np.ndarray, threshold: float = 0.65) -> np.ndarray:
    """Boolean mask of mesh nodes exceeding the extremity threshold."""
    return np.abs(efi_scores) >= threshold
