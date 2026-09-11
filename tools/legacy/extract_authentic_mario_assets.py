#!/usr/bin/env python3
"""Extract authentic NES/SNES Super Mario sprites from official game sheets
and scale with nearest-neighbor for a 100% pure game experience."""
import os
import json
import base64
from PIL import Image, ImageDraw

TOOLS_DIR = "/Users/a12345/Desktop/AI/Bitling/Tools"
OUT_DIR = os.path.join(TOOLS_DIR, "mario_extracted")
os.makedirs(OUT_DIR, exist_ok=True)

sheet_mario = Image.open(os.path.join(TOOLS_DIR, "mario_bros.png")).convert("RGBA")
sheet_items = Image.open(os.path.join(TOOLS_DIR, "item_objects.png")).convert("RGBA")
sheet_tiles = Image.open(os.path.join(TOOLS_DIR, "tile_set.png")).convert("RGBA")

# Helper to crop, trim transparency, and scale up cleanly with nearest neighbor
def extract_and_scale(sheet, rect, scale=4, pad_bottom=True):
    # rect: (x, y, w, h)
    x, y, w, h = rect
    crop = sheet.crop((x, y, x + w, y + h))
    
    # Scale up using Nearest Neighbor to keep sharp pixel art
    out_w, out_h = w * scale, h * scale
    scaled = crop.resize((out_w, out_h), Image.Resampling.NEAREST)
    return scaled

# Coordinates
crops = {
    # Small Mario (16px high)
    'small_idle': (sheet_mario, (178, 32, 12, 16)),
    'small_run': (sheet_mario, (80, 32, 15, 16)),
    'small_run2': (sheet_mario, (96, 32, 16, 16)),
    'small_jump': (sheet_mario, (144, 32, 16, 16)),
    'small_skid': (sheet_mario, (130, 32, 14, 16)),
    
    # Super Mario (32px high)
    'super_idle': (sheet_mario, (176, 0, 16, 32)),
    'super_run': (sheet_mario, (81, 0, 16, 32)),
    'super_run2': (sheet_mario, (97, 0, 15, 32)),
    'super_jump': (sheet_mario, (144, 0, 16, 32)),
    'super_skid': (sheet_mario, (128, 0, 16, 32)),
    
    # Fire Mario (32px high)
    'fire_idle': (sheet_mario, (176, 48, 16, 32)),
    'fire_run': (sheet_mario, (81, 48, 16, 32)),
    'fire_run2': (sheet_mario, (97, 48, 15, 32)),
    'fire_jump': (sheet_mario, (144, 48, 16, 32)),
    'fire_throw': (sheet_mario, (336, 48, 16, 32)),
    
    # Items
    'mushroom': (sheet_items, (0, 0, 16, 16)),
    'mushroom_1up': (sheet_items, (16, 0, 16, 16)),
    'flower': (sheet_items, (0, 32, 16, 16)),
    'star': (sheet_items, (1, 48, 15, 16)),
    'fireball': (sheet_items, (96, 144, 8, 8)),
    
    # Tiles
    'qblock': (sheet_tiles, (384, 0, 16, 16)),
    'qblock_hit': (sheet_tiles, (432, 0, 16, 16)),
    'coin': (sheet_tiles, (384, 16, 16, 16)),
    'pipe_top': (sheet_tiles, (0, 160, 32, 16)),
    'pipe_body': (sheet_tiles, (0, 176, 32, 16)),
}

# Scale factor: for Super Mario (32px), scale=4 gives 64x128 or 128x256
# Let's scale by 5 for crisp desktop presence
SCALE = 5

b64_dict = {}

for name, (sheet, rect) in crops.items():
    sc = SCALE
    if name == 'fireball':
        sc = SCALE * 2  # fireball is 8x8, so 10x gives 80x80
    scaled = extract_and_scale(sheet, rect, scale=sc)
    
    # Check if pipe composite needed
    out_path = os.path.join(OUT_DIR, f"{name}.png")
    scaled.save(out_path)
    
    with open(out_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
        b64_dict[name] = f"data:image/png;base64,{b64}"
        
    print(f"Extracted {name}: {scaled.size}")

# Build Full Green Pipe sprite (top + body)
pipe_top = extract_and_scale(sheet_tiles, (0, 160, 32, 16), scale=SCALE)
pipe_body = extract_and_scale(sheet_tiles, (0, 176, 32, 16), scale=SCALE)
pipe_full = Image.new("RGBA", (32 * SCALE, 32 * SCALE), (0, 0, 0, 0))
pipe_full.paste(pipe_top, (0, 0))
pipe_full.paste(pipe_body, (0, 16 * SCALE))
pipe_path = os.path.join(OUT_DIR, "pipe.png")
pipe_full.save(pipe_path)
with open(pipe_path, "rb") as f:
    b64_dict['pipe'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# Create Mario Avatar badge (120x120)
av = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
d = ImageDraw.Draw(av)
# Gold stadium outer ring
d.ellipse([2, 2, 118, 118], fill=(228, 34, 30, 255), outline=(255, 215, 0, 255), width=4)
# Inner retro sky blue circle
d.ellipse([7, 7, 113, 113], fill=(39, 145, 251, 255))
# 8-bit cloud background
d.rectangle([20, 56, 100, 76], fill=(255, 255, 255, 140))
d.ellipse([26, 44, 56, 74], fill=(255, 255, 255, 160))
d.ellipse([46, 34, 82, 74], fill=(255, 255, 255, 180))
d.ellipse([72, 46, 96, 74], fill=(255, 255, 255, 160))

# Mario Super standing bust
mario_super = extract_and_scale(sheet_mario, (176, 0, 16, 16), scale=5)  # Head & upper torso
mario_super = mario_super.resize((76, 76), Image.Resampling.NEAREST)
av.paste(mario_super, (22, 22), mario_super)

# Gold star emblem at bottom center
d.ellipse([46, 92, 74, 116], fill=(255, 215, 0, 255), outline=(210, 140, 0, 255), width=2)
# Draw star
d.polygon([
    (60, 95), (63, 102), (70, 102), (64, 106),
    (66, 113), (60, 108), (54, 113), (56, 106),
    (50, 102), (57, 102)
], fill=(255, 255, 255, 255))

av.save(os.path.join(OUT_DIR, "mario_avatar.png"))
av.save("/Users/a12345/Desktop/AI/Bitling/web/avatars/mario.png")
av.save("/Users/a12345/Desktop/AI/Bitling/docs/avatars/mario.png")
av.save("/Users/a12345/Desktop/AI/Bitling/Resources/avatars/mario.png")

with open(os.path.join(OUT_DIR, "mario_avatar.png"), "rb") as f:
    b64_dict['avatar'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# Save JSON bundle
json_path = os.path.join(TOOLS_DIR, "mario_sprites.json")
with open(json_path, "w") as f:
    json.dump(b64_dict, f)

print(f"Saved complete Mario sprite bundle with {len(b64_dict)} assets to {json_path}")
