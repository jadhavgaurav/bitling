#!/usr/bin/env python3
import json

with open("web/bitling.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Clean updateAmbientMovement()
content = content.replace(
    "function updateAmbientMovement() {\n    if (state.species === 'dragon' || (DESKTOP && state.species === 'spiderman')) return;",
    "function updateAmbientMovement() {\n    if (state.species === 'dragon') return;"
)
spidey_stage_ambient = "    if (DESKTOP && state.species === 'spiderman' && W >= 600) return;\n"
if "if (DESKTOP && state.species === 'spiderman' && W >= 600) return;" not in content:
    content = content.replace(
        "    if (pet.ambientTravelUntil > 0) {",
        spidey_stage_ambient + "    if (pet.ambientTravelUntil > 0) {"
    )

# 2. Update line in updatePet(dt) so velocity and gravity don't corrupt Spidey on desktop stage or asleep
content = content.replace(
    "if ((state.species === 'dragon' || (DESKTOP && state.species === 'spiderman' && W >= 600)) && state.hatched) {\n        pet.vx = 0; pet.vy = 0;",
    "if ((state.species === 'dragon' || (state.species === 'spiderman' && (state.asleep || (DESKTOP && W >= 600)))) && state.hatched) {\n        pet.vx = 0; pet.vy = 0;"
)
content = content.replace(
    "if ((state.species === 'dragon' || (DESKTOP && state.species === 'spiderman')) && state.hatched) {\n        pet.vx = 0; pet.vy = 0;",
    "if ((state.species === 'dragon' || (state.species === 'spiderman' && (state.asleep || (DESKTOP && W >= 600)))) && state.hatched) {\n        pet.vx = 0; pet.vy = 0;"
)
content = content.replace(
    "if (state.species === 'dragon' && state.hatched) {\n        pet.vx = 0; pet.vy = 0;",
    "if ((state.species === 'dragon' || (state.species === 'spiderman' && (state.asleep || (DESKTOP && W >= 600)))) && state.hatched) {\n        pet.vx = 0; pet.vy = 0;"
)

# 3. Guard pet.ax pull in grounded block
content = content.replace(
    "        if (!state.asleep && !(DESKTOP && state.species === 'spiderman')) {\n          const dx = pet.ax - pet.x;",
    "        if (!state.asleep && !(DESKTOP && state.species === 'spiderman' && W >= 600)) {\n          const dx = pet.ax - pet.x;"
)
content = content.replace(
    "        if (!state.asleep) {\n          const dx = pet.ax - pet.x;",
    "        if (!state.asleep && !(DESKTOP && state.species === 'spiderman' && W >= 600)) {\n          const dx = pet.ax - pet.x;"
)

# 4. Ensure updateSpiderman is hooked into update(dt)
shenron_update_hook = "if (state.species === 'dragon' && state.hatched) updateShenron(dt);"
spidey_update_hook = "if (state.species === 'dragon' && state.hatched) updateShenron(dt);\n    if (state.species === 'spiderman' && state.hatched) updateSpiderman(dt);"
if spidey_update_hook not in content:
    content = content.replace(shenron_update_hook, spidey_update_hook, 1)

# 5. Hook toggleSleep() for hanging sleep mode
toggle_sleep_old = """    } else if (state.species === 'spiderman') {
      pet.mode = 'ground';
      pet.landing = false;
      pet.grounded = true;
      pet.spideySwinging = false;
      pet.walking = false;
      pet.walkDir = 0;
      pet.vx = 0;
      pet.vy = 0;
      spidermanState.mode = 'perch';
      spidermanState.modeTimer = 0;
      spidermanState.anchor = null;
      spidermanState.eyeShutter = 0;
      if (typeof getSpideyLedges === 'function') {
        const ledges = getSpideyLedges();
        let nearest = ledges[0];
        let minDist = Infinity;
        for (const l of ledges) {
          const lx = l.x + l.w * 0.5, ly = l.y;
          const d = Math.hypot(lx - pet.x, ly - pet.y);
          if (d < minDist) { minDist = d; nearest = l; }
        }
        spidermanState.currentLedge = nearest;
        pet.y = nearest.y;
        pet.ax = pet.x;
      }
    } else {"""

toggle_sleep_new = """    } else if (state.species === 'spiderman') {
      pet.mode = 'fly';
      pet.landing = false;
      pet.grounded = false;
      pet.spideySwinging = false;
      pet.walking = false;
      pet.walkDir = 0;
      pet.vx = 0;
      pet.vy = 0;
      spidermanState.mode = 'sleep_dangle';
      spidermanState.modeTimer = 0;
      spidermanState.anchor = null;
      spidermanState.eyeShutter = 0;

      const r = petR();
      let anchorY = 30;
      let anchorX = pet.x;

      if (typeof getSpideyLedges === 'function') {
        const ledges = getSpideyLedges();
        let nearest = ledges[0];
        let minDist = Infinity;
        for (const l of ledges) {
          const lx = l.x + l.w * 0.5, ly = l.y;
          const d = Math.hypot(lx - pet.x, ly - pet.y);
          if (d < minDist) { minDist = d; nearest = l; }
        }
        spidermanState.currentLedge = nearest;
        if (nearest && !nearest.title.includes('Floor') && nearest.y > 140) {
          anchorY = Math.max(25, nearest.y - 140);
        } else {
          anchorY = 25;
        }
      } else {
        anchorY = 25;
      }

      spidermanState.sleepAnchor = { x: anchorX, y: anchorY };
      spidermanState.sleepRestLength = 120;
      spidermanState.sleepDragging = false;
      spidermanState.sleepBungee = false;
      spidermanState.bungeeVx = 0;
      spidermanState.bungeeVy = 0;
      pet.y = anchorY + spidermanState.sleepRestLength + r * 2.2;
      pet.x = anchorX;
      pet.ax = pet.x;
      pet.spideyPitch = 0;

      if (audio && audio.spideyThwip) audio.spideyThwip();
      if (typeof spawn === 'function') {
        spawn('spark', anchorX, anchorY, 6, { size: 6, spread: 10, dur: 0.5 });
      }
    } else {"""

if toggle_sleep_old in content:
    content = content.replace(toggle_sleep_old, toggle_sleep_new)

# 6. Hook wake() for acrobatic somersault landing flip
wake_old = """    if (state.species === 'spiderman') {
      spidermanState.mode = 'perch';
      spidermanState.modeTimer = 0;
      spidermanState.perchDuration = 2.0;
      spidermanState.anchor = null;
      pet.spideySwinging = false;
      pet.walking = false;
      pet.walkDir = 0;
    }"""
wake_old_rand = """    if (state.species === 'spiderman') {
      spidermanState.mode = 'perch';
      spidermanState.modeTimer = 0;
      spidermanState.perchDuration = rand(25.0, 45.0);
      spidermanState.anchor = null;
      pet.spideySwinging = false;
      pet.walking = false;
      pet.walkDir = 0;
    }"""

wake_new = """    if (state.species === 'spiderman') {
      if (spidermanState.sleepAnchor) {
        if (typeof spawn === 'function') {
          spawn('spark', spidermanState.sleepAnchor.x, spidermanState.sleepAnchor.y, 6, { size: 7, spread: 12, dur: 0.6 });
          spawn('spark', pet.x, pet.y - petR() * 2.1, 4, { size: 5, spread: 8, dur: 0.5 });
        }
        if (audio && audio.spideyZip) audio.spideyZip();
      }
      spidermanState.sleepAnchor = null;
      spidermanState.sleepDragging = false;
      spidermanState.sleepBungee = false;
      spidermanState.bungeeVx = 0;
      spidermanState.bungeeVy = 0;
      spidermanState.mode = 'flip';
      spidermanState.modeTimer = 0;
      spidermanState.flipFrom = { x: pet.x, y: pet.y };
      const targetY = spidermanState.currentLedge ? spidermanState.currentLedge.y : (groundY || (H - 35));
      spidermanState.flipTo = { x: pet.x, y: targetY };
      spidermanState.targetLedge = spidermanState.currentLedge;
      spidermanState.perchDuration = 2.5;
      spidermanState.anchor = null;
      pet.spideySwinging = false;
      pet.walking = false;
      pet.walkDir = 0;
      pet.spideyPitch = 0;
      say(pick([
        "Up and at 'em!",
        "Web's holding up nicely.",
        "Spider-Sense is tingling!",
        "Alright, back on patrol."
      ]), 2400);
    }"""

if wake_old in content:
    content = content.replace(wake_old, wake_new)
elif wake_old_rand in content:
    content = content.replace(wake_old_rand, wake_new)

# 7. Hook pointermove for sleep dragging
ptr_move_needle = "if (state.species === 'spiderman' && state.asleep && pet.pressing)"
ptr_move_old = "    if (!(DESKTOP && (state.species === 'dragon' || state.species === 'spiderman')) && pet.pressing && !pet.held && !state.asleep && Math.hypot(x - pet.pressX, y - pet.pressY) > 10) grab();"
ptr_move_block = """    if (state.species === 'spiderman' && state.asleep && pet.pressing) {
      if (Math.hypot(x - pet.pressX, y - pet.pressY) > 6) {
        spidermanState.sleepDragging = true;
        spidermanState.sleepBungee = false;
        pet.x = x - pet.holdOff.x;
        pet.y = y - pet.holdOff.y;
        if (typeof clampSpiderman === 'function') clampSpiderman();
      }
    }
"""

if ptr_move_needle in content:
    # Clean up any multiple duplicate blocks that might have accumulated
    import re
    content = re.sub(r"(\s*if \(state\.species === 'spiderman' && state\.asleep && pet\.pressing\) \{\s*if \(Math\.hypot\(x - pet\.pressX, y - pet\.pressY\) > 6\) \{\s*spidermanState\.sleepDragging = true;\s*spidermanState\.sleepBungee = false;\s*pet\.x = x - pet\.holdOff\.x;\s*pet\.y = y - pet\.holdOff\.y;\s*if \(typeof clampSpiderman === 'function'\) clampSpiderman\(\);\s*\}\s*\}\s*)+", "\n" + ptr_move_block, content)
elif ptr_move_old in content:
    content = content.replace(ptr_move_old, ptr_move_block + ptr_move_old)

# 8. Hook endPointer for sleep drag spring release
endpointer_old = """  const endPointer = () => {
    if (pet.held) release();
    else if (pet.pressing) { if (state.asleep) wake(); else petTap(); }
    pet.pressing = false;
  };"""
endpointer_new = """  const endPointer = () => {
    if (state.species === 'spiderman' && state.asleep && typeof spidermanState !== 'undefined' && spidermanState.sleepDragging) {
      spidermanState.sleepDragging = false;
      spidermanState.sleepBungee = true;
      spidermanState.bungeeVx = (typeof pointer !== 'undefined' && pointer.vx) ? pointer.vx : 0;
      spidermanState.bungeeVy = (typeof pointer !== 'undefined' && pointer.vy) ? pointer.vy : 0;
      if (audio && audio.spideyZip) audio.spideyZip();
      pet.pressing = false;
      return;
    }
    if (pet.held) release();
    else if (pet.pressing) { if (state.asleep) wake(); else petTap(); }
    pet.pressing = false;
  };"""
if endpointer_old in content:
    content = content.replace(endpointer_old, endpointer_new)

# 9. Hook interactive petTap to trigger immediate swing
pet_tap_old = "    else if (state.species === 'thor') audio.thorCatch();\n    else audio.squeak();"
pet_tap_new = """    else if (state.species === 'thor') audio.thorCatch();
    else if (state.species === 'spiderman') {
      if (audio && audio.spideySense) audio.spideySense();
      if (typeof spidermanState !== 'undefined') spidermanState.eyeShutter = 0.2;
      if (typeof triggerSpideySwing === 'function') triggerSpideySwing();
    }
    else audio.squeak();"""
if pet_tap_old in content:
    content = content.replace(pet_tap_old, pet_tap_new)

# 10. Hook doIdle to trigger swing
idle_old = "  function doIdle() {\n    if (ambientBlocked() || pet.ambientTravelUntil > 0) return;"
idle_new = """  function doIdle() {
    if (ambientBlocked() || pet.ambientTravelUntil > 0) return;
    if (state.species === 'spiderman' && DESKTOP && W >= 600) {
      if (typeof triggerSpideySwing === 'function') triggerSpideySwing();
      return;
    }"""
if idle_old in content:
    content = content.replace(idle_old, idle_new)

# 11. Replace Spider-Man engine block between SPIDERMAN_SPRITES and function drawKaiju()
start_marker = "  // ---------------------------------------------------------------- Spider-Man (Authentic 3D Living Desktop Pet)"
end_marker = "  function drawKaiju() {"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)
assert start_idx != -1 and end_idx != -1, f"Markers not found: start={start_idx}, end={end_idx}"

