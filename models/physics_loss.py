"""
Physics-informed penalty terms. These get added (weighted) to the
task loss (BCE for the tracker, denoising loss for the diffusion model)
so the networks are discouraged from producing physically impossible
states -- e.g. heavy precip with no corresponding moisture convergence.
"""
import torch


def moisture_convergence_penalty(precip: torch.Tensor, u_wind: torch.Tensor,
                                  v_wind: torch.Tensor, dx: float = 5000.0) -> torch.Tensor:
    """
    precip, u_wind, v_wind: [B, H, W] tensors (downscaled grid)
    dx: grid spacing in meters (5km target resolution)

    Penalizes precipitation predicted where wind-field divergence is
    positive (air is diverging, not converging moisture) -- a simplified
    stand-in for the full moisture-flux continuity equation. Swap in
    MetPy's `divergence` on real data for a physically exact term.
    """
    du_dx = torch.gradient(u_wind, dim=-1, spacing=dx)[0]
    dv_dy = torch.gradient(v_wind, dim=-2, spacing=dx)[0]
    divergence = du_dx + dv_dy

    # where divergence > 0 (diverging) but precip is high -> penalize
    violation = torch.relu(precip) * torch.relu(divergence)
    return violation.mean()


def energy_conservation_penalty(temp_field: torch.Tensor, coarse_temp_field: torch.Tensor) -> torch.Tensor:
    """Downscaled temperature field's spatial mean should match the coarse
    input's mean (energy shouldn't appear/disappear during downscaling)."""
    fine_mean = temp_field.mean(dim=(-2, -1))
    coarse_mean = coarse_temp_field.mean(dim=(-2, -1))
    return torch.nn.functional.mse_loss(fine_mean, coarse_mean)


def combined_physics_loss(precip, u_wind, v_wind, temp_fine, temp_coarse,
                           w_moisture=1.0, w_energy=1.0):
    return (w_moisture * moisture_convergence_penalty(precip, u_wind, v_wind)
            + w_energy * energy_conservation_penalty(temp_fine, temp_coarse))
