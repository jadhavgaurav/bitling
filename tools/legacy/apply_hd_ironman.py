#!/usr/bin/env python3
"""Apply HD Iron Man sprites, front-view hover, supersonic flight, and combat overhaul to web/bitling.html."""
import re
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "web/bitling.html"
SPRITES_DIR = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758/ironman_hd_sprites")

keys = {
    'idle': 'ironman_hd_front_idle.webp',
    'fly': 'ironman_hd_flight_right.webp',
    'repulsor': 'ironman_hd_repulsor_right.webp',
    'unibeam': 'ironman_hd_unibeam_right.webp',
    'inspect': 'ironman_hd_inspect_right.webp'
}

b64_assets = {}
for k, fname in keys.items():
    p = SPRITES_DIR / fname
    with open(p, 'rb') as f:
        data = f.read()
        b64 = base64.b64encode(data).decode('ascii')
        b64_assets[k] = f"data:image/webp;base64,{b64}"

print(f"Loaded {len(b64_assets)} HD WebP sprites:")
for k, v in b64_assets.items():
    print(f"  {k}: {len(v)} b64 chars")

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace IRONMAN_SPRITES
new_sprites_block = f"""  // ---------------------------------------------------------------- Iron Man HD sprites & renderer
  const IRONMAN_SPRITES = {{
    idle: '{b64_assets['idle']}',
    fly: '{b64_assets['fly']}',
    repulsor: '{b64_assets['repulsor']}',
    unibeam: '{b64_assets['unibeam']}',
    charge: '{b64_assets['unibeam']}',
    stance: '{b64_assets['idle']}',
    inspect: '{b64_assets['inspect']}',
    salute: '{b64_assets['repulsor']}',
  }};

  const ironmanImgIdle = new Image(); ironmanImgIdle.src = IRONMAN_SPRITES.idle;
  const ironmanImgFly = new Image(); ironmanImgFly.src = IRONMAN_SPRITES.fly;
  const ironmanImgRepulsor = new Image(); ironmanImgRepulsor.src = IRONMAN_SPRITES.repulsor;
  const ironmanImgUnibeam = new Image(); ironmanImgUnibeam.src = IRONMAN_SPRITES.unibeam;
  const ironmanImgCharge = ironmanImgUnibeam;
  const ironmanImgStance = ironmanImgIdle;
  const ironmanImgInspect = new Image(); ironmanImgInspect.src = IRONMAN_SPRITES.inspect;
  const ironmanImgSalute = ironmanImgRepulsor;"""

old_sprites_pattern = r"  // ---------------------------------------------------------------- Iron Man sprites & renderer\s*const IRONMAN_SPRITES = \{[\s\S]*?const ironmanImgSalute = new Image\(\); ironmanImgSalute\.src = IRONMAN_SPRITES\.salute;"
match = re.search(old_sprites_pattern, content)
assert match, "Could not find old IRONMAN_SPRITES block"
content = content[:match.start()] + new_sprites_block + content[match.end():]
print("Replaced IRONMAN_SPRITES block.")

