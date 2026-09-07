#!/usr/bin/env python3
"""One-off migration: ball mini-game -> debug (bug squashing) + git reactions.

Applied to web/jellykin.html. Kept in the repo as a record of the change; it is
idempotent-guarded (refuses to run twice) and asserts every anchor.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "web" / "jellykin.html"
s = SRC.read_text(encoding="utf-8")
if "function updateBugs" in s:
    raise SystemExit("already applied")


def patch(old: str, new: str) -> None:
    global s
    if s.count(old) != 1:
        raise SystemExit(f"anchor not found exactly once:\n{old[:160]}")
    s = s.replace(old, new)


# ---------------------------------------------------------------- copy + state
patch("    bored: ['play with me?', 'bored...', 'bounce the ball!', 'anyone?'],",
      "    bored: ['play with me?', 'bored...', 'any bugs to squash?', 'anyone?'],")
patch("    play: ['ball ball ball!', 'catch it!', 'bounce!'],",
      "    play: ['bugs! squash them!', 'debug time', 'found some bugs', 'exterminate!'],\n"
      "    squash: ['fixed!', 'squash!', 'gotcha', 'bug: 0, me: 1', 'closed as fixed'],")
patch("      meals: 0, games: 0, pets: 0, stageSeen: 0,\n    };",
      "      meals: 0, games: 0, pets: 0, stageSeen: 0,\n      commits: 0, pushes: 0, bugs: 0, lastCommitAt: 0,\n    };")
patch("    grow() { [659, 784, 988, 1318, 1568].forEach((f, i) => setTimeout(() => this.tone(f, f * 1.01, 0.22), i * 90)); },",
      "    grow() { [659, 784, 988, 1318, 1568].forEach((f, i) => setTimeout(() => this.tone(f, f * 1.01, 0.22), i * 90)); },\n"
      "    whoosh() { this.tone(160, 900, 0.5, 'sawtooth', 0.035); },")

# ---------------------------------------------------------------- objects
patch("  const ball = { active: false, x: 0, y: 0, vx: 0, vy: 0, r: 15, rot: 0, until: 0 };",
      "  const bugs = [];\n"
      "  const debug = { active: false, until: 0 };\n"
      "  const drop = { active: false, x: 0, y: 0, vy: 0, kind: 'commit', label: '', rest: false };\n"
      "  const rocket = { active: false, x: 0, y: 0, vy: 0, t: 0 };\n"
      "  let gitInfo = { dirty: 0, repo: '', branch: '', minutesSinceCommit: -1 };")
patch("    grounded: true, chew: 0, happy: 0, surprise: 0, yawn: 0, t: 0, idleAt: 2.5,\n  };",
      "    grounded: true, chew: 0, happy: 0, surprise: 0, yawn: 0, dizzy: 0, glance: 0, t: 0, idleAt: 2.5,\n  };")

# ---------------------------------------------------------------- particles
patch("        case 'spark':",
      "        case 'check':\n"
      "          ctx.fillStyle = 'hsl(150, 55%, 42%)';\n"
      "          ctx.font = `700 ${Math.round(s * 1.3)}px Fredoka, sans-serif`;\n"
      "          ctx.fillText('✓', p.x, p.y);\n"
      "          break;\n"
      "        case 'flame':\n"
      "          ctx.fillStyle = `hsl(${p.hue}, 95%, ${55 + 30 * (1 - a)}%)`;\n"
      "          ctx.beginPath(); ctx.arc(p.x, p.y, s * 0.45, 0, Math.PI * 2); ctx.fill();\n"
      "          break;\n"
      "        case 'spark':")

# ---------------------------------------------------------------- play -> debug
patch("""  function play() {
    if (!state.hatched || state.asleep) return;
    if (ball.active) { kickBall(); return; }
    if (state.energy < 15) { say(pick(LINES.tired)); pet.yawn = 1.2; return; }
    ball.active = true;
    ball.r = 15 * scale;
    ball.x = clamp(W / 2 + rand(-100, 100), ball.r, W - ball.r);
    ball.y = H * 0.2;
    ball.vx = rand(-200, 200);
    ball.vy = 0;
    ball.until = 16;
    state.games += 1;
    state.care += 2;
    state.joy = clamp(state.joy + 18);
    state.energy = clamp(state.energy - 8);
    say(pick(LINES.play));
    saveState();
  }
  function kickBall() {
    ball.vy = -650;
    ball.vx += rand(-300, 300);
    audio.pop();
    spawn('spark', ball.x, ball.y, 3, { spread: 4, vx: 80, vy: -40, size: 7, hue: 45, dur: 0.5 });
  }
