#!/usr/bin/env python3
import base64

outdir = "/tmp/goku_all_forms"
def get_b64(name):
    with open(f"{outdir}/{name}.webp", "rb") as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode("ascii")

b64_base_idle = get_b64("base_idle")
b64_base_kame_charge = get_b64("base_kame_charge")
b64_base_kame_fire = get_b64("base_kame_fire")
b64_base_kiblast = get_b64("base_kiblast")

b64_ssj_idle = get_b64("ssj_idle")
b64_ssj_kame_charge = get_b64("ssj_kame_charge")
b64_ssj_kame_fire = get_b64("ssj_kame_fire")
b64_ssj_kiblast = get_b64("ssj_kiblast")

b64_ssj2_idle = get_b64("ssj2_idle")
b64_ssj3_idle = get_b64("ssj3_idle")
b64_ui_idle = get_b64("ui_idle")

with open("web/bitling.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Locate start of GOKU_SPRITES and the end of drawGokuCharacter
start_anchor = "  const GOKU_SPRITES = {"
start_idx = content.find(start_anchor)
assert start_idx != -1, "start_anchor not found"

# Find end of Kid Goku original sprites: "kiBlast: 'data:image/png;base64,"
kiblast_needle = "kiBlast: 'data:image/png;base64,"
kiblast_idx = content.find(kiblast_needle, start_idx)
assert kiblast_idx != -1, "kiblast_needle not found"

# Find closing of kiBlast string and closing of GOKU_SPRITES
end_sprites_idx = content.find("};", kiblast_idx)
assert end_sprites_idx != -1, "end of GOKU_SPRITES not found"

# Extract Kid Goku's original sprites block (inner content)
kid_block = content[start_idx + len(start_anchor):end_sprites_idx].strip()

# Find where drawGokuCharacter ends and drawGoku begins
draw_goku_needle = "  function drawGoku() {"
draw_goku_idx = content.find(draw_goku_needle, end_sprites_idx)
assert draw_goku_idx != -1, "draw_goku_needle not found"

# Build replacement code for sprites and image initializations
new_sprites_code = f"""  const GOKU_SPRITES = {{
    kid: {{
      {kid_block}
    }},
    base: {{
      idle: '{b64_base_idle}',
      fly: '{b64_base_idle}',
      kameCharge: '{b64_base_kame_charge}',
      kameFire: '{b64_base_kame_fire}',
      kiBlast: '{b64_base_kiblast}'
    }},
    ssj: {{
      idle: '{b64_ssj_idle}',
      fly: '{b64_ssj_idle}',
      kameCharge: '{b64_ssj_kame_charge}',
      kameFire: '{b64_ssj_kame_fire}',
      kiBlast: '{b64_ssj_kiblast}'
    }},
    ssj2: {{
      idle: '{b64_ssj2_idle}',
      fly: '{b64_ssj2_idle}',
      kameCharge: '{b64_ssj_kame_charge}',
      kameFire: '{b64_ssj_kame_fire}',
      kiBlast: '{b64_ssj_kiblast}'
    }},
    ssj3: {{
      idle: '{b64_ssj3_idle}',
      fly: '{b64_ssj3_idle}',
      kameCharge: '{b64_ssj_kame_charge}',
      kameFire: '{b64_ssj_kame_fire}',
      kiBlast: '{b64_ssj_kiblast}'
    }},
    ui: {{
      idle: '{b64_ui_idle}',
      fly: '{b64_ui_idle}',
      kameCharge: '{b64_base_kame_charge}',
      kameFire: '{b64_base_kame_fire}',
      kiBlast: '{b64_base_kiblast}'
    }}
  }};

  const gokuFormImages = {{}};
  for (const [fKey, sMap] of Object.entries(GOKU_SPRITES)) {{
    gokuFormImages[fKey] = {{}};
    for (const [sKey, src] of Object.entries(sMap)) {{
      const img = new Image();
      img.src = src;
      gokuFormImages[fKey][sKey] = img;
    }}
  }}
  // Backward compatibility alias for tests
  const gokuImgIdle = gokuFormImages.kid.idle;
  const gokuImgFly = gokuFormImages.kid.fly;
  const gokuImgKameCharge = gokuFormImages.kid.kameCharge;
  const gokuImgKameFire = gokuFormImages.kid.kameFire;
  const gokuImgKiBlast = gokuFormImages.kid.kiBlast;

  function drawLightningArcs(r, t, count, color1, color2, radiusMult) {{
    ctx.save();
    ctx.strokeStyle = color1 || '#ffffff';
    ctx.lineWidth = Math.max(1.5, r * 0.045);
    ctx.shadowColor = color2 || '#67e8f9';
    ctx.shadowBlur = 10;
    for (let i = 0; i < count; i++) {{
      const seed = t * 14 + i * 2.17;
      if (Math.sin(seed * 7) < 0.25) continue;
      const ang = (i / count) * Math.PI * 2 + Math.sin(seed) * 0.5;
      const r1 = r * (0.45 + Math.cos(seed * 3) * 0.15) * (radiusMult || 1);
      const r2 = r * (1.05 + Math.sin(seed * 4) * 0.25) * (radiusMult || 1);
      const cy = -r * 1.35;
      const x1 = Math.cos(ang) * r1;
      const y1 = cy + Math.sin(ang) * r1;
      const mx = Math.cos(ang + 0.3) * (r1 + r2) * 0.5 + Math.sin(seed * 9) * (r * 0.12);
      const my = cy + Math.sin(ang + 0.3) * (r1 + r2) * 0.5 + Math.cos(seed * 9) * (r * 0.12);
      const x2 = Math.cos(ang) * r2;
      const y2 = cy + Math.sin(ang) * r2;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(mx, my);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }}
    ctx.restore();
  }}

  function drawGokuAura(r, t, formIndex, gPower, charging, firing, isKame, isTransforming, isPowerUp) {{
    const intensity = gPower.auraIntensity;
    if (intensity <= 0.1 && !charging && !firing && !isTransforming && !isPowerUp) return;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    const cy = -r * 1.35;
    const pulse = 1 + Math.sin(t * 16) * 0.08 * (isPowerUp || isTransforming ? 1.8 : 1);

    if (formIndex === 5) {{
      const auraR = r * (1.1 + intensity * 0.25) * pulse;
      const grad = ctx.createRadialGradient(0, cy, r * 0.2, 0, cy, auraR * 1.2);
      grad.addColorStop(0, `hsla(210, 100%, 95%, ${{clamp(0.85 * intensity, 0, 0.95)}})`);
      grad.addColorStop(0.35, `hsla(215, 100%, 80%, ${{clamp(0.55 * intensity, 0, 0.85)}})`);
      grad.addColorStop(0.7, `hsla(225, 90%, 65%, ${{clamp(0.25 * intensity, 0, 0.6)}})`);
      grad.addColorStop(1, 'hsla(230, 80%, 50%, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.ellipse(0, cy, auraR * 0.95, auraR * 1.15, 0, 0, Math.PI * 2);
      ctx.fill();

      // Celestial silver motes
      const moteCount = Math.floor(6 + intensity * 6);
      ctx.fillStyle = '#ffffff';
      for (let i = 0; i < moteCount; i++) {{
        const mp = (t * 2.5 + i * (Math.PI * 2 / moteCount)) % (Math.PI * 2);
        const mx = Math.sin(mp * 3 + i) * r * 0.85;
        const my = cy + Math.cos(mp * 2) * r * 1.1;
        const msize = Math.max(1.2, r * 0.035 * (1 + Math.sin(t * 12 + i)));
        ctx.beginPath();
        ctx.arc(mx, my, msize, 0, Math.PI * 2);
        ctx.fill();
      }}
    }} else if (formIndex >= 2) {{
      const auraR = r * (0.95 + intensity * 0.35) * pulse;
      const hue = formIndex === 4 ? 45 : 48;
      const grad = ctx.createRadialGradient(0, cy, r * 0.2, 0, cy, auraR * 1.15);
      grad.addColorStop(0, `hsla(${{hue}}, 100%, 90%, ${{clamp(0.75 * intensity, 0, 0.9)}})`);
      grad.addColorStop(0.4, `hsla(${{hue - 4}}, 100%, 65%, ${{clamp(0.48 * intensity, 0, 0.75)}})`);
      grad.addColorStop(0.75, `hsla(${{hue - 10}}, 100%, 50%, ${{clamp(0.22 * intensity, 0, 0.45)}})`);
      grad.addColorStop(1, `hsla(${{hue - 15}}, 100%, 45%, 0)`);
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.ellipse(0, cy, auraR * 0.95, auraR * 1.25, 0, 0, Math.PI * 2);
      ctx.fill();

      // Floating gold flame tongues
      const flameCount = formIndex === 4 ? 12 : 7;
      ctx.fillStyle = `hsla(${{hue}}, 100%, 85%, ${{clamp(0.45 * intensity, 0, 0.75)}})`;
      for (let i = 0; i < flameCount; i++) {{
        const prog = (t * 4.5 + i * (1 / flameCount)) % 1;
        const fx = Math.sin(i * 1.7 + t * 5) * r * 0.8;
        const fy = cy + r * 0.9 - prog * (r * 1.95);
        const fsize = (1 - prog) * r * (formIndex === 4 ? 0.28 : 0.18);
        ctx.beginPath();
        ctx.arc(fx, fy, Math.max(1, fsize), 0, Math.PI * 2);
        ctx.fill();
      }}
    }} else if (formIndex === 1 && (charging || firing || isPowerUp || intensity > 0.3)) {{
      const auraR = r * (0.8 + intensity * 0.2) * pulse;
      const grad = ctx.createRadialGradient(0, cy, r * 0.15, 0, cy, auraR);
      grad.addColorStop(0, 'rgba(255, 255, 255, 0.45)');
      grad.addColorStop(0.5, 'rgba(230, 240, 255, 0.25)');
      grad.addColorStop(1, 'rgba(200, 225, 255, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.ellipse(0, cy, auraR * 0.9, auraR * 1.1, 0, 0, Math.PI * 2);
      ctx.fill();
    }}

    // Lightning arcs for SSJ2 and SSJ3
    if (formIndex === 3) {{
      drawLightningArcs(r, t, 5, '#ffffff', '#67e8f9', 1.0);
    }} else if (formIndex === 4) {{
      drawLightningArcs(r, t, 8, '#ffffff', '#38bdf8', 1.25);
    }}

    ctx.restore();
  }}

"""

# Replace from start_idx up to draw_goku_idx with new_sprites_code
content = content[:start_idx] + new_sprites_code + content[draw_goku_idx:]

# 2. Update drawGoku() sprite selection to look up the active form
old_draw_sprite_lookup = """    let sprite = gokuImgIdle;
    let scaleMult = 2.5;
    let yOffset = 0.86;
    if (charging && isKame) {
      sprite = gokuImgKameCharge;
      scaleMult = 2.65;
      yOffset = 0.86;
    } else if (firing && isKame) {
      sprite = gokuImgKameFire;
      scaleMult = 3.25;
      yOffset = 0.85;
    } else if (firing || charging) {
      sprite = gokuImgKiBlast;
      scaleMult = 3.05;
      yOffset = 0.86;
    } else if (isFlying) {
      sprite = gokuImgFly;
      scaleMult = 2.75;
      yOffset = 0.88;
    }"""

new_draw_sprite_lookup = """    const formKeys = ['kid', 'base', 'ssj', 'ssj2', 'ssj3', 'ui'];
    const curFormKey = formKeys[formIndex] || 'kid';
    const formSprites = gokuFormImages[curFormKey] || gokuFormImages.kid;

    let sprite = formSprites.idle;
    let scaleMult = (formIndex === 0) ? 2.5 : 2.55;
    let yOffset = (formIndex === 0) ? 0.86 : 0.86;
    if (charging && isKame) {
      sprite = formSprites.kameCharge || formSprites.idle;
      scaleMult = 2.65;
      yOffset = 0.86;
    } else if (firing && isKame) {
      sprite = formSprites.kameFire || formSprites.idle;
      scaleMult = 3.25;
      yOffset = 0.85;
    } else if (firing || charging) {
      sprite = formSprites.kiBlast || formSprites.idle;
      scaleMult = 3.05;
      yOffset = 0.86;
    } else if (isFlying) {
      sprite = formSprites.fly || formSprites.idle;
      scaleMult = 2.75;
      yOffset = 0.88;
    }"""

assert old_draw_sprite_lookup in content, "old_draw_sprite_lookup not found"
content = content.replace(old_draw_sprite_lookup, new_draw_sprite_lookup, 1)

# 3. Update character rendering in drawGoku() to draw sprite for ALL forms!
old_render_branch = """      // 2. Character Drawing
      if (formIndex === 0 && sprite && sprite.complete && sprite.naturalWidth > 0) {
        ctx.save();
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        const sw = sprite.naturalWidth;
        const sh = sprite.naturalHeight;
        const targetW = r * scaleMult;
        const targetH = targetW * (sh / sw);
        ctx.drawImage(sprite, -targetW / 2, -targetH * yOffset, targetW, targetH);
        ctx.restore();
      } else {
        drawFlyingNimbus(r, t, pet.gokuSpeed);
        drawGokuCharacter(r, t, formIndex, stance);
      }"""

new_render_branch = """      // 2. Character Drawing - authentic Toriyama anime sprites across all 6 forms
      if (sprite && sprite.complete && sprite.naturalWidth > 0) {
        ctx.save();
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        const sw = sprite.naturalWidth;
        const sh = sprite.naturalHeight;
        const targetW = r * scaleMult;
        const targetH = targetW * (sh / sw);
        ctx.drawImage(sprite, -targetW / 2, -targetH * yOffset, targetW, targetH);
        ctx.restore();
      } else if (gokuFormImages.kid.idle && gokuFormImages.kid.idle.complete) {
        // Safe fallback to kid idle sprite
        const kSprite = gokuFormImages.kid.idle;
        const sw = kSprite.naturalWidth;
        const sh = kSprite.naturalHeight;
        const targetW = r * scaleMult;
        const targetH = targetW * (sh / sw);
        ctx.drawImage(kSprite, -targetW / 2, -targetH * yOffset, targetW, targetH);
      }"""

assert old_render_branch in content, "old_render_branch not found"
content = content.replace(old_render_branch, new_render_branch, 1)

with open("web/bitling.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully applied authentic Toriyama anime sprites to web/bitling.html!")
