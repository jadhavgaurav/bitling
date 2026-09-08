import base64
from pathlib import Path
import re

def main():
    adir = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758")
    idle_png = adir / "goku_hd_idle_right.png"
    fly_png = adir / "goku_hd_fly_right.png"

    with open(idle_png, "rb") as f:
        idle_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

    with open(fly_png, "rb") as f:
        fly_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

    target_file = Path("web/bitling.html")
    content = target_file.read_text(encoding="utf-8")

    # 1. Replace GOKU_SPRITES definition
    pattern_sprites = r"const GOKU_SPRITES = \{[\s\S]*?\};"
    match = re.search(pattern_sprites, content)
    assert match, "GOKU_SPRITES block not found"

    new_sprites = f"const GOKU_SPRITES = {{\n    idle: '{idle_b64}',\n    fly: '{fly_b64}'\n  }};"
    content = content[:match.start()] + new_sprites + content[match.end():]

    # 2. Replace sprite rendering block in drawGoku
    old_render_block = """      // -------------------------------------------------------- Sprite Rendering
      if (sprite && sprite.complete && sprite.naturalWidth > 0) {
        ctx.save();
        ctx.imageSmoothingEnabled = false; // crisp pixel art
        const sw = sprite.naturalWidth;
        const sh = sprite.naturalHeight;

        // Maintain the EXACT same large heroic size whether sitting idle or flying/dragging
        // gokuImgIdle reference width is 66px, gokuImgFly reference width is 43px.
        const isFlySprite = (sprite === gokuImgFly);
        const baseRefW = isFlySprite ? 43 : 66;
        const drawScale = (r * 2.45) / baseRefW;
        const dw = sw * drawScale;
        const dh = sh * drawScale;

        // Cloud base alignment offset: aligns the cloud at the exact same grounded origin
        const yOffset = isFlySprite ? 0.72 : 0.68;
        ctx.drawImage(sprite, -dw / 2, -dh * yOffset, dw, dh);
        ctx.restore();
      }"""

    new_render_block = """      // -------------------------------------------------------- Sprite Rendering
      if (sprite && sprite.complete && sprite.naturalWidth > 0) {
        ctx.save();
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        const sw = sprite.naturalWidth;
        const sh = sprite.naturalHeight;

        // Maintain the EXACT same large heroic size whether sitting idle or flying/dragging
        const isFlySprite = (sprite === gokuImgFly);
        const targetW = r * (isFlySprite ? 2.75 : 2.5);
        const targetH = targetW * (sh / sw);

        // Cloud base alignment offset: aligns the cloud at the exact same grounded origin
        const yOffset = isFlySprite ? 0.88 : 0.86;
        ctx.drawImage(sprite, -targetW / 2, -targetH * yOffset, targetW, targetH);
        ctx.restore();
      }"""

    assert old_render_block in content, "old_render_block not found in content"
    content = content.replace(old_render_block, new_render_block, 1)

    target_file.write_text(content, encoding="utf-8")
    print("Successfully patched web/bitling.html with HD Goku assets!")

if __name__ == "__main__":
    main()