""", """  function play() {
    if (!state.hatched || state.asleep || debug.active) return;
    if (state.energy < 15) { say(pick(LINES.tired)); pet.yawn = 1.2; return; }
    debug.active = true;
    debug.until = 25;
    for (let i = 0; i < 4; i++) spawnBug();
    state.games += 1;
    state.care += 2;
    state.energy = clamp(state.energy - 8);
    say(pick(LINES.play));
    saveState();
  }
  function endDebug() {
    debug.active = false;
    bugs.length = 0;
  }
  function spawnBug(x) {
    const bx = x !== undefined ? x : (Math.random() < 0.5 ? rand(14, W * 0.3) : rand(W * 0.7, W - 14));
    bugs.push({ x: clamp(bx, 12, W - 12), vx: rand(50, 90) * (Math.random() < 0.5 ? -1 : 1), dart: rand(0.5, 2), alive: true, squash: 0, wig: rand(0, 6) });
  }
  function squashBug(b, byPet) {
    if (!b.alive) return;
    b.alive = false;
    b.squash = 0.45;
    state.bugs += 1;
    state.joy = clamp(state.joy + 4);
    state.care += 1;
    audio.pop();
    spawn('check', b.x, groundY - 12, 2, { spread: 6, vx: 30, vy: -70, size: 12, dur: 0.9 });
    say(pick(LINES.squash), 1300);
    if (byPet) { pet.sq = -0.25; pet.sqv = 0; pet.happy = 0.6; }
  }
  function bugAt(x, y) {
    return bugs.find((b) => b.alive && Math.hypot(x - b.x, y - (groundY - 8)) < 20);
  }
  function spawnDrop(kind, label) {
    drop.active = true;
    drop.rest = false;
    drop.kind = kind;
    drop.label = label;
    drop.x = clamp(pet.x + rand(-30, 30), 30, W - 30);
    drop.y = -24;
    drop.vy = 0;
    pet.ax = drop.x;
  }
  function eatDrop() {
    drop.active = false;
    pet.chew = 0.7;
    state.full = clamp(state.full + 10);
    state.joy = clamp(state.joy + 8);
    state.care += 2;
    audio.munch();
    setTimeout(() => audio.munch(), 180);
    spawn('spark', pet.x, pet.y - petR(), 6, { spread: petR() * 0.5, vx: 80, vy: -90, size: 7, hue: drop.kind === 'merge' ? 275 : 175, dur: 0.8 });
    saveState();
  }
  function launchRocket(label) {
    rocket.active = true;
    rocket.x = pet.x;
    rocket.y = pet.y - petR() * 2.1;
    rocket.vy = -60;
    rocket.t = 0;
    pet.sq = 0.25; pet.sqv = 0;
    pet.happy = 2;
    audio.whoosh();
    spawn('spark', pet.x, pet.y - petR(), 10, { spread: petR(), vx: 120, vy: -100, size: 8, hue: 45, dur: 1.2 });
    say(label, 3200);
  }
