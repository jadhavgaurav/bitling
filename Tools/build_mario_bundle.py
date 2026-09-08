#!/usr/bin/env python3
"""Build authentic Super Mario sprites in 16-bit Super Mario World / SMB3 palette.
Produces small, super, fire, items, and avatar."""
import os
import json
import base64
from PIL import Image, ImageDraw

TOOLS_DIR = "/Users/a12345/Desktop/AI/Bitling/Tools"
OUT_DIR = os.path.join(TOOLS_DIR, "mario_final_sprites")
os.makedirs(OUT_DIR, exist_ok=True)

sheet_mario = Image.open(os.path.join(TOOLS_DIR, "mario_bros.png")).convert("RGBA")
sheet_items = Image.open(os.path.join(TOOLS_DIR, "item_objects.png")).convert("RGBA")
sheet_tiles = Image.open(os.path.join(TOOLS_DIR, "tile_set.png")).convert("RGBA")

# Palette definitions
C_TRANS = (0, 0, 0, 0)
C_RED = (228, 34, 30, 255)
C_RED_DARK = (156, 14, 14, 255)
C_BLUE = (16, 75, 205, 255)
C_BLUE_DARK = (8, 40, 135, 255)
C_WHITE = (255, 255, 255, 255)
C_SKIN = (255, 205, 150, 255)
C_BROWN_HAIR = (50, 20, 8, 255)
C_BROWN_BOOT = (110, 50, 15, 255)
C_GOLD = (255, 215, 0, 255)
C_BLACK = (20, 20, 20, 255)
C_GREEN_PIPE = (40, 180, 40, 255)
C_GREEN_PIPE_LIP = (90, 230, 90, 255)
C_GREEN_PIPE_DARK = (15, 80, 15, 255)

def recolor_mario_sprite(crop, stage='super', is_small=False):
    w, h = crop.size
    out = Image.new("RGBA", (w, h), C_TRANS)
    
    is_fire = (stage == 'fire')
    
    for y in range(h):
        for x in range(w):
            p = crop.getpixel((x, y))
            if p[3] == 0:
                continue
            r, g, b = p[:3]
            
            # Skin / Hands:
            if r > 200 and g > 130 and b < 60:
                # In small mario or super mario: gloves vs face
                if not is_small and y > h * 0.55 and (x < w * 0.35 or x > w * 0.65):
                    out.putpixel((x, y), C_WHITE) # White gloves
                elif is_small and y > h * 0.65 and (x < w * 0.3 or x > w * 0.7):
                    out.putpixel((x, y), C_WHITE) # White gloves on small mario
                else:
                    out.putpixel((x, y), C_SKIN) # Face
            # Red color (Cap & Overalls in SMB1):
            elif r > 150 and g < 70:
                if y < h * (0.42 if is_small else 0.32):
                    # Cap
                    out.putpixel((x, y), C_WHITE if is_fire else C_RED)
                else:
                    # Overalls
                    out.putpixel((x, y), C_RED if is_fire else C_BLUE)
            # Brown/Green color (Shirt & Hair/Mustache & Boots):
            elif g > 80 and b < 50:
                if y < h * (0.50 if is_small else 0.44):
                    # Mustache & Hair
                    out.putpixel((x, y), C_BROWN_HAIR)
                elif y > h * (0.80 if is_small else 0.76):
                    # Boots
                    out.putpixel((x, y), C_BROWN_BOOT)
                else:
                    # Shirt & Sleeves
                    out.putpixel((x, y), C_WHITE if is_fire else C_RED)
            else:
                out.putpixel((x, y), p)
                
    # Add overalls buttons on Super / Fire Mario
    if not is_small:
        # Check standard button locations
        for by in range(int(h * 0.46), int(h * 0.56)):
            for bx in range(int(w * 0.3), int(w * 0.7)):
                if out.getpixel((bx, by)) == (C_RED if is_fire else C_BLUE):
                    # Add tiny gold button accent
                    if (bx in (int(w * 0.38), int(w * 0.62))) and by == int(h * 0.50):
                        out.putpixel((bx, by), C_GOLD)
    return out

# Sprite coordinates
crops_def = {
    # Small Mario
    'small_idle': ((178, 32, 12, 16), True, 'small'),
    'small_run': ((80, 32, 15, 16), True, 'small'),
    'small_run2': ((96, 32, 16, 16), True, 'small'),
    'small_jump': ((144, 32, 16, 16), True, 'small'),
    
    # Super Mario
    'super_idle': ((176, 0, 16, 32), False, 'super'),
    'super_run': ((81, 0, 16, 32), False, 'super'),
    'super_run2': ((97, 0, 15, 32), False, 'super'),
    'super_jump': ((144, 0, 16, 32), False, 'super'),
    
    # Fire Mario
    'fire_idle': ((176, 0, 16, 32), False, 'fire'),
    'fire_run': ((81, 0, 16, 32), False, 'fire'),
    'fire_run2': ((97, 0, 15, 32), False, 'fire'),
    'fire_jump': ((144, 0, 16, 32), False, 'fire'),
    'fire_throw': ((336, 0, 16, 32), False, 'fire'),
}

