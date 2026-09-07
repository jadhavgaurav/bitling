#!/usr/bin/env python3
"""One-off migration: stop everything clipping at the edges of the pet's window.

Three fixes:

1. Speech bubbles were positioned from the pet's centre and clamped to a fixed 70px
   inset, so a long line ran off the left or right edge, and a wrapped line ran off
   the top. They are now clamped by their own measured size, and the tail slides
   along the bubble so it still points at the pet.
2. The pet was kept inside the window by its body radius, which ignores the ear caps
   of the grown stages and the parafoil, both of which are wider than the body. It is
   now clamped by its actual drawn half-width.
3. Beetles were clamped by their centre, so the antenna and legs of one at the far
   right poked past the edge.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "web" / "bitling.html"
s = SRC.read_text(encoding="utf-8")
if "function petHalfWidth" in s:
    raise SystemExit("already applied")


def patch(old: str, new: str) -> None:
    global s
    if s.count(old) != 1:
        raise SystemExit(f"anchor found {s.count(old)}x, expected 1:\n{old[:150]}")
    s = s.replace(old, new)


# ---------------------------------------------------------------- 1. bubble tail follows the pet
patch('  .bubble::after{content:"";position:absolute;left:50%;bottom:-6px;width:12px;height:12px;background:var(--bubble);transform:translateX(-50%) rotate(45deg);border-radius:2px}',
      '  .bubble::after{content:"";position:absolute;left:var(--tail,50%);bottom:-6px;width:12px;height:12px;background:var(--bubble);transform:translateX(-50%) rotate(45deg);border-radius:2px}')

# ---------------------------------------------------------------- 2. keep the bubble fully on screen
patch("""      bubble.style.left = `${Math.round(clamp(pet.x, 70, W - 70))}px`;
      bubble.style.top = `${Math.round(Math.max(60, top))}px`;""",
      """      // Clamp by the bubble's own measured box so long or wrapped lines cannot run off
      // any edge, then slide the tail along it so it still points at the pet.
      const bw = bubble.offsetWidth, bh = bubble.offsetHeight;
      const half = bw / 2;
      const cx = W > bw + 12 ? clamp(pet.x, half + 6, W - half - 6) : W / 2;
      const cy = Math.max(bh + 6, top);
      bubble.style.left = `${Math.round(cx)}px`;
      bubble.style.top = `${Math.round(cy)}px`;
      bubble.style.setProperty('--tail', `${Math.round(clamp(pet.x - (cx - half), 14, Math.max(14, bw - 14)))}px`);""")

# ---------------------------------------------------------------- 3. clamp the pet by what is actually drawn
patch("""  const petR = () => [46, 46, 58, 68][stageOf(state)] * scale;""",
      """  const petR = () => [46, 46, 58, 68][stageOf(state)] * scale;
  // How far the drawing actually reaches sideways from pet.x: the head and its ear caps
  // are wider than the body, and an open parafoil is wider still.
  function petHalfWidth() {
    const r = petR();
    const body = r * (stageOf(state) >= 2 ? 1.18 : 1.06);
    return pet.chute > 0.02 ? Math.max(body, r * 1.72) : body;
  }""")

for old, new in [
    ("    pet.ax = clamp(pet.ax * ratio, petR(), W - petR());\n    pet.x = clamp(pet.x * ratio, petR(), W - petR());",
     "    pet.ax = clamp(pet.ax * ratio, petHalfWidth(), W - petHalfWidth());\n    pet.x = clamp(pet.x * ratio, petHalfWidth(), W - petHalfWidth());"),
    ("      pet.x = clamp(pet.x, r, W - r);\n\n      if (pet.walkDir) pet.facing = pet.walkDir;",
     "      pet.x = clamp(pet.x, petHalfWidth(), W - petHalfWidth());\n\n      if (pet.walkDir) pet.facing = pet.walkDir;"),
    ("    pet.ax = clamp(best.x, r, W - r);", "    pet.ax = clamp(best.x, petHalfWidth(), W - petHalfWidth());"),
    ("      else pet.ax = clamp(W / 2 + rand(-W * 0.3, W * 0.3), petR(), W - petR());",
     "      else pet.ax = clamp(W / 2 + rand(-W * 0.3, W * 0.3), petHalfWidth(), W - petHalfWidth());"),
]:
    patch(old, new)

# release() and the landing paths clamp the anchor too
s = s.replace("    pet.ax = clamp(pet.x, r, W - r);", "    pet.ax = clamp(pet.x, petHalfWidth(), W - petHalfWidth());")
s = s.replace("    pet.ax = clamp(pet.x, petR(), W - petR());", "    pet.ax = clamp(pet.x, petHalfWidth(), W - petHalfWidth());")
s = s.replace("            pet.ax = clamp(pet.x, r, W - r);", "            pet.ax = clamp(pet.x, petHalfWidth(), W - petHalfWidth());")

# ---------------------------------------------------------------- 4. beetles keep their whole body inside
patch("""      if (b.x < 12) { b.x = 12; b.vx = Math.abs(b.vx); }
      if (b.x > W - 12) { b.x = W - 12; b.vx = -Math.abs(b.vx); }""",
      """      const edge = 18 * scale;
      if (b.x < edge) { b.x = edge; b.vx = Math.abs(b.vx); }
      if (b.x > W - edge) { b.x = W - edge; b.vx = -Math.abs(b.vx); }""")
patch("    bugs.push({ x: clamp(bx, 12, W - 12),", "    bugs.push({ x: clamp(bx, 18 * scale, W - 18 * scale),")

SRC.write_text(s, encoding="utf-8")
print("clipping fixes applied")