""")
patch("    state.asleep = true;\n    ball.active = false;\n    snack.active = false;",
      "    state.asleep = true;\n    endDebug();\n    drop.active = false;\n    rocket.active = false;\n    snack.active = false;")

# ---------------------------------------------------------------- hit tests
patch("    if (ball.active && Math.hypot(x - ball.x, y - ball.y) < ball.r * 1.7) { kickBall(); return; }\n    if (!state.hatched) {\n      const r = eggR();\n      if (Math.hypot(x - pet.ax, y - (groundY - r * 1.1)) < r * 1.5) eggTap();\n      return;\n    }\n    const r = petR();\n    if (Math.hypot(x - pet.x, y - (pet.y - r)) < r * 1.25) { if (state.asleep) wake(); else petTap(); }",
      "    const bug = bugAt(x, y);\n    if (bug) { squashBug(bug, false); return; }\n    if (!state.hatched) {\n      const r = eggR();\n      if (Math.hypot(x - pet.ax, y - (groundY - r * 1.1)) < r * 1.5) eggTap();\n      return;\n    }\n    const r = petR();\n    if (Math.hypot(x - pet.x, y - (pet.y - r)) < r * 1.25) { if (state.asleep) wake(); else petTap(); }")
patch("    pointer.vx = 0; pointer.vy = 0;\n    if (ball.active && Math.hypot(x - ball.x, y - ball.y) < ball.r * 1.7) { kickBall(); return; }",
      "    pointer.vx = 0; pointer.vy = 0;\n    const bug = bugAt(x, y);\n    if (bug) { squashBug(bug, false); return; }")

# ---------------------------------------------------------------- pet update
patch("    for (const k of ['chew', 'happy', 'surprise', 'yawn']) pet[k] = Math.max(0, pet[k] - dt);",
      "    for (const k of ['chew', 'happy', 'surprise', 'yawn', 'dizzy', 'glance']) pet[k] = Math.max(0, pet[k] - dt);")
patch("        const speed = (ball.active || snack.active) ? 5 : 2.5;",
      "        const speed = (debug.active || snack.active || drop.active) ? 5 : 2.5;")
patch("""        } else if (ball.active) {
          pet.lookT.x = clamp((ball.x - pet.x) / (r * 3), -1, 1);
          pet.lookT.y = clamp((ball.y - (pet.y - r)) / (r * 3), -1, 1);
        } else if""", """        } else if (pet.glance > 0) {
          pet.lookT.x = Math.sign(Math.sin(pet.t * 14)) * 0.9; pet.lookT.y = -0.2;
        } else if (drop.active) {
          pet.lookT.x = clamp((drop.x - pet.x) / (r * 3), -1, 1);
          pet.lookT.y = clamp((drop.y - (pet.y - r)) / (r * 3), -1, 1);
        } else if (rocket.active) {
          pet.lookT.x = clamp((rocket.x - pet.x) / (r * 3), -1, 1);
          pet.lookT.y = clamp((rocket.y - (pet.y - r)) / (r * 3), -1, 1);
        } else if (bugs.length) {
          const b = bugs.find((k) => k.alive) || bugs[0];
          pet.lookT.x = clamp((b.x - pet.x) / (r * 3), -1, 1);
          pet.lookT.y = 0.8;
        } else if""")

# ---------------------------------------------------------------- update systems
old_update_ball_start = "  function updateBall(dt) {\n    if (!ball.active) return;"
i = s.index(old_update_ball_start)
j = s.index("  function doIdle() {", i)
s = s[:i] + """  function updateBugs(dt) {
    if (!bugs.length) { if (debug.active) debug.active = false; return; }
    const r = petR();
    const canStomp = state.hatched && !state.asleep && !pet.held && !pet.carried;
    for (let i = bugs.length - 1; i >= 0; i--) {
      const b = bugs[i];
      if (!b.alive) { b.squash -= dt; if (b.squash <= 0) bugs.splice(i, 1); continue; }
      b.dart -= dt;
      if (b.dart <= 0) {
        b.dart = rand(0.4, 1.8);
        b.vx = (Math.random() < 0.5 ? -1 : 1) * rand(40, 110);
      }
      const away = b.x - pet.x;
      if (Math.abs(away) < r * 1.6 && Math.random() < 0.06) b.vx = Math.sign(away || 1) * rand(90, 150);
      b.x += b.vx * dt;
      if (b.x < 12) { b.x = 12; b.vx = Math.abs(b.vx); }
      if (b.x > W - 12) { b.x = W - 12; b.vx = -Math.abs(b.vx); }
      if (canStomp && pet.grounded && Math.abs(b.x - pet.x) < r * 0.55) squashBug(b, true);
    }
    if (!debug.active) return;
    debug.until -= dt;
    const alive = bugs.filter((b) => b.alive);
    if (!alive.length) {
      debug.active = false;
      state.joy = clamp(state.joy + 10);
      say(pick(['all bugs squashed!', 'clean build!', 'zero bugs. for now.']), 2600);
      saveState();
      return;
    }
    if (debug.until <= 0) { endDebug(); say('some got away...', 2200); return; }
    let best = alive[0], bestDist = Infinity;
    for (const b of alive) { const d = Math.abs(b.x - pet.x); if (d < bestDist) { bestDist = d; best = b; } }
    pet.ax = clamp(best.x, r, W - r);
    if (canStomp && pet.grounded && bestDist < r * 1.3 && bestDist > r * 0.55 && !reduceMotion) {
      pet.vy = -260; pet.grounded = false; pet.sq = 0.15; pet.sqv = 0;
      pet.vx = Math.sign(best.x - pet.x) * 120;
    }
  }

  function updateDrop(dt) {
    if (!drop.active) return;
    if (!drop.rest) {
      drop.vy += 1300 * dt;
      drop.y += drop.vy * dt;
      if (drop.y >= groundY - 12) { drop.y = groundY - 12; drop.vy = 0; drop.rest = true; }
    }
    const r = petR();
    if (!pet.held && !pet.carried && Math.hypot(drop.x - pet.x, drop.y - (pet.y - r * 0.8)) < r * 1.05) eatDrop();
  }

  function updateRocket(dt) {
    if (!rocket.active) return;
    rocket.t += dt;
    rocket.vy -= 1100 * dt;
    rocket.y += rocket.vy * dt;
    rocket.x += Math.sin(rocket.t * 7) * 14 * dt;
    spawn('flame', rocket.x, rocket.y + 14 * scale, 1, { spread: 2, vx: 25, vy: 140, size: 7, dur: 0.35, hue: rand(20, 45) });
    if (rocket.y < -60) rocket.active = false;
  }