# 2. Replace drawIronMan implementation
new_draw_ironman = """  function drawIronMan() {
    const asleep = state.asleep;
    const charging = pet.zapCharge > 0 && !asleep;
    const firing = pet.zap > 0;
    const isBoss = pet.zapBoss || false;
    const isKame = (pet.zapStyle === 'unibeam') || isBoss;
    const isCarried = !!(pet.carried || pet.held);

    // Desktop vs Browser flight velocity tracking
    const isDesktopFlying = pet.mode === 'fly' && (Math.abs(pet.flyVX || 0) > 0.05 || Math.abs(pet.flyVY || 0) > 0.05);
    const flightVx = isDesktopFlying ? (pet.flyVX * 260) : (pet.mode === 'fly' ? (pet.vx || 0) : 0);
    const flightVy = isDesktopFlying ? (pet.flyVY * 260) : (pet.mode === 'fly' ? (pet.vy || 0) : 0);

    const vx = (pet.held ? pet.vx : (pet.dragVx || flightVx || 0));
    const vy = (pet.held ? pet.vy : (pet.dragVy || flightVy || 0));
    const rawSpeed = Math.hypot(vx, vy) || (pet.dragSpeed || (isDesktopFlying ? 260 : 0));

    // Exponential smoothing on velocity
    pet.ironmanSpeed = (pet.ironmanSpeed || 0) * 0.84 + rawSpeed * 0.16;

    // Immediately face the drag / flight direction
    if (isCarried && Math.abs(vx) > 12) {
      pet.facing = vx < 0 ? -1 : 1;
    } else if (isDesktopFlying && Math.abs(pet.flyVX) > 0.15) {
      pet.facing = pet.flyVX < 0 ? -1 : 1;
    } else if (pet.mode === 'fly' && Math.abs(vx) > 15) {
      pet.facing = vx < 0 ? -1 : 1;
    }
    const f = pet.facing || 1;

    // Aerodynamic banking / pitch in local coordinates
    const forwardV = vx * f;
    const targetPitch = isCarried
      ? clamp((forwardV / 700) + (vy / 950), -0.26, 0.26)
      : (isDesktopFlying || (pet.mode === 'fly' && Math.abs(forwardV) > 20)
        ? clamp((forwardV / 800) + (vy / 1000), -0.24, 0.24)
        : (pet.walking ? 0.05 : 0));
    pet.ironmanPitch = (pet.ironmanPitch || 0) * 0.82 + targetPitch * 0.18;

    const isFlying = ((pet.walking || (pet.ironmanSpeed || 0) > 30 || isDesktopFlying || (pet.mode === 'fly' && Math.hypot(vx, vy) > 30) || (isCarried && Math.abs(vx) > 30)) && !charging && !firing);

    // Sprite selection based on action state
    let sprite = ironmanImgIdle;
    let drawH = petR() * 3.25;
    let drawW = drawH * (245 / 480);
    let drawX = -drawW * 0.50;
    let drawY = -drawH * 0.95;

    let cX = 0.50, cY = 0.244;
    let eX = 0.50, eY = 0.075;
    let isFront = true;
    let bX = 0.50, bY = 0.965;
    const lbX = 0.265, rbX = 0.735;
    const lpX = 0.155, rpX = 0.845, pY = 0.431;

    if (isCarried) {
      sprite = ironmanImgIdle;
      isFront = true;
    } else if (charging || firing) {
      isFront = false;
      if (isKame) {
        sprite = ironmanImgUnibeam;
        drawH = petR() * 3.25;
        drawW = drawH * (275 / 480);
        drawX = -drawW * 0.48;
        drawY = -drawH * 0.93;
        cX = 0.356; cY = 0.231;
        eX = 0.356; eY = 0.080;
        bX = 0.340; bY = 0.940;
      } else {
        sprite = ironmanImgRepulsor;
        drawH = petR() * 3.25;
        drawW = drawH * (169 / 480);
        drawX = -drawW * 0.45;
        drawY = -drawH * 0.95;
        cX = 0.408; cY = 0.198;
        eX = 0.420; eY = 0.080;
        bX = 0.503; bY = 0.979;
      }
    } else if (pet.working || (typeof snack !== 'undefined' && snack.active)) {
      sprite = ironmanImgInspect;
      isFront = false;
      drawH = petR() * 3.25;
      drawW = drawH * (244 / 480);
      drawX = -drawW * 0.48;
      drawY = -drawH * 0.95;
      cX = 0.484; cY = 0.271;
      eX = 0.484; eY = 0.100;
      bX = 0.492; bY = 0.969;
    } else if (isFlying) {
      sprite = ironmanImgFly;
      isFront = false;
      drawW = petR() * 3.40;
      drawH = drawW * (375 / 480);
      drawX = -drawW * 0.48;
      drawY = -drawH * 0.65;
      cX = 0.708; cY = 0.413;
      eX = 0.833; eY = 0.140;
      bX = 0.062; bY = 0.827;
    }

    stageBody({ shadow: !isCarried, bob: isCarried ? 0.01 : 0.04, bobRate: 2.2, sway: isCarried ? 0 : 0.015 }, (r, t) => {
      ctx.save();

      // Neutralize squash/stretch deformation so high-def armor stays rigid
      const sx = (1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6);
      const sy = (1 + pet.sq) * (1 + pet.stretch);
      if (Math.abs(sx) > 0.05 && Math.abs(sy) > 0.05) {
        ctx.scale(1 / sx, 1 / sy);
      }

      // Flip for facing direction
      ctx.scale(f, 1);

      // Aerodynamic pitch
      ctx.rotate(pet.ironmanPitch);

      // -------------------------------------------------------- Supersonic Plasma Slipstream behind Boots
      const bootAnchorX = drawX + bX * drawW;
      const bootAnchorY = drawY + bY * drawH;

      if (isFlying && !asleep) {
        const speedRatio = clamp((pet.ironmanSpeed || 0) / 240, isCarried ? 0.5 : 0.4, 1.4);
        const trailLen = r * (1.6 + speedRatio * 1.8);

        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const grad = ctx.createLinearGradient(bootAnchorX, bootAnchorY, bootAnchorX - trailLen, bootAnchorY);
        grad.addColorStop(0, 'rgba(0, 240, 255, 0.98)');
        grad.addColorStop(0.25, 'rgba(0, 160, 255, 0.85)');
        grad.addColorStop(0.65, 'rgba(255, 120, 0, 0.45)');
        grad.addColorStop(1, 'rgba(255, 50, 0, 0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(bootAnchorX, bootAnchorY - r * 0.16);
        ctx.bezierCurveTo(bootAnchorX - r * 0.4, bootAnchorY - r * 0.10, bootAnchorX - trailLen * 0.7, bootAnchorY - r * 0.04, bootAnchorX - trailLen, bootAnchorY);
        ctx.bezierCurveTo(bootAnchorX - trailLen * 0.7, bootAnchorY + r * 0.04, bootAnchorX - r * 0.4, bootAnchorY + r * 0.10, bootAnchorX, bootAnchorY + r * 0.16);
        ctx.closePath();
        ctx.fill();

        for (let i = 0; i < 5; i++) {
          const phase = (t * 4.5 + i * 0.65) % 1;
          const sparkDist = r * 0.2 + phase * trailLen;
          const sparkY = bootAnchorY + Math.sin(t * 20 + i) * r * 0.10;
          ctx.fillStyle = `rgba(${i % 2 === 0 ? '0, 240, 255' : '255, 200, 50'}, ${0.9 * (1 - phase)})`;
          ctx.beginPath();
          ctx.arc(bootAnchorX - sparkDist, sparkY, r * (0.04 + (1 - phase) * 0.06), 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }

      // -------------------------------------------------------- Draw High-Definition Character Sprite
      ctx.drawImage(sprite, drawX, drawY, drawW, drawH);

      // -------------------------------------------------------- Boot Repulsor Thruster Exhaust
      if (!asleep) {
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const pulse = Math.sin(t * 30) * 0.15;

        if (isFront) {
          // Dual downward thruster exhaust plumes under both boots
          const boots = [
            drawX + lbX * drawW,
            drawX + rbX * drawW
          ];
          const jetLen = r * (0.55 + pulse);
          const jetW = r * 0.18;

          for (const bx of boots) {
            const by = drawY + bY * drawH;
            const jg = ctx.createLinearGradient(bx, by, bx, by + jetLen);
            jg.addColorStop(0, '#ffffff');
            jg.addColorStop(0.25, 'rgba(0, 240, 255, 0.95)');
            jg.addColorStop(0.70, 'rgba(255, 140, 0, 0.55)');
            jg.addColorStop(1, 'rgba(255, 50, 0, 0)');
            ctx.fillStyle = jg;
            ctx.beginPath();
            ctx.moveTo(bx - jetW * 0.5, by);
            ctx.lineTo(bx + jetW * 0.5, by);
            ctx.lineTo(bx, by + jetLen);
            ctx.closePath();
            ctx.fill();

            // Sole flare
            const bg = ctx.createRadialGradient(bx, by, 1, bx, by, jetW * 1.4);
            bg.addColorStop(0, '#ffffff');
            bg.addColorStop(0.5, 'rgba(0, 240, 255, 0.9)');
            bg.addColorStop(1, 'rgba(0, 150, 255, 0)');
            ctx.fillStyle = bg;
            ctx.beginPath(); ctx.arc(bx, by, jetW * 1.4, 0, Math.PI * 2); ctx.fill();
          }

          // Twin palm repulsor stabilizer glow
          const palms = [
            drawX + lpX * drawW,
            drawX + rpX * drawW
          ];
          const py = drawY + pY * drawH;
          const pgPulse = 0.8 + Math.sin(t * 12) * 0.2;
          for (const px of palms) {
            const pg = ctx.createRadialGradient(px, py, 1, px, py, r * 0.15 * pgPulse);
            pg.addColorStop(0, '#ffffff');
            pg.addColorStop(0.4, 'rgba(0, 240, 255, 0.85)');
            pg.addColorStop(1, 'rgba(0, 150, 255, 0)');
            ctx.fillStyle = pg;
            ctx.beginPath(); ctx.arc(px, py, r * 0.15 * pgPulse, 0, Math.PI * 2); ctx.fill();
          }

        } else if (sprite === ironmanImgFly) {
          // Trailing supersonic plume at boot soles
          const jetLen = r * (0.65 + pulse);
          const jetW = r * 0.20;
          const jg = ctx.createLinearGradient(bootAnchorX, bootAnchorY, bootAnchorX - jetLen, bootAnchorY);
          jg.addColorStop(0, '#ffffff');
          jg.addColorStop(0.3, 'rgba(0, 240, 255, 0.95)');
          jg.addColorStop(0.7, 'rgba(255, 140, 0, 0.6)');
          jg.addColorStop(1, 'rgba(255, 50, 0, 0)');
          ctx.fillStyle = jg;
          ctx.beginPath();
          ctx.moveTo(bootAnchorX, bootAnchorY - jetW * 0.5);
          ctx.lineTo(bootAnchorX, bootAnchorY + jetW * 0.5);
          ctx.lineTo(bootAnchorX - jetLen, bootAnchorY);
          ctx.closePath();
          ctx.fill();

        } else {
          // Single downward hover jet under boots
          const jetLen = r * (0.45 + pulse);
          const jetW = r * 0.18;
          const jg = ctx.createLinearGradient(bootAnchorX, bootAnchorY, bootAnchorX, bootAnchorY + jetLen);
          jg.addColorStop(0, '#ffffff');
          jg.addColorStop(0.3, 'rgba(0, 240, 255, 0.95)');
          jg.addColorStop(0.7, 'rgba(255, 140, 0, 0.6)');
          jg.addColorStop(1, 'rgba(255, 50, 0, 0)');
          ctx.fillStyle = jg;
          ctx.beginPath();
          ctx.moveTo(bootAnchorX - jetW * 0.5, bootAnchorY);
          ctx.lineTo(bootAnchorX + jetW * 0.5, bootAnchorY);
          ctx.lineTo(bootAnchorX, bootAnchorY + jetLen);
          ctx.closePath();
          ctx.fill();
        }
        ctx.restore();
      }

      // -------------------------------------------------------- Glowing Cyan Visors & Chest Arc Reactor
      if (!asleep) {
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';

        const reactorX = drawX + cX * drawW;
        const reactorY = drawY + cY * drawH;
        const eyeX = drawX + eX * drawW;
        const eyeY = drawY + eY * drawH;

        // Chest Arc Reactor glow
        const arcPulse = 0.90 + Math.sin(t * 8) * 0.15;
        const arcR = r * (0.16 * arcPulse) * (charging && isKame ? 2.4 : 1.0);
        const arcGrad = ctx.createRadialGradient(reactorX, reactorY, 1, reactorX, reactorY, arcR * 2.6);
        arcGrad.addColorStop(0, '#ffffff');
        arcGrad.addColorStop(0.35, 'rgba(0, 245, 255, 0.95)');
        arcGrad.addColorStop(0.70, 'rgba(0, 160, 255, 0.50)');
        arcGrad.addColorStop(1, 'rgba(0, 100, 255, 0)');
        ctx.fillStyle = arcGrad;
        ctx.beginPath(); ctx.arc(reactorX, reactorY, arcR * 2.6, 0, Math.PI * 2); ctx.fill();

        // Eye Visors horizontal flare
        const eyeW = r * 0.22, eyeH = r * 0.08;
        const eg = ctx.createRadialGradient(eyeX, eyeY, 1, eyeX, eyeY, eyeW);
        eg.addColorStop(0, '#ffffff');
        eg.addColorStop(0.4, 'rgba(0, 240, 255, 0.95)');
        eg.addColorStop(1, 'rgba(0, 150, 255, 0)');
        ctx.fillStyle = eg;
        ctx.beginPath();
        ctx.ellipse(eyeX, eyeY, eyeW, eyeH, 0, 0, Math.PI * 2);
        ctx.fill();

        // ---------------------------------------------------- Charging Aura / Repulsor Surge
        if (charging) {
          const auraK = clamp(1 - pet.zapCharge / (pet.zapFull || 0.9), 0, 1);
          const surgeR = r * (0.35 + auraK * (isKame ? 0.9 : 0.45));
          const targetX = isKame ? reactorX : (drawX + 0.858 * drawW);
          const targetY = isKame ? reactorY : (drawY + 0.135 * drawH);

          const cg = ctx.createRadialGradient(targetX, targetY, 2, targetX, targetY, surgeR);
          cg.addColorStop(0, '#ffffff');
          cg.addColorStop(0.35, 'rgba(0, 240, 255, 0.95)');
          cg.addColorStop(0.75, 'rgba(0, 140, 255, 0.45)');
          cg.addColorStop(1, 'rgba(0, 100, 255, 0)');
          ctx.fillStyle = cg;
          ctx.beginPath(); ctx.arc(targetX, targetY, surgeR, 0, Math.PI * 2); ctx.fill();

          // High-tech targeting arc rings
          ctx.strokeStyle = `rgba(180, 245, 255, ${0.85 * auraK})`;
          ctx.lineWidth = 2.2;
          ctx.beginPath();
          ctx.arc(targetX, targetY, surgeR * 0.75, 0, Math.PI * 2);
          ctx.stroke();

          // Ion lightning sparks
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.6;
          for (let i = 0; i < 4; i++) {
            const ang = (i / 4) * Math.PI * 2 + t * 25;
            const dist = surgeR * (0.8 + Math.sin(t * 30 + i) * 0.3);
            ctx.beginPath();
            ctx.moveTo(targetX, targetY);
            ctx.lineTo(targetX + Math.cos(ang) * dist, targetY + Math.sin(ang) * dist);
            ctx.stroke();
          }
        }
        ctx.restore();
      }

      ctx.restore();
    });
  }"""

