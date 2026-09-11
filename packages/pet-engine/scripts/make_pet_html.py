#!/usr/bin/env python3
"""Derive Resources/pet.html (desktop mode) from the shared web page source.

The web page is the single source of truth for the creature. This script wraps it
in a full HTML document and applies the desktop-only patches: transparent
background, hidden HUD, native bridge (window.webkit.messageHandlers.pet),
window-level drag handled by the Swift host, and native name / reset prompts.
Every patch asserts its anchor so a drifted source fails loudly instead of
silently producing a broken pet.
"""
from __future__ import annotations

import sys
import base64
from pathlib import Path


def patch(src: str, old: str, new: str) -> str:
    if src.count(old) != 1:
        raise SystemExit(f"anchor not found exactly once:\n{old[:120]}")
    return src.replace(old, new)


def build(source: Path, target: Path) -> None:
    s = source.read_text(encoding="utf-8")
    asset_root = Path(__file__).resolve().parent.parent.parent.parent / "apps/macos/web/assets"
    for filename in ("shenron.png", "shenron-head.png", "shenron-body.png", "shenron-limb.png"):
        asset = asset_root / filename
        sprite = "data:image/png;base64," + base64.b64encode(asset.read_bytes()).decode("ascii")
        s = s.replace(f"assets/{filename}", sprite)

    # --- state: prefer the host-injected snapshot, mirror saves to the host
    s = patch(
        s,
        "      const raw = localStorage.getItem(STORE_KEY);\n      if (!raw) return null;",
        "      const injected = typeof window.__petSavedState === 'string' ? window.__petSavedState : null;\n"
        "      const raw = injected || localStorage.getItem(STORE_KEY);\n      if (!raw) return null;",
    )
    s = patch(
        s,
        "    try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (_) { /* storage unavailable */ }\n  }",
        "    const json = JSON.stringify(state);\n"
        "    try { localStorage.setItem(STORE_KEY, json); } catch (_) { /* storage unavailable */ }\n"
        "    native({ type: 'save', json });\n  }",
    )

    # --- geometry: the window is a tight box around the creature
    s = patch(
        s,
        "    scale = clamp(Math.min(W, H) / 520, 0.7, 1.3);\n    if (W <= 0 || H <= 0) return;",
        "    scale = clamp(Math.min(W, H) / 520, 0.7, 1.3);\n"
        "    if (DESKTOP) {\n"
        "      // The creature is sized by its window, so the size setting only has to\n"
        "      // resize the window and everything here follows.\n"
        "      const grow = state.species === 'dragon' ? shenron.size : (state.species === 'spiderman' ? 1.0 : W / 300);\n"
        "      // Floaters hang lower than the middle so a speech bubble still has headroom\n"
        "      // above them. At 0.54 the bubble hit the top of the window and was clamped\n"
        "      // back down onto the creature's head.\n"
        "      groundY = Math.round(floats() ? H * 0.66 : H - 34 * grow);\n"
        "      scale = 0.8 * grow;\n"
        "    }\n"
        "    hitDpr = dpr;\n"
        "    if (W <= 0 || H <= 0) return;",
    )

    # --- creature fields used by the host
    s = patch(
        s,
        "    screenText: '', screenTint: '', screenT: 0, shake: 0, deploying: false, deployProgress: 0,\n  };",
        "    screenText: '', screenTint: '', screenT: 0, shake: 0, deploying: false, deployProgress: 0,\n"
        "    carried: false, dragSpeed: 0, walkDir: 0,\n  };",
    )

    # --- stretch while the host drags the window
    s = patch(
        s,
        "      pet.stretch = lerp(pet.stretch, 0, Math.min(1, dt * 10));",
        "      pet.stretch = lerp(pet.stretch, pet.carried ? clamp(pet.dragSpeed / 3500, 0, 0.3) : 0, Math.min(1, dt * 10));",
    )

    # --- look priority: carried, walking, then the usual chain
    s = patch(
        s,
        "      if (!state.asleep) {\n        if (snack.active) {",
        "      if (!state.asleep) {\n"
        "        if (pet.carried) {\n          pet.lookT.x = 0; pet.lookT.y = 0.7;\n        } else if (pet.walkDir) {\n"
        "          pet.lookT.x = pet.walkDir * 0.8; pet.lookT.y = 0.1;\n        } else if (snack.active) {",
    )

    # --- transparent stage, no sleep dimming over the desktop
    s = patch(
        s,
        "  function draw() {\n    drawBackground();\n",
        "  function draw() {\n    if (DESKTOP) ctx.clearRect(0, 0, W, H); else drawBackground();\n",
    )
    s = patch(
        s,
        "    if (state.asleep) {\n      ctx.fillStyle = 'rgba(10,14,40,0.42)';",
        "    if (state.asleep && !DESKTOP) {\n      ctx.fillStyle = 'rgba(10,14,40,0.42)';",
    )

    # --- click fallback must not double-fire after a handled pointer tap
    s = patch(
        s,
        "  let lastPointerDown = -1e9;\n",
        "  let lastPointerDown = -1e9;\n  let suppressClickUntil = 0;\n",
    )
    s = patch(
        s,
        "    if (performance.now() - lastPointerDown < 400) return;\n    audio.ensure();\n    tapAt(e.offsetX, e.offsetY);",
        "    if (performance.now() - lastPointerDown < 400 || performance.now() < suppressClickUntil) return;\n"
        "    audio.ensure();\n    tapAt(e.offsetX, e.offsetY);",
    )
    s = patch(
        s,
        "  const endPointer = () => {\n"
        "    if (state.species === 'spiderman' && state.asleep && typeof spidermanState !== 'undefined' && spidermanState.sleepDragging) {\n"
        "      spidermanState.sleepDragging = false;\n"
        "      spidermanState.sleepBungee = true;\n"
        "      spidermanState.bungeeVx = (typeof pointer !== 'undefined' && pointer.vx) ? pointer.vx : 0;\n"
        "      spidermanState.bungeeVy = (typeof pointer !== 'undefined' && pointer.vy) ? pointer.vy : 0;\n"
        "      if (audio && audio.spideyZip) audio.spideyZip();\n"
        "      pet.pressing = false;\n"
        "      return;\n"
        "    }\n"
        "    if (pet.held) release();\n"
        "    else if (pet.pressing) { if (state.asleep) wake(); else petTap(); }\n"
        "    pet.pressing = false;\n"
        "  };",
        "  const endPointer = () => {\n"
        "    suppressClickUntil = performance.now() + 400;\n"
        "    if (state.species === 'spiderman' && state.asleep && typeof spidermanState !== 'undefined' && spidermanState.sleepDragging) {\n"
        "      spidermanState.sleepDragging = false;\n"
        "      spidermanState.sleepBungee = true;\n"
        "      spidermanState.bungeeVx = (typeof pointer !== 'undefined' && pointer.vx) ? pointer.vx : 0;\n"
        "      spidermanState.bungeeVy = (typeof pointer !== 'undefined' && pointer.vy) ? pointer.vy : 0;\n"
        "      if (audio && audio.spideyZip) audio.spideyZip();\n"
        "      pet.pressing = false;\n"
        "      return;\n"
        "    }\n"
        "    if (pet.held) release();\n"
        "    else if (pet.pressing && !pet.carried) { if (state.asleep) wake(); else petTap(); }\n"
        "    pet.pressing = false;\n"
        "  };",
    )

    # --- native prompts instead of <dialog>
    s = patch(
        s,
        "  function openNameDialog(first) {\n    if (nameDialog.open) return;",
        "  function openNameDialog(first) {\n"
        "    if (DESKTOP) { native({ type: 'askName', first: !!first, suggestion: state.name || pick(NAMES) }); return; }\n"
        "    if (nameDialog.open) return;",
    )
    s = patch(
        s,
        "  resetDialog.addEventListener('close', () => {\n    if (resetDialog.returnValue !== 'yes') return;\n",
        "  function doReset() {\n",
    )
    s = patch(
        s,
        "    say('a new box arrives', 2400);\n  });",
        "    say('a new box arrives', 2400);\n    pushState(true);\n  }\n"
        "  resetDialog.addEventListener('close', () => { if (resetDialog.returnValue === 'yes') doReset(); });",
    )

    # --- click-through: the window is a big transparent rectangle, and everywhere the
    # creature is not drawn has to let the click reach whatever is behind it. On the desktop
    # the canvas is cleared every frame and only the creature is painted on it, so its alpha
    # channel is an exact mask of the pet. Probe it and tell the host what the cursor is over.
    s = patch(
        s,
        "  const pointer = { x: 0, y: 0, over: false, lastT: -10, vx: 0, vy: 0, pt: 0 };\n",
        "  const pointer = { x: 0, y: 0, over: false, lastT: -10, vx: 0, vy: 0, pt: 0 };\n"
        "  let hitDpr = 1, hoverOn = null, hoverSentAt = 0, hoverTick = 0;\n"
        "  function reportHover() {\n"
        "    if (++hoverTick % 2) return;                       // thirty probes a second\n"
        "    let on = pet.held || pet.pressing;                 // never let go of a fast drag\n"
        "    if (!on) {\n"
        "      const pad = Math.max(1, Math.round(4 * hitDpr)); // a few forgiving pixels around the point\n"
        "      const x = Math.round(pointer.x * hitDpr), y = Math.round(pointer.y * hitDpr);\n"
        "      const x0 = Math.max(0, x - pad), y0 = Math.max(0, y - pad);\n"
        "      const x1 = Math.min(canvas.width, x + pad + 1), y1 = Math.min(canvas.height, y + pad + 1);\n"
        "      if (x1 > x0 && y1 > y0) {\n"
        "        const d = ctx.getImageData(x0, y0, x1 - x0, y1 - y0).data;\n"
        "        for (let i = 3; i < d.length; i += 4) { if (d[i] > 8) { on = true; break; } }\n"
        "      }\n"
        "    }\n"
        "    // Report changes at once, and repeat regardless twice a second: the host treats\n"
        "    // silence as a fault and stops swallowing clicks rather than trapping the cursor.\n"
        "    const now = performance.now();\n"
        "    if (on === hoverOn && now - hoverSentAt < 500) return;\n"
        "    hoverOn = on; hoverSentAt = now;\n"
        "    native({ type: 'hover', on });\n"
        "  }\n",
    )
    s = patch(
        s,
        "    update(dt);\n    draw();\n    requestAnimationFrame(frame);",
        "    update(dt);\n    draw();\n    if (DESKTOP) reportHover();\n    requestAnimationFrame(frame);",
    )

    # --- state snapshots for the menu bar
    s = patch(
        s,
        "  function displayName() { return state.name || 'Bitling'; }\n",
        "  function displayName() { return state.name || 'Bitling'; }\n"
        "  let lastPushed = '';\n"
        "  function pushState(force) {\n"
        "    if (!DESKTOP) return;\n"
        "    const snap = {\n"
        "      type: 'state', name: displayName(), stage: STAGES[stageOf(state)],\n"
        "      full: Math.round(state.full), energy: Math.round(state.energy), joy: Math.round(state.joy),\n"
        "      asleep: state.asleep, hatched: state.hatched, sound: state.sound, age: state.hatched ? ageText(state) : '',\n"
        "      commits: state.commits, pushes: state.pushes, bugs: state.bugs,\n"
        "      bugsToday: state.bugsDay === new Date().toISOString().slice(0, 10) ? state.bugsToday : 0,\n"
        "      working: pet.working, screen: pet.screenT > 0 ? pet.screenTint : '',\n"
        "      species: state.species, locomotion: species().kind,\n"
        "      shenronSettings: state.shenronSettings,\n"
        "      goku: getGokuSnapshot(),\n"
        "      thor: getThorSnapshot(),\n"
        "      attack: (species().attack && species().attack.style) || 'beam',\n"
        "    };\n"
        "    const key = JSON.stringify(snap);\n"
        "    if (!force && key === lastPushed) return;\n"
        "    lastPushed = key;\n"
        "    native(snap);\n"
        "  }\n",
    )
    s = patch(
        s,
        "    document.documentElement.dataset.sky = sky.night > 0.55 ? 'night' : 'day';\n  }",
        "    document.documentElement.dataset.sky = sky.night > 0.55 ? 'night' : 'day';\n    pushState(false);\n  }",
    )

    # --- host -> page API
    s = patch(
        s,
        "  // ---------------------------------------------------------------- boot\n",
        "  // ---------------------------------------------------------------- host bridge\n"
        "  window.petNative = {\n"
        "    setWindowRooftops(list) {\n      setSpideyRooftops(list);\n    },\n    setUserActive(active) {\n      setSpideyUserActive(active);\n    },\n    stageSize(value) {\n"
        "      const size = Number(value);\n"
        "      if (!Number.isFinite(size)) return;\n"
        "      shenron.size = clamp(size, 0.45, 2);\n"
        "      resize();\n"
        "      if (state.species === 'dragon') { clampShenron(); shenron.nextTurn = 0; }\n"
        "    },\n"
        "    stageDrag(dx, dy) {\n"
        "      if (state.species !== 'dragon' && state.species !== 'spiderman') return;\n"
        "      if (!Number.isFinite(dx) || !Number.isFinite(dy)) return;\n"
        "      if (state.species === 'dragon') {\n"
        "        pet.x += dx; pet.y += dy; clampShenron();\n"
        "        shenron.targetX = pet.x; shenron.targetY = pet.y; restAmbient();\n"
        "      } else if (state.species === 'spiderman') {\n"
        "        pet.x += dx; pet.y += dy;\n"
        "        if (state.asleep && typeof spidermanState !== 'undefined') {\n"
        "          spidermanState.sleepDragging = true;\n"
        "          spidermanState.sleepBungee = false;\n"
        "          spidermanState.bungeeVx = dx * 28;\n"
        "          spidermanState.bungeeVy = dy * 28;\n"
        "        }\n"
        "        if (typeof clampSpiderman === 'function') clampSpiderman();\n"
        "      }\n"
        "    },\n"
        "    shenronSetting(key, value) {\n"
        "      if (!Object.hasOwn(SHENRON_SETTING_RANGES, key)) return;\n"
        "      const number = Number(value);\n"
        "      if (!Number.isFinite(number)) return;\n"
        "      const range = SHENRON_SETTING_RANGES[key];\n"
        "      state.shenronSettings[key] = clamp(number, range[0], range[1]);\n"
        "      if (key === 'length') resetShenronSpine();\n"
        "      saveState(); pushState(true);\n"
        "    },\n"
        "    gokuSetting(key, value) {\n"
        "      if (!Object.hasOwn(GOKU_SETTING_RANGES, key)) return;\n"
        "      const number = Number(value);\n"
        "      if (!Number.isFinite(number)) return;\n"
        "      const range = GOKU_SETTING_RANGES[key];\n"
        "      state.gokuSettings[key] = clamp(number, range[0], range[1]);\n"
        "      saveState(); pushState(true);\n"
        "    },\n"
        "    gokuSimulate(commits) {\n"
        "      setGokuSimulatedCommits(commits);\n"
        "      pushState(true);\n"
        "    },\n"
        "    // Dev/test only: spawn a specific Goku enemy class instead of leaving it to\n"
        "    // the weighted random pick, so the whole pack can be exercised from the\n"
        "    // control room without waiting on real commits. No-op for every other species.\n"
        "    gokuSpawnEnemy(kind) {\n"
        "      if (state.species !== 'goku') return;\n"
        "      const valid = ['fighter', 'flying', 'fast', 'elite', 'boss'];\n"
        "      const id = valid.includes(kind) ? kind : 'fighter';\n"
        "      const targetX = pet.x > W / 2 ? rand(30, W * 0.35) : rand(W * 0.65, W - 30);\n"
        "      spawnBug(targetX, id === 'boss', undefined, id);\n"
        "      pushState(true);\n"
        "    },\n"
        "    // Dev/test only: jump straight to a form by index (0 Kid .. 5 Ultra Instinct)\n"
        "    // via the same simulated-commits override the commit-count slider already uses.\n"
        "    gokuForceForm(idx) {\n"
        "      const i = clamp(Math.round(Number(idx) || 0), 0, GOKU_CONFIG.forms.length - 1);\n"
        "      setGokuSimulatedCommits(GOKU_CONFIG.forms[i].minCommits);\n"
        "      pushState(true);\n"
        "    },\n"
        "    thorSetting(key, value) {\n"
        "      if (!Object.hasOwn(THOR_SETTING_RANGES, key)) return;\n"
        "      const number = Number(value);\n"
        "      if (!Number.isFinite(number)) return;\n"
        "      const range = THOR_SETTING_RANGES[key];\n"
        "      state.thorSettings[key] = clamp(number, range[0], range[1]);\n"
        "      saveState(); pushState(true);\n"
        "    },\n"
        "    thorSimulate(commits) {\n"
        "      setThorSimulatedCommits(commits);\n"
        "      pushState(true);\n"
        "    },\n"
        "    action(name) {\n"
        "      audio.ensure();\n"
        "      switch (name) {\n"
        "        case 'feed': feed(); break;\n"
        "        case 'play': play(); break;\n"
        "        case 'sleep': toggleSleep(); break;\n"
        "        case 'pat': if (!state.hatched) eggTap(); else if (state.asleep) wake(); else petTap(); break;\n"
        "        case 'sound': state.sound = !state.sound; if (state.sound) audio.pop(); saveState(); updateHud(); pushState(true); break;\n"
        "        default: break;\n"
        "      }\n"
        "    },\n"
        "    grab() {\n"
        "      if (!state.hatched) { egg.wobble = 1; return; }\n"
        "      pet.carried = true; pet.happy = 0; pet.surprise = 1e9; pet.dragSpeed = 0;\n"
        "      say(pick(LINES.held), 1800);\n"
        "      audio.squeak();\n"
        "    },\n"
        "    drag(vx, vy) {\n"
        "      const dx = Number(vx) || 0;\n"
        "      const dy = Number(vy) || 0;\n"
        "      pet.dragVx = dx; pet.dragVy = dy;\n"
        "      pet.dragSpeed = Math.hypot(dx, dy);\n"
        "      // Turn to face the way it is being carried, once the pull is clearly sideways.\n"
        "      if (Math.abs(dx) > 15) pet.facing = dx < 0 ? -1 : 1;\n"
        "    },\n"
        "    release() {\n"
        "      pet.carried = false; pet.pressing = false; pet.dragSpeed = 0;\n"
        "      restAmbient();\n"
        "      if (state.species === 'spiderman' && state.asleep && typeof spidermanState !== 'undefined') {\n"
        "        spidermanState.sleepDragging = false;\n"
        "        spidermanState.sleepBungee = true;\n"
        "        if (audio && audio.spideyZip) audio.spideyZip();\n"
        "      }\n"
        "      pet.dragVx = 0; pet.dragVy = 0;\n"
        "      pet.surprise = Math.min(pet.surprise, 0.3);\n"
        "      suppressClickUntil = performance.now() + 500;\n"
        "    },\n"
        "    land(impact) {\n"
        "      const imp = clamp(Number(impact) || 0, 0, 0.45);\n"
        "      if (!state.hatched) { egg.wobble = Math.max(egg.wobble, imp * 2); return; }\n"
        "      pet.grounded = true; pet.y = groundY;\n"
        "      land(imp * 1600);\n"
        "    },\n"
        "    flight(phase) { handleFlight(phase); },\n"
        "    walking(dir) { pet.walkDir = Math.sign(Number(dir) || 0); if (!pet.walkDir) restAmbient(); },\n"
        "    cursor(x, y) { pointer.x = Number(x) || 0; pointer.y = Number(y) || 0; pointer.over = true; pointer.lastT = pet.t; },\n"
        "    setName(name) {\n"
        "      const v = String(name || '').trim().slice(0, 16);\n"
        "      const wasUnnamed = !state.name;\n"
        "      state.name = v || state.name || pick(NAMES);\n"
        "      saveState(); updateHud(); pushState(true);\n"
        "      if (wasUnnamed) say(`I'm ${state.name}! pat me, drag me, feed me`, 3600);\n"
        "    },\n"
        "    reset() { doReset(); },\n"
        "    gitEvent(ev) { handleGitEvent(ev); pushState(true); },\n"
        "    flightVec(x, y) {\n"
        "      pet.flyVX = Number(x) || 0;\n"
        "      pet.flyVY = Number(y) || 0;\n"
        "      // Turn into the flight as well as into a drag: it should not fly backwards.\n"
        "      if (Math.abs(pet.flyVX) > 0.35) pet.facing = pet.flyVX < 0 ? -1 : 1;\n"
        "    },\n"
        "    setSpecies(id) {\n"
        "      if (!SPECIES[id] || state.species === id) return;\n"
        "      const previous = species();\n"
        "      state.species = id;\n"
        "      restAmbient();\n"
        "      pet.ax = pet.x; pet.fx = pet.x; pet.fy = pet.y;\n"
        "      pet.vx = 0; pet.vy = 0; pet.flyVX = 0; pet.flyVY = 0; pet.hoverUntil = 0;\n"
        "      if (!state.name || state.name === previous.name || state.name === 'Ember') state.name = species().name;\n"
        "      pet.grounded = !floats(); pet.mode = floats() ? 'fly' : 'ground';\n"
        "      pet.thrown = false; pet.chuteOpen = false; pet.chute = 0; pet.landing = false;\n"
        "      shenron.nextTurn = 0;\n"

        "      saveState();\n"
        "      resize();               // a walker stands on the floor, a floater hangs mid window\n"
        "      pet.ax = pet.x; pet.fx = pet.x; pet.fy = pet.y; pet.walkDir = 0; pet.walking = false;\n"
        "      native({ type: 'rest' });\n"
        "      bubble.hidden = true; bubbleUntil = 0;\n"
        "      say(line('hello'), 2600);\n"
        "      pushState(true);\n"
        "    },\n"
        "    gitStatus(info) { handleGitStatus(info); },\n"
        "    swarmMode(on) { hostSwarm = !!on; if (!hostSwarm) hostBugs = []; },\n"
        "    swarm(list) { hostBugs = Array.isArray(list) ? list : []; },\n"
        "    killed(boss) { countKill(true, !!boss); pet.happy = boss ? 2 : 0.8; },\n"
        "    // Read-only snapshot for diagnostics.\n"
        "    // Advance the simulation by a fixed number of steps and redraw. Used for\n"
        "    // deterministic verification and for capturing documentation screenshots.\n"
        "    advance(seconds) {\n"
        "      const steps = Math.min(900, Math.max(0, Math.round((Number(seconds) || 0) * 60)));\n"
        "      for (let i = 0; i < steps; i++) update(1 / 60);\n"
        "      draw();\n"
        "      if (DESKTOP) reportHover();\n"
        "    },\n"
        "    // Put the pet at an exact position. Verification helper only.\n"
        "    place(x) {\n"
        "      const v = Math.max(0, Math.min(W, Number(x) || 0));\n"
        "      pet.x = v; pet.ax = v; draw();\n"
        "    },\n"
        "    debug() {\n"
        "      return { mode: pet.mode, grounded: pet.grounded, thrown: pet.thrown, chuteOpen: pet.chuteOpen,\n"
        "        chute: Number(pet.chute.toFixed(3)), knee: Number(pet.knee.toFixed(3)), r: petR(), scale, W, H, groundY,\n"
        "        x: Math.round(pet.x), y: Math.round(pet.y), stage: stageOf(state),\n"
        "        facing: pet.facing, flyVX: pet.flyVX || 0, flyVY: pet.flyVY || 0,\n"
        "        species: state.species, asleep: state.asleep, bugs: activeBugCount(), swarm: swarmOn(),\n"
        "        zap: Number(pet.zap.toFixed(2)), charge: Number(pet.zapCharge.toFixed(2)),\n"
        "        cool: Number(pet.zapCool.toFixed(2)), aiming: !!pet.zapAim,\n"
        "        rocket: rocket.active ? { y: Math.round(rocket.y), fade: Number(rocket.fade.toFixed(2)) } : null };\n"
        "    },\n"
        "  };\n\n"
        "  // ---------------------------------------------------------------- boot\n",
    )
    s = patch(
        s,
        "  updateHud();\n  if (state.hatched) {\n",
        "  updateHud();\n  pushState(true);\n"
        "  native({ type: 'species', list: speciesOrder.map((id) => ({\n"
        "    id, name: SPECIES[id].name, blurb: SPECIES[id].blurb,\n"
        "    kind: SPECIES[id].kind, accent: SPECIES[id].accent,\n"
        "  })) });\n"
        "  native({ type: 'ready' });\n  if (state.hatched) {\n",
    )

    doc = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n"
        + s.split("<style>", 1)[0]
        + "</head>\n<body>\n<style>"
        + s.split("<style>", 1)[1]
        + "\n</body>\n</html>\n"
    )
    target.write_text(doc, encoding="utf-8")
    print(f"wrote {target} ({len(doc)} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: make_pet_html.py <web-source.html> <out pet.html>")
    build(Path(sys.argv[1]), Path(sys.argv[2]))
