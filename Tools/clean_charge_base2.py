from pathlib import Path
from PIL import Image
import numpy as np

adir = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758")
im = Image.open(adir / "pikachu_pristine_charge.png").convert("RGBA")
arr = np.array(im)
h, w = arr.shape[:2]

# Below y = 0.85*h
# Any pixel where R > 220, G > 220, B > 220 (white/light gray) is removed
sub = arr[int(h * 0.85):, :]
is_white = (sub[:, :, 0] > 200) & (sub[:, :, 1] > 200) & (sub[:, :, 2] > 200)
# Also outline pixels around the white base (black pixels that aren't touching feet)
# The feet are around x = 300 to 750
sub[is_white, 3] = 0

# Also erase anything below y = 790
arr[int(h * 0.85):, :] = sub
arr[int(h * 0.96):, :] = 0

cleaned = Image.fromarray(arr).crop(Image.fromarray(arr).getbbox())
cleaned.save(adir / "pikachu_pristine_charge.png")
print("Cleaned charge sprite:", cleaned.size)