old_draw_pattern = r"  function drawIronMan\(\) \{[\s\S]*?\n  \}"
match = re.search(old_draw_pattern, content)
assert match, "Could not find old drawIronMan function"
content = content[:match.start()] + new_draw_ironman + content[match.end():]
print("Replaced drawIronMan implementation.")

# 3. Update species('ironman').attack.origin
old_origin_pattern = r"      origin: \(r\) => \{[\s\S]*?return \[\{ x: Math\.round\(pet\.x \+ pet\.facing \* r \* 0\.65\), y: Math\.round\(pet\.y - r \* 1\.45\) \}\];\s*\},"
new_origin = """      origin: (r) => {
        const isBoss = (pet.zapBoss || (pet.zapStyle === 'unibeam'));
        if (isBoss) {
          // Unibeam shoots from chest Arc Reactor in ironmanImgUnibeam
          return [{ x: Math.round(pet.x + pet.facing * r * (-0.23)), y: Math.round(pet.y - r * 2.27) }];
        }
        // Palm Repulsor shoots from raised right palm in ironmanImgRepulsor
        return [{ x: Math.round(pet.x + pet.facing * r * 0.47), y: Math.round(pet.y - r * 2.65) }];
      },"""

match = re.search(old_origin_pattern, content)
if match:
    content = content[:match.start()] + new_origin + content[match.end():]
    print("Updated attack.origin.")
