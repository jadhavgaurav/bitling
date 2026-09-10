from pathlib import Path
from PIL import Image
import numpy as np

def chroma_key(im_path, out_path, tolerance=55, shadow_filter=True):
    im = Image.open(im_path).convert("RGBA")
    arr = np.array(im)
    
    # Target magenta is around R > 200, G < 60, B > 200
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    
    # Distance to magenta (255, 0, 255)
    dist = np.sqrt((r.astype(float) - 255)**2 + (g.astype(float) - 0)**2 + (b.astype(float) - 255)**2)
    is_magenta = dist < 120
    
    arr[is_magenta, 3] = 0
    
    # Also if shadow_filter is true, remove dark gray floor shadow if present
    # floor shadow is dark gray: low R, G, B near bottom
    if shadow_filter:
        h = arr.shape[0]
        bottom_region = slice(int(h * 0.75), h)
        sub = arr[bottom_region]
        is_gray_shadow = (sub[:, :, 0] < 80) & (sub[:, :, 1] < 80) & (sub[:, :, 2] < 80) & (np.abs(sub[:, :, 0].astype(int) - sub[:, :, 1].astype(int)) < 15)
        # only where not yellow pikachu feet
        sub[is_gray_shadow, 3] = 0
        arr[bottom_region] = sub
        
    result = Image.fromarray(arr)
    bbox = result.getbbox()
    if bbox:
        result = result.crop(bbox)
        
    result.save(out_path)
    print(f"Saved {out_path} with size {result.size}")
    return result

def main():
    adir = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758")
    
    # 1. Idle
    idle_raw = list(adir.glob("pikachu_pixel_sprite_*.jpg"))[0]
    chroma_key(idle_raw, adir / "pikachu_pristine_idle.png", shadow_filter=False)
    
    # 2. Attack charge
    atk_raw = list(adir.glob("pikachu_attack_sprite_*.jpg"))[0]
    chroma_key(atk_raw, adir / "pikachu_pristine_charge.png", shadow_filter=True)
    
    # 3. Dangling / Carried
    dangle_raw = list(adir.glob("pikachu_dangling_sprite_*.jpg"))[0]
    chroma_key(dangle_raw, adir / "pikachu_pristine_dangle.png", shadow_filter=False)

    # 4. Scamper / Run: crop one clean running frame from the sheet
    run_raw = list(adir.glob("pikachu_scamper_sprite_*.jpg"))[0]
    im_run = Image.open(run_raw).convert("RGBA")
    # The middle-left running Pikachu is at roughly (x: 20-380, y: 320-640)
    w, h = im_run.size
    cell1 = im_run.crop((int(w * 0.05), int(h * 0.33), int(w * 0.48), int(h * 0.65)))
    cell1_path = adir / "temp_run1.png"
    cell1.save(cell1_path)
    chroma_key(cell1_path, adir / "pikachu_pristine_run1.png", shadow_filter=True)
    cell1_path.unlink()

    cell2 = im_run.crop((int(w * 0.52), int(h * 0.33), int(w * 0.95), int(h * 0.65)))
    cell2_path = adir / "temp_run2.png"
    cell2.save(cell2_path)
    chroma_key(cell2_path, adir / "pikachu_pristine_run2.png", shadow_filter=True)
    cell2_path.unlink()

if __name__ == "__main__":
    main()
