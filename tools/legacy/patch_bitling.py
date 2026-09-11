#!/usr/bin/env python3
"""One-off migration: jelly blob + egg -> Bitling robot + box, test/deploy reactions.

Applied to web/bitling.html. Idempotent-guarded, asserts every anchor.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "web" / "bitling.html"
s = SRC.read_text(encoding="utf-8")
if "function drawFace" in s:
    raise SystemExit("already applied")


def patch(old: str, new: str, count: int = 1) -> None:
    global s
    if s.count(old) != count:
        raise SystemExit(f"anchor found {s.count(old)}x, expected {count}:\n{old[:160]}")
    s = s.replace(old, new)


def replace_range(start_marker: str, end_marker: str, new: str) -> None:
    global s
    i = s.index(start_marker)
    j = s.index(end_marker, i)
    s = s[:i] + new + s[j:]


# ---------------------------------------------------------------- names + copy
patch("  const STAGES = ['Egg', 'Hatchling', 'Bitling', 'Luminous Bitling'];",
      "  const STAGES = ['Boxed', 'Bootling', 'Bitling', 'Overclocked Bitling'];")
patch("    egg: ['tap me!', 'something is inside...', '*wobble*', 'knock knock'],",
      "    egg: ['unbox me!', 'something is beeping in here', '*rattle*', 'knock knock', 'this side up'],\n"
      "    testFail: ['tests are red…', 'who broke the build?', 'ERR ERR ERR', 'it worked on my machine'],\n"
      "    testPass: ['tests green!', 'all green. ship it.', 'zero failures'],\n"
      "    deployFail: ['deploy failed. rollback?', 'prod said no', 'abort abort'],")
patch("    else say(pick(['*crack*', 'something moved!', 'almost...']));",
      "    else say(pick(['*rattle*', 'tape is tearing', 'almost open...']));")
patch("    say('hello!!', 3000);", "    say('hello, world!', 3000);")
patch("      nameLabel.textContent = 'A mysterious egg';\n      subLabel.textContent = state.taps === 0 ? 'Tap it and see' : 'Keep tapping';",
      "      nameLabel.textContent = 'A mysterious box';\n      subLabel.textContent = state.taps === 0 ? 'Tap to unbox' : 'Keep tapping';")
patch('        <span id="nameLabel">A mysterious egg</span>\n        <small id="subLabel">Tap it and see</small>',
      '        <span id="nameLabel">A mysterious box</span>\n        <small id="subLabel">Tap to unbox</small>')
patch('      <h2 id="nameTitle">It hatched!</h2>', '      <h2 id="nameTitle">It booted up!</h2>')
patch("    nameTitle.textContent = first ? 'It hatched!' : 'Rename';", "    nameTitle.textContent = first ? 'It booted up!' : 'Rename';")
patch("    $('#aboutTitle').textContent = state.hatched ? `About ${displayName()}` : 'About the egg';",
      "    $('#aboutTitle').textContent = state.hatched ? `About ${displayName()}` : 'About the box';")
patch("        : 'The egg will be replaced with a fresh one.';", "        : 'The box will be replaced with a fresh one.';")
patch("    say('a new egg appears', 2400);", "    say('a new box arrives', 2400);")
patch("      if (Math.random() < 0.6) say(pick(LINES.egg));\n      egg.wobble = 0.7;",
      "      if (Math.random() < 0.6) say(pick(LINES.egg));\n      egg.wobble = 0.5;")
patch("<p>Grows to the next stage with age and care points. Needs drift slowly while you are away, but a Bitling never dies. It only sulks. The desktop app also feeds it your git commits.</p>",
      "<p>Grows to the next stage with age and care points. Needs drift slowly while you are away, but a Bitling never dies. It only sulks. The desktop app also feeds it your commits and reacts to test runs and deploys.</p>")

# ---------------------------------------------------------------- snacks: battery, chip, cookie
patch("    snack.kind = pick(['berry', 'cookie', 'leaf']);", "    snack.kind = pick(['battery', 'chip', 'cookie']);")
patch("hue: snack.kind === 'leaf' ? 120 : snack.kind === 'berry' ? 350 : 30 });",
      "hue: snack.kind === 'battery' ? 130 : snack.kind === 'chip' ? 220 : 30 });")
patch('''      <svg viewBox="0 0 24 24"><circle cx="12" cy="14" r="7"/><path d="M12 7c0-3 2-4 5-4-1 3-2 4-5 4z"/></svg><span>Feed</span>''',
      '''      <svg viewBox="0 0 24 24"><rect x="3" y="7" width="16" height="10" rx="2"/><path d="M19 10h2v4h-2M6 10v4M9 10v4M12 10v4"/></svg><span>Feed</span>''')

# ---------------------------------------------------------------- audio
patch("    whoosh() { this.tone(160, 900, 0.5, 'sawtooth', 0.035); },",
      "    whoosh() { this.tone(160, 900, 0.5, 'sawtooth', 0.035); },\n"
      "    error() { this.tone(320, 120, 0.3, 'square', 0.05); setTimeout(() => this.tone(260, 100, 0.35, 'square', 0.05), 220); },\n"
      "    ok() { this.tone(660, 660, 0.12, 'triangle', 0.07); setTimeout(() => this.tone(990, 990, 0.2, 'triangle', 0.07), 130); },")

# ---------------------------------------------------------------- state fields
patch("    grounded: true, chew: 0, happy: 0, surprise: 0, yawn: 0, dizzy: 0, glance: 0, t: 0, idleAt: 2.5,\n  };",
      "    grounded: true, chew: 0, happy: 0, surprise: 0, yawn: 0, dizzy: 0, glance: 0, t: 0, idleAt: 2.5,\n"
      "    screenText: '', screenTint: '', screenT: 0, shake: 0, deploying: false, deployProgress: 0,\n  };")
patch("    for (const k of ['chew', 'happy', 'surprise', 'yawn', 'dizzy', 'glance']) pet[k] = Math.max(0, pet[k] - dt);",
      "    for (const k of ['chew', 'happy', 'surprise', 'yawn', 'dizzy', 'glance', 'shake', 'screenT']) pet[k] = Math.max(0, pet[k] - dt);\n"
      "    if (pet.screenT <= 0 && (pet.screenText || (pet.screenTint && !pet.deploying))) { pet.screenText = ''; if (!pet.deploying) pet.screenTint = ''; }\n"
      "    if (pet.deploying) pet.deployProgress = Math.min(0.92, pet.deployProgress + dt * 0.05);")

# ---------------------------------------------------------------- particles: cardboard shards
patch("          ctx.fillStyle = '#f7e8cf';\n          ctx.translate(p.x, p.y); ctx.rotate(p.rot);",
      "          ctx.fillStyle = '#d9b483';\n          ctx.translate(p.x, p.y); ctx.rotate(p.rot);")

# ---------------------------------------------------------------- box + robot + snacks drawing
replace_range("  const CRACKS = [", "  function drawBugs() {", r"""  function roundRect(x, y, w, h, rad) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, rad);
  }

  const BOX_TEARS = [
    [[-0.9, -1.55], [-0.6, -1.5], [-0.72, -1.35]],
    [[0.2, -1.62], [0.5, -1.47], [0.35, -1.3], [0.7, -1.2]],
    [[-0.3, -1.1], [0.0, -1.0], [-0.2, -0.85]],
  ];
  function drawBox() {
    const r = eggR(), x = pet.ax, y = groundY;
    drawShadow(x, r * 1.15, 0);
    const rot = (egg.wobble > 0 ? Math.sin(egg.wobble * 22) * 0.1 * egg.wobble : 0) + 0.01 * Math.sin(pet.t * 1.5);
    const open = clamp(state.taps / 3, 0, 1);
    const w = r * 2.3, h = r * 1.7;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.fillStyle = '#d9b483';
    ctx.strokeStyle = '#a9804f';
    ctx.lineWidth = Math.max(1.5, r * 0.06);
    ctx.beginPath(); ctx.rect(-w / 2, -h, w, h); ctx.fill(); ctx.stroke();
    ctx.fillStyle = 'rgba(0,0,0,0.08)';
    ctx.fillRect(-w / 2, -h, w * 0.18, h);
    ctx.fillStyle = 'rgba(255,240,200,0.55)';
    ctx.fillRect(-r * 0.22, -h, r * 0.44, h);
    ctx.strokeStyle = '#7d5a33';
    ctx.lineWidth = Math.max(1, r * 0.05);
    for (const ax of [r * 0.58, r * 0.84]) {
      ctx.beginPath(); ctx.moveTo(ax, -h * 0.3); ctx.lineTo(ax, -h * 0.68);
      ctx.moveTo(ax - r * 0.11, -h * 0.56); ctx.lineTo(ax, -h * 0.68); ctx.lineTo(ax + r * 0.11, -h * 0.56); ctx.stroke();
    }
    ctx.fillStyle = '#7d5a33';
    ctx.font = `700 ${Math.round(r * 0.26)}px Fredoka, sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText('FRAGILE', -r * 0.5, -h * 0.4);
    if (state.taps > 0) {
      ctx.fillStyle = `hsla(170, 90%, 65%, ${0.35 + 0.3 * Math.sin(pet.t * 6)})`;
      ctx.fillRect(-w / 2 + r * 0.1, -h - r * 0.04, w - r * 0.2, r * 0.08);
    }
    ctx.fillStyle = '#e2c18f';
    ctx.strokeStyle = '#a9804f';
    ctx.lineWidth = Math.max(1.5, r * 0.06);
    for (const sgn of [-1, 1]) {
      ctx.save();
      ctx.translate(sgn * w / 2, -h);
      ctx.rotate(sgn * open * 2.4);
      ctx.beginPath(); ctx.rect(sgn === -1 ? 0 : -w / 2, -r * 0.14, w / 2, r * 0.14); ctx.fill(); ctx.stroke();
      ctx.restore();
    }
    ctx.strokeStyle = '#8b6a4b';
    ctx.lineWidth = 2;
    for (let i = 0; i < Math.min(state.taps, 3); i++) {
      ctx.beginPath();
      BOX_TEARS[i].forEach(([px, py], k) => (k === 0 ? ctx.moveTo(px * r, py * r) : ctx.lineTo(px * r, py * r)));
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawFace(hy, r, f) {
    const t = pet.t;
    const ey = hy - (pet.deploying ? r * 0.18 : r * 0.08);
    const ex = r * 0.38;
    const ew = r * 0.26, eh = r * 0.3 * (pet.surprise > 0 ? 1.25 : 1);
    const lids = f.asleep ? 1 : Math.max(pet.blink, f.sleepy ? 0.45 : 0, pet.yawn > 0 ? 0.7 : 0);
    const erroring = pet.screenTint === 'error' && pet.screenT > 0;
    const happyEyes = pet.happy > 0 && !f.asleep && pet.surprise <= 0 && pet.dizzy <= 0 && !erroring;
    ctx.lineWidth = Math.max(1.5, r * 0.07);
    for (const sgn of [-1, 1]) {
      const x = sgn * ex;
      if (erroring) {
        ctx.beginPath();
        ctx.moveTo(x - ew * 0.5, ey - eh * 0.5); ctx.lineTo(x + ew * 0.5, ey + eh * 0.5);
        ctx.moveTo(x + ew * 0.5, ey - eh * 0.5); ctx.lineTo(x - ew * 0.5, ey + eh * 0.5);
        ctx.stroke();
        continue;
      }
      if (pet.dizzy > 0) { ctx.beginPath(); ctx.arc(x, ey, ew * 0.5, t * 9 + sgn, t * 9 + sgn + 4.5); ctx.stroke(); continue; }
      if (happyEyes) { ctx.beginPath(); ctx.arc(x, ey + eh * 0.35, ew * 0.75, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke(); continue; }
      if (lids >= 0.97) { ctx.beginPath(); ctx.moveTo(x - ew * 0.5, ey); ctx.lineTo(x + ew * 0.5, ey); ctx.stroke(); continue; }
      const px = pet.look.x * ew * 0.25, py = pet.look.y * eh * 0.2;
      if (pet.surprise > 0) {
        ctx.beginPath(); ctx.arc(x + px, ey + py, ew * 0.55, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath(); ctx.arc(x + px, ey + py, ew * 0.2, 0, Math.PI * 2); ctx.fill();
        continue;
      }
      const h = Math.max(1, eh * (1 - lids * 0.8));
      roundRect(x - ew / 2 + px, ey - h / 2 + py, ew, h, ew * 0.25);
      ctx.fill();
      if (f.mood < 38 && !f.asleep) {
        ctx.beginPath(); ctx.moveTo(x + sgn * ew * 0.6, ey - h * 0.75); ctx.lineTo(x - sgn * ew * 0.4, ey - h * 1.1); ctx.stroke();
      }
    }
    const my = ey + r * 0.38;
    if (pet.chew > 0) {
      for (let i = -1; i <= 1; i++) {
        if (Math.sin(pet.chew * 40 + i * 2) > 0) { roundRect(i * r * 0.17 - r * 0.06, my - r * 0.06, r * 0.12, r * 0.12, r * 0.02); ctx.fill(); }
      }
    } else if (pet.yawn > 0 && !f.asleep) {
      const open = r * 0.18 * Math.sin(Math.PI * clamp(1 - pet.yawn / 1.2, 0, 1));
      roundRect(-r * 0.14, my - open / 2, r * 0.28, Math.max(1, open), r * 0.05); ctx.fill();
    } else if (pet.surprise > 0) {
      ctx.beginPath(); ctx.arc(0, my, r * 0.07, 0, Math.PI * 2); ctx.stroke();
    } else if (erroring) {
      ctx.beginPath(); ctx.moveTo(-r * 0.24, my);
      for (let i = 1; i <= 4; i++) ctx.lineTo(-r * 0.24 + i * r * 0.12, my + (i % 2 ? -r * 0.07 : r * 0.07));
      ctx.stroke();
    } else {
      const curve = f.asleep ? r * 0.03 : happyEyes ? r * 0.16 : r * 0.14 * ((f.mood - 50) / 50);
      ctx.beginPath(); ctx.moveTo(-r * 0.2, my); ctx.quadraticCurveTo(0, my + curve, r * 0.2, my); ctx.stroke();
    }
  }

  function drawPet() {
    const st = stageOf(state);
    const r = petR();
    const t = pet.t;
    const asleep = state.asleep;
    const mood = moodOf(state);
    const sleepy = !asleep && state.energy < 25;
    const hue = st === 3 ? 250 + 60 * Math.sin(t * 0.5) : 250;
    const sqy = (1 + pet.sq) * (1 + pet.stretch);
    const sqx = (1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6);

    drawShadow(pet.x, r, groundY - pet.y);

    ctx.save();
    ctx.translate(pet.x + (pet.shake > 0 ? Math.sin(t * 70) * r * 0.08 : 0), pet.y);
    ctx.scale(sqx, sqy);
    const outline = `hsl(${hue}, 22%, 52%)`;
    const shell = ctx.createLinearGradient(0, -3 * r, 0, 0);
    shell.addColorStop(0, `hsl(${hue}, 35%, 95%)`);
    shell.addColorStop(1, `hsl(${hue}, 28%, 80%)`);
    const lw = Math.max(1.5, r * 0.06);
    ctx.lineWidth = lw;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    const walking = !asleep && (pet.walkDir !== 0 || (pet.grounded && Math.abs(pet.ax - pet.x) > 3));
    const step = walking ? Math.sin(t * 14) : 0;
    const breathe = asleep ? Math.sin(t * 1.2) * 0.02 : Math.sin(t * 2.2) * 0.012;
    const carried = !!(pet.carried || pet.held);

    ctx.fillStyle = `hsl(${hue}, 25%, 45%)`;
    for (const sgn of [-1, 1]) {
      const lift = walking ? Math.max(0, step * sgn) * r * 0.12 : 0;
      roundRect(sgn * r * 0.45 - r * 0.3, -r * 0.22 - lift, r * 0.6, r * 0.22, r * 0.08);
      ctx.fill();
    }

    for (const sgn of [-1, 1]) {
      const sx = sgn * r * 0.78, sy = -r * 1.0;
      let theta = 0.35 + breathe * 3;
      if (carried) theta = 2.9;
      else if (pet.happy > 0) theta = 2.2 + Math.sin(t * 12) * 0.35;
      else if (pet.screenTint === 'error' && pet.screenT > 0) theta = 0.9 + Math.sin(t * 20) * 0.2;
      else if (walking) theta = 0.35 + step * sgn * 0.4;
      const ex = sx + sgn * Math.sin(theta) * r * 0.55, ey = sy + Math.cos(theta) * r * 0.55;
      ctx.strokeStyle = outline; ctx.lineWidth = r * 0.2;
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey); ctx.stroke();
      ctx.strokeStyle = `hsl(${hue}, 30%, 88%)`; ctx.lineWidth = r * 0.11;
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey); ctx.stroke();
      ctx.fillStyle = `hsl(${hue}, 30%, 90%)`; ctx.strokeStyle = outline; ctx.lineWidth = lw;
      ctx.beginPath(); ctx.arc(ex, ey, r * 0.16, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    }

    ctx.fillStyle = shell; ctx.strokeStyle = outline; ctx.lineWidth = lw;
    roundRect(-r * 0.75, -r * 1.3, r * 1.5, r * 1.12, r * 0.28); ctx.fill(); ctx.stroke();
    const leds = st >= 2 ? [state.full, state.energy, state.joy] : [state.energy];
    leds.forEach((v, i) => {
      const cx = (i - (leds.length - 1) / 2) * r * 0.3;
      const on = v > 25;
      ctx.fillStyle = on ? (v > 55 ? 'hsl(150, 70%, 55%)' : 'hsl(40, 90%, 58%)') : 'hsl(0, 60%, 55%)';
      ctx.globalAlpha = on ? 0.9 : 0.5 + 0.4 * Math.abs(Math.sin(t * 5));
      ctx.beginPath(); ctx.arc(cx, -r * 0.72, r * 0.07, 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = 1;
    });
    ctx.fillStyle = `hsl(${hue}, 25%, 60%)`;
    ctx.fillRect(-r * 0.18, -r * 1.45, r * 0.36, r * 0.2);

    const hy = -r * 1.95 + breathe * r * 2;
    if (st >= 2) {
      ctx.fillStyle = `hsl(${hue}, 28%, 70%)`; ctx.strokeStyle = outline;
      for (const sgn of [-1, 1]) { roundRect(sgn * r * 1.0 - r * 0.1, hy - r * 0.22, r * 0.2, r * 0.44, r * 0.06); ctx.fill(); ctx.stroke(); }
    }
    ctx.fillStyle = shell; ctx.strokeStyle = outline;
    roundRect(-r * 1.0, hy - r * 0.68, r * 2.0, r * 1.36, r * 0.36); ctx.fill(); ctx.stroke();

    const tint = pet.screenTint;
    let tipColor = 'hsl(170, 90%, 62%)';
    if (tint === 'error') tipColor = 'hsl(0, 90%, 60%)';
    else if (tint === 'ok') tipColor = 'hsl(150, 80%, 55%)';
    else if (tint === 'deploy') tipColor = `hsl(40, 95%, ${55 + 15 * Math.sin(t * 8)}%)`;
    else if (state.full < 30) tipColor = 'hsl(40, 95%, 60%)';
    else if (asleep) tipColor = `hsl(${hue}, 20%, 55%)`;
    const antennas = st === 3 ? [-0.35, 0.35] : [0];
    for (const ax of antennas) {
      ctx.strokeStyle = outline; ctx.lineWidth = lw;
      ctx.beginPath(); ctx.moveTo(ax * r, hy - r * 0.68); ctx.lineTo(ax * r * 1.3, hy - r * 1.05); ctx.stroke();
      ctx.save();
      ctx.shadowColor = tipColor; ctx.shadowBlur = r * 0.35; ctx.fillStyle = tipColor;
      ctx.beginPath(); ctx.arc(ax * r * 1.3, hy - r * 1.12, r * 0.12, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
    if (st === 3) {
      ctx.strokeStyle = `hsla(${hue + 120}, 80%, 65%, ${0.5 + 0.3 * Math.sin(t * 3)})`; ctx.lineWidth = lw;
      ctx.beginPath(); ctx.ellipse(0, hy - r * 1.4, r * 0.7, r * 0.18, 0, 0, Math.PI * 2); ctx.stroke();
    }

    const sw = r * 1.62, sh = r * 1.0;
    let screenBg = '#1d2140';
    if (tint === 'error') screenBg = `hsl(0, 60%, ${18 + 12 * Math.abs(Math.sin(t * 10))}%)`;
    else if (tint === 'ok') screenBg = 'hsl(150, 45%, 16%)';
    else if (tint === 'deploy') screenBg = 'hsl(230, 45%, 16%)';
    ctx.fillStyle = screenBg; ctx.strokeStyle = outline; ctx.lineWidth = lw;
    roundRect(-sw / 2, hy - sh / 2, sw, sh, r * 0.22); ctx.fill(); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.05)';
    roundRect(-sw / 2, hy - sh / 2, sw, sh * 0.45, r * 0.22); ctx.fill();

    const glow = tint === 'error' ? 'hsl(0, 90%, 65%)' : tint === 'ok' ? 'hsl(150, 85%, 60%)' : tint === 'deploy' ? 'hsl(40, 95%, 65%)' : (asleep ? 'hsl(170, 40%, 45%)' : 'hsl(170, 90%, 68%)');
    ctx.save();
    ctx.shadowColor = glow; ctx.shadowBlur = r * 0.25;
    ctx.fillStyle = glow; ctx.strokeStyle = glow;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    if (pet.screenText) {
      ctx.font = `700 ${Math.round(r * 0.5)}px ui-monospace, Menlo, monospace`;
      ctx.fillText(pet.screenText, 0, hy + (pet.deploying ? -r * 0.1 : 0));
    } else {
      drawFace(hy, r, { asleep, sleepy, mood });
    }
    if (pet.deploying) {
      const bw = sw * 0.72, bh = r * 0.13, by = hy + sh / 2 - r * 0.24;
      ctx.shadowBlur = 0; ctx.fillStyle = 'rgba(255,255,255,0.15)';
      roundRect(-bw / 2, by - bh / 2, bw, bh, bh / 2); ctx.fill();
      ctx.fillStyle = glow; ctx.shadowBlur = r * 0.2;
      roundRect(-bw / 2, by - bh / 2, Math.max(bh, bw * pet.deployProgress), bh, bh / 2); ctx.fill();
    }
    ctx.restore();
    ctx.restore();
  }

  function drawSnack() {
    if (!snack.active) return;
    const u = 9 * scale;
    ctx.save();
    ctx.translate(snack.x, snack.y);
    ctx.lineJoin = 'round';
    if (snack.kind === 'battery') {
      ctx.rotate(-0.35);
      ctx.fillStyle = 'hsl(140, 55%, 45%)';
      roundRect(-u * 1.2, -u * 0.6, u * 2.4, u * 1.2, u * 0.2); ctx.fill();
      ctx.fillStyle = '#9aa3ad';
      ctx.fillRect(u * 1.2, -u * 0.28, u * 0.3, u * 0.56);
      ctx.strokeStyle = '#eafff1'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(u * 0.55, 0); ctx.lineTo(u * 0.95, 0); ctx.moveTo(u * 0.75, -u * 0.2); ctx.lineTo(u * 0.75, u * 0.2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-u * 0.9, 0); ctx.lineTo(-u * 0.5, 0); ctx.stroke();
    } else if (snack.kind === 'chip') {
      ctx.fillStyle = '#2b2f3a';
      roundRect(-u * 0.9, -u * 0.9, u * 1.8, u * 1.8, u * 0.15); ctx.fill();
      ctx.fillStyle = 'hsl(45, 90%, 60%)';
      ctx.fillRect(-u * 0.4, -u * 0.4, u * 0.8, u * 0.8);
      ctx.strokeStyle = '#c9ced8'; ctx.lineWidth = 1.5;
      for (const k of [-0.5, 0, 0.5]) {
        ctx.beginPath(); ctx.moveTo(-u * 0.9, k * u); ctx.lineTo(-u * 1.25, k * u); ctx.moveTo(u * 0.9, k * u); ctx.lineTo(u * 1.25, k * u);
        ctx.moveTo(k * u, -u * 0.9); ctx.lineTo(k * u, -u * 1.25); ctx.moveTo(k * u, u * 0.9); ctx.lineTo(k * u, u * 1.25); ctx.stroke();
      }
    } else {
      ctx.fillStyle = 'hsl(32, 60%, 62%)';
      ctx.beginPath(); ctx.arc(0, 0, u * 1.05, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'hsl(25, 55%, 28%)';
      for (const [dx, dy] of [[-0.4, -0.3], [0.35, -0.1], [-0.1, 0.45], [0.4, 0.5]]) { ctx.beginPath(); ctx.arc(dx * u, dy * u, u * 0.17, 0, Math.PI * 2); ctx.fill(); }
    }
    ctx.restore();
  }

""")
patch("    if (!state.hatched) drawEgg();", "    if (!state.hatched) drawBox();")

# ---------------------------------------------------------------- test + deploy reactions
patch("    const loud = kind === 'commit' || kind === 'push' || kind === 'merge';",
      "    const loud = ['commit', 'push', 'merge', 'test-failed', 'deploy-started', 'deploy-finished', 'deploy-failed'].includes(kind);")
patch("      wake();\n      say('who is committing?', 2000);\n    }",
      "      wake();\n      say(kind === 'test-failed' ? 'who broke the build?' : 'who is committing?', 2000);\n    }")
patch("""      case 'cherry-pick':
        spawnDrop('commit', 'cherry');
        say('cherry! nom', 2200);
        break;
      default:
        break;
    }""", """      case 'cherry-pick':
        spawnDrop('commit', 'cherry');
        say('cherry! nom', 2200);
        break;
      case 'test-failed': {
        const count = Math.max(0, Math.min(99, Number(ev.count) || 0));
        const label = String(ev.name || ev.repo || '').trim();
        pet.screenText = 'ERR'; pet.screenTint = 'error'; pet.screenT = 2.8; pet.shake = 0.9;
        pet.happy = 0; pet.deploying = false;
        state.joy = clamp(state.joy - 3);
        audio.error();
        const bugCount = count > 0 ? Math.min(5, count) : 2;
        for (let i = 0; i < bugCount; i++) spawnBug();
        debug.active = true; debug.until = 45;
        const line = count > 0
          ? `${count} test${count === 1 ? '' : 's'} failing${label ? ` in ${label}` : ''}`
          : (label ? `${label} is red` : pick(LINES.testFail));
        setTimeout(() => say(line, 3400), 300);
        break;
      }
      case 'test-passed': {
        const label = String(ev.name || ev.repo || '').trim();
        pet.screenText = 'OK'; pet.screenTint = 'ok'; pet.screenT = 2; pet.happy = 1.6;
        state.joy = clamp(state.joy + 6);
        audio.ok();
        for (const b of bugs) if (b.alive) squashBug(b, false);
        say(label ? `${label} is green!` : pick(LINES.testPass), 2800);
        break;
      }
      case 'deploy-started': {
        const target = String(ev.target || ev.name || '').trim();
        pet.deploying = true; pet.deployProgress = 0; pet.screenTint = 'deploy'; pet.screenText = '';
        say(target ? `deploying ${target}…` : 'deploying…', 3200);
        break;
      }
      case 'deploy-finished': {
        const target = String(ev.target || ev.name || '').trim();
        pet.deploying = false; pet.deployProgress = 1;
        pet.screenText = '100%'; pet.screenTint = 'ok'; pet.screenT = 1.6;
        state.joy = clamp(state.joy + 10);
        state.care += 3;
        audio.ok();
        setTimeout(() => launchRocket(target ? `deployed to ${target}!` : 'deployed!'), 1000);
        break;
      }
      case 'deploy-failed': {
        const target = String(ev.target || ev.name || '').trim();
        pet.deploying = false;
        pet.screenText = 'ERR'; pet.screenTint = 'error'; pet.screenT = 3.2; pet.shake = 0.7;
        state.joy = clamp(state.joy - 5);
        audio.error();
        spawn('dust', pet.x, pet.y - petR() * 2.6, 8, { spread: petR() * 0.6, vx: 30, vy: -40, g: -30, size: 16, dur: 1.6 });
        say(target ? `${target} deploy failed. rollback?` : pick(LINES.deployFail), 3400);
        break;
      }
      case 'say':
        say(shortMessage(msg) || 'hi', 3000);
        break;
      default:
        break;
    }""")

SRC.write_text(s, encoding="utf-8")
print("patched", SRC)