else:
    print("WARNING: Could not find exact attack.origin pattern to replace.")

# 4. Add combat voice triggers for Iron Man
old_combat_sound = """          } else if (shotStyle === 'unibeam') {
            audio.iroUnibeam();
          } else if (shotStyle === 'repulsor') {
            audio.iroRepulsor();
          }"""

new_combat_sound = """          } else if (shotStyle === 'unibeam') {
            audio.iroUnibeam();
            if (state.species === 'ironman') say("UNIBEAM FIRE!", 1400);
          } else if (shotStyle === 'repulsor') {
            audio.iroRepulsor();
            if (state.species === 'ironman' && Math.random() < 0.75) {
              say(pick(["Repulsor blast!", "Target neutralized.", "Eat repulsor!", "Jarvis, fire!"]), 1000);
            }
          }"""

if old_combat_sound in content:
    content = content.replace(old_combat_sound, new_combat_sound, 1)
    print("Added firing speech for Iron Man.")
else:
    print("WARNING: Could not find old_combat_sound in HTML")

# 5. Add charge voice trigger for Unibeam
old_charge = """        if (resolved && resolved.sound === 'kameCharge') {
          audio.kameCharge();
          if (state.species === 'goku') say("KA... ME... HA... ME...", Math.round(pet.zapFull * 1000) + 150);
        }
        else audio.charge();"""

new_charge = """        if (resolved && resolved.sound === 'kameCharge') {
          audio.kameCharge();
          if (state.species === 'goku') say("KA... ME... HA... ME...", Math.round(pet.zapFull * 1000) + 150);
        } else if (resolved && resolved.sound === 'iroUnibeam') {
          audio.charge();
          if (state.species === 'ironman') say("Jarvis: 'Rerouting all power to chest Arc Reactor.'", Math.round(pet.zapFull * 1000) + 150);
        }
        else audio.charge();"""

if old_charge in content:
    content = content.replace(old_charge, new_charge, 1)
    print("Added charge speech for Unibeam.")
else:
    print("WARNING: Could not find old_charge in HTML")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully updated web/bitling.html!")
