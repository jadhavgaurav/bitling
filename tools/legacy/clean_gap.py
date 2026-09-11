from pathlib import Path
from PIL import Image
import numpy as np

adir = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758")
im = Image.open(adir / "pikachu_pristine_charge.png").convert("RGBA")
arr = np.array(im)
arr[715:, 390:740, 3] = 0
cleaned = Image.fromarray(arr).crop(Image.fromarray(arr).getbbox())
cleaned.save(adir / "pikachu_pristine_charge.png")
print("Cleaned gap between feet:", cleaned.size)