SCALE = 5 # 5x nearest neighbor scaling for crisp retro pixels
b64_dict = {}

for name, (rect, is_small, stage) in crops_def.items():
    x, y, w, h = rect
    crop = sheet_mario.crop((x, y, x + w, y + h))
    recolored = recolor_mario_sprite(crop, stage, is_small)
    
    # Scale with nearest neighbor
    scaled = recolored.resize((w * SCALE, h * SCALE), Image.Resampling.NEAREST)
    out_file = os.path.join(OUT_DIR, f"{name}.png")
    scaled.save(out_file)
    
    with open(out_file, "rb") as f:
        b64_dict[name] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# Render Items in 16-bit perfection:
# 1. Super Mushroom (16x16 -> 80x80)
mush_im = Image.new("RGBA", (16, 16), C_TRANS)
mush_d = ImageDraw.Draw(mush_im)
# Black outline dome
mush_d.rectangle([2, 1, 13, 8], fill=C_BLACK)
mush_d.rectangle([1, 2, 14, 9], fill=C_BLACK)
mush_d.rectangle([0, 3, 15, 10], fill=C_BLACK)
# Red dome
mush_d.rectangle([2, 2, 13, 8], fill=C_RED)
mush_d.rectangle([1, 3, 14, 9], fill=C_RED)
# White spots
mush_d.rectangle([5, 2, 10, 6], fill=C_WHITE)
mush_d.rectangle([1, 5, 3, 8], fill=C_WHITE)
mush_d.rectangle([12, 5, 14, 8], fill=C_WHITE)
# Stalk / Face
mush_d.rectangle([3, 10, 12, 14], fill=C_BLACK)
mush_d.rectangle([4, 10, 11, 14], fill=(255, 230, 195))
# Eyes
mush_d.rectangle([5, 11, 5, 13], fill=C_BLACK)
mush_d.rectangle([10, 11, 10, 13], fill=C_BLACK)
mush_scaled = mush_im.resize((80, 80), Image.Resampling.NEAREST)
mush_scaled.save(os.path.join(OUT_DIR, "mushroom.png"))
with open(os.path.join(OUT_DIR, "mushroom.png"), "rb") as f:
    b64_dict['mushroom'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# 2. Fire Flower (16x16 -> 80x80)
ff_im = Image.new("RGBA", (16, 16), C_TRANS)
ff_d = ImageDraw.Draw(ff_im)
# Petals (Red outside, Yellow inside, White center)
ff_d.ellipse([1, 1, 14, 10], fill=C_RED, outline=C_BLACK)
ff_d.ellipse([3, 2, 12, 9], fill=C_GOLD)
ff_d.ellipse([5, 3, 10, 8], fill=C_WHITE)
ff_d.rectangle([7, 4, 8, 7], fill=C_BLACK) # Eyes
# Stem & Leaves
ff_d.rectangle([7, 10, 8, 14], fill=(0, 180, 0))
ff_d.rectangle([3, 12, 12, 13], fill=(0, 180, 0))
ff_scaled = ff_im.resize((80, 80), Image.Resampling.NEAREST)
ff_scaled.save(os.path.join(OUT_DIR, "flower.png"))
with open(os.path.join(OUT_DIR, "flower.png"), "rb") as f:
    b64_dict['flower'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# 3. Super Star (16x16 -> 80x80)
star_im = Image.new("RGBA", (16, 16), C_TRANS)
star_d = ImageDraw.Draw(star_im)
star_d.polygon([
    (8, 0), (10, 5), (15, 6), (11, 10),
    (13, 15), (8, 12), (3, 15), (5, 10),
    (1, 6), (6, 5)
], fill=C_GOLD, outline=C_BLACK)
# Star eyes
star_d.rectangle([6, 6, 6, 9], fill=C_BLACK)
star_d.rectangle([9, 6, 9, 9], fill=C_BLACK)
star_scaled = star_im.resize((80, 80), Image.Resampling.NEAREST)
star_scaled.save(os.path.join(OUT_DIR, "star.png"))
with open(os.path.join(OUT_DIR, "star.png"), "rb") as f:
    b64_dict['star'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# 4. Question Mark Block (16x16 -> 80x80)
qb_crop = sheet_tiles.crop((384, 0, 400, 16)).copy()
qb_crop.putpixel((0, 0), (0, 0, 0, 0))
qb_crop.putpixel((1, 0), (228, 140, 20, 255))
qb_scaled = qb_crop.resize((80, 80), Image.Resampling.NEAREST)
qb_scaled.save(os.path.join(OUT_DIR, "qblock.png"))
with open(os.path.join(OUT_DIR, "qblock.png"), "rb") as f:
    b64_dict['qblock'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# 5. Empty / Hit Block (16x16 -> 80x80)
qbh_crop = sheet_tiles.crop((432, 0, 448, 16))
qbh_scaled = qbh_crop.resize((80, 80), Image.Resampling.NEAREST)
qbh_scaled.save(os.path.join(OUT_DIR, "qblock_hit.png"))
with open(os.path.join(OUT_DIR, "qblock_hit.png"), "rb") as f:
    b64_dict['qblock_hit'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# 6. Spinning Coin (16x16 -> 80x80)
coin_im = Image.new("RGBA", (16, 16), C_TRANS)
coin_d = ImageDraw.Draw(coin_im)
coin_d.ellipse([3, 1, 12, 14], fill=C_GOLD, outline=C_BLACK)
coin_d.ellipse([5, 3, 10, 12], fill=(255, 235, 100))
coin_d.rectangle([7, 5, 8, 10], fill=C_WHITE)
coin_scaled = coin_im.resize((80, 80), Image.Resampling.NEAREST)
coin_scaled.save(os.path.join(OUT_DIR, "coin.png"))
with open(os.path.join(OUT_DIR, "coin.png"), "rb") as f:
    b64_dict['coin'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# 7. Fireball (8x8 -> 64x64)
fb_crop = sheet_items.crop((96, 144, 104, 152))
fb_scaled = fb_crop.resize((64, 64), Image.Resampling.NEAREST)
fb_scaled.save(os.path.join(OUT_DIR, "fireball.png"))
with open(os.path.join(OUT_DIR, "fireball.png"), "rb") as f:
    b64_dict['fireball'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# 8. Green Warp Pipe (32x32 -> 160x160)
pipe_im = Image.new("RGBA", (32, 32), C_TRANS)
pipe_d = ImageDraw.Draw(pipe_im)
# Lip
pipe_d.rectangle([0, 0, 31, 14], fill=C_GREEN_PIPE, outline=C_BLACK)
pipe_d.rectangle([3, 1, 6, 13], fill=C_GREEN_PIPE_LIP)
pipe_d.rectangle([25, 1, 30, 13], fill=C_GREEN_PIPE_DARK)
# Body
pipe_d.rectangle([2, 14, 29, 31], fill=C_GREEN_PIPE, outline=C_BLACK)
pipe_d.rectangle([5, 15, 8, 30], fill=C_GREEN_PIPE_LIP)
pipe_d.rectangle([23, 15, 28, 30], fill=C_GREEN_PIPE_DARK)
pipe_scaled = pipe_im.resize((160, 160), Image.Resampling.NEAREST)
pipe_scaled.save(os.path.join(OUT_DIR, "pipe.png"))
with open(os.path.join(OUT_DIR, "pipe.png"), "rb") as f:
    b64_dict['pipe'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# 9. Avatar Badge (120x120)
av = Image.new("RGBA", (120, 120), C_TRANS)
av_d = ImageDraw.Draw(av)
# Gold stadium outer ring
av_d.ellipse([2, 2, 118, 118], fill=C_RED, outline=C_GOLD, width=4)
# Inner retro sky blue circle
av_d.ellipse([7, 7, 113, 113], fill=(39, 145, 251, 255))
# 8-bit cloud background
av_d.rectangle([20, 56, 100, 76], fill=(255, 255, 255, 140))
av_d.ellipse([26, 44, 56, 74], fill=(255, 255, 255, 160))
av_d.ellipse([46, 34, 82, 74], fill=(255, 255, 255, 180))
av_d.ellipse([72, 46, 96, 74], fill=(255, 255, 255, 160))

# Super Mario Bust
mario_super_bust = recolor_mario_sprite(sheet_mario.crop((176, 0, 192, 18)), 'super')
mario_super_bust = mario_super_bust.resize((80, 90), Image.Resampling.NEAREST)
av.paste(mario_super_bust, (20, 16), mario_super_bust)

# Gold star emblem at bottom center
av_d.ellipse([46, 92, 74, 116], fill=C_GOLD, outline=(210, 140, 0, 255), width=2)
# Draw white star
av_d.polygon([
    (60, 95), (63, 102), (70, 102), (64, 106),
    (66, 113), (60, 108), (54, 113), (56, 106),
    (50, 102), (57, 102)
], fill=C_WHITE)

av.save(os.path.join(OUT_DIR, "mario_avatar.png"))
av.save("/Users/a12345/Desktop/AI/Bitling/web/avatars/mario.png")
av.save("/Users/a12345/Desktop/AI/Bitling/docs/avatars/mario.png")
av.save("/Users/a12345/Desktop/AI/Bitling/Resources/avatars/mario.png")

with open(os.path.join(OUT_DIR, "mario_avatar.png"), "rb") as f:
    b64_dict['avatar'] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

# Write JSON bundle
json_path = os.path.join(TOOLS_DIR, "mario_sprites.json")
with open(json_path, "w") as f:
    json.dump(b64_dict, f)

print(f"Successfully generated complete 16-bit Super Mario bundle with {len(b64_dict)} sprites at {json_path}!")
