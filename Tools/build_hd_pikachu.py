#!/usr/bin/env python3
import cv2
import os
import numpy as np
from PIL import Image

adir = "/Users/a12345/.gemini/antigravity-ide/brain/f8f3c39d-54d9-4f31-a36d-c26a9c9f0cb8"
outdir = "/tmp/pikachu_hd"
os.makedirs(outdir, exist_ok=True)

sources = {
    "idle": f"{adir}/pikachu_hd_idle_1789016215498.jpg",
    "run": f"{adir}/pikachu_hd_run_1789016377289.jpg",
    "charge": f"{adir}/pikachu_hd_charge_1789016392528.jpg",
    "attack": f"{adir}/pikachu_hd_attack_1789016407907.jpg",
    "dangle": f"{adir}/pikachu_hd_dangle_1789016424609.jpg",
    "sleep": f"{adir}/pikachu_hd_sleep_1789016442736.jpg",
}

for name, path in sources.items():
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    h, w = img.shape[:2]

    # Sample background color from four corners
    bg = np.median([img[:15, :15].mean(axis=(0,1)),
                    img[:15, -15:].mean(axis=(0,1)),
                    img[-15:, :15].mean(axis=(0,1)),
                    img[-15:, -15:].mean(axis=(0,1))], axis=0)

    diff = np.linalg.norm(img.astype(np.float32) - bg, axis=2)

    # Threshold selection for clean alpha
    if name in ("charge", "attack"):
        min_d, max_d = 12.0, 22.0
    else:
        min_d, max_d = 14.0, 24.0

    alpha = np.clip((diff - min_d) / (max_d - min_d) * 255.0, 0, 255).astype(np.uint8)

    # For semi-transparent pixels, unblend background so edges don't have dark fringe
    a_norm = (alpha.astype(np.float32) / 255.0)[:, :, None]
    unblended = np.where(a_norm > 0.05, (img.astype(np.float32) - (1.0 - a_norm) * bg) / np.maximum(a_norm, 0.05), img.astype(np.float32))
    unblended = np.clip(unblended, 0, 255).astype(np.uint8)

    rgba = cv2.cvtColor(unblended, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha

    # Crop to bounding box where alpha > 10
    y_indices, x_indices = np.where(alpha > 10)
    y1, y2 = max(0, y_indices.min() - 3), min(h, y_indices.max() + 4)
    x1, x2 = max(0, x_indices.min() - 3), min(w, x_indices.max() + 4)
    cropped = rgba[y1:y2, x1:x2]

    # Standardize height to 440px while maintaining aspect ratio (or 260px for sleep, 360px for run)
    ch, cw = cropped.shape[:2]
    if name == "sleep":
        target_h = 260
    elif name == "run":
        target_h = 360
    else:
        target_h = 440
    target_w = int(cw * (target_h / ch))
    resized = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)

    # Soft feather right edge for attack blast
    if name == "attack":
        fade_w = 32
        ramp = np.linspace(1.0, 0.0, fade_w)
        resized[:, -fade_w:, 3] = (resized[:, -fade_w:, 3].astype(np.float32) * ramp).astype(np.uint8)

    webp_path = f"{outdir}/{name}.webp"
    pil_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGRA2RGBA))
    pil_img.save(webp_path, "WEBP", quality=90, method=5)

    size = os.path.getsize(webp_path)
    print(f"Exported {name}.webp: {target_w}x{target_h}, {size:,} bytes")

print("All HD Pikachu sprites successfully built!")
