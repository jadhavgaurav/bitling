#!/usr/bin/env python3
import base64

outdir = "/tmp/pikachu_hd"
def get_b64(name):
    with open(f"{outdir}/{name}.webp", "rb") as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode("ascii")

b64_idle = get_b64("idle")
b64_run = get_b64("run")
b64_charge = get_b64("charge")
b64_attack = get_b64("attack")
b64_dangle = get_b64("dangle")
b64_sleep = get_b64("sleep")

with open("web/bitling.html", "r", encoding="utf-8") as f:
    content = f.read()

# Locate start of PIKACHU_SPRITES and the start of MARIO section
start_anchor = "  // ---------------------------------------------------------------- Pikachu, the Electric Mouse Pokémon"
start_idx = content.find(start_anchor)
assert start_idx != -1, "start_anchor not found in web/bitling.html"

next_section_anchor = "  // ---------------------------------------------------------------- Super Mario (Living 3D Cinema / Disney Style) sprites & renderer"
end_idx = content.find(next_section_anchor, start_idx)
assert end_idx != -1, "next_section_anchor not found in web/bitling.html"

new_pikachu_code = f"""  // ---------------------------------------------------------------- Pikachu, the Electric Mouse Pokémon
  const PIKACHU_SPRITES = {{
    idle: '{b64_idle}',
    run: '{b64_run}',
    charge: '{b64_charge}',
    attack: '{b64_attack}',
    dangle: '{b64_dangle}',
    sleep: '{b64_sleep}'
  }};

  const pikaImgIdle = new Image(); pikaImgIdle.src = PIKACHU_SPRITES.idle;
  const pikaImgRun = new Image(); pikaImgRun.src = PIKACHU_SPRITES.run;
  const pikaImgCharge = new Image(); pikaImgCharge.src = PIKACHU_SPRITES.charge;
  const pikaImgAttack = new Image(); pikaImgAttack.src = PIKACHU_SPRITES.attack;
  const pikaImgDangle = new Image(); pikaImgDangle.src = PIKACHU_SPRITES.dangle;
  const pikaImgSleep = new Image(); pikaImgSleep.src = PIKACHU_SPRITES.sleep;

  function drawPikachu() {{
    const asleep = state.asleep;
    const charging = pet.zapCharge > 0 && !asleep;
    const firing = pet.zap > 0;
    const isBoss = pet.zapBoss || false;
    const isCarried = !!(pet.carried || pet.held);
    const vx = (pet.held ? pet.vx : (pet.dragVx || 0));
    const vy = (pet.held ? pet.vy : (pet.dragVy || 0));
    const rawSpeed = Math.hypot(vx, vy) || (pet.dragSpeed || 0);

    // Exponential smoothing on velocity
    pet.pikaSpeed = (pet.pikaSpeed || 0) * 0.84 + rawSpeed * 0.16;

    // Face drag / movement direction
    if (charging || firing) {{
      if (pet.zapX !== undefined && Math.abs(pet.zapX - pet.x) > 2) {{
        pet.facing = pet.zapX < pet.x ? -1 : 1;
      }}
    }} else if (isCarried && Math.abs(vx) > 12) {{
      pet.facing = vx < 0 ? -1 : 1;
    }} else if (pet.walking && pet.walkDir) {{
      pet.facing = pet.walkDir < 0 ? -1 : 1;
    }}
    const f = pet.facing || 1;

    // Aerodynamic tilt / pitch when carried or scampering fast
    const forwardV = vx * f;
    let targetPitch = 0;
    if (isCarried) {{
      targetPitch = clamp((forwardV / 700) + (vy / 900), -0.25, 0.25);
    }} else if (pet.walking) {{
      targetPitch = 0.04;
    }}
    pet.pikaPitch = (pet.pikaPitch || 0) * 0.78 + targetPitch * 0.22;

    stageBody({{
      shadow: !isCarried && !asleep,
      bob: isCarried ? 0.02 : (pet.walking ? 0.08 : (asleep ? 0.01 : 0.04)),
      bobRate: pet.walking ? 9 : (asleep ? 1.5 : 2.5),
      sway: (isCarried || asleep) ? 0 : 0.02
    }}, (r, t) => {{
      ctx.save();

      // Neutralize squash/stretch deformation from stageBody so the HD art stays pristine
      const sx = (1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6);
      const sy = (1 + pet.sq) * (1 + pet.stretch);
      if (Math.abs(sx) > 0.05 && Math.abs(sy) > 0.05) {{
        ctx.scale(1 / sx, 1 / sy);
      }}

      // Flip for facing direction and apply aerodynamic banking
      ctx.scale(f, 1);
      ctx.rotate(pet.pikaPitch);

      // Select high-definition anime sprite pose based on state
      let sprite = pikaImgIdle;
      let targetH = r * 2.48;
      let yOffset = 0.95;

      if (asleep) {{
        sprite = pikaImgSleep;
        targetH = r * 1.50;
        yOffset = 0.96;
      }} else if (isCarried) {{
        sprite = pikaImgDangle;
        targetH = r * 2.48;
        yOffset = 0.88;
      }} else if (firing) {{
        sprite = pikaImgAttack;
        targetH = r * 2.48;
        yOffset = 0.94;
      }} else if (charging) {{
        sprite = pikaImgCharge;
        targetH = r * 2.48;
        yOffset = 0.94;
      }} else if (pet.walking) {{
        sprite = pikaImgRun;
        targetH = r * 2.05;
        yOffset = 0.92;
      }}

      // -------------------------------------------------------- Dynamic Electrical Cheek Sparking Aura
      if (charging || firing) {{
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const auraR = r * (isBoss ? 1.9 : 1.35);
        const glow = ctx.createRadialGradient(r * 0.25, -r * 0.65, r * 0.1, r * 0.25, -r * 0.65, auraR);
        glow.addColorStop(0, 'rgba(255, 255, 255, 0.85)');
        glow.addColorStop(0.3, 'rgba(255, 235, 60, 0.6)');
        glow.addColorStop(0.7, 'rgba(255, 170, 0, 0.25)');
        glow.addColorStop(1, 'rgba(255, 170, 0, 0)');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(r * 0.25, -r * 0.65, auraR, 0, Math.PI * 2);
        ctx.fill();

        // Dancing electric sparks & lightning tendrils around body
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = Math.max(1.5, r * 0.05);
        const numArcs = isBoss ? 8 : 5;
        for (let i = 0; i < numArcs; i++) {{
          const ang = (i / numArcs) * Math.PI * 2 + Math.sin(t * 25 + i) * 0.4;
          const d1 = r * (0.45 + Math.sin(t * 18 + i) * 0.2);
          const d2 = auraR * 0.85;
          ctx.beginPath();
          ctx.moveTo(r * 0.2 + Math.cos(ang) * d1, -r * 0.6 + Math.sin(ang) * d1);
          ctx.lineTo(r * 0.2 + Math.cos(ang + 0.3) * (d1 + d2) * 0.5, -r * 0.6 + Math.sin(ang + 0.3) * (d1 + d2) * 0.5);
          ctx.lineTo(r * 0.2 + Math.cos(ang) * d2, -r * 0.6 + Math.sin(ang) * d2);
          ctx.stroke();
        }}
        ctx.restore();
      }}

      // -------------------------------------------------------- Cute Static Sparks while Carried
      if (isCarried) {{
        ctx.save();
        ctx.fillStyle = 'rgba(255, 240, 80, 0.85)';
        for (let s = 0; s < 3; s++) {{
          const spPhase = (t * 5 + s * 1.1) % 1;
          const spX = r * (0.35 + Math.sin(s * 2.5 + t * 8) * 0.3);
          const spY = -r * (0.8 + spPhase * 0.6);
          ctx.beginPath();
          ctx.arc(spX, spY, r * (0.05 + (1 - spPhase) * 0.04), 0, Math.PI * 2);
          ctx.fill();
        }}
        ctx.restore();
      }}

      // -------------------------------------------------------- High-Definition Sprite Rendering
      if (sprite && sprite.complete && sprite.naturalWidth > 0) {{
        ctx.save();
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        const sw = sprite.naturalWidth;
        const sh = sprite.naturalHeight;
        const targetW = targetH * (sw / sh);
        ctx.drawImage(sprite, -targetW / 2, -targetH * yOffset, targetW, targetH);
        ctx.restore();
      }} else {{
        // Vector fallback
        ctx.fillStyle = '#ffdd00';
        ctx.beginPath();
        ctx.arc(0, -r * 0.8, r * 0.75, 0, Math.PI * 2);
        ctx.fill();
        // Red cheeks
        ctx.fillStyle = '#ff3333';
        ctx.beginPath();
        ctx.arc(r * 0.45, -r * 0.7, r * 0.18, 0, Math.PI * 2);
        ctx.arc(-r * 0.45, -r * 0.7, r * 0.18, 0, Math.PI * 2);
        ctx.fill();
      }}

      // -------------------------------------------------------- Berry / Snack Eating Overlay
      if (pet.chew > 0 && !isCarried && !asleep) {{
        ctx.save();
        ctx.translate(r * 0.15, -r * 0.52);
        ctx.rotate(0.12 + Math.sin(t * 14) * 0.1);

        // Oran Berry (blue berry with green leaves)
        ctx.fillStyle = '#2980b9';
        ctx.beginPath();
        ctx.arc(0, 0, r * 0.18, 0, Math.PI * 2);
        ctx.fill();
        // Berry leaves
        ctx.fillStyle = '#27ae60';
        ctx.beginPath();
        ctx.ellipse(0, -r * 0.16, r * 0.08, r * 0.05, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }}

      // -------------------------------------------------------- Sleeping Zzz
      if (asleep) {{
        ctx.save();
        ctx.fillStyle = '#ffffff';
        ctx.font = `bold ${{Math.max(10, r * 0.35)}}px sans-serif`;
        for (let z = 0; z < 3; z++) {{
          const zPhase = (t * 1.4 + z * 0.33) % 1;
          const zx = r * 0.35 + zPhase * r * 0.7;
          const zy = -r * 0.7 - zPhase * r * 0.9;
          ctx.globalAlpha = Math.sin(zPhase * Math.PI) * 0.85;
          ctx.fillText('z', zx, zy);
        }}
        ctx.restore();
      }}

      ctx.restore();
    }});
  }}

"""

new_content = content[:start_idx] + new_pikachu_code + content[end_idx:]

with open("web/bitling.html", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully replaced Pikachu sprites and renderer in web/bitling.html!")
