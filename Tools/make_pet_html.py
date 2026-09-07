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
from pathlib import Path


def patch(src: str, old: str, new: str) -> str:
    if src.count(old) != 1:
        raise SystemExit(f"anchor not found exactly once:\n{old[:120]}")
    return src.replace(old, new)


def build(source: Path, target: Path) -> None:
    s = source.read_text(encoding="utf-8")

    # --- desktop flag + native bridge helper
    s = patch(
        s,
        "  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;\n",
        "  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;\n"
        "  const HOST = (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.pet) || null;\n"
        "  // ?desktop=1 previews the desktop layout in an ordinary browser (no host, bridge calls are dropped).\n"
        "  const DESKTOP = !!HOST || /[?&]desktop=1/.test(window.location.search) || window.__forceDesktop === true;\n"
        "  if (DESKTOP) document.documentElement.classList.add('desktop');\n"
        "  function native(msg) {\n"
        "    if (!HOST) return;\n"
        "    try { HOST.postMessage(msg); } catch (_) { /* host gone */ }\n"
        "  }\n",
    )

    # --- desktop CSS
    s = patch(
        s,
        "  @media (prefers-reduced-motion:reduce){ .bubble{animation:none} }\n",
        "  @media (prefers-reduced-motion:reduce){ .bubble{animation:none} }\n"
        "  html.desktop,html.desktop body,html.desktop #app{background:transparent}\n"
        "  html.desktop .hud,html.desktop .dock{display:none}\n"
        "  html.desktop #stage{cursor:default}\n"
        "  html.desktop .bubble{white-space:normal;max-width:calc(100vw - 16px);text-align:center;font-size:15px;padding:6px 11px;line-height:1.25}\n",
    )

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
        "    if (DESKTOP) { groundY = Math.round(H - 36); scale = 0.85; }\n"
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
        "      pet.stretch = lerp(pet.stretch, 0, Math.min(1, dt * 10));\n      if (!pet.grounded) {",
        "      pet.stretch = lerp(pet.stretch, pet.carried ? clamp(pet.dragSpeed / 3500, 0, 0.3) : 0, Math.min(1, dt * 10));\n"
        "      if (!pet.grounded) {",
    )

    # --- look priority: carried, walking, then the usual chain
    s = patch(
        s,
        "      if (!state.asleep) {\n        if (snack.active) {",
        "      if (!state.asleep) {\n"
        "        if (pet.carried) {\n          pet.lookT.x = 0; pet.lookT.y = 0.7;\n        } else if (pet.walkDir) {\n"
        "          pet.lookT.x = pet.walkDir * 0.8; pet.lookT.y = 0.1;\n        } else if (snack.active) {",
    )

    # --- idle wander walks the window instead of the anchor
    s = patch(
        s,
        "    else if (r < 0.82) { pet.ax = clamp(W / 2 + rand(-W * 0.25, W * 0.25), petR(), W - petR()); }",
        "    else if (r < 0.82) {\n"
        "      if (DESKTOP) native({ type: 'walk', dir: Math.random() < 0.5 ? -1 : 1 });\n"
        "      else pet.ax = clamp(W / 2 + rand(-W * 0.25, W * 0.25), petR(), W - petR());\n"
        "    }",
    )

    # --- walking bob
    s = patch(
        s,
        "    const sqy = (1 + pet.sq) * (1 + pet.stretch);\n    const sqx = (1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6);\n\n    drawShadow",
        "    const bob = pet.walkDir && pet.grounded ? 0.04 * Math.sin(t * 16) : 0;\n"
        "    const sqy = (1 + pet.sq + bob) * (1 + pet.stretch);\n"
        "    const sqx = (1 - pet.sq * 0.85 - bob * 0.8) * (1 - pet.stretch * 0.6);\n\n    drawShadow",
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
        "  const endPointer = () => {\n    if (pet.held) release();\n    else if (pet.pressing) { if (state.asleep) wake(); else petTap(); }\n    pet.pressing = false;\n  };",
        "  const endPointer = () => {\n"
        "    suppressClickUntil = performance.now() + 400;\n"
        "    if (pet.held) release();\n"
        "    else if (pet.pressing && !pet.carried) { if (state.asleep) wake(); else petTap(); }\n"
        "    pet.pressing = false;\n  };",
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
        "    drag(vx, vy) { pet.dragSpeed = Math.hypot(Number(vx) || 0, Number(vy) || 0); },\n"
        "    release() {\n"
        "      pet.carried = false; pet.pressing = false; pet.dragSpeed = 0;\n"
        "      pet.surprise = Math.min(pet.surprise, 0.3);\n"
        "      suppressClickUntil = performance.now() + 500;\n"
        "    },\n"
        "    land(impact) {\n"
        "      const imp = clamp(Number(impact) || 0, 0, 0.45);\n"
        "      if (!state.hatched) { egg.wobble = Math.max(egg.wobble, imp * 2); return; }\n"
        "      pet.sq = -imp; pet.sqv = 0;\n"
        "      if (imp > 0.12) {\n"
        "        spawn('dust', pet.x, groundY - 4, 6, { spread: petR() * 0.8, vx: 70, vy: -25, g: -10, size: 9, dur: 0.7 });\n"
        "        audio.thud();\n"
        "      }\n"
        "    },\n"
        "    walking(dir) { pet.walkDir = Math.sign(Number(dir) || 0); },\n"
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
        "    gitStatus(info) { handleGitStatus(info); },\n"
        "  };\n\n"
        "  // ---------------------------------------------------------------- boot\n",
    )
    s = patch(
        s,
        "  updateHud();\n  if (state.hatched) {\n    setTimeout(() => say(awayMs",
        "  updateHud();\n  pushState(true);\n  native({ type: 'ready' });\n  if (state.hatched) {\n    setTimeout(() => say(awayMs",
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
