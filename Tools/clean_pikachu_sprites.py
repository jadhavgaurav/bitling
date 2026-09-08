from pathlib import Path
from PIL import Image
import numpy as np

adir = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758")

# 1. Clean run1
im_run = Image.open(adir / "pikachu_pristine_run1.png").convert("RGBA")
arr = np.array(im_run)
# Trim the bottom magenta/shadow strip (anything with purple/magenta tint or below y=240)
# Purplish/magenta is R > 100, B > 100, G < 80
is_strip = (arr[:, :, 0] > 100) & (arr[:, :, 2] > 100) & (arr[:, :, 1] < 80)
arr[is_strip, 3] = 0
# Bottom 15% clean
arr[int(arr.shape[0]*0.88):, :, 3] = 0
res_run = Image.fromarray(arr).crop(Image.fromarray(arr).getbbox())
res_run.save(adir / "pikachu_pristine_run.png")
print("Cleaned run sprite:", res_run.size)

# 2. Clean charge (remove the gray shadow under feet)
im_charge = Image.open(adir / "pikachu_pristine_charge.png").convert("RGBA")
arr_c = np.array(im_charge)
# Under feet (bottom 12%)
h, w = arr_c.shape[:2]
bottom_y = int(h * 0.88)
# Gray shadow has low saturation (R, G, B all close, between 30 and 150)
sub = arr_c[bottom_y:, :]
diff1 = np.abs(sub[:, :, 0].astype(int) - sub[:, :, 1].astype(int))
diff2 = np.abs(sub[:, :, 1].astype(int) - sub[:, :, 2].astype(int))
is_gray = (diff1 < 25) & (diff2 < 25) & (sub[:, :, 1] < 160)
sub[is_gray, 3] = 0
arr_c[bottom_y:, :] = sub
res_charge = Image.fromarray(arr_c).crop(Image.fromarray(arr_c).getbbox())
res_charge.save(adir / "pikachu_pristine_charge.png")
print("Cleaned charge sprite:", res_charge.size)

# 3. Clean idle
im_idle = Image.open(adir / "pikachu_pristine_idle.png").convert("RGBA")
bbox = im_idle.getbbox()
im_idle = im_idle.crop(bbox)
im_idle.save(adir / "pikachu_pristine_idle.png")
print("Cleaned idle sprite:", im_idle.size)

# 4. Clean dangle
im_dangle = Image.open(adir / "pikachu_pristine_dangle.png").convert("RGBA")
bbox_d = im_dangle.getbbox()
im_dangle = im_dangle.crop(bbox_d)
im_dangle.save(adir / "pikachu_pristine_dangle.png")
print("Cleaned dangle sprite:", im_dangle.size)
