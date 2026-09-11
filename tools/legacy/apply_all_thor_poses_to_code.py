#!/usr/bin/env python3
import json

with open("/tmp/thor_all_poses_b64.json", "r") as f:
    poses = json.load(f)

with open("web/bitling.html", "r", encoding="utf-8") as f:
    content = f.read()

start_anchor = "  // ---------------------------------------------------------------- Thor HD authentic sprites & renderer"
end_anchor = "  function drawThorAttack(r, k, isBoss, style) {"

start_idx = content.find(start_anchor)
assert start_idx != -1, "start_anchor not found"

end_idx = content.find(end_anchor, start_idx)
assert end_idx != -1, "end_anchor not found"

new_code = f"""  // ---------------------------------------------------------------- Thor HD authentic sprites & renderer
  const THOR_SPRITES = {{
    idle: '{poses["idle"]}',
    fly: '{poses["fly"]}',
    charge: '{poses["charge"]}',
    attack: '{poses["attack"]}',
    sb_idle: '{poses["sb_idle"]}',
    sb_fly: '{poses["sb_fly"]}',
    sb_attack: '{poses["sb_attack"]}',
    dangle: '{poses["dangle"]}',
    sleep: '{poses["sleep"]}'
  }};

  const thorImgIdle = new Image(); thorImgIdle.src = THOR_SPRITES.idle;
  const thorImgFly = new Image(); thorImgFly.src = THOR_SPRITES.fly;
  const thorImgCharge = new Image(); thorImgCharge.src = THOR_SPRITES.charge;
  const thorImgAttack = new Image(); thorImgAttack.src = THOR_SPRITES.attack;
  const thorImgSbIdle = new Image(); thorImgSbIdle.src = THOR_SPRITES.sb_idle;
  const thorImgSbFly = new Image(); thorImgSbFly.src = THOR_SPRITES.sb_fly;
  const thorImgSbAttack = new Image(); thorImgSbAttack.src = THOR_SPRITES.sb_attack;
  const thorImgDangle = new Image(); thorImgDangle.src = THOR_SPRITES.dangle;
  const thorImgSleep = new Image(); thorImgSleep.src = THOR_SPRITES.sleep;

  function drawThor() {{
    const asleep = state.asleep;
    const charging = (pet.zapCharge > 0 || (pet.attacking > 0 && pet.attacking < 0.45)) && !asleep;
    const firing = (pet.zap > 0 || pet.attacking >= 0.45) && !asleep;
    const isBoss = pet.zapBoss || false;
    const isThrow = (pet.zapStyle === 'weaponThrow') || isBoss;

    // Flight and velocity tracking
    const isCarried = !!(pet.carried || pet.held);
    const isDesktopFlying = pet.mode === 'fly' && (Math.abs(pet.flyVX || 0) > 0.05 || Math.abs(pet.flyVY || 0) > 0.05);
    const flightVx = isDesktopFlying ? (pet.flyVX * 260) : (pet.mode === 'fly' ? (pet.vx || 0) : 0);
    const flightVy = isDesktopFlying ? (pet.flyVY * 260) : (pet.mode === 'fly' ? (pet.vy || 0) : 0);

    const vx = (pet.held ? pet.vx : (pet.dragVx || flightVx || 0));
    const vy = (pet.held ? pet.vy : (pet.dragVy || flightVy || 0));
    const rawSpeed = Math.hypot(vx, vy) || (pet.dragSpeed || (isDesktopFlying ? 260 : 0));

    pet.thorSpeed = (pet.thorSpeed || 0) * 0.84 + rawSpeed * 0.16;

    // Facing direction
    if (charging || firing) {{
      if (pet.zapX !== undefined && Math.abs(pet.zapX - pet.x) > 2) {{
        pet.facing = pet.zapX < pet.x ? -1 : 1;
      }}
    }} else if (isCarried && Math.abs(vx) > 12) {{
      pet.facing = vx < 0 ? -1 : 1;
    }} else if (isDesktopFlying && Math.abs(pet.flyVX) > 0.15) {{
      pet.facing = pet.flyVX < 0 ? -1 : 1;
    }} else if (pet.mode === 'fly' && Math.abs(vx) > 15) {{
      pet.facing = vx < 0 ? -1 : 1;
    }}
    const f = pet.facing || 1;

    // Aerodynamic banking pitch
    const forwardV = vx * f;
    let targetPitch = 0;
    if (charging || firing) {{
      const r = petR();
      const targetX = pet.zapX !== undefined ? pet.zapX : (pet.x + f * 120);
      const targetY = pet.zapY !== undefined ? pet.zapY : (groundY - 9 * scale);
      const dy = targetY - (pet.y - r * 1.3);
      const dx = Math.max(24, Math.abs(targetX - pet.x));
      targetPitch = clamp((dy / dx) * 0.75, -0.45, 0.45);
    }} else if (isCarried) {{
      targetPitch = clamp((forwardV / 700) + (vy / 950), -0.26, 0.26);
    }} else if (isDesktopFlying || (pet.mode === 'fly' && Math.abs(forwardV) > 15)) {{
      targetPitch = clamp((forwardV / 800) + (vy / 1000), -0.22, 0.22);
    }}
    // Flight and velocity tracking with exponential smoothing
    const isCarried = !!(pet.carried || pet.held);
    const isDesktopFlying = pet.mode === 'fly' && (Math.abs(pet.flyVX || 0) > 0.05 || Math.abs(pet.flyVY || 0) > 0.05);
    const flightVx = isDesktopFlying ? (pet.flyVX * 260) : (pet.mode === 'fly' ? (pet.vx || 0) : 0);
    const flightVy = isDesktopFlying ? (pet.flyVY * 260) : (pet.mode === 'fly' ? (pet.vy || 0) : 0);

    const vx = (pet.held ? pet.vx : (pet.dragVx || flightVx || 0));
    const vy = (pet.held ? pet.vy : (pet.dragVy || flightVy || 0));
    const rawSpeed = Math.hypot(vx, vy) || (pet.dragSpeed || (isDesktopFlying ? 260 : 0));

    pet.thorSpeed = (pet.thorSpeed || 0) * 0.82 + rawSpeed * 0.18;

    // Facing direction: immediately turn into drag / flight motion
    if (charging || firing) {{
      if (pet.zapX !== undefined && Math.abs(pet.zapX - pet.x) > 2) {{
        pet.facing = pet.zapX < pet.x ? -1 : 1;
      }}
    }} else if (isCarried && Math.abs(vx) > 10) {{
      pet.facing = vx < 0 ? -1 : 1;
    }} else if (isDesktopFlying && Math.abs(pet.flyVX) > 0.1) {{
      pet.facing = pet.flyVX < 0 ? -1 : 1;
    }} else if (pet.mode === 'fly' && Math.abs(vx) > 12) {{
      pet.facing = vx < 0 ? -1 : 1;
    }}
    const f = pet.facing || 1;

    // Aerodynamic banking pitch
    const forwardV = vx * f;
    let targetPitch = 0;
    if (charging || firing) {{
      const r = petR();
      const targetX = pet.zapX !== undefined ? pet.zapX : (pet.x + f * 120);
      const targetY = pet.zapY !== undefined ? pet.zapY : (groundY - 9 * scale);
      const dy = targetY - (pet.y - r * 1.3);
      const dx = Math.max(24, Math.abs(targetX - pet.x));
      targetPitch = clamp((dy / dx) * 0.75, -0.45, 0.45);
    }} else if (isCarried) {{
      targetPitch = clamp((forwardV / 650) + (vy / 900), -0.22, 0.22);
    }} else if (pet.isHostFlying || isDesktopFlying || (pet.mode === 'fly' && Math.abs(forwardV) > 15)) {{
      targetPitch = clamp((forwardV / 750) + (vy / 950), -0.20, 0.20);
    }}
    pet.thorPitch = (pet.thorPitch || 0) * 0.78 + targetPitch * 0.22;

    const pwr = getThorPower();
    const isStormbreaker = pwr.isStormbreaker;
    const lightningMult = pwr.lightningIntensity || 1.0;
    const stormMult = pwr.auraIntensity || 1.0;

    // Flight detection: active dragging movement, host transit, browser flight, or fast velocity
    const isMovingDrag = isCarried && (Math.hypot(vx, vy) > 18 || (pet.dragSpeed || 0) > 18 || (pet.thorSpeed || 0) > 20);
    const isHostFlying = pet.mode === 'fly' && (pet.isHostFlying || isDesktopFlying || Math.abs(flightVx) > 10 || Math.abs(flightVy) > 10);
    const isBrowserFlying = !DESKTOP && pet.mode === 'fly' && Math.hypot(pet.vx || 0, pet.vy || 0) > 10;
    const isFlyingNow = (isMovingDrag || isHostFlying || isBrowserFlying || (pet.thorSpeed || 0) > 25 || pet.flying) && !charging && !firing && !asleep;

    // Stage body bob and life
    stageBody({{
      shadow: false,
      bob: isCarried ? 0.015 : (isFlyingNow ? 0.045 : (asleep ? 0.012 : 0.038)),
      bobRate: isFlyingNow ? 6.5 : (asleep ? 1.4 : 2.4),
      sway: (isCarried || asleep) ? 0 : 0.018
    }}, (r, t) => {{
      ctx.save();

      // Breathing kinematics
      const breathe = asleep ? Math.sin(t * 1.5) * 0.015 : (isFlyingNow ? 0 : Math.sin(t * 2.6) * 0.022);
      ctx.scale(f * (1 + breathe * 0.25), 1 + breathe);
      ctx.rotate(pet.thorPitch);

      // -------------------------------------------------------------
      // 1. GOD OF THUNDER ELECTRIC AURA
      // -------------------------------------------------------------
      if (charging || firing || isFlyingNow || isStormbreaker || pwr.basePower > 0.2) {{
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const auraPulse = 1.0 + Math.sin(t * 14) * 0.12;
        const auraR = r * (1.5 + (charging || firing ? 0.7 : (isFlyingNow ? 0.35 : 0.15)) * stormMult) * auraPulse;
        const glow = ctx.createRadialGradient(0, -r * 0.95, r * 0.1, 0, -r * 0.95, auraR);
        glow.addColorStop(0, `hsla(195, 100%, 88%, ${{0.35 * stormMult}})`);
        glow.addColorStop(0.35, `hsla(205, 100%, 65%, ${{0.20 * stormMult}})`);
        glow.addColorStop(0.75, `hsla(215, 100%, 55%, ${{0.08 * stormMult}})`);
        glow.addColorStop(1, 'hsla(215, 100%, 50%, 0)');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.ellipse(0, -r * 0.95, auraR * 1.1, auraR * 1.25, 0, 0, Math.PI * 2);
        ctx.fill();

        // Branching lightning sparks dancing around body
        const numSparks = (charging || firing ? 7 : (isFlyingNow ? 5 : (isStormbreaker ? 4 : 2)));
        ctx.strokeStyle = '#ffffff';
        ctx.shadowColor = '#38bdf8';
        ctx.shadowBlur = 10;
        ctx.lineWidth = Math.max(1.4, r * 0.045);
        for (let i = 0; i < numSparks; i++) {{
          const ph = (t * 9 + i * 1.4) % (Math.PI * 2);
          const ang = (i / numSparks) * Math.PI * 2 + Math.sin(t * 12 + i) * 0.4;
          const dist = r * (0.8 + Math.sin(ph) * 0.4);
          const sxPt = Math.cos(ang) * dist;
          const syPt = -r * 0.95 + Math.sin(ang) * dist * 1.2;
          ctx.beginPath();
          ctx.moveTo(sxPt, syPt);
          ctx.lineTo(sxPt + (Math.sin(t * 22 + i) * r * 0.28 - r * 0.14), syPt + (Math.cos(t * 22 + i) * r * 0.28 - r * 0.14));
          ctx.lineTo(sxPt + (Math.sin(t * 32 + i) * r * 0.4 - r * 0.2), syPt + (Math.cos(t * 32 + i) * r * 0.4 - r * 0.2));
          ctx.stroke();
        }}
        ctx.restore();
      }}

      // -------------------------------------------------------------
      // 2. COMPLETE HEROIC POSE SELECTION
      // -------------------------------------------------------------
      let sprite = isStormbreaker ? thorImgSbIdle : thorImgIdle;
      let targetH = r * 2.50;
      let yOffset = 0.94;

      if (asleep) {{
        sprite = thorImgSleep;
        targetH = r * 2.15;
        yOffset = 0.96;
      }} else if (firing) {{
        sprite = isStormbreaker ? thorImgSbAttack : thorImgAttack;
        targetH = r * 2.65;
        yOffset = 0.94;
      }} else if (charging) {{
        sprite = isStormbreaker ? thorImgSbAttack : thorImgCharge;
        targetH = r * 2.65;
        yOffset = 0.94;
      }} else if (isFlyingNow) {{
        sprite = isStormbreaker ? thorImgSbFly : thorImgFly;
        targetH = r * 2.70;
        yOffset = 0.92;
      }} else if (isCarried) {{
        // Dangle vertically under gravity when carried
        sprite = thorImgDangle;
        targetH = r * 2.50;
        yOffset = 0.94;
      }}

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
        // Fallback placeholder while image initializes
        ctx.fillStyle = '#1c2029';
        ctx.beginPath();
        ctx.ellipse(0, -r * 0.9, r * 0.6, r * 0.9, 0, 0, Math.PI * 2);
        ctx.fill();
      }}

      // -------------------------------------------------------------
      // 3. CUTE STATIC SPARKS ON MJOLNIR WHILE HOVERING
      // -------------------------------------------------------------
      if (isCarried && !isFlyingNow) {{
        ctx.save();
        ctx.strokeStyle = '#ffffff';
        ctx.shadowColor = '#38bdf8';
        ctx.shadowBlur = 8;
        ctx.lineWidth = Math.max(1.2, r * 0.035);
        for (let s = 0; s < 3; s++) {{
          const spPhase = (t * 6 + s * 1.2) % (Math.PI * 2);
          const mx = r * 0.35 + Math.cos(spPhase) * r * 0.12;
          const my = -r * 0.68 + Math.sin(spPhase) * r * 0.12;
          ctx.beginPath();
          ctx.moveTo(mx, my);
          ctx.lineTo(mx + Math.sin(t * 20 + s) * r * 0.15, my - r * 0.1);
          ctx.stroke();
        }}
        ctx.restore();
      }}

      // -------------------------------------------------------------
      // 4. ASGARDIAN FEAST MEAD TANKARD WHILE EATING
      // -------------------------------------------------------------
      if (pet.chew > 0 && !isCarried && !asleep) {{
        ctx.save();
        ctx.translate(r * 0.35, -r * 0.88);
        ctx.rotate(0.2 + Math.sin(t * 15) * 0.15);
        // Golden tankard
        ctx.fillStyle = '#d97706';
        ctx.fillRect(-r * 0.12, -r * 0.16, r * 0.24, r * 0.32);
        // Foam head
        ctx.fillStyle = '#fef3c7';
        ctx.beginPath();
        ctx.arc(0, -r * 0.16, r * 0.13, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }}

      // -------------------------------------------------------------
      // 5. SUPERSONIC FLIGHT LIGHTNING STREAMERS
      // -------------------------------------------------------------
      if (isFlyingNow) {{
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        ctx.strokeStyle = '#ffffff';
        ctx.shadowColor = '#00d2ff';
        ctx.shadowBlur = 12;
        ctx.lineWidth = Math.max(1.6, r * 0.045);
        for (let i = 0; i < 4; i++) {{
          const py = -r * 0.65 + (i - 1.5) * r * 0.35;
          const streamLen = r * 0.85 + Math.sin(t * 18 + i) * r * 0.45;
          ctx.beginPath();
          ctx.moveTo(-r * 0.65, py);
          ctx.lineTo(-r * 0.65 - streamLen * 0.5, py + Math.sin(t * 22 + i) * r * 0.15);
          ctx.lineTo(-r * 0.65 - streamLen, py);
          ctx.stroke();
        }}
        ctx.restore();
      }}

      // -------------------------------------------------------------
      // 6. ASGARDIAN RUNIC SLEEPING ZZZ
      // -------------------------------------------------------------
      if (asleep) {{
        ctx.save();
        ctx.fillStyle = '#38bdf8';
        ctx.shadowColor = 'rgba(56, 189, 248, 0.8)';
        ctx.shadowBlur = 8;
        ctx.font = `bold ${{Math.max(12, r * 0.36)}}px sans-serif`;
        const runes = ['ᚦ', 'ᛟ', 'ᚱ', 'Z', 'z'];
        for (let z = 0; z < 3; z++) {{
          const zPhase = (t * 0.9 + z * 0.33) % 1;
          const zx = -r * 0.15 + zPhase * r * 0.45;
          const zy = -r * 1.95 - zPhase * r * 0.7;
          ctx.globalAlpha = Math.sin(zPhase * Math.PI) * 0.85;
          ctx.fillText(runes[z % runes.length], zx, zy);
        }}
        ctx.restore();
      }}

      ctx.restore();
    }});

    // Milestone announcement when Stormbreaker awakens
    if (thorState.awakeningAnim > 0) {{
      ctx.save();
      ctx.fillStyle = '#38bdf8';
      ctx.font = 'bold 15px -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.shadowColor = 'rgba(56, 189, 248, 0.9)';
      ctx.shadowBlur = 12;
      ctx.fillText('⚡ STORMBREAKER AWAKENED! ⚡', pet.x, pet.y - petR() * 3.4);
      ctx.restore();
    }}
  }}

"""

content = content[:start_idx] + new_code + content[end_idx:]

with open("web/bitling.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully updated web/bitling.html with all 9 animated Thor poses and living kinematics!")
