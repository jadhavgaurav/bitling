#!/usr/bin/env python3
"""One-off migration: emergency parachute.

Thrown from a height and falling fast, Bitling pops a chute: canopy above, cords to
both raised arms, legs swinging, a slow swaying descent. On touchdown the chute
collapses and folds away. Below a safe height it just takes the landing on its knees.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "web" / "bitling.html"
s = SRC.read_text(encoding="utf-8")
if "chuteOpen" in s:
    raise SystemExit("already applied")


def patch(old: str, new: str) -> None:
    global s
    if s.count(old) != 1:
        raise SystemExit(f"anchor found {s.count(old)}x, expected 1:\n{old[:160]}")
    s = s.replace(old, new)


# ---------------------------------------------------------------- state + copy
patch("    spin: 0, spinV: 0, thrown: false,\n",
      "    spin: 0, spinV: 0, thrown: false,\n"
      "    chuteOpen: false, chute: 0, chuteSway: 0, chuteCut: 0,\n")
patch("    held: ['whee!', 'eep!', 'flying!', 'careful!'],",
      "    held: ['whee!', 'eep!', 'flying!', 'careful!'],\n"
      "    chute: ['deploying chute!', 'geronimo!', 'this is fine', 'physics!', 'engaging drag'],\n"
      "    landed: ['stuck the landing', 'ten out of ten', 'chute stowed', 'that was on purpose'],")
patch("    whoosh() { this.tone(160, 900, 0.5, 'sawtooth', 0.035); },",
      "    whoosh() { this.tone(160, 900, 0.5, 'sawtooth', 0.035); },\n"
      "    poof() { this.tone(700, 240, 0.28, 'triangle', 0.05); },")

# ---------------------------------------------------------------- deploy / cut
patch("  // ---------------------------------------------------------------- flight\n",
      """  // ---------------------------------------------------------------- parachute
  function openChute() {
    if (pet.chuteOpen || state.asleep || !state.hatched) return;
    pet.chuteOpen = true;
    pet.chute = 0;
    pet.chuteSway = 0;
    pet.spinV = 0;
    pet.spin = 0;
    audio.poof();
    spawn('spark', pet.x, pet.y - petR() * 3.4, 6, { spread: petR() * 0.8, vx: 90, vy: -40, size: 7, hue: 190, dur: 0.6 });
    say(pick(LINES.chute), 2200);
  }
  function cutChute(landed) {
    if (!pet.chuteOpen) return;
    pet.chuteOpen = false;
    pet.chuteCut = 0.9;
    if (landed) {
      spawn('dust', pet.x, groundY - 4, 5, { spread: petR() * 0.7, vx: 55, vy: -20, g: -10, size: 8, dur: 0.7 });
      if (Math.random() < 0.7) say(pick(LINES.landed), 2200);
    }
  }

  // ---------------------------------------------------------------- flight
