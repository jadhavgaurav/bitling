#!/usr/bin/env python3
import cv2
import os
import numpy as np
from PIL import Image

adir = "/Users/a12345/.gemini/antigravity-ide/brain/4535171a-efe5-4b68-affe-9d00e2014a0e"
outdir = "/tmp/goku_all_forms"
os.makedirs(outdir, exist_ok=True)

sources = {
    "base_idle": f"{adir}/goku_base_idle_1788964376532.jpg",
    "base_kame_charge": f"{adir}/goku_adult_kame_charge_1788964514222.jpg",
    "base_kame_fire": f"{adir}/goku_adult_kame_fire_1788964805590.jpg",
    "base_kiblast": f"{adir}/goku_adult_kiblast_1788964846014.jpg",
    "ssj_idle": f"{adir}/goku_ssj_idle_1788964403647.jpg",
    "ssj_kame_charge": f"{adir}/goku_ssj_kame_charge_1788964896626.jpg",
    "ssj_kame_fire": f"{adir}/goku_ssj_kame_fire_1788964869449.jpg",
    "ssj_kiblast": f"{adir}/goku_ssj_kiblast_1788964924030.jpg",
    "ssj2_idle": f"{adir}/goku_ssj2_idle_1788964426976.jpg",
    "ssj3_idle": f"{adir}/goku_ssj3_idle_1788964455489.jpg",
    "ui_idle": f"{adir}/goku_ui_idle_1788964481384.jpg",
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

    # Threshold selection:
    if name == "ui_idle":
        min_d, max_d = 20.0, 32.0
    elif "kame_fire" in name:
        min_d, max_d = 12.0, 24.0
    elif "kiblast" in name:
        min_d, max_d = 14.0, 22.0
    else:
        min_d, max_d = 14.0, 20.0

    alpha = np.clip((diff - min_d) / (max_d - min_d) * 255.0, 0, 255).astype(np.uint8)

    # Clean dark halos between ki blast rays
    if "kiblast" in name:
        blast_region = np.zeros((h, w), dtype=bool)
        blast_region[:int(h*0.65), int(w*0.70):] = True
        cut_thresh = 90 if name == "base_kiblast" else 75
        alpha[blast_region & (diff < cut_thresh)] = 0

    # For semi-transparent pixels, unblend background so edges don't have dark fringe
    a_norm = (alpha.astype(np.float32) / 255.0)[:, :, None]
    unblended = np.where(a_norm > 0.05, (img.astype(np.float32) - (1.0 - a_norm) * bg) / np.maximum(a_norm, 0.05), img.astype(np.float32))
    unblended = np.clip(unblended, 0, 255).astype(np.uint8)

    rgba = cv2.cvtColor(unblended, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha

    # Crop to bounding box where alpha > 10
    y_indices, x_indices = np.where(alpha > 10)
    y1, y2 = max(0, y_indices.min() - 4), min(h, y_indices.max() + 5)
    x1, x2 = max(0, x_indices.min() - 4), min(w, x_indices.max() + 5)
    cropped = rgba[y1:y2, x1:x2]

    # Standardize height to 480px while maintaining aspect ratio
    ch, cw = cropped.shape[:2]
    target_h = 480
    target_w = int(cw * (target_h / ch))
    resized = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)

    # Soft feather on right edge for kame_fire so beam connects seamlessly
    if "kame_fire" in name:
        fade_w = 40
        ramp = np.linspace(1.0, 0.0, fade_w)
        for y in range(int(target_h * 0.55)):
            resized[y, -fade_w:, 3] = (resized[y, -fade_w:, 3].astype(np.float32) * ramp).astype(np.uint8)

    webp_path = f"{outdir}/{name}.webp"
    pil_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGRA2RGBA))
    pil_img.save(webp_path, "WEBP", quality=90, method=5)

    size = os.path.getsize(webp_path)
    print(f"Exported {name}.webp: {target_w}x{target_h}, {size:,} bytes")

print("All form sprites successfully built!")
