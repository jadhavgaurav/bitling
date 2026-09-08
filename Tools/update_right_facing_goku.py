import base64
from pathlib import Path

def main():
    adir = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758")
    idle_path = adir / "goku_pristine_idle_right.png"
    fly_path = adir / "goku_pristine_fly_right.png"

    with open(idle_path, "rb") as f:
        idle_b64 = base64.b64encode(f.read()).decode("ascii")

    with open(fly_path, "rb") as f:
        fly_b64 = base64.b64encode(f.read()).decode("ascii")

    target_file = Path("web/bitling.html")
    content = target_file.read_text(encoding="utf-8")

    start_marker = "  // ---------------------------------------------------------------- Son Goku, the Dragon Ball hero\n"
    end_marker = "  // ---------------------------------------------------------------- Nimbo, the cloud rider\n"

    idx_start = content.find(start_marker)
    idx_end = content.find(end_marker)

    assert idx_start != -1, "start_marker not found"
    assert idx_end != -1, "end_marker not found"
    assert idx_start < idx_end, "markers in wrong order"

    new_goku_block = f'''  // ---------------------------------------------------------------- Son Goku, the Dragon Ball hero
  // Authentic Kid Goku flying on the Flying Nimbus (Kintoun), styled directly after Akira Toriyama's
  // iconic Dragon Ball artwork and pixel sprite. Sprites face right by default to match Bitling convention.
  // Features dual Kamehameha/Ki Blast attacks, aerodynamic drag-surfing with banking, and cloud puffs.
  const GOKU_SPRITES = {{
    idle: 'data:image/png;base64,{idle_b64}',
    fly: 'data:image/png;base64,{fly_b64}'
  }};

  const gokuImgIdle = new Image(); gokuImgIdle.src = GOKU_SPRITES.idle;
  const gokuImgFly = new Image(); gokuImgFly.src = GOKU_SPRITES.fly;

  function drawGoku() {{
    const asleep = state.asleep;
    const charging = pet.zapCharge > 0 && !asleep;
    const firing = pet.zap > 0;
    const isBoss = pet.zapBoss || false;
    const isKame = (pet.zapStyle === 'kamehameha') || isBoss;
    const grow = charging ? clamp(1 - pet.zapCharge / (pet.zapFull || 0.9), 0, 1) : 0;

    // Drag / Flight detection & silky smooth velocity tracking
    const isCarried = !!(pet.carried || pet.held);
    const vx = (pet.held ? pet.vx : (pet.dragVx || 0));
    const vy = (pet.held ? pet.vy : (pet.dragVy || 0));
    const rawSpeed = Math.hypot(vx, vy) || (pet.dragSpeed || 0);

    // Exponential smoothing on velocity to eliminate jitter and flickering
    pet.gokuSpeed = (pet.gokuSpeed || 0) * 0.84 + rawSpeed * 0.16;

    // Immediately face the drag / pull direction (positive vx is right, negative vx is left)
    if (isCarried && Math.abs(vx) > 12) {{
      pet.facing = vx < 0 ? -1 : 1;
    }}
    const f = pet.facing || 1;

    // Aerodynamic banking / pitch in local coordinates (+X is Goku's forward direction)
    // Forward motion dips nose aerodynamically into the wind; climbing lifts nose up; diving dips nose down
    const forwardV = vx * f;
    const targetPitch = isCarried
      ? clamp((forwardV / 700) + (vy / 950), -0.26, 0.26)
      : (pet.walking ? 0.05 : 0);
    pet.gokuPitch = (pet.gokuPitch || 0) * 0.82 + targetPitch * 0.18;

    // Zero-flicker flying stance: while carried or in flight, Goku is heroically surfing on Flying Nimbus!
    const isFlying = isCarried || pet.walking || pet.gokuSpeed > 30;
    const sprite = isFlying ? gokuImgFly : gokuImgIdle;

    stageBody({{ shadow: false, bob: isCarried ? 0.01 : 0.05, bobRate: 2.2, sway: isCarried ? 0 : 0.02 }}, (r, t) => {{
      ctx.save();

      // Neutralize squash/stretch deformation from stageBody so the pixel art stays pristine and unwarped
      const sx = (1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6);
      const sy = (1 + pet.sq) * (1 + pet.stretch);
      if (Math.abs(sx) > 0.05 && Math.abs(sy) > 0.05) {{
        ctx.scale(1 / sx, 1 / sy);
      }}

      // Flip for facing direction (f = 1 faces right, f = -1 faces left)
      ctx.scale(f, 1);

      // Aerodynamic pitch into flight direction
      ctx.rotate(pet.gokuPitch);


      // -------------------------------------------------------- Kamehameha Aura (Charging/Firing)
      if ((charging || firing) && isKame) {{
        const power = firing ? 1 : grow;
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const auraR = r * (1.8 + power * 0.9);
        const glow = ctx.createRadialGradient(0, -r * 0.35, r * 0.2, 0, -r * 0.35, auraR);
        glow.addColorStop(0, `hsla(192, 100%, 86%, ${{0.55 * power}})`);
        glow.addColorStop(0.35, `hsla(205, 100%, 65%, ${{0.32 * power}})`);
        glow.addColorStop(0.75, `hsla(215, 100%, 55%, ${{0.14 * power}})`);
        glow.addColorStop(1, 'hsla(215, 100%, 50%, 0)');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.ellipse(0, -r * 0.35, auraR * 1.15, auraR * 1.35, 0, 0, Math.PI * 2);
        ctx.fill();

        // Electric Ki lightning sparks
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = Math.max(1.4, r * 0.05);
        for (let i = 0; i < 6; i++) {{
          const ph = (t * 6 + i * 1.05) % (Math.PI * 2);
          const dist1 = r * (0.6 + Math.sin(ph) * 0.2);
          const dist2 = auraR * 0.85;
          const ang = (i / 6) * Math.PI * 2 + Math.sin(t * 12 + i) * 0.3;
          ctx.beginPath();
          ctx.moveTo(Math.cos(ang) * dist1, -r * 0.35 + Math.sin(ang) * dist1);
          ctx.lineTo(Math.cos(ang + 0.25) * (dist1 + dist2) * 0.5, -r * 0.35 + Math.sin(ang + 0.25) * (dist1 + dist2) * 0.5);
          ctx.lineTo(Math.cos(ang) * dist2, -r * 0.35 + Math.sin(ang) * dist2);
          ctx.stroke();
        }}
        ctx.restore();

      // -------------------------------------------------------- Small Bug Ki Blast Golden Aura
      }} else if ((charging || firing) && !isKame) {{
        const power = firing ? 1 : grow;
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const auraR = r * (1.3 + power * 0.6);
        const glow = ctx.createRadialGradient(r * 0.4, -r * 0.3, r * 0.1, r * 0.4, -r * 0.3, auraR);
        glow.addColorStop(0, `hsla(55, 100%, 90%, ${{0.7 * power}})`);
        glow.addColorStop(0.4, `hsla(45, 100%, 65%, ${{0.38 * power}})`);
        glow.addColorStop(0.8, `hsla(30, 100%, 50%, ${{0.15 * power}})`);
        glow.addColorStop(1, 'hsla(30, 100%, 45%, 0)');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(r * 0.4, -r * 0.3, auraR, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }}

      // -------------------------------------------------------- Sprite Rendering
      if (sprite && sprite.complete && sprite.naturalWidth > 0) {{
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
      }} else {{
        // Vector fallback
        ctx.fillStyle = '#fed732';
        ctx.beginPath();
        ctx.ellipse(0, r * 0.3, r * 1.2, r * 0.55, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#4d3f84';
        ctx.beginPath();
        ctx.ellipse(0, -r * 0.2, r * 0.5, r * 0.6, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#fedebb';
        ctx.beginPath();
        ctx.arc(0, -r * 0.9, r * 0.45, 0, Math.PI * 2);
        ctx.fill();
      }}

      // -------------------------------------------------------- Dynamic Overlays

      // 1. Waving Arm (suppressed while carried)
      if (pet.waving > 0 && !isCarried) {{
        ctx.save();
        const waveAngle = Math.sin(t * 9) * 0.35;
        ctx.translate(r * 0.4, -r * 0.75);
        ctx.rotate(0.45 + waveAngle);

        ctx.fillStyle = '#fedebb';
        ctx.fillRect(-r * 0.08, -r * 0.42, r * 0.16, r * 0.42);

        ctx.fillStyle = '#c9302c';
        ctx.fillRect(-r * 0.1, -r * 0.42, r * 0.2, r * 0.14);

        ctx.fillStyle = '#fedebb';
        ctx.beginPath();
        ctx.arc(0, -r * 0.52, r * 0.14, 0, Math.PI * 2);
        ctx.fill();
        for (let fi = -2; fi <= 2; fi++) {{
          ctx.beginPath();
          ctx.arc(fi * r * 0.055, -r * 0.63, r * 0.045, 0, Math.PI * 2);
          ctx.fill();
        }}
        ctx.restore();
      }}

      // 2. Roast Meat Bone (suppressed while carried)
      if (pet.chew > 0 && !isCarried) {{
        ctx.save();
        ctx.translate(r * 0.08, -r * 0.62);
        ctx.rotate(0.18 + Math.sin(t * 14) * 0.08);

        ctx.fillStyle = '#f8f8f8';
        ctx.beginPath();
        ctx.arc(-r * 0.38, -r * 0.07, r * 0.075, 0, Math.PI * 2);
        ctx.arc(-r * 0.38, r * 0.07, r * 0.075, 0, Math.PI * 2);
        ctx.arc(r * 0.38, -r * 0.07, r * 0.075, 0, Math.PI * 2);
        ctx.arc(r * 0.38, r * 0.07, r * 0.075, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillRect(-r * 0.35, -r * 0.045, r * 0.7, r * 0.09);

        ctx.fillStyle = '#9e472a';
        ctx.strokeStyle = '#632511';
        ctx.lineWidth = Math.max(1, r * 0.03);
        ctx.beginPath();
        ctx.ellipse(0, 0, r * 0.26, r * 0.2, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.restore();
      }}

      // 3. Kamehameha Charging Ki Sphere at Hip
      if (charging && isKame) {{
        ctx.save();
        const pulse = r * (0.28 + grow * 0.24 + Math.sin(t * 30) * 0.06);
        const kg = ctx.createRadialGradient(r * 0.45, -r * 0.08, 2, r * 0.45, -r * 0.08, pulse);
        kg.addColorStop(0, '#ffffff');
        kg.addColorStop(0.35, '#85f0ff');
        kg.addColorStop(0.75, 'rgba(0, 170, 255, 0.75)');
        kg.addColorStop(1, 'rgba(0, 80, 255, 0)');
        ctx.fillStyle = kg;
        ctx.beginPath();
        ctx.arc(r * 0.45, -r * 0.08, pulse, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }}

      // 4. Kamehameha Firing Muzzle Bloom
      if (firing && isKame) {{
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const mrad = r * (0.85 + Math.sin(t * 40) * 0.15);
        const mg = ctx.createRadialGradient(r * 0.65, -r * 0.12, 3, r * 0.65, -r * 0.12, mrad);
        mg.addColorStop(0, '#ffffff');
        mg.addColorStop(0.35, '#a2f5ff');
        mg.addColorStop(0.75, 'rgba(0, 190, 255, 0.85)');
        mg.addColorStop(1, 'rgba(0, 90, 255, 0)');
        ctx.fillStyle = mg;
        ctx.beginPath();
        ctx.arc(r * 0.65, -r * 0.12, mrad, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }}

      // 5. Ki Blast Orb (Small Bugs)
      if (firing && !isKame) {{
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const krad = r * (0.48 + Math.sin(t * 35) * 0.08);
        const kg = ctx.createRadialGradient(r * 0.75, -r * 0.18, 2, r * 0.75, -r * 0.18, krad);
        kg.addColorStop(0, '#ffffff');
        kg.addColorStop(0.35, '#fff066');
        kg.addColorStop(0.75, 'rgba(255, 170, 0, 0.85)');
        kg.addColorStop(1, 'rgba(255, 80, 0, 0)');
        ctx.fillStyle = kg;
        ctx.beginPath();
        ctx.arc(r * 0.75, -r * 0.18, krad, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }}

      // 6. Sleeping Zzz (when asleep)
      if (asleep) {{
        ctx.save();
        ctx.fillStyle = '#ffffff';
        ctx.font = `bold ${{Math.max(10, r * 0.38)}}px sans-serif`;
        const zOff = (t * 0.8) % 1;
        ctx.globalAlpha = 1 - zOff;
        ctx.fillText('Z', r * 0.45 + zOff * 10, -r * 1.1 - zOff * 18);
        ctx.fillText('z', r * 0.65 + zOff * 10, -r * 1.3 - zOff * 22);
        ctx.restore();
      }}

      ctx.restore();
    }});
  }}
'''

    content = content[:idx_start] + new_goku_block + "\n" + content[idx_end:]
    target_file.write_text(content, encoding="utf-8")
    print(f"Updated web/bitling.html with right-facing sprites. New length: {len(content)}")

if __name__ == "__main__":
    main()