""" + s[j:]
patch("    updateBall(dt);", "    updateBugs(dt);\n    updateDrop(dt);\n    updateRocket(dt);")

# ---------------------------------------------------------------- idle nags
patch("    if (state.joy < 35 && r < 0.4) { say(pick(LINES.bored)); return; }",
      "    if (state.joy < 35 && r < 0.4) { say(pick(LINES.bored)); return; }\n"
      "    const hour = new Date().getHours();\n"
      "    if (gitInfo.dirty >= 10 && r < 0.3) { say(`${gitInfo.dirty} files uncommitted…`, 3000); pet.glance = 1; return; }\n"
      "    if (gitInfo.minutesSinceCommit > 24 * 60 && hour >= 9 && hour < 20 && r < 0.25) { say(pick(['no commits today?', 'the repo misses you', 'git log is lonely']), 3000); return; }")

# ---------------------------------------------------------------- drawing
patch("""    const px = x + pet.look.x * er * 0.42, py = ey + pet.look.y * er * 0.35;""",
      """      const px = pet.dizzy > 0 ? x + Math.cos(t * 9 + s) * er * 0.35 : x + pet.look.x * er * 0.42;
      const py = pet.dizzy > 0 ? ey + Math.sin(t * 9 + s) * er * 0.3 : ey + pet.look.y * er * 0.35;""")

old_draw_ball_start = "  function drawBall() {\n    if (!ball.active) return;"
i = s.index(old_draw_ball_start)
j = s.index("  function draw() {", i)
s = s[:i] + """  function drawBugs() {
    for (const b of bugs) {
      const u = 6.5 * scale;
      ctx.save();
      ctx.translate(b.x, groundY - 1);
      if (!b.alive) {
        ctx.globalAlpha = clamp(b.squash / 0.45, 0, 1);
        ctx.fillStyle = '#4a3540';
        ctx.beginPath(); ctx.ellipse(0, -u * 0.3, u * 2, u * 0.45, 0, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
        continue;
      }
      ctx.scale(Math.sign(b.vx) || 1, 1);
      const wig = Math.sin(pet.t * 28 + b.wig);
      ctx.strokeStyle = '#3a2a33';
      ctx.lineWidth = 1.2;
      ctx.lineCap = 'round';
      for (let k = -1; k <= 1; k++) {
        const swing = wig * (k === 0 ? -1 : 1) * u * 0.35;
        ctx.beginPath(); ctx.moveTo(k * u * 0.7, -u * 0.6); ctx.lineTo(k * u * 0.7 + swing - u * 0.2, 0); ctx.stroke();
      }
      ctx.fillStyle = '#d9534f';
      ctx.beginPath(); ctx.ellipse(0, -u * 0.95, u * 1.35, u * 0.85, 0, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#3a2a33';
      ctx.beginPath(); ctx.moveTo(0, -u * 1.8); ctx.lineTo(0, -u * 0.1); ctx.lineWidth = 1; ctx.stroke();
      for (const [dx, dy] of [[-0.6, -1.15], [0.35, -1.25], [-0.2, -0.6], [0.7, -0.7]]) {
        ctx.beginPath(); ctx.arc(dx * u, dy * u, u * 0.18, 0, Math.PI * 2); ctx.fill();
      }
      ctx.beginPath(); ctx.arc(u * 1.3, -u * 0.95, u * 0.5, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.moveTo(u * 1.5, -u * 1.3); ctx.lineTo(u * 2.0, -u * 2.0 + wig * u * 0.2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(u * 1.6, -u * 1.2); ctx.lineTo(u * 2.3, -u * 1.5 - wig * u * 0.2); ctx.stroke();
      ctx.fillStyle = '#fff';
      ctx.beginPath(); ctx.arc(u * 1.5, -u * 1.05, u * 0.16, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
  }

  function drawDrop() {
    if (!drop.active) return;
    const u = 12 * scale;
    ctx.save();
    ctx.translate(drop.x, drop.y);
    ctx.rotate(drop.rest ? 0 : Math.sin(pet.t * 6) * 0.15);
    ctx.shadowColor = drop.kind === 'merge' ? 'hsla(275, 70%, 60%, 0.7)' : 'hsla(175, 70%, 50%, 0.7)';
    ctx.shadowBlur = u * 0.9;
    ctx.fillStyle = drop.kind === 'merge' ? 'hsl(275, 55%, 55%)' : 'hsl(175, 60%, 42%)';
    ctx.beginPath(); ctx.roundRect(-u, -u, u * 2, u * 2, u * 0.35); ctx.fill();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = 'rgba(255,255,255,0.7)';
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(0, 0, u * 0.5, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, -u * 0.5); ctx.lineTo(0, -u * 0.95); ctx.moveTo(0, u * 0.5); ctx.lineTo(0, u * 0.95); ctx.stroke();
    ctx.fillStyle = '#fff';
    ctx.font = `600 ${Math.round(u * 0.75)}px ui-monospace, Menlo, monospace`;
    ctx.textAlign = 'center';
    ctx.fillText(drop.label.slice(0, 7), 0, u * 1.9);
    ctx.restore();
  }

  function drawRocket() {
    if (!rocket.active) return;
    const u = 9 * scale;
    ctx.save();
    ctx.translate(rocket.x, rocket.y);
    ctx.rotate(Math.sin(rocket.t * 7) * 0.12);
    ctx.fillStyle = '#f4f1ea';
    ctx.beginPath();
    ctx.moveTo(0, -u * 2.2);
    ctx.quadraticCurveTo(u * 1.1, -u * 0.6, u * 0.8, u * 1.2);
    ctx.lineTo(-u * 0.8, u * 1.2);
    ctx.quadraticCurveTo(-u * 1.1, -u * 0.6, 0, -u * 2.2);
    ctx.fill();
    ctx.fillStyle = '#e0524f';
    ctx.beginPath(); ctx.moveTo(-u * 0.8, u * 0.3); ctx.lineTo(-u * 1.6, u * 1.6); ctx.lineTo(-u * 0.7, u * 1.2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(u * 0.8, u * 0.3); ctx.lineTo(u * 1.6, u * 1.6); ctx.lineTo(u * 0.7, u * 1.2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(0, -u * 2.2); ctx.quadraticCurveTo(u * 0.6, -u * 1.4, u * 0.55, -u * 0.9); ctx.lineTo(-u * 0.55, -u * 0.9); ctx.quadraticCurveTo(-u * 0.6, -u * 1.4, 0, -u * 2.2); ctx.fill();
    ctx.fillStyle = '#5eb1d8';
    ctx.beginPath(); ctx.arc(0, -u * 0.1, u * 0.38, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }

""" + s[j:]
patch("    else { drawSnack(); drawPet(); drawBall(); }",
      "    else { drawSnack(); drawDrop(); drawBugs(); drawPet(); drawRocket(); }")
patch("    ball.active = false; snack.active = false; particles.length = 0;",
      "    endDebug(); drop.active = false; rocket.active = false; snack.active = false; particles.length = 0;")

# ---------------------------------------------------------------- git reactions (shared logic, fed by the desktop host)
patch("  // ---------------------------------------------------------------- hud\n",
      """  // ---------------------------------------------------------------- git reactions
  function shortMessage(msg) {
    const m = String(msg || '').trim().split('\\n')[0];
    return m.length > 28 ? `${m.slice(0, 26)}…` : m;
  }
  function handleGitEvent(ev) {
    if (!ev || typeof ev !== 'object') return;
    if (!state.hatched) { egg.wobble = 1; say('something is happening out there', 2400); return; }
    const kind = String(ev.kind || '');
    const msg = String(ev.message || '');
    const branch = String(ev.branch || '');
    const lower = msg.toLowerCase();
    const hour = new Date().getHours();
    const loud = kind === 'commit' || kind === 'push' || kind === 'merge';
    if (state.asleep) {
      if (!loud) return;
      wake();
      say('who is committing?', 2000);
    }
    audio.ensure();
    switch (kind) {
      case 'commit': {
        state.commits += 1;
        state.lastCommitAt = now();
        spawnDrop('commit', ev.hash ? String(ev.hash).slice(0, 7) : 'commit');
        let line = msg.trim() ? `commit: ${shortMessage(msg)}` : 'a commit!';
        if (/\\b(fix|fixes|fixed|bug|hotfix)\\b/.test(lower)) { line = 'bug fixed? squash!'; spawnBug(clamp(pet.x + rand(-80, 80), 14, W - 14)); }
        else if (/\\bwip\\b/.test(lower)) line = 'wip? okay…';
        else if (/typo/.test(lower)) line = 'hehe, typo';
        else if (/^revert\\b/i.test(msg.trim())) { line = 'undo undo undo'; pet.surprise = 1.2; }
        else if (msg.trim().length > 0 && msg.trim().length < 8) line = `"${msg.trim()}"? that's the message?`;
        const churn = (Number(ev.insertions) || 0) + (Number(ev.deletions) || 0);
        if (churn > 400) { line = `chonky commit! ${churn} lines`; pet.sq = 0.3; pet.sqv = 0; }
        setTimeout(() => say(line, 3200), 900);
        if (hour >= 23 || hour < 5) setTimeout(() => { say('go to sleep, human', 2600); pet.yawn = 1.2; }, 4400);
        break;
      }
      case 'amend':
        say('amended. nobody saw.', 2600);
        pet.happy = 0.8;
        break;
      case 'merge':
        state.commits += 1;
        state.lastCommitAt = now();
        spawnDrop('merge', 'merge');
        spawn('spark', pet.x, pet.y - petR(), 16, { spread: petR(), vx: 120, vy: -120, size: 9, hue: 275, dur: 1.4 });
        say(branch ? `merged into ${branch}!` : 'merged!', 3000);
        pet.happy = 1.5;
        break;
      case 'push':
        state.pushes += 1;
        launchRocket(branch ? `shipped ${branch}!` : 'shipped!');
        break;
      case 'checkout':
        pet.glance = 1.2;
        say(branch ? `now on ${branch}` : 'switched branch', 2600);
        break;
      case 'rebase':
        pet.dizzy = 4;
        say('rebasing… hold on', 2600);
        break;
      case 'rebase-done':
        pet.dizzy = 0;
        pet.happy = 1;
        say('rebased, phew', 2400);
        break;
      case 'pull':
        pet.happy = 0.8;
        say('fresh from origin', 2400);
        break;
      case 'stash':
        say('tucked it away', 2200);
        break;
      case 'reset':
        pet.surprise = 1.5;
        say('wait, where did it go?', 2600);
        break;
      case 'cherry-pick':
        spawnDrop('commit', 'cherry');
        say('cherry! nom', 2200);
        break;
      default:
        break;
    }
    saveState();
  }
  function handleGitStatus(info) {
    if (!info || typeof info !== 'object') return;
    gitInfo = {
      dirty: Number(info.dirty) || 0,
      repo: String(info.repo || ''),
      branch: String(info.branch || ''),
      minutesSinceCommit: Number.isFinite(Number(info.minutesSinceCommit)) ? Number(info.minutesSinceCommit) : -1,
    };
  }

  // ---------------------------------------------------------------- hud
""")

# ---------------------------------------------------------------- markup
patch("""    <button type="button" id="playBtn" disabled>
      <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M4.5 8.5c5 1 10 1 15 0M4.5 15.5c5-1 10-1 15 0"/></svg><span>Play</span>
    </button>""", """    <button type="button" id="playBtn" disabled>
      <svg viewBox="0 0 24 24"><path d="M8 10a4 4 0 0 1 8 0v5a4 4 0 0 1-8 0z"/><path d="M12 6V4M9 7 7 5M15 7l2-2M8 12H4M20 12h-4M8 15H5M19 15h-3M9 18l-2 2M15 18l2 2"/></svg><span>Debug</span>
    </button>""")
patch("""        <dt>Games</dt><dd id="sGames">0</dd>
        <dt>Pats</dt><dd id="sPets">0</dd>""", """        <dt>Debug runs</dt><dd id="sGames">0</dd>
        <dt>Bugs squashed</dt><dd id="sBugs">0</dd>
        <dt>Commits caught</dt><dd id="sCommits">0</dd>
        <dt>Pats</dt><dd id="sPets">0</dd>""")
patch("    $('#sGames').textContent = String(state.games);",
      "    $('#sGames').textContent = String(state.games);\n    $('#sBugs').textContent = String(state.bugs);\n    $('#sCommits').textContent = String(state.commits);")
patch("<p>Grows to the next stage with age and care points. Needs drift slowly while you are away, but a Jellykin never dies. It only sulks.</p>",
      "<p>Grows to the next stage with age and care points. Needs drift slowly while you are away, but a Jellykin never dies. It only sulks. The desktop app also feeds it your git commits.</p>")

SRC.write_text(s, encoding="utf-8")
print("patched", SRC)
