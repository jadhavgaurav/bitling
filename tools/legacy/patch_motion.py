#!/usr/bin/env python3
"""One-off migration: jelly motion -> robot motion.

Real walk cycle with strides and facing, knee bends instead of body squash, stomps
instead of hops, head tilt on pats, dangling legs when carried, tumbling when thrown,
and flight (take off, hover anywhere, land). Also moves the desktop-mode detection
into the shared page so shared logic can call native() safely.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "web" / "bitling.html"
s = SRC.read_text(encoding="utf-8")
if "function takeOff" in s:
    raise SystemExit("already applied")


def patch(old: str, new: str) -> None:
    global s
    if s.count(old) != 1:
        raise SystemExit(f"anchor found {s.count(old)}x, expected 1:\n{old[:160]}")
    s = s.replace(old, new)


def replace_range(start_marker: str, end_marker: str, new: str) -> None:
    global s
    i = s.index(start_marker)
    j = s.index(end_marker, i)
    s = s[:i] + new + s[j:]


# ---------------------------------------------------------------- desktop detection lives in the shared page now
patch("  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;\n",
      "  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;\n"
      "  const HOST = (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.pet) || null;\n"
      "  // ?desktop=1 or window.__forceDesktop previews the desktop layout in an ordinary browser (bridge calls are dropped).\n"
      "  const DESKTOP = !!HOST || /[?&]desktop=1/.test(window.location.search) || window.__forceDesktop === true;\n"
      "  if (DESKTOP) document.documentElement.classList.add('desktop');\n"
      "  function native(msg) {\n"
      "    if (!HOST) return;\n"
      "    try { HOST.postMessage(msg); } catch (_) { /* host gone */ }\n"
      "  }\n")
patch("  @media (prefers-reduced-motion:reduce){ .bubble{animation:none} }\n",
      "  @media (prefers-reduced-motion:reduce){ .bubble{animation:none} }\n"
      "  html.desktop,html.desktop body,html.desktop #app{background:transparent}\n"
      "  html.desktop .hud,html.desktop .dock{display:none}\n"
      "  html.desktop #stage{cursor:default}\n"
      "  html.desktop .bubble{white-space:normal;max-width:calc(100vw - 16px);text-align:center;font-size:15px;padding:6px 11px;line-height:1.25}\n")

# ---------------------------------------------------------------- fields
patch("    screenText: '', screenTint: '', screenT: 0, shake: 0, deploying: false, deployProgress: 0,\n  };",
      "    mode: 'ground', landing: false, fx: 0, fy: 0, flyT: 0, hoverUntil: 0, thrust: 0,\n"
      "    facing: 1, stride: 0, walking: false, knee: 0, tilt: 0, stomp: 0, turnT: 0, stretchT: 0, tapT: 0,\n"
      "    spin: 0, spinV: 0, thrown: false,\n"
      "    screenText: '', screenTint: '', screenT: 0, shake: 0, deploying: false, deployProgress: 0,\n  };")
patch("    for (const k of ['chew', 'happy', 'surprise', 'yawn', 'dizzy', 'glance', 'shake', 'screenT', 'wave', 'workT']) pet[k] = Math.max(0, pet[k] - dt);",
      "    for (const k of ['chew', 'happy', 'surprise', 'yawn', 'dizzy', 'glance', 'shake', 'screenT', 'wave', 'workT', 'tilt', 'stomp', 'turnT', 'stretchT', 'tapT']) pet[k] = Math.max(0, pet[k] - dt);\n"
      "    pet.knee = lerp(pet.knee, 0, Math.min(1, dt * 6));")

# ---------------------------------------------------------------- squash -> robot gestures
patch("    pet.happy = 1.2;\n    pet.sq = -0.22; pet.sqv = 0;\n    audio.squeak();",
      "    pet.happy = 1.2;\n    pet.tilt = 1;\n    pet.sq = -0.04; pet.sqv = 0;\n    audio.squeak();")
patch("    if (byPet) { pet.sq = -0.25; pet.sqv = 0; pet.happy = 0.6; }",
      "    if (byPet) { pet.knee = 0.5; pet.happy = 0.6; }")
patch("    rocket.t = 0;\n    pet.sq = 0.25; pet.sqv = 0;\n    pet.happy = 2;",
      "    rocket.t = 0;\n    pet.stretchT = 1.4;\n    pet.happy = 2;")
patch("    state.asleep = false;\n    pet.sq = 0.2; pet.sqv = 0;\n    pet.yawn = 1.2;",
      "    state.asleep = false;\n    pet.stretchT = 1.6;\n    pet.yawn = 1.2;")
patch("    pet.x = pet.ax; pet.y = groundY; pet.grounded = true;\n    pet.sq = 0.35; pet.sqv = 0;\n    pet.happy = 1.5;",
      "    pet.x = pet.ax; pet.y = groundY; pet.grounded = true;\n    pet.knee = 0.6;\n    pet.happy = 1.5;")
patch("    audio.grow();\n    pet.sq = 0.35; pet.sqv = 0;\n    pet.happy = 2;",
      "    audio.grow();\n    pet.stretchT = 2;\n    pet.happy = 2;")
patch("        if (churn > 400) { line = `chonky commit! ${churn} lines`; pet.sq = 0.3; pet.sqv = 0; }",
      "        if (churn > 400) { line = `chonky commit! ${churn} lines`; pet.knee = 0.5; }")
patch("    pet.ax = W / 2; pet.x = W / 2; pet.y = groundY; pet.sq = 0; pet.sqv = 0; pet.happy = 0;",
      "    pet.ax = W / 2; pet.x = W / 2; pet.y = groundY; pet.sq = 0; pet.sqv = 0; pet.happy = 0;\n"
      "    pet.mode = 'ground'; pet.landing = false; pet.thrown = false; pet.spin = 0; pet.spinV = 0; pet.thrust = 0; pet.knee = 0;")

# ---------------------------------------------------------------- land / release / grab
patch("""  function land(vy) {
    const imp = clamp(vy / 1600, 0, 0.4);
    pet.sq = -imp; pet.sqv = 0;
    if (imp > 0.12) {""", """  function land(vy) {
    const imp = clamp(vy / 1600, 0, 0.4);
    pet.knee = clamp(imp * 1.8, 0.15, 0.75);
    pet.spin = 0; pet.spinV = 0; pet.thrown = false;
    pet.mode = 'ground'; pet.landing = false; pet.thrust = 0;
    if (imp > 0.12) {""")
patch("""    pet.ax = clamp(pet.x, petR(), W - petR());
    if (pet.y >= groundY && pet.vy >= -60) { pet.y = groundY; pet.grounded = true; land(Math.abs(pet.vy)); pet.vy = 0; }
    else if (pet.y >= groundY) { pet.y = groundY - 1; }
  }""", """    pet.ax = clamp(pet.x, petR(), W - petR());
    const speed = Math.hypot(pet.vx, pet.vy);
    if (pet.mode === 'fly' && speed < 260) {
      // Dropped gently mid-air while flying: hover where it was left.
      pet.vx = 0; pet.vy = 0; pet.fx = pet.x; pet.fy = Math.min(pet.y, groundY - 1);
      pet.landing = false; pet.hoverUntil = pet.t + rand(5, 12);
      return;
    }
    pet.mode = 'ground'; pet.landing = false; pet.thrust = 0;
    if (pet.y >= groundY && pet.vy >= -60) { pet.y = groundY; pet.grounded = true; land(Math.abs(pet.vy)); pet.vy = 0; }
    else {
      if (pet.y >= groundY) pet.y = groundY - 1;
      pet.thrown = true; pet.spinV = clamp(pet.vx / 150, -6, 6);
    }
  }""")

# ---------------------------------------------------------------- stomp instead of pounce
patch("""    if (canStomp && pet.grounded && bestDist < r * 1.3 && bestDist > r * 0.55 && !reduceMotion) {
      pet.vy = -260; pet.grounded = false; pet.sq = 0.15; pet.sqv = 0;
      pet.vx = Math.sign(best.x - pet.x) * 120;
    }""", """    if (canStomp && pet.grounded && bestDist < r * 1.1 && pet.stomp <= 0 && !reduceMotion) pet.stomp = 0.35;""")
patch("      if (canStomp && pet.grounded && Math.abs(b.x - pet.x) < r * 0.55) squashBug(b, true);",
      "      if (canStomp && pet.grounded && Math.abs(b.x - pet.x) < r * 0.62) squashBug(b, true);")

# ---------------------------------------------------------------- come down before ground activities
patch("    if (state.full >= 95) { say(pick(LINES.full)); return; }\n    snack.active = true;",
      "    if (state.full >= 95) { say(pick(LINES.full)); return; }\n    comeDown();\n    snack.active = true;")
patch("    if (state.energy < 15) { say(pick(LINES.tired)); pet.yawn = 1.2; return; }\n    debug.active = true;",
      "    if (state.energy < 15) { say(pick(LINES.tired)); pet.yawn = 1.2; return; }\n    comeDown();\n    debug.active = true;")
patch("  function spawnDrop(kind, label) {\n    drop.active = true;",
      "  function spawnDrop(kind, label) {\n    comeDown();\n    drop.active = true;")
patch("    if (state.asleep) { wake(); return; }\n    state.asleep = true;",
      "    if (state.asleep) { wake(); return; }\n    comeDown();\n    state.asleep = true;")

# ---------------------------------------------------------------- flight helpers (before the pointer section)
patch("  // ---------------------------------------------------------------- pointer\n",
      """  // ---------------------------------------------------------------- flight
  function takeOff() {
    if (!state.hatched || state.asleep || pet.held || pet.carried || pet.thrown || pet.mode === 'fly') return false;
    if (state.energy < 25 || snack.active || drop.active || debug.active) return false;
    const r = petR();
    pet.mode = 'fly'; pet.landing = false; pet.grounded = false; pet.thrown = false;
    pet.vx = 0; pet.vy = 0; pet.flyT = 0; pet.hoverUntil = pet.t + rand(6, 16);
    state.energy = clamp(state.energy - 2);
    audio.tone(120, 260, 0.45, 'triangle', 0.03);
    if (DESKTOP) native({ type: 'fly', x: rand(0.08, 0.92), y: rand(0.15, 0.75) });
    else { pet.fx = rand(r * 1.5, W - r * 1.5); pet.fy = rand(H * 0.25, groundY - r * 2.5); }
    return true;
  }
  function comeDown() {
    if (pet.mode !== 'fly' || pet.landing) return;
    pet.landing = true;
    if (DESKTOP) native({ type: 'land' });
    else { const r = petR(); pet.fx = clamp(pet.x + rand(-60, 60), r, W - r); pet.fy = groundY; }
  }
  function finishLanding() {
    const r = petR();
    pet.mode = 'ground'; pet.landing = false; pet.grounded = true; pet.thrown = false;
    pet.y = groundY; pet.vx = 0; pet.vy = 0; pet.thrust = 0;
    pet.knee = 0.55;
    pet.ax = clamp(pet.x, r, W - r);
    spawn('dust', pet.x, groundY - 4, 4, { spread: r * 0.6, vx: 50, vy: -20, g: -10, size: 8, dur: 0.6 });
  }
  function handleFlight(phase) {
    switch (String(phase)) {
      case 'takeoff':
      case 'hover':
        pet.mode = 'fly'; pet.landing = false; pet.grounded = false; pet.thrown = false; pet.spin = 0; pet.spinV = 0;
        if (phase === 'hover') pet.hoverUntil = pet.t + rand(5, 12);
        break;
      case 'landing':
        pet.mode = 'fly'; pet.landing = true;
        break;
      case 'landed':
        finishLanding();
        break;
      case 'thrown':
        pet.mode = 'ground'; pet.landing = false; pet.grounded = false; pet.thrown = true; pet.thrust = 0;
        pet.spinV = rand(-5, 5);
        break;
      default:
        break;
    }
  }

  // ---------------------------------------------------------------- pointer
""")

# ---------------------------------------------------------------- updatePet
look_start = "      if (!state.asleep) {\n        if (snack.active) {"
look_end = "      } else { pet.lookT.x = 0; pet.lookT.y = 0.3; }\n"
li = s.index(look_start)
lj = s.index(look_end, li) + len(look_end)
look_chain = s[li:lj]

replace_range("  function updatePet(dt) {", "  function updateSnack(dt) {", """  function updatePet(dt) {
    pet.t += dt;
    for (const k of ['chew', 'happy', 'surprise', 'yawn', 'dizzy', 'glance', 'shake', 'screenT', 'wave', 'workT', 'tilt', 'stomp', 'turnT', 'stretchT', 'tapT']) pet[k] = Math.max(0, pet[k] - dt);
    pet.knee = lerp(pet.knee, 0, Math.min(1, dt * 6));
    if (pet.working && pet.workT <= 0) pet.working = false;
    if (pet.screenT <= 0 && (pet.screenText || (pet.screenTint && !pet.deploying))) { pet.screenText = ''; if (!pet.deploying) pet.screenTint = ''; }
    if (pet.deploying) pet.deployProgress = Math.min(0.92, pet.deployProgress + dt * 0.05);
    egg.wobble = Math.max(0, egg.wobble - dt * 1.4);

    if (pet.blinking) {
      pet.blinkT += dt;
      pet.blink = Math.sin(Math.PI * Math.min(1, pet.blinkT / 0.24));
      if (pet.blinkT >= 0.24) { pet.blinking = false; pet.blink = 0; pet.nextBlink = rand(2.5, 6); }
    } else {
      pet.nextBlink -= dt;
      if (pet.nextBlink <= 0) { pet.blinking = true; pet.blinkT = 0; }
    }

    const r = petR();
    if (pet.held) {
      const tx = pointer.x - pet.holdOff.x, ty = pointer.y - pet.holdOff.y;
      const k = Math.min(1, dt * 18);
      const nx = lerp(pet.x, tx, k), ny = lerp(pet.y, ty, k);
      pet.vx = (nx - pet.x) / dt; pet.vy = (ny - pet.y) / dt;
      pet.x = nx; pet.y = ny;
      pet.stretch = lerp(pet.stretch, clamp(Math.hypot(pet.vx, pet.vy) / 3500, 0, 0.3), Math.min(1, dt * 10));
      pet.lookT.x = clamp(pet.vx / 800, -1, 1);
      pet.lookT.y = 0.6;
    } else {
      pet.stretch = lerp(pet.stretch, 0, Math.min(1, dt * 10));
      if (!pet.grounded) {
        if (pet.mode === 'fly') {
          if (!DESKTOP) {
            pet.x += (pet.fx - pet.x) * Math.min(1, dt * 2.2);
            pet.y += (pet.fy - pet.y) * Math.min(1, dt * 2.2);
            if (Math.abs(pet.fx - pet.x) > 4) pet.facing = Math.sign(pet.fx - pet.x);
            pet.vx = 0; pet.vy = 0;
            if (pet.landing && Math.abs(pet.y - groundY) < 3) finishLanding();
          }
        } else if (DESKTOP) {
          // The host moves the window while thrown; only the tumble is simulated here.
          if (pet.thrown) pet.spin += pet.spinV * dt;
        } else {
          pet.vy += 2400 * dt;
          pet.y += pet.vy * dt;
          pet.x += pet.vx * dt;
          if (pet.thrown) pet.spin += pet.spinV * dt;
          if (pet.y >= groundY) {
            pet.y = groundY; pet.grounded = true;
            land(pet.vy); pet.vy = 0; pet.vx *= 0.4;
            pet.ax = clamp(pet.x, r, W - r);
          }
        }
      } else {
        pet.vx *= Math.pow(0.02, dt);
        pet.x += pet.vx * dt;
        if (!state.asleep) {
          const dx = pet.ax - pet.x;
          const speed = ((debug.active || snack.active || drop.active) ? 150 : 75) * scale;
          if (Math.abs(dx) > 2) {
            pet.x += Math.sign(dx) * Math.min(Math.abs(dx), speed * dt);
            pet.facing = Math.sign(dx);
          }
        }
      }
      pet.x = clamp(pet.x, r, W - r);

      if (pet.walkDir) pet.facing = pet.walkDir;
      pet.walking = !state.asleep && !pet.carried && pet.grounded && (pet.walkDir !== 0 || Math.abs(pet.ax - pet.x) > 2);
      if (pet.walking) pet.stride += dt * 9;
      else pet.stride = lerp(pet.stride, Math.round(pet.stride / Math.PI) * Math.PI, Math.min(1, dt * 10));

      if (pet.mode === 'fly') {
        pet.flyT += dt;
        pet.thrust = lerp(pet.thrust, pet.landing ? 0.6 : 1, Math.min(1, dt * 4));
        if (!reduceMotion && Math.random() < 0.5) spawn('flame', pet.x, pet.y - r * 0.1, 1, { spread: r * 0.12, vx: 20, vy: 120, g: 0, size: 6, dur: 0.35, hue: rand(20, 45) });
        if (!pet.landing && pet.hoverUntil > 0 && pet.t > pet.hoverUntil) comeDown();
      } else {
        pet.thrust = lerp(pet.thrust, 0, Math.min(1, dt * 8));
      }
      if (pet.grounded && !pet.thrown) { pet.spin = lerp(pet.spin, 0, Math.min(1, dt * 10)); pet.spinV = 0; }

""" + look_chain + """    }
    const lk = Math.min(1, dt * 9);
    pet.look.x = lerp(pet.look.x, pet.lookT.x, lk);
    pet.look.y = lerp(pet.look.y, pet.lookT.y, lk);

    const sqAcc = -pet.sq * 220 - pet.sqv * 10;
    pet.sqv += sqAcc * dt;
    pet.sq = clamp(pet.sq + pet.sqv * dt, -0.5, 0.5);
  }

""")

# ---------------------------------------------------------------- doIdle
replace_range("  function doIdle() {", "  function update(dt) {", """  function doIdle() {
    if (!state.hatched) {
      if (Math.random() < 0.6) say(pick(LINES.egg));
      egg.wobble = 0.5;
      return;
    }
    if (state.asleep || pet.held || pet.carried || pet.thrown) return;
    if (pet.working) { if (Math.random() < 0.35) say(pick(LINES.working), 2400); return; }
    const r = Math.random();
    if (state.full < 30 && r < 0.5) { say(pick(LINES.hungry)); comeDown(); return; }
    if (state.energy < 25 && r < 0.5) { say(pick(LINES.sleepy)); pet.yawn = 1.2; audio.yawn(); comeDown(); return; }
    if (state.joy < 35 && r < 0.4) { say(pick(LINES.bored)); pet.tapT = 1.6; return; }
    const hour = new Date().getHours();
    if (gitInfo.dirty >= 10 && r < 0.3) { say(`${gitInfo.dirty} files uncommitted…`, 3000); pet.glance = 1; return; }
    if (gitInfo.minutesSinceCommit > 24 * 60 && hour >= 9 && hour < 20 && r < 0.25) { say(pick(['no commits today?', 'the repo misses you', 'git log is lonely']), 3000); return; }
    if (pet.mode === 'fly') {
      if (r < 0.5) { pet.wander.x = rand(-1, 1); pet.wander.y = rand(-0.3, 0.7); }
      else if (r < 0.7) say(pick(['nice view', 'scanning…', 'I can see your dock from here', 'hovering is cheap']), 2400);
      return;
    }
    if (r < 0.14) { pet.facing = -pet.facing; pet.turnT = 0.5; pet.wander.x = pet.facing * 0.6; pet.wander.y = 0; }
    else if (r < 0.26) { pet.stretchT = 1.6; if (Math.random() < 0.4) say(pick(['*stretch*', 'servos ok', 'recalibrating']), 1500); }
    else if (r < 0.4) {
      if (takeOff()) { if (Math.random() < 0.6) say(pick(['brb, hovering', 'let me see from up here', 'going up', 'thrusters on']), 2000); }
      else { pet.wander.x = rand(-1, 1); pet.wander.y = rand(-0.6, 0.4); }
    }
    else if (r < 0.54) { pet.wander.x = rand(-1, 1); pet.wander.y = rand(-0.6, 0.4); }
    else if (r < 0.7) { say(pick(sky.night > 0.6 ? LINES.night : LINES.happy)); }
    else if (r < 0.8 && state.joy < 50) { pet.tapT = 1.4; }
    else if (!reduceMotion) {
      if (DESKTOP) native({ type: 'walk', dir: Math.random() < 0.5 ? -1 : 1 });
      else pet.ax = clamp(W / 2 + rand(-W * 0.3, W * 0.3), petR(), W - petR());
    }
  }

""")

# ---------------------------------------------------------------- drawPet
replace_range("  function drawPet() {", "  function drawSnack() {", """  function drawPet() {
    const st = stageOf(state);
    const r = petR();
    const t = pet.t;
    const asleep = state.asleep;
    const mood = moodOf(state);
    const sleepy = !asleep && state.energy < 25;
    const hue = st === 3 ? 250 + 60 * Math.sin(t * 0.5) : 250;
    const flying = pet.mode === 'fly';
    const carried = !!(pet.carried || pet.held);
    const lift = flying ? (DESKTOP ? 160 : groundY - pet.y) : Math.max(0, groundY - pet.y);

    drawShadow(pet.x, r, lift);

    ctx.save();
    ctx.translate(pet.x + (pet.shake > 0 ? Math.sin(t * 70) * r * 0.08 : 0), pet.y + (flying ? Math.sin(t * 2.4) * r * 0.06 : 0));
    let lean = 0;
    if (pet.thrown) lean = pet.spin;
    else if (flying) lean = pet.facing * 0.07 + Math.sin(t * 1.7) * 0.03;
    else if (pet.walking) lean = pet.facing * 0.04;
    ctx.rotate(lean);
    ctx.scale((1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6), (1 + pet.sq) * (1 + pet.stretch));

    const outline = `hsl(${hue}, 22%, 52%)`;
    const shell = ctx.createLinearGradient(0, -3.2 * r, 0, 0);
    shell.addColorStop(0, `hsl(${hue}, 35%, 95%)`);
    shell.addColorStop(1, `hsl(${hue}, 28%, 80%)`);
    const lw = Math.max(1.5, r * 0.06);
    ctx.lineWidth = lw;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    const strideA = pet.walking ? Math.sin(pet.stride) : 0;
    const breathe = asleep ? Math.sin(t * 1.2) * 0.02 : Math.sin(t * 2.2) * 0.012;
    const kneeDrop = pet.knee * r * 0.22 + (asleep ? r * 0.1 : 0);
    const stretchUp = pet.stretchT > 0 ? Math.sin(Math.PI * clamp(pet.stretchT / 1.6, 0, 1)) : 0;

    if (pet.thrust > 0.05 && !asleep) {
      const f = pet.thrust * (0.8 + 0.2 * Math.sin(t * 40));
      ctx.save();
      ctx.globalAlpha = 0.9;
      ctx.fillStyle = 'hsl(30, 100%, 60%)';
      ctx.beginPath(); ctx.ellipse(0, -r * 0.2 + kneeDrop, r * 0.22 * f, r * 0.5 * f, 0, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'hsl(50, 100%, 75%)';
      ctx.beginPath(); ctx.ellipse(0, -r * 0.3 + kneeDrop, r * 0.12 * f, r * 0.3 * f, 0, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }

    for (const sgn of [-1, 1]) {
      const phase = strideA * sgn;
      let footX = sgn * r * 0.42 + (pet.walking ? pet.facing * phase * r * 0.22 : 0);
      let footY = 0;
      if (pet.walking) footY -= Math.max(0, phase) * r * 0.16;
      if (pet.stomp > 0 && sgn === pet.facing) footY -= Math.sin(Math.PI * clamp(pet.stomp / 0.35, 0, 1)) * r * 0.4;
      if (pet.tapT > 0 && sgn === 1) footY -= Math.max(0, Math.sin(t * 16)) * r * 0.1;
      if (flying) { footY -= r * 0.3; footX = sgn * r * 0.3; }
      if (carried || pet.thrown) footY += r * 0.12 + Math.sin(t * 5 + sgn) * r * 0.08;
      const hipX = sgn * r * 0.33, hipY = -r * 0.5 + kneeDrop;
      ctx.strokeStyle = outline; ctx.lineWidth = r * 0.17;
      ctx.beginPath(); ctx.moveTo(hipX, hipY); ctx.lineTo(footX, footY - r * 0.1); ctx.stroke();
      ctx.strokeStyle = `hsl(${hue}, 25%, 66%)`; ctx.lineWidth = r * 0.09;
      ctx.beginPath(); ctx.moveTo(hipX, hipY); ctx.lineTo(footX, footY - r * 0.1); ctx.stroke();
      ctx.fillStyle = `hsl(${hue}, 25%, 45%)`;
      roundRect(footX - r * 0.3, footY - r * 0.2, r * 0.6, r * 0.2, r * 0.08);
      ctx.fill();
    }

    ctx.translate(0, kneeDrop);

    for (const sgn of [-1, 1]) {
      const sx = sgn * r * 0.78, sy = -r * 1.25;
      let theta = 0.35 + breathe * 3;
      if (carried) theta = 2.9;
      else if (pet.thrown) theta = 1.6 + Math.sin(t * 9 + sgn) * 0.6;
      else if (pet.wave > 0) theta = 2.5 + Math.sin(t * 14) * 0.5 * (sgn === 1 ? 1 : 0.3);
      else if (stretchUp > 0) theta = 0.35 + stretchUp * 2.5;
      else if (pet.happy > 0) theta = 2.2 + Math.sin(t * 12) * 0.35;
      else if (pet.screenTint === 'error' && pet.screenT > 0) theta = 0.9 + Math.sin(t * 20) * 0.2;
      else if (flying) theta = 0.9 + Math.sin(t * 2 + sgn) * 0.1;
      else if (asleep) theta = 0.12;
      else if (pet.walking) theta = 0.35 + strideA * sgn * 0.45;
      const ex = sx + sgn * Math.sin(theta) * r * 0.55, ey = sy + Math.cos(theta) * r * 0.55;
      ctx.strokeStyle = outline; ctx.lineWidth = r * 0.2;
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey); ctx.stroke();
      ctx.strokeStyle = `hsl(${hue}, 30%, 88%)`; ctx.lineWidth = r * 0.11;
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey); ctx.stroke();
      ctx.fillStyle = `hsl(${hue}, 30%, 90%)`; ctx.strokeStyle = outline; ctx.lineWidth = lw;
      ctx.beginPath(); ctx.arc(ex, ey, r * 0.16, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    }

    ctx.fillStyle = shell; ctx.strokeStyle = outline; ctx.lineWidth = lw;
    roundRect(-r * 0.75, -r * 1.55, r * 1.5, r * 1.08, r * 0.28); ctx.fill(); ctx.stroke();
    const leds = st >= 2 ? [state.full, state.energy, state.joy] : [state.energy];
    leds.forEach((v, i) => {
      const cx = (i - (leds.length - 1) / 2) * r * 0.3;
      const on = v > 25;
      ctx.fillStyle = on ? (v > 55 ? 'hsl(150, 70%, 55%)' : 'hsl(40, 90%, 58%)') : 'hsl(0, 60%, 55%)';
      ctx.globalAlpha = on ? 0.9 : 0.5 + 0.4 * Math.abs(Math.sin(t * 5));
      ctx.beginPath(); ctx.arc(cx, -r * 0.95, r * 0.07, 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = 1;
    });
    ctx.fillStyle = `hsl(${hue}, 25%, 60%)`;
    ctx.fillRect(-r * 0.18, -r * 1.72, r * 0.36, r * 0.2);

    const hy = -r * 2.22 + breathe * r * 2 - stretchUp * r * 0.12 + (asleep ? r * 0.08 : 0);
    ctx.save();
    ctx.translate(pet.facing * r * 0.05, hy);
    ctx.rotate(pet.tilt > 0 ? Math.sin(pet.tilt * 9) * 0.16 * pet.tilt : (asleep ? 0.06 : 0));
    if (st >= 2) {
      ctx.fillStyle = `hsl(${hue}, 28%, 70%)`; ctx.strokeStyle = outline;
      for (const sgn of [-1, 1]) { roundRect(sgn * r * 1.0 - r * 0.1, -r * 0.22, r * 0.2, r * 0.44, r * 0.06); ctx.fill(); ctx.stroke(); }
    }
    ctx.fillStyle = shell; ctx.strokeStyle = outline;
    roundRect(-r * 1.0, -r * 0.68, r * 2.0, r * 1.36, r * 0.36); ctx.fill(); ctx.stroke();

    const tint = pet.screenTint;
    let tipColor = 'hsl(170, 90%, 62%)';
    if (tint === 'error') tipColor = 'hsl(0, 90%, 60%)';
    else if (tint === 'ok') tipColor = 'hsl(150, 80%, 55%)';
    else if (tint === 'deploy') tipColor = `hsl(40, 95%, ${55 + 15 * Math.sin(t * 8)}%)`;
    else if (pet.wave > 0) tipColor = `hsl(200, 95%, ${55 + 20 * Math.abs(Math.sin(t * 12))}%)`;
    else if (pet.working) tipColor = `hsl(25, 95%, ${52 + 14 * Math.sin(t * 5)}%)`;
    else if (flying) tipColor = `hsl(30, 100%, ${58 + 12 * Math.sin(t * 20)}%)`;
    else if (state.full < 30) tipColor = 'hsl(40, 95%, 60%)';
    else if (asleep) tipColor = `hsl(${hue}, 20%, 55%)`;
    const antennas = st === 3 ? [-0.35, 0.35] : [0];
    for (const ax of antennas) {
      ctx.strokeStyle = outline; ctx.lineWidth = lw;
      ctx.beginPath(); ctx.moveTo(ax * r, -r * 0.68); ctx.lineTo(ax * r * 1.3, -r * 1.05); ctx.stroke();
      ctx.save();
      ctx.shadowColor = tipColor; ctx.shadowBlur = r * 0.35; ctx.fillStyle = tipColor;
      ctx.beginPath(); ctx.arc(ax * r * 1.3, -r * 1.12, r * 0.12, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
    if (st === 3) {
      ctx.strokeStyle = `hsla(${hue + 120}, 80%, 65%, ${0.5 + 0.3 * Math.sin(t * 3)})`; ctx.lineWidth = lw;
      ctx.beginPath(); ctx.ellipse(0, -r * 1.4, r * 0.7, r * 0.18, 0, 0, Math.PI * 2); ctx.stroke();
    }

    const sw = r * 1.62, sh = r * 1.0;
    let screenBg = '#1d2140';
    if (tint === 'error') screenBg = `hsl(0, 60%, ${18 + 12 * Math.abs(Math.sin(t * 10))}%)`;
    else if (tint === 'ok') screenBg = 'hsl(150, 45%, 16%)';
    else if (tint === 'deploy') screenBg = 'hsl(230, 45%, 16%)';
    ctx.fillStyle = screenBg; ctx.strokeStyle = outline; ctx.lineWidth = lw;
    roundRect(-sw / 2, -sh / 2, sw, sh, r * 0.22); ctx.fill(); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.05)';
    roundRect(-sw / 2, -sh / 2, sw, sh * 0.45, r * 0.22); ctx.fill();

    const glow = tint === 'error' ? 'hsl(0, 90%, 65%)' : tint === 'ok' ? 'hsl(150, 85%, 60%)' : tint === 'deploy' ? 'hsl(40, 95%, 65%)' : (asleep ? 'hsl(170, 40%, 45%)' : 'hsl(170, 90%, 68%)');
    ctx.save();
    ctx.translate(pet.facing * r * 0.07, 0);
    ctx.shadowColor = glow; ctx.shadowBlur = r * 0.25;
    ctx.fillStyle = glow; ctx.strokeStyle = glow;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    if (pet.screenText) {
      ctx.font = `700 ${Math.round(r * 0.5)}px ui-monospace, Menlo, monospace`;
      ctx.fillText(pet.screenText, 0, pet.deploying ? -r * 0.1 : 0);
    } else {
      drawFace(0, r, { asleep, sleepy, mood });
    }
    if (pet.working && !asleep) {
      const cx = sw / 2 - r * 0.17, cy = -sh / 2 + r * 0.17;
      ctx.lineWidth = Math.max(1, r * 0.04);
      ctx.beginPath(); ctx.arc(cx, cy, r * 0.08, t * 6, t * 6 + 4.2); ctx.stroke();
    }
    if (pet.deploying) {
      const bw = sw * 0.72, bh = r * 0.13, by = sh / 2 - r * 0.24;
      ctx.shadowBlur = 0; ctx.fillStyle = 'rgba(255,255,255,0.15)';
      roundRect(-bw / 2, by - bh / 2, bw, bh, bh / 2); ctx.fill();
      ctx.fillStyle = glow; ctx.shadowBlur = r * 0.2;
      roundRect(-bw / 2, by - bh / 2, Math.max(bh, bw * pet.deployProgress), bh, bh / 2); ctx.fill();
    }
    ctx.restore();
    ctx.restore();
    ctx.restore();
  }

""")

# Bubble sits above a taller robot now.
patch("      const top = state.hatched ? pet.y - r * 2 * (1 + pet.sq) - 14 : groundY - r * 2.2 - 12;",
      "      const top = state.hatched ? pet.y - r * 3.05 - (pet.mode === 'fly' ? 8 : 0) - 10 : groundY - r * 2.2 - 12;")

SRC.write_text(s, encoding="utf-8")
print("patched", SRC)
