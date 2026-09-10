#!/usr/bin/env python3
import os
import io
import json
import base64
from PIL import Image, ImageDraw, ImageEnhance

def load_and_crop(path):
    im = Image.open(path)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    return im

def to_webp_b64(im, max_h=None, max_w=None):
    w, h = im.size
    scale = 1.0
    if max_h and h > max_h:
        scale = min(scale, max_h / h)
    if max_w and w > max_w:
        scale = min(scale, max_w / w)
    if scale < 1.0:
        new_size = (int(w * scale), int(h * scale))
        im = im.resize(new_size, Image.Resampling.LANCZOS)
    
    buf = io.BytesIO()
    im.save(buf, format='WEBP', quality=92, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')

def main():
    raw_dir = 'Tools/mario_3d_raw'
    
    # 1. Load 3D assets
    jamboree = load_and_crop(os.path.join(raw_dir, 'jamboree_mario.png'))
    super_stride = load_and_crop(os.path.join(raw_dir, 'super_idle.png'))
    super_jump = load_and_crop(os.path.join(raw_dir, 'jump_mario.png'))
    small_mario = load_and_crop(os.path.join(raw_dir, 'small_mario.png'))
    fire_full = load_and_crop(os.path.join(raw_dir, 'fire_mario_3dw.png'))
    
    # Separate Fire Mario body and fireball from fire_mario_3dw.png
    # In fire_full, fireball is on the right
    fw, fh = fire_full.size
    # Find gap in alpha
    alpha = fire_full.split()[-1]
    col_has_pixels = [any(alpha.getpixel((x, y)) > 10 for y in range(fh)) for x in range(fw)]
    gap_x = int(fw * 0.65)
    for x in range(int(fw * 0.55), fw - 1):
        if not col_has_pixels[x] and col_has_pixels[x+1]:
            gap_x = x + 1
            break
        elif col_has_pixels[x] and not col_has_pixels[x+1]:
            gap_x = x
            break

    fire_body = fire_full.crop((0, 0, gap_x, fh))
    fb_bbox = fire_body.getbbox()
    if fb_bbox:
        fire_body = fire_body.crop(fb_bbox)

    fireball = fire_full.crop((gap_x, 0, fw, fh))
    fb_proj_bbox = fireball.getbbox()
    if fb_proj_bbox:
        fireball = fireball.crop(fb_proj_bbox)

    mushroom = load_and_crop(os.path.join(raw_dir, 'movie_mushroom.png'))
    star = load_and_crop(os.path.join(raw_dir, 'super_star_3dw.png'))
    coin = load_and_crop(os.path.join(raw_dir, 'hd_coin.png'))
    pipe = load_and_crop(os.path.join(raw_dir, 'hd_pipe.png'))
    qblock = load_and_crop(os.path.join(raw_dir, 'qblock.png'))

    # Struck Question Mark block: bronze / shaded empty block
    qblock_hit = qblock.copy()
    enhancer = ImageEnhance.Color(qblock_hit)
    qblock_hit = enhancer.enhance(0.3)
    enhancer_b = ImageEnhance.Brightness(qblock_hit)
    qblock_hit = enhancer_b.enhance(0.7)

    # 2. Build WebP dictionary
    sprites = {
        'small_idle': to_webp_b64(small_mario, max_h=200),
        'super_idle': to_webp_b64(jamboree, max_h=280),
        'super_stride': to_webp_b64(super_stride, max_h=280),
        'super_jump': to_webp_b64(super_jump, max_h=280),
        'fire_throw': to_webp_b64(fire_body, max_h=280),
        'fireball': to_webp_b64(fireball, max_h=120),
        'mushroom': to_webp_b64(mushroom, max_h=140),
        'star': to_webp_b64(star, max_h=140),
        'coin': to_webp_b64(coin, max_h=140),
        'pipe': to_webp_b64(pipe, max_h=220),
        'qblock': to_webp_b64(qblock, max_h=140),
        'qblock_hit': to_webp_b64(qblock_hit, max_h=140),
    }

    # 3. Create 3D Movie Mario Avatar Badge (120x120)
    movie_mario = Image.open(os.path.join(raw_dir, 'movie_mario.png'))
    mw, mh = movie_mario.size
    bust = movie_mario.crop((int(mw * 0.12), 0, int(mw * 0.90), int(mh * 0.78)))

    target_size = (120, 120)
    badge = Image.new('RGBA', target_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    cx, cy, r = 60, 60, 56

    for rad in range(r, 0, -1):
        ratio = rad / r
        red = int(89 + (229 - 89) * (1 - ratio * 0.6))
        green = int(13 + (37 - 13) * (1 - ratio))
        blue = int(13 + (33 - 13) * (1 - ratio))
        draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(red, green, blue, 255))

    mask = Image.new('L', target_size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2], fill=255)

    bust.thumbnail((110, 110), Image.Resampling.LANCZOS)
    bx = (120 - bust.size[0]) // 2
    by = 120 - bust.size[1] - 4
    badge.paste(bust, (bx, by), bust)

    final_badge = Image.new('RGBA', target_size, (0, 0, 0, 0))
    final_badge.paste(badge, (0, 0), mask)

    draw_final = ImageDraw.Draw(final_badge)
    for w_offset, (cr, cg, cb, a) in enumerate([
        (255, 235, 120, 255),
        (245, 190, 20, 255),
        (190, 130, 10, 255),
        (120, 70, 5, 200)
    ]):
        draw_final.ellipse([cx - r - w_offset, cy - r - w_offset, cx + r + w_offset, cy + r + w_offset], outline=(cr, cg, cb, a), width=1)

    # Save avatars
    for av_path in ['web/avatars/mario.png', 'docs/avatars/mario.png', 'Resources/avatars/mario.png']:
        os.makedirs(os.path.dirname(av_path), exist_ok=True)
        final_badge.save(av_path)
        print('Saved avatar:', av_path)

    # Save JSON bundle
    with open('Tools/mario_3d_sprites.json', 'w') as f:
        json.dump(sprites, f, indent=2)
    print(f'Saved Tools/mario_3d_sprites.json with {len(sprites)} 3D sprites ({os.path.getsize("Tools/mario_3d_sprites.json")} bytes)')

if __name__ == '__main__':
    main()
