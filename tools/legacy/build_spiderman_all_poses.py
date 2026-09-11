#!/usr/bin/env python3
import cv2
import numpy as np
from PIL import Image
import os, base64, json

art_dir = "/Users/a12345/.gemini/antigravity-ide/brain/f8f3c39d-54d9-4f31-a36d-c26a9c9f0cb8/scratch"
out_dir = "/tmp/spiderman_poses"
os.makedirs(out_dir, exist_ok=True)

def standardize(img, target_h=420):
    h, w = img.shape[:2]
    # crop transparent borders
    alpha = img[:, :, 3]
    y_idx, x_idx = np.where(alpha > 12)
    if len(y_idx) > 0 and len(x_idx) > 0:
        y1, y2 = y_idx.min(), y_idx.max() + 1
        x1, x2 = x_idx.min(), x_idx.max() + 1
        cropped = img[y1:y2, x1:x2]
    else:
        cropped = img
    ch, cw = cropped.shape[:2]
    target_w = max(10, int(cw * (target_h / ch)))
    return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)

print("Loading raw transparent PNG assets...")

# 1. Idle Perch: 3-point gargoyle crouch on window titlebar
raw_idle = cv2.imread(f"{art_dir}/Spiderman-Picture-PNG-Transparent.png", cv2.IMREAD_UNCHANGED)
assert raw_idle is not None, "raw_idle not found"
p_idle = standardize(raw_idle, target_h=380)

# 2. Crawl: 4-point wall cling / scamper
raw_crawl = cv2.imread(f"{art_dir}/Spiderman-Picture-Download-PNG-Image.png", cv2.IMREAD_UNCHANGED)
assert raw_crawl is not None, "raw_crawl not found"
p_crawl = standardize(raw_crawl, target_h=400)

# 3. Swing Down: Downward pendulum dive holding web line
raw_swing_down = cv2.imread(f"{art_dir}/Spiderman-Picture-PNG-HD.png", cv2.IMREAD_UNCHANGED)
assert raw_swing_down is not None, "raw_swing_down not found"
p_swing_down = standardize(raw_swing_down, target_h=420)

# 4. Swing Up: Dynamic rising swing arc
raw_swing_up = cv2.imread(f"{art_dir}/files_22_4.png", cv2.IMREAD_UNCHANGED)
assert raw_swing_up is not None, "raw_swing_up not found"
p_swing_up = standardize(raw_swing_up, target_h=420)

# 5. Apex Flip: Mid-air layout acrobatic somersault
raw_flip = cv2.imread(f"{art_dir}/files_2_6.png", cv2.IMREAD_UNCHANGED)
assert raw_flip is not None, "raw_flip not found"
p_flip = standardize(raw_flip, target_h=410)

# 6. Dangle: Upside-down hanging pose from web line
raw_dangle = cv2.imread(f"{art_dir}/files_2_2.png", cv2.IMREAD_UNCHANGED)
assert raw_dangle is not None, "raw_dangle not found"
raw_dangle[1270:, :] = 0
p_dangle = standardize(raw_dangle, target_h=420)

# 7. Shoot: Signature double-wrist web shooter gesture firing forward
raw_shoot = cv2.imread(f"{art_dir}/files_22_1.png", cv2.IMREAD_UNCHANGED)
assert raw_shoot is not None, "raw_shoot not found"
p_shoot = standardize(raw_shoot, target_h=420)

# 8. Attack: Slingshot dive kick combat strike
raw_attack = cv2.imread(f"{art_dir}/Spiderman-Picture-PNG-Free-Download.png", cv2.IMREAD_UNCHANGED)
assert raw_attack is not None, "raw_attack not found"
p_attack = standardize(raw_attack, target_h=420)

# 9. Sleep: Calm resting posture with dimming for sleep state
p_sleep = p_idle.copy()
sh, sw = p_sleep.shape[:2]
# slight relax angle
M_sleep = cv2.getRotationMatrix2D((sw // 2, sh // 2), 4, 0.98)
p_sleep = cv2.warpAffine(p_sleep, M_sleep, (sw, sh), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
alpha_s = p_sleep[:, :, 3] > 0
# Dim color channels slightly for resting night state
p_sleep[alpha_s, 0] = np.clip(p_sleep[alpha_s, 0].astype(np.float32) * 0.85, 0, 255).astype(np.uint8)
p_sleep[alpha_s, 1] = np.clip(p_sleep[alpha_s, 1].astype(np.float32) * 0.85, 0, 255).astype(np.uint8)
p_sleep[alpha_s, 2] = np.clip(p_sleep[alpha_s, 2].astype(np.float32) * 0.88, 0, 255).astype(np.uint8)
p_sleep = standardize(p_sleep, target_h=360)

poses = {
    "idle": p_idle,
    "crawl": p_crawl,
    "swing_down": p_swing_down,
    "swing_up": p_swing_up,
    "apex_flip": p_flip,
    "dangle": p_dangle,
    "shoot": p_shoot,
    "attack": p_attack,
    "sleep": p_sleep
}

print("Encoding poses to WebP...")
b64_dict = {}
for name, img in poses.items():
    png_path = f"{out_dir}/{name}.png"
    webp_path = f"{out_dir}/{name}.webp"
    cv2.imwrite(png_path, img)
    # Convert to PIL and save optimized WebP
    pil_img = Image.open(png_path)
    pil_img.save(webp_path, "WEBP", quality=90, method=6)
    
    with open(webp_path, "rb") as f:
        raw_b64 = base64.b64encode(f.read()).decode("ascii")
        b64_dict[name] = f"data:image/webp;base64,{raw_b64}"
    
    sz = os.path.getsize(webp_path)
    print(f"Pose '{name}': {img.shape[1]}x{img.shape[0]}, WebP size: {sz/1024:.1f} KB")

# 10. Avatar generation: 256x256 circular/transparent bust icon
ah, aw = raw_shoot.shape[:2]
head_crop = raw_shoot[int(ah*0.08):int(ah*0.52), int(aw*0.18):int(aw*0.82)]
head_alpha = head_crop[:, :, 3]
y_idx, x_idx = np.where(head_alpha > 12)
if len(y_idx) > 0:
    head_crop = head_crop[y_idx.min():y_idx.max()+1, x_idx.min():x_idx.max()+1]
hch, hcw = head_crop.shape[:2]
max_dim = max(hch, hcw)
square_avatar = np.zeros((max_dim, max_dim, 4), dtype=np.uint8)
oy = (max_dim - hch) // 2
ox = (max_dim - hcw) // 2
square_avatar[oy:oy+hch, ox:ox+hcw] = head_crop
avatar_256 = cv2.resize(square_avatar, (256, 256), interpolation=cv2.INTER_AREA)

# Save avatars to required Bitling paths
avatar_paths = [
    f"{out_dir}/avatar.png",
    "Resources/avatars/spiderman.png",
    "web/avatars/spiderman.png",
    "docs/avatars/spiderman.png"
]
for p in avatar_paths:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    cv2.imwrite(p, avatar_256)
    print(f"Saved avatar to {p}")

# Save JSON dictionary
json_path = f"{out_dir}/spiderman_all_poses_b64.json"
with open(json_path, "w") as f:
    json.dump(b64_dict, f, indent=2)

total_kb = sum(os.path.getsize(f"{out_dir}/{k}.webp") for k in poses) / 1024
print(f"All 9 poses + avatar built successfully! Total bundle size: {total_kb:.1f} KB")
