from pathlib import Path
from PIL import Image
import numpy as np

adir = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758")
im = Image.open(adir / "pikachu_pristine_charge.png").convert("RGBA")
arr = np.array(im)
h, w = arr.shape[:2]

# The white base is under y = int(h * 0.88)
# Yellow/orange feet have R > 180, G > 120, B < 60
bottom = arr[int(h * 0.86):, :]
is_not_foot = ~((bottom[:, :, 0] > 180) & (bottom[:, :, 1] > 120) & (bottom[:, :, 2] < 70)) & (bottom[:, :, 3] > 0)
# Make sure we don't erase black outlines of the foot
is_black = (bottom[:, :, 0] < 30) & (bottom[:, :, 1] < 30) & (bottom[:, :, 2] < 30)
# Erase white/gray floor platform
is_platform = (bottom[:, :, 0] > 160) & (bottom[:, :, 1] > 160) & (bottom[:, :, 2] > 160)
bottom[is_platform, 3] = 0

# Also erase anything below the bottom of the lowest foot pixel
arr[int(h * 0.86):, :] = bottom
# Crop to bounding box
im_cleaned = Image.fromarray(arr).crop(Image.fromarray(arr).getbbox())
im_cleaned.save(adir / "pikachu_pristine_charge.png")
print("Cleaned charge sprite:", im_cleaned.size)