# Load existing base64 sprite dictionary
with open("/tmp/spiderman_poses/spiderman_all_poses_b64.json", "r") as f:
    sprites = json.load(f)

spiderman_full_block = f"""  // ---------------------------------------------------------------- Spider-Man (Authentic 3D Living Desktop Pet)
  const SPIDERMAN_SPRITES = {{
    idle: '{sprites["idle"]}',
    crawl: '{sprites["crawl"]}',
    swing_down: '{sprites["swing_down"]}',
    swing_up: '{sprites["swing_up"]}',
    apex_flip: '{sprites["apex_flip"]}',
    dangle: '{sprites["dangle"]}',
    shoot: '{sprites["shoot"]}',
    attack: '{sprites["attack"]}',
    sleep: '{sprites["sleep"]}'
  }};

  const spideyImgIdle = new Image(); spideyImgIdle.src = SPIDERMAN_SPRITES.idle;
  const spideyImgCrawl = new Image(); spideyImgCrawl.src = SPIDERMAN_SPRITES.crawl;
  const spideyImgSwingDown = new Image(); spideyImgSwingDown.src = SPIDERMAN_SPRITES.swing_down;
  const spideyImgSwingUp = new Image(); spideyImgSwingUp.src = SPIDERMAN_SPRITES.swing_up;
  const spideyImgFlip = new Image(); spideyImgFlip.src = SPIDERMAN_SPRITES.apex_flip;
  const spideyImgDangle = new Image(); spideyImgDangle.src = SPIDERMAN_SPRITES.dangle;
  const spideyImgShoot = new Image(); spideyImgShoot.src = SPIDERMAN_SPRITES.shoot;
  const spideyImgAttack = new Image(); spideyImgAttack.src = SPIDERMAN_SPRITES.attack;
  const spideyImgSleep = new Image(); spideyImgSleep.src = SPIDERMAN_SPRITES.sleep;

  // Window skyline rooftops and patrol state
  let spideyRooftops = [];
  let spideyUserActive = true;

  function setSpideyRooftops(list) {{
    if (Array.isArray(list)) spideyRooftops = list;
  }}
  function setSpideyUserActive(active) {{
    spideyUserActive = !!active;
  }}

  function clampSpiderman() {{
    const r = petR();
    const gY = groundY || (H - 35);
    pet.x = clamp(pet.x, r * 1.5, Math.max(r * 1.5, W - r * 1.5));
    const minY = (state.asleep && spidermanState.sleepAnchor) ? Math.max(30, spidermanState.sleepAnchor.y + 40) : 70;
    pet.y = clamp(pet.y, minY, Math.max(minY, gY));
  }}

  function spidermanHit(x, y) {{
    const r = petR();
    if (state.asleep && spidermanState.sleepAnchor) {{
      return Math.hypot(x - pet.x, y - (pet.y - r * 1.1)) < r * 1.65;
    }}
    return Math.hypot(x - pet.x, y - (pet.y - r * 0.9)) < r * 1.45;
  }}

  const spidermanState = {{
    mode: 'perch', // 'perch' | 'aim' | 'swing' | 'flip' | 'crawl' | 'dangle' | 'sleep_dangle'
    modeTimer: 0,
    perchDuration: 2.0, // starts swinging lively right after boot / switch
    currentLedge: null,
    targetLedge: null,
    targetSpot: null,
    anchor: null,
    swingT: 0,
    swingDuration: 1.15,
    swingFrom: {{ x: 0, y: 0 }},
    swingTo: {{ x: 0, y: 0 }},
    flipT: 0,
    flipFrom: {{ x: 0, y: 0 }},
    flipTo: {{ x: 0, y: 0 }},
    splat: null,
    eyeBlinkTimer: 3.5,
    eyeShutter: 1.0,
    lastActiveT: 0,
    // Hanging Sleep Mode & Bungee Spring State
    sleepAnchor: null,
    sleepRestLength: 120,
    sleepDragging: false,
    sleepBungee: false,
    bungeeVx: 0,
    bungeeVy: 0,
    sleepZTimer: 0,
  }};

  function getSpideyLedges() {{
    const list = [];
    const gY = groundY || (H - 35);
    // 1. Desk floor / dock top is always a dependable ground ledge
    list.push({{ x: 40, y: gY, w: Math.max(200, W - 80), h: 35, title: 'Screen Floor' }});

    // 2. Real application windows reported by macOS via CGWindowListCopyWindowInfo
    if (spideyRooftops && spideyRooftops.length > 0) {{
      for (const r of spideyRooftops) {{
        if (r.w > 140 && r.h > 90 && r.x < W && r.x + r.w > 0 && r.y < H && r.y + r.h > 0) {{
          // If window is at the very top of screen (y <= 40), perch on toolbar/header at y=95..110 so Spidey is 100% visible
          const topY = Math.max(95, Math.min(gY - 20, r.y <= 40 ? r.y + 75 : r.y));
          const appName = r.title || 'Window';
          if (r.w > 750) {{
            // Broad window (e.g. IDE, Browser, Editor): create two distinct vantage points
            list.push({{
              x: Math.max(20, r.x + 40),
              y: topY,
              w: Math.min(r.w * 0.42, 450),
              h: 35,
              title: appName + ' (Left)'
            }});
            list.push({{
              x: Math.min(W - 460, r.x + r.w * 0.54),
              y: topY,
              w: Math.min(r.w * 0.42, 450),
              h: 35,
              title: appName + ' (Right)'
            }});
          }} else {{
            list.push({{
              x: Math.max(20, r.x),
              y: topY,
              w: Math.min(r.w, W - Math.max(20, r.x)),
              h: 35,
              title: appName
            }});
          }}

          // If window is very tall (> 500px) and middle isn't too close to ground, add a mid sill
          if (r.h > 500 && (r.y + r.h * 0.5) < gY - 120) {{
            list.push({{
              x: Math.max(30, r.x + 50),
              y: Math.max(120, r.y + r.h * 0.5),
              w: Math.max(160, r.w - 100),
              h: 30,
              title: appName + ' (Sill)'
            }});
          }}
        }}
      }}
    }}

    // 3. Fallback synthetic city towers if only floor is available
    if (list.length <= 1) {{
      list.push(
        {{ x: 30, y: Math.max(110, gY - 280), w: Math.max(140, W * 0.28), h: 280, title: 'Daily Bugle Tower' }},
        {{ x: Math.max(180, W * 0.36), y: Math.max(110, gY - 180), w: Math.max(140, W * 0.28), h: 180, title: 'Oscorp Plaza' }},
        {{ x: Math.max(320, W * 0.68), y: Math.max(110, gY - 340), w: Math.max(140, W * 0.28), h: 340, title: 'Stark Tower' }}
      );
    }}
    return list;
  }}

  function triggerSpideySwing() {{
    if (state.species !== 'spiderman' || !state.hatched || state.asleep || pet.held || pet.carried) return;
    if (!DESKTOP || W < 600) return;
    const ledges = getSpideyLedges();
    if (!ledges || ledges.length === 0) return;

    // Filter candidates that are a good swing distance away (>= 150px)
    // Prefer ledges with different titles / different windows
    let candidates = ledges.filter(l => {{
      const lx = l.x + l.w * 0.5;
      const ly = l.y;
      const d = Math.hypot(lx - pet.x, ly - pet.y);
      const isDiff = !spidermanState.currentLedge || l.title !== spidermanState.currentLedge.title;
      return d >= 160 && isDiff;
    }});

    if (candidates.length === 0) {{
      candidates = ledges.filter(l => Math.hypot(l.x + l.w * 0.5 - pet.x, l.y - pet.y) >= 140);
    }}
    if (candidates.length === 0) candidates = ledges;

    // Prefer ledges within realistic swing range (<= 1400px) so he travels gracefully across windows
    const nearby = candidates.filter(l => Math.abs(l.x + l.w * 0.5 - pet.x) <= 1400);
    const target = (nearby.length > 0) ? pick(nearby) : pick(candidates);

    spidermanState.targetLedge = target;
    spidermanState.mode = 'aim';
    spidermanState.modeTimer = 0;

    const landingX = clamp(target.x + target.w * rand(0.25, 0.75), 60, W - 60);
    const landingY = target.y;
    spidermanState.targetSpot = {{ x: landingX, y: landingY }};
    pet.facing = (landingX < pet.x) ? -1 : 1;

    // Choose overhead web anchor point above the midpoint of trajectory
    const midX = (pet.x + landingX) * 0.5;
    const highestY = Math.min(pet.y, landingY);
    const anchorY = Math.max(20, highestY - rand(160, 260));
    const anchorX = clamp(midX + (pet.facing * rand(20, 50)), 40, W - 40);
    spidermanState.anchor = {{ x: anchorX, y: anchorY }};

    if (audio && audio.spideyThwip) audio.spideyThwip();
  }}

  function updateSpiderman(dt) {{
    if (state.species !== 'spiderman' || !state.hatched) return;
    const r = petR();

    // Expressive mechanical eye shutter blinking animation
    spidermanState.eyeBlinkTimer -= dt;
    if (spidermanState.eyeBlinkTimer <= 0) {{
      spidermanState.eyeShutter = Math.max(0, spidermanState.eyeShutter - dt * 22);
      if (spidermanState.eyeShutter <= 0) {{
        spidermanState.eyeBlinkTimer = rand(2.5, 6.0);
      }}
    }} else {{
      spidermanState.eyeShutter = Math.min(1.0, spidermanState.eyeShutter + dt * 16);
    }}

    if (state.asleep) {{
      if (!spidermanState.sleepAnchor) {{
        const anchorY = 25;
        spidermanState.sleepAnchor = {{ x: pet.x, y: anchorY }};
        spidermanState.sleepRestLength = 120;
        pet.mode = 'fly';
        pet.grounded = false;
        pet.y = anchorY + spidermanState.sleepRestLength + r * 2.2;
      }}
      spidermanState.mode = 'sleep_dangle';
      spidermanState.eyeShutter = 0;
      pet.mode = 'fly';
      pet.grounded = false;
      pet.spideySwinging = false;
      pet.walking = false;
      pet.walkDir = 0;

      const sa = spidermanState.sleepAnchor;
      const eqX = sa.x;
      const eqY = sa.y + (spidermanState.sleepRestLength || 120) + r * 2.2;

      // Cute periodic sleep Zzz particles drifting up from mask
      spidermanState.sleepZTimer = (spidermanState.sleepZTimer || 0) + dt;
      if (spidermanState.sleepZTimer >= 1.4 && !spidermanState.sleepDragging) {{
        spidermanState.sleepZTimer = 0;
        if (typeof spawn === 'function') {{
          spawn('z', pet.x + (pet.facing || 1) * 10, pet.y + 6, 1, {{ vy: -30, size: 7, dur: 2.2 }});
        }}
      }}

      if (spidermanState.sleepDragging) {{
        // While dragging: body tilts along web cord line of tension
        const dx = pet.x - sa.x;
        const dy = (pet.y - r * 2.2) - sa.y;
        const cordAngle = Math.atan2(dx, Math.max(10, dy));
        const targetPitch = clamp(-cordAngle * 0.9, -0.75, 0.75);
        pet.spideyPitch = lerp(pet.spideyPitch || 0, targetPitch, Math.min(1, dt * 14));
      }} else if (spidermanState.sleepBungee) {{
        // Releasing after drag: Hooke's Law damped spring oscillation!
        const dx = pet.x - eqX;
        const dy = pet.y - eqY;
        const kSpring = 26.0;
        const cDamp = 3.8;

        const ax = -kSpring * dx - cDamp * (spidermanState.bungeeVx || 0);
        const ay = -kSpring * dy - cDamp * (spidermanState.bungeeVy || 0);

        spidermanState.bungeeVx = (spidermanState.bungeeVx || 0) + ax * dt;
        spidermanState.bungeeVy = (spidermanState.bungeeVy || 0) + ay * dt;

        pet.x += spidermanState.bungeeVx * dt;
        pet.y += spidermanState.bungeeVy * dt;

        const cordAngle = Math.atan2(pet.x - sa.x, Math.max(10, (pet.y - r * 2.2) - sa.y));
        const targetPitch = clamp(-cordAngle * 0.9, -0.75, 0.75);
        pet.spideyPitch = lerp(pet.spideyPitch || 0, targetPitch, Math.min(1, dt * 12));

        if (Math.hypot(dx, dy) < 0.9 && Math.hypot(spidermanState.bungeeVx, spidermanState.bungeeVy) < 1.8) {{
          pet.x = eqX;
          pet.y = eqY;
          spidermanState.bungeeVx = 0;
          spidermanState.bungeeVy = 0;
          spidermanState.sleepBungee = false;
        }}
      }} else {{
        // At rest: gentle harmonic pendulum sway
        const sway = Math.sin(pet.t * 1.5) * 0.045;
        pet.spideyPitch = lerp(pet.spideyPitch || 0, sway, Math.min(1, dt * 3));
      }}
      clampSpiderman();
      return;
    }}

    if (pet.held || pet.carried) {{
      spidermanState.mode = 'dangle';
      spidermanState.anchor = null;
      spidermanState.eyeShutter = 1.0;
      pet.spideySwinging = false;
      return;
    }}

    // If released from being held/carried, smoothly land on nearest ledge
    if (spidermanState.mode === 'dangle' && !pet.held && !pet.carried) {{
      const ledges = getSpideyLedges();
      let nearest = ledges[0];
      let minDist = Infinity;
      for (const l of ledges) {{
        const lx = l.x + l.w * 0.5;
        const ly = l.y;
        const d = Math.hypot(lx - pet.x, ly - pet.y);
        if (d < minDist) {{ minDist = d; nearest = l; }}
      }}
      spidermanState.currentLedge = nearest;
      spidermanState.targetLedge = null;
      pet.x = clamp(pet.x, nearest.x + 20, nearest.x + nearest.w - 20);
      pet.y = nearest.y;
      pet.ax = pet.x;
      pet.mode = 'ground';
      pet.grounded = true;
      spidermanState.mode = 'crawl';
      spidermanState.modeTimer = 0;
      if (audio && audio.spideyZip) audio.spideyZip();
      return;
    }}

    // Bug reaction (Spidey Sense)
    const bug = (bugs && bugs.length > 0) ? bugs[0] : null;
    if (bug && pet.zap <= 0 && pet.zapCharge <= 0) {{
      const dBug = Math.hypot(bug.x - pet.x, bug.y - pet.y);
      if (dBug < 400) {{
        pet.facing = bug.x < pet.x ? -1 : 1;
        spidermanState.eyeShutter = 0.45; // Focused tactical squint
      }}
    }}

    // In desktop full stage mode (DESKTOP && W >= 600) or active animation (flip / swing / crawl), run state machine
    if (spidermanState.mode !== 'flip' && spidermanState.mode !== 'swing' && spidermanState.mode !== 'crawl' && (!DESKTOP || W < 600)) {{
      return;
    }}

    const ledges = getSpideyLedges();

    // Ensure we have a valid starting ledge
    if (!spidermanState.currentLedge) {{
      let nearest = ledges[0];
      let minDist = Infinity;
      for (const l of ledges) {{
        const lx = l.x + l.w * 0.5;
        const ly = l.y;
        const d = Math.hypot(lx - pet.x, ly - pet.y);
        if (d < minDist) {{ minDist = d; nearest = l; }}
      }}
      spidermanState.currentLedge = nearest;
      if (Math.hypot(pet.x - (nearest.x + nearest.w * 0.5), pet.y - nearest.y) > 120) {{
        pet.x = nearest.x + nearest.w * 0.5;
        pet.y = nearest.y;
        pet.ax = pet.x;
      }}
    }}

    // State machine
    if (spidermanState.mode === 'perch') {{
      pet.mode = 'ground';
      pet.grounded = true;
      pet.spideySwinging = false;
      pet.walking = false;
      spidermanState.modeTimer += dt;

      // Expressive awareness: glance towards cursor if user is working nearby
      if (pointer && pointer.x !== undefined && Math.abs(pointer.x - pet.x) > 30) {{
        pet.facing = pointer.x < pet.x ? -1 : 1;
      }}

      // Automatic active window skyline patrol: swing between windows every 2.5 - 6.5s!
      if (spidermanState.modeTimer >= spidermanState.perchDuration) {{
        triggerSpideySwing();
      }}
    }} else if (spidermanState.mode === 'aim') {{
      spidermanState.modeTimer += dt;
      pet.facing = (spidermanState.anchor.x < pet.x) ? -1 : 1;
      if (spidermanState.modeTimer >= 0.20) {{
        // Launch into pendulum swing!
        spidermanState.mode = 'swing';
        spidermanState.modeTimer = 0;
        spidermanState.swingDuration = clamp(Math.hypot(spidermanState.targetSpot.x - pet.x, spidermanState.targetSpot.y - pet.y) / 450, 0.9, 1.35);
        pet.spideySwinging = true;
        pet.mode = 'fly';
        pet.grounded = false;
        spidermanState.swingFrom = {{ x: pet.x, y: pet.y }};
        spidermanState.swingTo = {{ x: spidermanState.targetSpot.x, y: spidermanState.targetSpot.y }};
        if (audio && audio.spideyZip) audio.spideyZip();
      }}
    }} else if (spidermanState.mode === 'swing') {{
      spidermanState.modeTimer += dt;
      const progress = Math.min(1.0, spidermanState.modeTimer / spidermanState.swingDuration);
      spidermanState.swingT = progress;

      const ax = spidermanState.anchor.x, ay = spidermanState.anchor.y;
      const startAngle = Math.atan2(spidermanState.swingFrom.y - ay, spidermanState.swingFrom.x - ax);
      const endAngle = Math.atan2(spidermanState.swingTo.y - 28 - ay, spidermanState.swingTo.x - ax);
      const chordFrom = Math.hypot(spidermanState.swingFrom.x - ax, spidermanState.swingFrom.y - ay);
      const chordTo = Math.hypot(spidermanState.swingTo.x - ax, spidermanState.swingTo.y - 28 - ay);

      // Pendulum harmonic sinusoidal easing
      const pEased = 0.5 - 0.5 * Math.cos(progress * Math.PI);
      const curAngle = lerp(startAngle, endAngle, pEased);
      const curChord = lerp(chordFrom, chordTo, progress);

      pet.x = ax + Math.cos(curAngle) * curChord;
      pet.y = ay + Math.sin(curAngle) * curChord;

      pet.facing = (spidermanState.swingTo.x >= spidermanState.swingFrom.x) ? 1 : -1;
      clampSpiderman();

      if (progress >= 0.88) {{
        // Web release! Somersault flip to ledge
        spidermanState.mode = 'flip';
        spidermanState.modeTimer = 0;
        spidermanState.flipFrom = {{ x: pet.x, y: pet.y }};
        spidermanState.flipTo = {{ x: spidermanState.swingTo.x, y: spidermanState.swingTo.y }};
        spidermanState.anchor = null; // web severed
        if (audio && audio.spideyZip) audio.spideyZip();
      }}
    }} else if (spidermanState.mode === 'flip') {{
      spidermanState.modeTimer += dt;
      const flipDur = 0.38;
      const fProg = Math.min(1.0, spidermanState.modeTimer / flipDur);
      spidermanState.flipT = fProg;

      const fx = lerp(spidermanState.flipFrom.x, spidermanState.flipTo.x, fProg);
      const arc = 38 * Math.sin(fProg * Math.PI);
      const fy = lerp(spidermanState.flipFrom.y, spidermanState.flipTo.y, fProg) - arc;
      pet.x = fx;
      pet.y = fy;
      clampSpiderman();

      if (fProg >= 1.0) {{
        // Land on the ledge!
        spidermanState.mode = 'crawl';
        spidermanState.modeTimer = 0;
        pet.spideySwinging = false;
        pet.grounded = true;
        pet.mode = 'ground';
        pet.ax = pet.x;
        spidermanState.currentLedge = spidermanState.targetLedge;
        spidermanState.targetLedge = null;
        if (audio && audio.spideyZip) audio.spideyZip();
        if (Math.random() < 0.40) {{
          const lTitle = spidermanState.currentLedge ? spidermanState.currentLedge.title : '';
          const lines = [
            "Nailed the landing!",
            "Friendly neighborhood Spider-Man on duty!",
            "Clear view from up here.",
            "Thwip thwip!"
          ];
          if (lTitle && !lTitle.includes('Floor')) {{
            lines.push("Perched on " + lTitle + "!");
            lines.push("Checking out " + lTitle + "!");
          }}
          say(pick(lines), 2400);
        }}
      }}
    }} else if (spidermanState.mode === 'crawl') {{
      spidermanState.modeTimer += dt;
      pet.walking = true;
      pet.walkDir = pet.facing || 1;
      pet.x += (pet.facing || 1) * 48 * dt;
      pet.ax = pet.x;
      clampSpiderman();
      if (spidermanState.modeTimer >= 0.75) {{
        pet.walking = false;
        pet.walkDir = 0;
        spidermanState.mode = 'perch';
        spidermanState.modeTimer = 0;
        spidermanState.perchDuration = spideyUserActive ? rand(4.0, 6.5) : rand(2.5, 4.5);
      }}
    }}
  }}

  function drawWebSplat(c, x, y, splatR) {{
    c.save();
    c.strokeStyle = 'rgba(255, 255, 255, 0.85)';
    c.lineWidth = Math.max(1.2, splatR * 0.08);
    const spokes = 8;
    for (let i = 0; i < spokes; i++) {{
      const a = (i / spokes) * Math.PI * 2;
      c.beginPath();
      c.moveTo(x, y);
      c.lineTo(x + Math.cos(a) * splatR, y + Math.sin(a) * splatR);
      c.stroke();
      if (i % 2 === 0) {{
        c.fillStyle = 'rgba(255, 255, 255, 0.9)';
        c.beginPath();
        c.arc(x + Math.cos(a) * (splatR * 0.6), y + Math.sin(a) * (splatR * 0.6), splatR * 0.12, 0, Math.PI * 2);
        c.fill();
      }}
    }}
    // Concentric web ring
    c.beginPath();
    c.arc(x, y, splatR * 0.5, 0, Math.PI * 2);
    c.stroke();
    c.restore();
  }}

  function drawSpiderman() {{
    const asleep = state.asleep;
    const isCarried = !!(pet.carried || pet.held);
    const charging = pet.zapCharge > 0 && !asleep;
    const firing = pet.zap > 0;
    const isBoss = pet.zapBoss || false;
    const isSwinging = !!(pet.spideySwinging || spidermanState.mode === 'swing' || spidermanState.mode === 'flip');
    const vx = (pet.held ? pet.vx : (pet.dragVx || 0));
    const vy = (pet.held ? pet.vy : (pet.dragVy || 0));
    const rawSpeed = Math.hypot(vx, vy) || (pet.dragSpeed || 0);

    pet.spideySpeed = (pet.spideySpeed || 0) * 0.84 + rawSpeed * 0.16;

    // Determine facing direction
    if (charging || firing) {{
      if (pet.zapX !== undefined && Math.abs(pet.zapX - pet.x) > 2) {{
        pet.facing = pet.zapX < pet.x ? -1 : 1;
      }}
    }} else if (isCarried && Math.abs(vx) > 12) {{
      pet.facing = vx < 0 ? -1 : 1;
    }} else if (pet.walking && pet.walkDir) {{
      pet.facing = pet.walkDir;
    }} else if (isSwinging && spidermanState.swingTo) {{
      pet.facing = (spidermanState.swingTo.x >= spidermanState.swingFrom.x) ? 1 : -1;
    }}

    const f = pet.facing || 1;

    // Aerodynamic flight pitch and dangle tilt
    let targetPitch = 0;
    if (asleep) {{
      targetPitch = pet.spideyPitch || 0;
    }} else if (isCarried) {{
      targetPitch = clamp((vx / 1500) * 0.35, -0.32, 0.32);
    }} else if (isSwinging) {{
      targetPitch = f * 0.22 * Math.sin(spidermanState.swingT * Math.PI);
    }}
    if (!asleep) {{
      pet.spideyPitch = (pet.spideyPitch || 0) * 0.82 + targetPitch * 0.18;
    }}

    // -------------------------------------------------------- Procedural Dynamic Web Line & Anchor Splat
    const r = petR();
    if (asleep && spidermanState.sleepAnchor) {{
      const sa = spidermanState.sleepAnchor;
      const pitch = pet.spideyPitch || 0;
      const feetX = pet.x + Math.sin(pitch) * r * 0.9;
      const feetY = pet.y - r * 2.2 * Math.cos(pitch);

      ctx.save();
      // Fixed anchor web splat at top of window
      drawWebSplat(ctx, sa.x, sa.y, 18);

      const dist = Math.hypot(feetX - sa.x, feetY - sa.y);
      const L0 = spidermanState.sleepRestLength || 120;
      const stretch = dist / L0;
      const coreWidth = clamp(1.9 / Math.sqrt(Math.max(0.4, stretch)), 0.8, 2.5);
      const glowWidth = coreWidth * 2.2;

      let midX = (feetX + sa.x) * 0.5;
      let midY = (feetY + sa.y) * 0.5;

      if (dist < L0 * 0.85) {{
        // Slack curve when pushed upwards towards anchor
        const slack = (L0 - dist) * 0.45;
        midX += (pet.facing || 1) * slack * 0.4;
        midY += slack;
      }} else {{
        // Tension flutter when stretched or swinging
        const flutter = (spidermanState.sleepDragging || spidermanState.sleepBungee)
          ? Math.sin(pet.t * 38) * Math.min(5, Math.max(0, stretch - 1) * 4.5)
          : Math.sin(pet.t * 1.6) * 0.8;
        const perpX = -(feetY - sa.y) / (dist || 1);
        const perpY = (feetX - sa.x) / (dist || 1);
        midX += perpX * flutter;
        midY += perpY * flutter;
      }}

      // Outer silk glow
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
      ctx.lineWidth = glowWidth;
      ctx.beginPath();
      ctx.moveTo(sa.x, sa.y);
      ctx.quadraticCurveTo(midX, midY, feetX, feetY);
      ctx.stroke();

      // Inner white core
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = coreWidth;
      ctx.beginPath();
      ctx.moveTo(sa.x, sa.y);
      ctx.quadraticCurveTo(midX, midY, feetX, feetY);
      ctx.stroke();

      ctx.restore();
    }} else if (spidermanState.anchor && (spidermanState.mode === 'swing' || spidermanState.mode === 'aim')) {{
      const ax = spidermanState.anchor.x, ay = spidermanState.anchor.y;
      const wx = pet.x + f * r * 0.42;
      const wy = pet.y - r * 0.85;

      ctx.save();
      // Anchor web splat
      drawWebSplat(ctx, ax, ay, 18);

      // Catenary sag and harmonic high-speed flutter
      const flutter = Math.sin(pet.t * 36) * 3.2 * (1 - spidermanState.swingT);
      const midX = (wx + ax) * 0.5;
      const midY = (wy + ay) * 0.5 + flutter;

      // Web glow & core
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.42)';
      ctx.lineWidth = 3.6;
      ctx.beginPath();
      ctx.moveTo(wx, wy);
      ctx.quadraticCurveTo(midX, midY, ax, ay);
      ctx.stroke();

      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.moveTo(wx, wy);
      ctx.quadraticCurveTo(midX, midY, ax, ay);
      ctx.stroke();
      ctx.restore();
    }}

    // Dangle elastic silk cord when held/carried (awake only)
    if (isCarried && !asleep && !spidermanState.sleepAnchor) {{
      ctx.save();
      const topY = Math.max(0, pet.y - 400);
      drawWebSplat(ctx, pet.x, topY, 14);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
      ctx.lineWidth = 3.2;
      ctx.beginPath();
      ctx.moveTo(pet.x, pet.y - r * 0.9);
      ctx.lineTo(pet.x, topY);
      ctx.stroke();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.moveTo(pet.x, pet.y - r * 0.9);
      ctx.lineTo(pet.x, topY);
      ctx.stroke();
      ctx.restore();
    }}

    stageBody({{
      shadow: !isCarried && !asleep && !isSwinging,
      bob: isCarried ? 0.02 : (pet.walking ? 0.07 : (asleep ? 0 : 0.035)),
      bobRate: pet.walking ? 8.5 : (asleep ? 1.4 : 2.6),
      sway: (isCarried || asleep || isSwinging) ? 0 : 0.02
    }}, (r, t) => {{
      ctx.save();

      // Neutralize stage squash/stretch so pristine 3D art stays undistorted
      const sx = (1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6);
      const sy = (1 + pet.sq) * (1 + pet.stretch);
      if (Math.abs(sx) > 0.05 && Math.abs(sy) > 0.05) {{
        ctx.scale(1 / sx, 1 / sy);
      }}

      // Organic chest breathing respiration
      if (!isCarried && !isSwinging) {{
        ctx.scale(1, 1 + (asleep ? 0.012 : 0.018) * Math.sin(t * (asleep ? 1.8 : 3.2)));
      }}

      // Facing scale and aerodynamic pitch tilt
      ctx.scale(f, 1);
      ctx.rotate(pet.spideyPitch);

      // Select high-definition 3D pose
      let sprite = spideyImgIdle;
      let targetH = r * 2.38;
      let yOffset = 0.94;

      if (asleep) {{
        sprite = spideyImgDangle;
        targetH = r * 2.55;
        yOffset = 0.90;
      }} else if (isCarried) {{
        sprite = spideyImgDangle;
        targetH = r * 2.55;
        yOffset = 0.90;
      }} else if (firing) {{
        sprite = isBoss ? spideyImgAttack : spideyImgShoot;
        targetH = r * 2.50;
        yOffset = 0.94;
      }} else if (charging) {{
        sprite = spideyImgShoot;
        targetH = r * 2.50;
        yOffset = 0.94;
      }} else if (spidermanState.mode === 'flip') {{
        sprite = spideyImgFlip;
        targetH = r * 2.45;
        yOffset = 0.92;
      }} else if (isSwinging) {{
        sprite = (spidermanState.swingT < 0.5) ? spideyImgSwingDown : spideyImgSwingUp;
        targetH = r * 2.50;
        yOffset = 0.94;
      }} else if (pet.walking) {{
        sprite = spideyImgCrawl;
        targetH = r * 2.25;
        yOffset = 0.88;
      }} else {{
        sprite = spideyImgIdle;
        targetH = r * 2.38;
        yOffset = 0.94;
      }}

      // Draw high-resolution Spider-Man pose image
      if (sprite && sprite.complete && sprite.naturalWidth > 0) {{
        const aspect = sprite.naturalWidth / sprite.naturalHeight;
        const drawH = targetH;
        const drawW = drawH * aspect;
        const drawX = -drawW * 0.5;
        const drawY = -drawH * yOffset;

        ctx.drawImage(sprite, drawX, drawY, drawW, drawH);
      }}

      // Spider-Sense Ditko Lightning Halo Waves
      const bugNear = (bugs && bugs.length > 0 && Math.hypot(bugs[0].x - pet.x, bugs[0].y - pet.y) < 420);
      if (bugNear || pet.zapCharge > 0) {{
        ctx.save();
        const numArcs = 7;
        for (let i = 0; i < numArcs; i++) {{
          const a = -Math.PI * 0.85 + (i / (numArcs - 1)) * Math.PI * 0.7;
          const d1 = r * 1.35 + Math.sin(t * 18 + i * 2) * 5;
          const d2 = r * 1.85 + Math.cos(t * 22 + i) * 6;
          const midA = a + (i % 2 === 0 ? 0.08 : -0.08);

          ctx.strokeStyle = (i % 2 === 0) ? '#ffe600' : '#e23636';
          ctx.lineWidth = 2.2;
          ctx.shadowColor = '#ffe600';
          ctx.shadowBlur = 8;
          ctx.beginPath();
          ctx.moveTo(Math.cos(a) * d1, -r * 1.2 + Math.sin(a) * d1);
          ctx.lineTo(Math.cos(midA) * ((d1 + d2) * 0.5), -r * 1.2 + Math.sin(midA) * ((d1 + d2) * 0.5));
          ctx.lineTo(Math.cos(a) * d2, -r * 1.2 + Math.sin(a) * d2);
          ctx.stroke();
        }}
        ctx.restore();
      }}

      ctx.restore();
    }});
  }}

  // -------------------------------------------------------- Dynamic Web Ballistic & Slingshot Attack
  function drawSpidermanWebAttack(r, k, isBoss, attackStyle) {{
    ctx.save();
    const f = pet.facing || 1;
    const ox = pet.x + f * r * 0.75;
    const oy = pet.y - r * 0.92;
    const targetX = pet.zapX !== undefined ? pet.zapX : (pet.x + f * 420);
    const targetY = pet.zapY !== undefined ? pet.zapY : (pet.y - r * 0.4);

    const curX = lerp(ox, targetX, Math.min(1.0, k * 2.2));
    const curY = lerp(oy, targetY, Math.min(1.0, k * 2.2));

    if (isBoss) {{
      // Dual-anchor Slingshot Catapult Launch
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.95)';
      ctx.lineWidth = Math.max(2.5, r * 0.08);
      ctx.shadowColor = 'rgba(255, 255, 255, 0.8)';
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.moveTo(ox - f * r * 2.5, oy - r * 1.5);
      ctx.lineTo(ox, oy);
      ctx.moveTo(ox - f * r * 2.5, oy + r * 0.5);
      ctx.lineTo(ox, oy);
      ctx.stroke();

      // Forward supersonic impact beam
      ctx.strokeStyle = '#e23636';
      ctx.lineWidth = Math.max(3.5, r * 0.12 * k);
      ctx.beginPath();
      ctx.moveTo(ox, oy);
      ctx.lineTo(curX, curY);
      ctx.stroke();

      drawWebSplat(ctx, targetX, targetY, r * 0.75 * (1 - k));
    }} else {{
      // Standard Thwip Web Stream firing forward
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = Math.max(2.0, r * 0.06);
      ctx.shadowColor = 'rgba(255, 255, 255, 0.9)';
      ctx.shadowBlur = 4;
      ctx.beginPath();
      ctx.moveTo(ox, oy);
      ctx.lineTo(curX, curY);
      ctx.stroke();

      // Expanding Web Net Cocoon at target
      const netRadius = r * 0.65 * (1 - k);
      drawWebSplat(ctx, targetX, targetY, netRadius);
    }}

    ctx.restore();
  }}

"""

content = content[:start_idx] + spiderman_full_block + content[end_idx:]

with open("web/bitling.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated web/bitling.html successfully")
