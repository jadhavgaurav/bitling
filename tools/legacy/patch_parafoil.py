#!/usr/bin/env python3
"""One-off migration: dome parachute -> ram-air parafoil.

The first canopy was four fat quadratic lobes in candy colours, which read as
scoops of ice cream. This replaces it with a cell wing: a shallow arched band
divided into seven cells, open cell mouths along the leading edge, rib seams and
suspension lines cascading into two risers at the shoulders, in the robot's own
palette with one teal accent.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "web" / "bitling.html"
s = SRC.read_text(encoding="utf-8")
if "ram-air parafoil" in s.lower():
    raise SystemExit("already applied")


def patch(old: str, new: str) -> None:
    global s
    if s.count(old) != 1:
        raise SystemExit(f"anchor found {s.count(old)}x, expected 1:\n{old[:160]}")
    s = s.replace(old, new)


patch("""    const chute = pet.chute;
    if (chute > 0.02) {
      // Canopy above, cords down to the hands: drawn first so the robot sits in front.
      const open = chute * chute * (3 - 2 * chute);
      const cw = r * 2.5 * open, ch = r * 0.95 * open;
      const cy = -r * 3.3 - r * 0.5 * open;
      const flap = Math.sin(t * 3) * r * 0.05 * open;
      ctx.save();
      ctx.globalAlpha = clamp(chute, 0, 1);
      ctx.strokeStyle = `hsl(${hue}, 20%, 45%)`;
      ctx.lineWidth = Math.max(1, r * 0.03);
      for (const cx of [-r * 0.62, -r * 0.2, r * 0.2, r * 0.62]) {
        ctx.beginPath();
        ctx.moveTo(cx * open, cy + ch * 0.55);
        ctx.lineTo(Math.sign(cx) * r * 0.85, -r * 2.0);
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
    }""", """    const chute = pet.chute;
    if (chute > 0.02) {
      // Ram-air parafoil: a shallow cell wing, drawn first so the robot hangs in front of it.
      const open = chute * chute * (3 - 2 * chute);
      const CELLS = 7, STEPS = 36;
      const span = r * 3.2 * open;
      const arch = r * 0.66 * open;
      const depth = r * 0.46 * open;
      const cy = -r * 3.5 - r * 0.3 * open;
      const billow = Math.sin(t * 2.6) * r * 0.03 * open;
      const xAt = (u) => (span / 2) * u;
      const yTop = (u) => cy - (arch + billow) * (1 - u * u);
      const yBot = (u) => yTop(u) + depth + Math.abs(u) * r * 0.07;
      const edge = `hsl(${hue}, 24%, 44%)`;

      ctx.save();
      ctx.globalAlpha = clamp(chute, 0, 1);
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';

      // Suspension lines cascade from every rib into two risers at the shoulders.
      ctx.strokeStyle = `hsla(${hue}, 25%, 38%, 0.7)`;
      ctx.lineWidth = Math.max(0.6, r * 0.016);
      for (let i = 0; i <= CELLS; i++) {
        const u = -1 + (2 * i) / CELLS;
        ctx.beginPath();
        ctx.moveTo(xAt(u), yBot(u));
        ctx.lineTo((u < 0 ? -1 : 1) * r * 0.6, -r * 2.05);
        ctx.stroke();
      }

      const outlinePath = () => {
        ctx.beginPath();
        ctx.moveTo(xAt(-1), yTop(-1));
        for (let i = 1; i <= STEPS; i++) { const u = -1 + (2 * i) / STEPS; ctx.lineTo(xAt(u), yTop(u)); }
        for (let i = STEPS; i >= 0; i--) { const u = -1 + (2 * i) / STEPS; ctx.lineTo(xAt(u), yBot(u)); }
        ctx.closePath();
      };

      // Alternating cells, clipped to the wing silhouette.
      ctx.save();
      outlinePath();
      ctx.clip();
      for (let i = 0; i < CELLS; i++) {
        const u0 = -1 + (2 * i) / CELLS, u1 = -1 + (2 * (i + 1)) / CELLS;
        ctx.fillStyle = i % 2 ? `hsl(${hue}, 30%, 92%)` : 'hsl(176, 58%, 54%)';
        ctx.beginPath();
        ctx.moveTo(xAt(u0), yTop(u0) - r);
        ctx.lineTo(xAt(u1), yTop(u1) - r);
        ctx.lineTo(xAt(u1), yBot(u1) + r);
        ctx.lineTo(xAt(u0), yBot(u0) + r);
        ctx.closePath();
        ctx.fill();
      }
      // Open cell mouths along the leading edge.
      ctx.fillStyle = 'rgba(18,22,46,0.5)';
      for (let i = 0; i < CELLS; i++) {
        const u = -1 + (2 * i + 1) / CELLS;
        const w = (span / CELLS) * 0.44, h = depth * 0.3;
        roundRect(xAt(u) - w / 2, yBot(u) - h - depth * 0.1, w, h, h * 0.5);
        ctx.fill();
      }
      ctx.restore();

      // Rib seams, then the silhouette.
      ctx.strokeStyle = `hsla(${hue}, 24%, 42%, 0.5)`;
      ctx.lineWidth = Math.max(0.7, r * 0.018);
      for (let i = 1; i < CELLS; i++) {
        const u = -1 + (2 * i) / CELLS;
        ctx.beginPath(); ctx.moveTo(xAt(u), yTop(u)); ctx.lineTo(xAt(u), yBot(u)); ctx.stroke();
      }
      ctx.strokeStyle = edge;
      ctx.lineWidth = Math.max(1, r * 0.03);
      outlinePath();
      ctx.stroke();
      ctx.restore();
    }
    if (pet.chuteCut > 0) {
      // Cut away: the wing bundles up and tumbles off over the shoulder.
      const k = pet.chuteCut / 0.9;
      ctx.save();
      ctx.globalAlpha = k;
      ctx.translate(pet.facing * (r * 0.5 + r * 1.1 * (1 - k)), -r * 2.4 - r * 0.5 * (1 - k));
      ctx.rotate((1 - k) * pet.facing * 2.2);
      ctx.fillStyle = 'hsl(176, 58%, 54%)';
      roundRect(-r * 0.26, -r * 0.15, r * 0.52, r * 0.3, r * 0.12);
      ctx.fill();
      ctx.strokeStyle = `hsla(${hue}, 24%, 40%, 0.85)`;
      ctx.lineWidth = Math.max(0.7, r * 0.02);
      ctx.beginPath();
      ctx.moveTo(-r * 0.1, r * 0.15);
      ctx.quadraticCurveTo(-r * 0.3, r * 0.45, -pet.facing * r * 0.45, r * 0.6);
      ctx.stroke();
      ctx.restore();
    }""")

SRC.write_text(s, encoding="utf-8")
print("patched", SRC)
