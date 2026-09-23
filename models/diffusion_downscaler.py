"""
Stage 2: Amplitude-preserving downscaler.

A small conditional DDPM: takes a coarse (12km) cropped anomaly patch
+ topography as conditioning, iteratively denoises a 5km-resolution
patch. Conditioning on topography (not just upsampling) plus training
on a loss that doesn't average over the ensemble is what keeps the
extreme peaks from being smoothed out, the way plain CNN/U-Net
super-resolution would.

Architecturally this follows the same idea as NVIDIA's CorrDiff and
Google's GenCast: diffusion models for weather because they model the
full conditional distribution instead of regressing to the mean.
"""
import math
import torch
import torch.nn as nn
from diffusers import UNet2DModel, DDPMScheduler


class ConditionalDownscaler(nn.Module):
    """Wraps a UNet2DModel; conditioning (coarse field + topography,
    both upsampled to the target grid) is concatenated as extra input
    channels -- a simple, effective way to condition a diffusion UNet."""

    def __init__(self, out_channels: int = 3, cond_channels: int = 2,
                 image_size: int = 64, base_channels: int = 64):
        super().__init__()
        # GroupNorm inside the UNet needs num_groups to evenly divide every
        # block's channel count; diffusers defaults norm_num_groups=32,
        # which breaks for small base_channels (e.g. 16). Pick the largest
        # group size <=8 that divides base_channels so small demo configs
        # (base_channels=16) and larger production ones both work.
        norm_num_groups = min(8, base_channels)
        while base_channels % norm_num_groups != 0:
            norm_num_groups -= 1

        self.unet = UNet2DModel(
            sample_size=image_size,
            in_channels=out_channels + cond_channels,
            out_channels=out_channels,
            layers_per_block=2,
            block_out_channels=(base_channels, base_channels * 2, base_channels * 4),
            down_block_types=("DownBlock2D", "AttnDownBlock2D", "DownBlock2D"),
            up_block_types=("UpBlock2D", "AttnUpBlock2D", "UpBlock2D"),
            norm_num_groups=norm_num_groups,
        )
        self.scheduler = DDPMScheduler(num_train_timesteps=1000)

    def forward(self, noisy_target, timesteps, condition):
        x = torch.cat([noisy_target, condition], dim=1)
        return self.unet(x, timesteps).sample

    @torch.no_grad()
    def sample(self, condition, out_channels=3, num_inference_steps=50, device="cpu"):
        """Iteratively denoise from Gaussian noise, conditioned on the
        coarse upsampled field + topography, to produce the 5km output."""
        b, _, h, w = condition.shape
        x = torch.randn(b, out_channels, h, w, device=device)
        self.scheduler.set_timesteps(num_inference_steps)
        for t in self.scheduler.timesteps:
            noise_pred = self.forward(x, t.to(device), condition)
            x = self.scheduler.step(noise_pred, t, x).prev_sample
        return x  # [B, out_channels, H, W] -- e.g. wind_u, wind_v, precip at 5km


def training_step(model: ConditionalDownscaler, clean_target, condition, device="cpu"):
    """One DDPM training step: add noise, predict it, MSE loss.
    Add `physics_loss.combined_physics_loss(...)` on the *predicted*
    denoised sample for the physics-informed variant."""
    b = clean_target.shape[0]
    noise = torch.randn_like(clean_target)
    timesteps = torch.randint(0, model.scheduler.config.num_train_timesteps, (b,), device=device)
    noisy = model.scheduler.add_noise(clean_target, noise, timesteps)
    noise_pred = model(noisy, timesteps, condition)
    return torch.nn.functional.mse_loss(noise_pred, noise)
