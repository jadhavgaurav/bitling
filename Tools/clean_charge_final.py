from pathlib import Path
from PIL import Image
import numpy as np

adir = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758")
im = Image.open(adir / "pikachu_pristine_charge.png").convert("RGBA")
arr = np.array(im)
h, w = arr.shape[:2]

# Below y = 700:
# Left of x = 320: erase
arr[700:, :340, 3] = 0
# Right of x = 750: erase
arr[700:, 760:, 3] = 0
# Between feet (x between 400 and 640 below y = 710):
arr[710:, 390:640, 3] = 0
# Below feet (y > 775):
arr[775:, :, 3] = 0

cleaned = Image.fromarray(arr).crop(Image.fromarray(arr).getbbox())
cleaned.save(adir / "pikachu_pristine_charge.png")
print("Cleaned charge sprite:", cleaned.size)
