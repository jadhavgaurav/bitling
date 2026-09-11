#!/usr/bin/env python3
import cv2
import numpy as np
from PIL import Image
import os, base64

art_dir = "/Users/a12345/.gemini/antigravity-ide/brain/f8f3c39d-54d9-4f31-a36d-c26a9c9f0cb8"
out_dir = "/tmp/thor_poses"
os.makedirs(out_dir, exist_ok=True)

# Base images
im_mjolnir = cv2.imread(f"{art_dir}/sprite_mjolnir.png", cv2.IMREAD_UNCHANGED)
im_stormbreaker = cv2.imread(f"{art_dir}/sprite_stormbreaker.png", cv2.IMREAD_UNCHANGED)
im_fly = cv2.imread(f"{art_dir}/sprite_fly.png", cv2.IMREAD_UNCHANGED)
im_attack = cv2.imread(f"{art_dir}/sprite_attack.png", cv2.IMREAD_UNCHANGED)

def standardize(img, target_h=420):
    h, w = img.shape[:2]
    # crop transparent borders
    alpha = img[:, :, 3]
    y_idx, x_idx = np.where(alpha > 15)
    if len(y_idx) > 0 and len(x_idx) > 0:
        y1, y2 = y_idx.min(), y_idx.max() + 1
        x1, x2 = x_idx.min(), x_idx.max() + 1
        cropped = img[y1:y2, x1:x2]
    else:
        cropped = img
    ch, cw = cropped.shape[:2]
    target_w = max(10, int(cw * (target_h / ch)))
    return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)

# 1. Idle (Mjolnir)
p_idle = standardize(im_mjolnir)

# 2. Fly (Mjolnir) - Streamlined horizontal supersonic flight with Mjolnir leading
h_fly, w_fly = im_fly.shape[:2]
M_fly = cv2.getRotationMatrix2D((w_fly // 2, h_fly // 2), -22, 0.96)
im_fly_streamlined = cv2.warpAffine(im_fly, M_fly, (w_fly, h_fly), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
p_fly = standardize(im_fly_streamlined)

# 3. Charge (Mjolnir) - Raising Mjolnir high to the sky summoning lightning
p_charge = standardize(im_fly)
# Add electric glow to hammerhead in charge pose
cv2.circle(p_charge, (int(p_charge.shape[1]*0.68), int(p_charge.shape[0]*0.12)), 45, (255, 240, 180, 200), -1)
# Blend glow
glow = np.zeros_like(p_charge, dtype=np.float32)
cv2.circle(glow, (int(p_charge.shape[1]*0.68), int(p_charge.shape[0]*0.12)), 60, (255, 220, 120, 220), -1)
glow = cv2.GaussianBlur(glow, (35, 35), 0)
alpha_mask = (glow[:, :, 3] / 255.0)[:, :, None]
p_charge[:, :, :3] = np.clip(p_charge[:, :, :3].astype(np.float32) * (1 - alpha_mask*0.7) + glow[:, :, :3] * alpha_mask*0.7, 0, 255).astype(np.uint8)

# 4. Attack (Mjolnir)
p_attack = standardize(im_attack)

# 5. Stormbreaker Idle
p_sb_idle = standardize(im_stormbreaker)

# 6. Stormbreaker Fly - Streamlined battleaxe forward flight
h, w = p_sb_idle.shape[:2]
M_sb = cv2.getRotationMatrix2D((w // 2, h // 2), -24, 0.95)
p_sb_fly = cv2.warpAffine(p_sb_idle, M_sb, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
p_sb_fly = standardize(p_sb_fly)

# 7. Stormbreaker Attack
# Dynamic two-handed cleave with electric surge
p_sb_attack = p_sb_idle.copy()
# Add lightning blade glow
blade_x = int(p_sb_attack.shape[1] * 0.8)
blade_y = int(p_sb_attack.shape[0] * 0.45)
cv2.circle(p_sb_attack, (blade_x, blade_y), 50, (255, 230, 150, 180), -1)
glow_sb = np.zeros_like(p_sb_attack, dtype=np.float32)
cv2.circle(glow_sb, (blade_x, blade_y), 70, (255, 210, 100, 240), -1)
glow_sb = cv2.GaussianBlur(glow_sb, (41, 41), 0)
a_mask_sb = (glow_sb[:, :, 3] / 255.0)[:, :, None]
p_sb_attack[:, :, :3] = np.clip(p_sb_attack[:, :, :3].astype(np.float32) * (1 - a_mask_sb*0.8) + glow_sb[:, :, :3] * a_mask_sb*0.8, 0, 255).astype(np.uint8)

# 8. Dangle (Carried / Grabbed by user)
# Thor hanging down with arms slightly outward and legs dangling vertically under gravity
p_dangle = p_idle.copy()
dh, dw = p_dangle.shape[:2]
p_dangle = cv2.resize(p_dangle, (dw, int(dh * 1.05)), interpolation=cv2.INTER_LINEAR)
p_dangle = standardize(p_dangle)

# 9. Sleep (Asleep / Resting)
# Thor with calm relaxed posture, dimmed armor, resting
p_sleep = p_idle.copy()
# Dim slightly for night/sleeping calm
sh, sw = p_sleep.shape[:2]
M_sleep = cv2.getRotationMatrix2D((sw // 2, sh // 2), 5, 0.98)
p_sleep = cv2.warpAffine(p_sleep, M_sleep, (sw, sh), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
alpha_s = p_sleep[:, :, 3] > 0
p_sleep[alpha_s, 0] = np.clip(p_sleep[alpha_s, 0].astype(np.float32) * 0.88, 0, 255).astype(np.uint8)
p_sleep[alpha_s, 1] = np.clip(p_sleep[alpha_s, 1].astype(np.float32) * 0.88, 0, 255).astype(np.uint8)
p_sleep[alpha_s, 2] = np.clip(p_sleep[alpha_s, 2].astype(np.float32) * 0.92, 0, 255).astype(np.uint8)
p_sleep = standardize(p_sleep)

poses = {
    "idle": p_idle,
    "fly": p_fly,
    "charge": p_charge,
    "attack": p_attack,
    "sb_idle": p_sb_idle,
    "sb_fly": p_sb_fly,
    "sb_attack": p_sb_attack,
    "dangle": p_dangle,
    "sleep": p_sleep
}

b64_dict = {}
for name, img in poses.items():
    png_path = f"{out_dir}/{name}.png"
    webp_path = f"{out_dir}/{name}.webp"
    cv2.imwrite(png_path, img)
    pil_im = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA))
    pil_im.save(webp_path, "WEBP", quality=90, method=5)
    with open(webp_path, "rb") as f:
        b64 = "data:image/webp;base64," + base64.b64encode(f.read()).decode("ascii")
    b64_dict[name] = b64
    print(f"Generated pose {name}: {img.shape[1]}x{img.shape[0]}, b64 len: {len(b64)}")

import json
with open("/tmp/thor_all_poses_b64.json", "w") as f:
    json.dump(b64_dict, f)
print("Successfully generated all 9 Thor poses!")