""")

# ---------------------------------------------------------------- timers + physics
patch("    pet.knee = lerp(pet.knee, 0, Math.min(1, dt * 6));\n    if (pet.working && pet.workT <= 0) pet.working = false;",
      "    pet.knee = lerp(pet.knee, 0, Math.min(1, dt * 6));\n"
      "    pet.chuteCut = Math.max(0, pet.chuteCut - dt);\n"
      "    pet.chute = clamp(pet.chute + (pet.chuteOpen ? dt * 4 : -dt * 5), 0, 1);\n"
      "    if (pet.chuteOpen) pet.chuteSway += dt * (1.6 + 0.5 * Math.sin(pet.t * 0.7));\n"
      "    if (pet.working && pet.workT <= 0) pet.working = false;")
patch("""        } else if (DESKTOP) {
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
        }""", """        } else if (DESKTOP) {
          // The host moves the window while thrown; only the tumble is simulated here.
          if (pet.thrown && !pet.chuteOpen) pet.spin += pet.spinV * dt;
        } else {
          if (!pet.chuteOpen && pet.vy > 620 && groundY - pet.y > groundY * 0.28) openChute();
          if (pet.chuteOpen) {
            pet.vy = lerp(pet.vy, 150, Math.min(1, dt * 3));
            pet.vx = lerp(pet.vx, Math.sin(pet.chuteSway) * 70, Math.min(1, dt * 2));
          } else {
            pet.vy += 2400 * dt;
            if (pet.thrown) pet.spin += pet.spinV * dt;
          }
          pet.y += pet.vy * dt;
          pet.x += pet.vx * dt;
          if (pet.y >= groundY) {
            pet.y = groundY; pet.grounded = true;
            const chuted = pet.chuteOpen;
            cutChute(true);
            land(chuted ? 200 : pet.vy); pet.vy = 0; pet.vx *= 0.4;
            pet.ax = clamp(pet.x, r, W - r);
          }
        }""")
patch("    pet.spin = 0; pet.spinV = 0; pet.thrown = false;\n    pet.mode = 'ground'; pet.landing = false; pet.thrust = 0;",
      "    pet.spin = 0; pet.spinV = 0; pet.thrown = false;\n    cutChute(false);\n    pet.mode = 'ground'; pet.landing = false; pet.thrust = 0;")
patch("      case 'thrown':\n        pet.mode = 'ground'; pet.landing = false; pet.grounded = false; pet.thrown = true; pet.thrust = 0;\n        pet.spinV = rand(-5, 5);\n        break;",
      "      case 'thrown':\n        pet.mode = 'ground'; pet.landing = false; pet.grounded = false; pet.thrown = true; pet.thrust = 0;\n        pet.spinV = rand(-5, 5);\n        break;\n"
      "      case 'chute':\n        openChute();\n        break;\n"
      "      case 'chute-cut':\n        cutChute(true);\n        break;")
patch("  function grab() {\n    pet.held = true;\n    pet.grounded = false;",
      "  function grab() {\n    cutChute(false);\n    pet.held = true;\n    pet.grounded = false;")

# ---------------------------------------------------------------- drawing
patch("""    let lean = 0;
    if (pet.thrown) lean = pet.spin;""", """    let lean = 0;
    if (pet.chuteOpen || pet.chute > 0.05) lean = Math.sin(pet.chuteSway) * 0.16;
    else if (pet.thrown) lean = pet.spin;""")
patch("""    if (pet.thrust > 0.05 && !asleep) {""", """    const chute = pet.chute;
    if (chute > 0.02) {
      // Canopy above, cords down to the hands: drawn first so the robot sits in front.
      const open = chute * chute * (3 - 2 * chute);
      const cw = r * 2.2 * open, ch = r * 1.1 * open;
      const cy = -r * 3.05 - r * 1.5 * open;
      const flap = Math.sin(t * 3) * r * 0.05 * open;
      ctx.save();
      ctx.globalAlpha = clamp(chute, 0, 1);
      ctx.strokeStyle = `hsl(${hue}, 20%, 45%)`;
      ctx.lineWidth = Math.max(1, r * 0.03);
      for (const cx of [-r * 0.62, -r * 0.2, r * 0.2, r * 0.62]) {
        ctx.beginPath();
        ctx.moveTo(cx * open, cy + ch * 0.55);
        ctx.lineTo(Math.sign(cx) * r * 0.85, -r * 1.85);
        ctx.stroke();
      }
      const panels = ['hsl(8, 78%, 62%)', 'hsl(38, 88%, 62%)', 'hsl(190, 70%, 58%)', 'hsl(150, 55%, 55%)'];
      for (let i = 0; i < 4; i++) {
        const x0 = -cw / 2 + (cw / 4) * i, x1 = x0 + cw / 4;
        ctx.fillStyle = panels[i];
        ctx.beginPath();
        ctx.moveTo(x0, cy + ch * 0.5);
        ctx.quadraticCurveTo((x0 + x1) / 2, cy - ch * 0.95 - flap, x1, cy + ch * 0.5);
        ctx.quadraticCurveTo((x0 + x1) / 2, cy + ch * 0.66 + flap, x0, cy + ch * 0.5);
        ctx.closePath();
        ctx.fill();
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.55)';
      ctx.lineWidth = Math.max(1, r * 0.035);
      ctx.beginPath();
      ctx.moveTo(-cw / 2, cy + ch * 0.5);
      ctx.quadraticCurveTo(0, cy - ch * 1.0 - flap, cw / 2, cy + ch * 0.5);
      ctx.stroke();
      ctx.restore();
    }
    if (pet.chuteCut > 0) {
      ctx.save();
      ctx.globalAlpha = pet.chuteCut / 0.9;
      ctx.fillStyle = 'hsl(38, 70%, 62%)';
      ctx.beginPath();
      ctx.ellipse(pet.facing * r * 0.5, -r * 0.35, r * 0.5 * (1 - pet.chuteCut / 0.9) + r * 0.2, r * 0.16, 0.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
    if (pet.thrust > 0.05 && !asleep) {""")
patch("      if (flying) { footY -= r * 0.3; footX = sgn * r * 0.3; }\n      if (carried || pet.thrown) footY += r * 0.12 + Math.sin(t * 5 + sgn) * r * 0.08;",
      "      if (flying) { footY -= r * 0.3; footX = sgn * r * 0.3; }\n"
      "      if (pet.chuteOpen) { footY += r * 0.18; footX = sgn * r * 0.34 + Math.sin(t * 3 + sgn * 1.5) * r * 0.16; }\n"
      "      else if (carried || pet.thrown) footY += r * 0.12 + Math.sin(t * 5 + sgn) * r * 0.08;")
patch("      if (carried) theta = 2.9;\n      else if (pet.thrown) theta = 1.6 + Math.sin(t * 9 + sgn) * 0.6;",
      "      if (pet.chuteOpen) theta = 2.75;\n      else if (carried) theta = 2.9;\n      else if (pet.thrown) theta = 1.6 + Math.sin(t * 9 + sgn) * 0.6;")

SRC.write_text(s, encoding="utf-8")
print("patched", SRC)
