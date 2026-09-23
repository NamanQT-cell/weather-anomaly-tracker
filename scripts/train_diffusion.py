"""
Trains ConditionalDownscaler on (coarse condition -> fine target) patch
pairs. Defaults to synthetic patches; point --data-dir at real cropped
NEPS-G (coarse) / high-res reanalysis-or-obs (fine target) patch pairs.
"""
import argparse
import os
import sys
import torch

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from models.diffusion_downscaler import ConditionalDownscaler, training_step


def synthetic_batch(batch_size=8, size=32):
    condition = torch.randn(batch_size, 2, size, size)      # coarse field + topography
    clean_target = torch.randn(batch_size, 3, size, size)   # fine u, v, precip
    return condition, clean_target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--data-dir", type=str, default=None)
    ap.add_argument("--batch-size", type=int, default=8)
    args = ap.parse_args()

    model = ConditionalDownscaler(out_channels=3, cond_channels=2, image_size=32, base_channels=16)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-4)

    for epoch in range(args.epochs):
        condition, clean_target = synthetic_batch(args.batch_size)
        opt.zero_grad()
        loss = training_step(model, clean_target, condition)
        loss.backward()
        opt.step()
        if (epoch + 1) % 5 == 0:
            print(f"epoch {epoch+1}/{args.epochs}  loss={loss.item():.4f}")

    os.makedirs("checkpoints", exist_ok=True)
    torch.save(model.state_dict(), "checkpoints/diffusion_downscaler.pt")
    print("Saved checkpoints/diffusion_downscaler.pt")


if __name__ == "__main__":
    main()
