import base64
from pathlib import Path
from PIL import Image

def get_b64_resized(img_path, target_height):
    im = Image.open(img_path).convert("RGBA")
    w, h = im.size
    aspect = w / h
    target_width = int(round(target_height * aspect))
    resized = im.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    temp_path = img_path.parent / f"temp_{img_path.name}"
    resized.save(temp_path, format="PNG", optimize=True)
    with open(temp_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    temp_path.unlink()
    print(f"{img_path.name}: {im.size} -> {resized.size}, b64 len {len(data)}")
    return data, resized.size

def main():
    adir = Path("/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758")
    
    idle_b64, idle_size = get_b64_resized(adir / "pikachu_pristine_idle.png", 86)
    charge_b64, charge_size = get_b64_resized(adir / "pikachu_pristine_charge.png", 82)
    run_b64, run_size = get_b64_resized(adir / "pikachu_pristine_run.png", 54)
    dangle_b64, dangle_size = get_b64_resized(adir / "pikachu_pristine_dangle.png", 86)

    bitling_path = Path("web/bitling.html")
    content = bitling_path.read_text(encoding="utf-8")

    # 1. Add Pikachu audio methods to audio object
    # Find audio methods right after kiBlast()
    kiblast_needle = "    kiBlast() {\n      this.tone(1100, 320, 0.14, 'sawtooth', 0.06);\n      setTimeout(() => this.tone(480, 140, 0.1, 'sine', 0.04), 40);\n    },"
    
    pikachu_audio = """    kiBlast() {
      this.tone(1100, 320, 0.14, 'sawtooth', 0.06);
      setTimeout(() => this.tone(480, 140, 0.1, 'sine', 0.04), 40);
    },
    pikaPika() {
      this.tone(920, 1280, 0.09, 'triangle', 0.12);
      setTimeout(() => this.tone(1180, 780, 0.11, 'sine', 0.10), 95);
      setTimeout(() => this.tone(960, 1320, 0.09, 'triangle', 0.12), 230);
      setTimeout(() => this.tone(1220, 820, 0.13, 'sine', 0.10), 330);
    },
    pikaChuuu() {
      this.tone(860, 1180, 0.13, 'triangle', 0.12);
      setTimeout(() => this.tone(1000, 1450, 0.19, 'sine', 0.13), 150);
      setTimeout(() => {
        this.tone(1720, 560, 0.40, 'sawtooth', 0.14);
        this.tone(1220, 400, 0.42, 'triangle', 0.11);
      }, 370);
      setTimeout(() => this.thunderbolt(), 690);
    },
    pikaChu() {
      this.tone(920, 1220, 0.09, 'triangle', 0.12);
      setTimeout(() => this.tone(1120, 1380, 0.08, 'sine', 0.11), 100);
      setTimeout(() => this.tone(1380, 680, 0.16, 'sawtooth', 0.09), 190);
    },
    pikaQuestion() {
      this.tone(850, 1420, 0.18, 'triangle', 0.11);
    },
    electroBall() {
      this.tone(1450, 340, 0.16, 'sawtooth', 0.08);
      setTimeout(() => this.tone(580, 190, 0.12, 'square', 0.05), 50);
      setTimeout(() => this.tone(940, 360, 0.10, 'triangle', 0.06), 110);
    },
    thunderbolt() {
      this.tone(1650, 480, 0.24, 'sawtooth', 0.10);
      setTimeout(() => this.tone(920, 130, 0.30, 'square', 0.08), 40);
      setTimeout(() => this.tone(150, 35, 0.58, 'triangle', 0.15), 90);
      setTimeout(() => this.tone(95, 25, 0.72, 'sine', 0.16), 190);
    },"""

    if "pikaPika()" not in content:
        assert kiblast_needle in content, "kiblast_needle not found in bitling.html"
        content = content.replace(kiblast_needle, pikachu_audio, 1)
        print("Added Pikachu audio methods!")

    # 2. Add SPECIES.pikachu definition right before kaiju
    kaiju_needle = "  defineSpecies({\n    id: 'kaiju', name: 'Rumble', kind: 'ground',"
    
    pikachu_species = """  defineSpecies({
    id: 'pikachu', name: 'Pikachu', kind: 'ground',
    blurb: 'The iconic Electric Mouse Pokémon. Charges electricity in rosy-red cheek pouches, flings crackling Electro Balls at small bugs, and summons 100,000-Volt Thunderbolts on boss bugs!',
    accent: '#ffdd00',
    radius: [44, 40, 48, 56],
    reach: () => 3.2,
    half: (r) => r * 1.55,
    draw: () => drawPikachu(),
    attack: {
      style: 'thunderbolt',
      behind: false,
      charge: 0.95,
      resolve(isBoss) {
        if (isBoss) {
          return { style: 'thunderbolt', charge: 0.95, sound: 'pikaChuuu' };
        }
        return { style: 'electroball', charge: 0.24, sound: 'pikaPika' };
      },
      origin: (r) => [{ x: Math.round(pet.x + pet.facing * r * 0.55), y: Math.round(pet.y - r * 1.1) }],
      draw(r, k, isBoss, style) {
        const ox = pet.x + pet.facing * r * 0.55, oy = pet.y - r * 1.1;
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';

        if (style === 'thunderbolt' || isBoss) {
          // ------------------------------------------------ 100,000-Volt Sky Lightning Strike
          const targetX = pet.zapX, targetY = pet.zapY;
          // Core lightning bolt from sky (y=0) to target
          const boltWidth = Math.max(3.5, r * (0.16 + k * 0.12));
          
          // Outer electric glow
          ctx.strokeStyle = `hsla(55, 100%, 72%, ${0.95 * k})`;
          ctx.lineWidth = boltWidth * 2.8;
          ctx.beginPath();
          ctx.moveTo(targetX, 0);
          // Zig-zag lightning path
          const segs = 7;
          for (let s = 1; s <= segs; s++) {
            const py = (targetY / segs) * s;
            const xOff = (s === segs) ? 0 : Math.sin(s * 3.7 + pet.t * 30) * r * 0.35;
            ctx.lineTo(targetX + xOff, py);
          }
          ctx.stroke();

          // Inner pure white electric core
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = boltWidth;
          ctx.beginPath();
          ctx.moveTo(targetX, 0);
          for (let s = 1; s <= segs; s++) {
            const py = (targetY / segs) * s;
            const xOff = (s === segs) ? 0 : Math.sin(s * 3.7 + pet.t * 30) * r * 0.35;
            ctx.lineTo(targetX + xOff, py);
          }
          ctx.stroke();

          // Ground electric impact shockwave
          const impactR = r * (0.8 + k * 1.4);
          const radGrad = ctx.createRadialGradient(targetX, targetY, 3, targetX, targetY, impactR);
          radGrad.addColorStop(0, '#ffffff');
          radGrad.addColorStop(0.3, 'rgba(255, 240, 60, 0.9)');
          radGrad.addColorStop(0.7, 'rgba(255, 180, 0, 0.5)');
          radGrad.addColorStop(1, 'rgba(255, 180, 0, 0)');
          ctx.fillStyle = radGrad;
          ctx.beginPath();
          ctx.ellipse(targetX, targetY, impactR * 1.3, impactR * 0.6, 0, 0, Math.PI * 2);
          ctx.fill();

          // Radial electric arcs dancing on floor
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2;
          for (let a = 0; a < 6; a++) {
            const ang = (a / 6) * Math.PI * 2;
            const dist = impactR * (0.5 + Math.sin(pet.t * 20 + a) * 0.35);
            ctx.beginPath();
            ctx.moveTo(targetX, targetY);
            ctx.lineTo(targetX + Math.cos(ang) * dist, targetY + Math.sin(ang) * dist * 0.5);
            ctx.stroke();
          }

        } else {
          // ------------------------------------------------ Crackling Electro Ball for Small Bugs
          const len = Math.hypot(pet.zapX - ox, pet.zapY - oy);
          const ang = Math.atan2(pet.zapY - oy, pet.zapX - ox);
          ctx.translate(ox, oy);
          ctx.rotate(ang);

          // Fast plasma beam trail to bug
          ctx.strokeStyle = `hsla(52, 100%, 75%, ${0.9 * k})`;
          ctx.lineWidth = Math.max(2, r * 0.1);
          ctx.beginPath();
          ctx.moveTo(0, 0);
          ctx.lineTo(len, 0);
          ctx.stroke();

          // Traveling electric spark plasma ball
          const ballR = r * (0.28 + Math.sin(pet.t * 35) * 0.06);
          const bg = ctx.createRadialGradient(len, 0, 2, len, 0, ballR);
          bg.addColorStop(0, '#ffffff');
          bg.addColorStop(0.4, 'rgba(255, 235, 60, 0.95)');
          bg.addColorStop(0.8, 'rgba(255, 160, 0, 0.5)');
          bg.addColorStop(1, 'rgba(255, 160, 0, 0)');
          ctx.fillStyle = bg;
          ctx.beginPath();
          ctx.arc(len, 0, ballR, 0, Math.PI * 2);
          ctx.fill();

          // Spark crackles around ball
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.6;
          for (let i = 0; i < 4; i++) {
            const spAng = (i / 4) * Math.PI * 2 + pet.t * 15;
            const dist = ballR * 1.3;
            ctx.beginPath();
            ctx.moveTo(len, 0);
            ctx.lineTo(len + Math.cos(spAng) * dist, Math.sin(spAng) * dist);
            ctx.stroke();
          }
        }
        ctx.restore();
      }
    },
    voice: {
      hello: ['Pika-pika!', 'Pikachu!', 'Pika?'],
      happy: ['Pikachu!!', 'Pika-chuu!', 'Pika! (wagging tail)', 'Pi-ka!'],
      hungry: ['Pika... (hungry)', 'Chuuu...', 'Pika pika berry!'],
      sleepy: ['Chuuu... (yawn)', 'Pika... zzz', 'curling into tail'],
      bored: ['Pika? (ear twitch)', 'Chuu...', 'sparking cheeks quietly'],
      petted: ['Pikaaa! (blushing)', 'Chuuu~', 'Pika-pi! (happy wiggles)'],
      eat: ['Chomp! Pika!', 'munch munch', 'delish! Pika!'],
      zapped: ['Pika-CHUUU! 100,000 Volts!', 'Zapped! Pika!', 'Bug fainted!'],
      play: ['Pika-pika! (running in circles)', 'Catch me! Pika!', 'Cheeks sparking!'],
      working: ['Pika... (charging electric focus)', 'Chuuu...', 'steady sparks'],
      done: ['Pikachu!!', 'All bugs fainted!', 'Build cleared, Pika!'],
      testFail: ['Pika?! Failing tests!', 'Cheeks glowing red!', 'Pika... CHUU!'],
      testPass: ['Pikachu!! All green!', 'Pika-pika green build!'],
      shipped: ['Pika-CHUUU! Deployed to the stars!', 'Rocket away, Pika!'],
      held: ['Pikaaa! Put me down!', 'Watch the tail! Pika!', 'Static tingling!'],
      landed: ['Pika! Landed on four paws!', 'Pikachu! Safe on the ground.'],
      night: ['Pika... (tail glowing gently)', 'quiet night in Kanto', 'sweet dreams, Pika'],
    },
  });

  defineSpecies({
    id: 'kaiju', name: 'Rumble', kind: 'ground',"""

    if "id: 'pikachu'" not in content:
        assert kaiju_needle in content, "kaiju_needle not found"
        content = content.replace(kaiju_needle, pikachu_species, 1)
        print("Added SPECIES.pikachu!")

    # 3. Add drawPikachu implementation right before drawKaiju
    draw_kaiju_needle = "  function drawKaiju() {"
    
    draw_pikachu = f'''  // ---------------------------------------------------------------- Pikachu, the Electric Mouse Pokémon
  const PIKACHU_SPRITES = {{
    idle: 'data:image/png;base64,{idle_b64}',
    charge: 'data:image/png;base64,{charge_b64}',
    run: 'data:image/png;base64,{run_b64}',
    dangle: 'data:image/png;base64,{dangle_b64}'
  }};

  const pikaImgIdle = new Image(); pikaImgIdle.src = PIKACHU_SPRITES.idle;
  const pikaImgCharge = new Image(); pikaImgCharge.src = PIKACHU_SPRITES.charge;
  const pikaImgRun = new Image(); pikaImgRun.src = PIKACHU_SPRITES.run;
  const pikaImgDangle = new Image(); pikaImgDangle.src = PIKACHU_SPRITES.dangle;

  function drawPikachu() {{
    const asleep = state.asleep;
    const charging = pet.zapCharge > 0 && !asleep;
    const firing = pet.zap > 0;
    const isBoss = pet.zapBoss || false;
    const isCarried = !!(pet.carried || pet.held);
    const vx = (pet.held ? pet.vx : (pet.dragVx || 0));
    const vy = (pet.held ? pet.vy : (pet.dragVy || 0));
    const rawSpeed = Math.hypot(vx, vy) || (pet.dragSpeed || 0);

    // Exponential smoothing on velocity
    pet.pikaSpeed = (pet.pikaSpeed || 0) * 0.84 + rawSpeed * 0.16;

    // Face drag direction
    if (isCarried && Math.abs(vx) > 12) {{
      pet.facing = vx < 0 ? -1 : 1;
    }}
    const f = pet.facing || 1;

    // Select sprite pose based on state
    let sprite = pikaImgIdle;
    let baseRefW = 78;
    let yAlign = 0.92;

    if (isCarried) {{
      sprite = pikaImgDangle;
      baseRefW = 44;
      yAlign = 0.88;
    }} else if (charging || firing) {{
      sprite = pikaImgCharge;
      baseRefW = 84;
      yAlign = 0.90;
    }} else if (pet.walking) {{
      sprite = pikaImgRun;
      baseRefW = 80;
      yAlign = 0.88;
    }}

    stageBody({{ shadow: !isCarried, bob: isCarried ? 0.02 : (pet.walking ? 0.08 : 0.04), bobRate: pet.walking ? 9 : 2.5, sway: isCarried ? 0 : 0.02 }}, (r, t) => {{
      ctx.save();

      // Neutralize squash/stretch deformation so pixel art stays pristine
      const sx = (1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6);
      const sy = (1 + pet.sq) * (1 + pet.stretch);
      if (Math.abs(sx) > 0.05 && Math.abs(sy) > 0.05) {{
        ctx.scale(1 / sx, 1 / sy);
      }}

      // Flip for facing direction
      ctx.scale(f, 1);

      // -------------------------------------------------------- Dynamic Electrical Cheek Sparking Aura
      if (charging || firing) {{
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const auraR = r * (isBoss ? 1.9 : 1.35);
        const glow = ctx.createRadialGradient(r * 0.25, -r * 0.65, r * 0.1, r * 0.25, -r * 0.65, auraR);
        glow.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
        glow.addColorStop(0.3, 'rgba(255, 235, 60, 0.55)');
        glow.addColorStop(0.7, 'rgba(255, 170, 0, 0.2)');
        glow.addColorStop(1, 'rgba(255, 170, 0, 0)');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(r * 0.25, -r * 0.65, auraR, 0, Math.PI * 2);
        ctx.fill();

        // Dancing electric sparks & lightning tendrils around body
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = Math.max(1.5, r * 0.05);
        const numArcs = isBoss ? 7 : 4;
        for (let i = 0; i < numArcs; i++) {{
          const ang = (i / numArcs) * Math.PI * 2 + Math.sin(t * 25 + i) * 0.4;
          const d1 = r * (0.45 + Math.sin(t * 18 + i) * 0.2);
          const d2 = auraR * 0.85;
          ctx.beginPath();
          ctx.moveTo(r * 0.2 + Math.cos(ang) * d1, -r * 0.6 + Math.sin(ang) * d1);
          ctx.lineTo(r * 0.2 + Math.cos(ang + 0.3) * (d1 + d2) * 0.5, -r * 0.6 + Math.sin(ang + 0.3) * (d1 + d2) * 0.5);
          ctx.lineTo(r * 0.2 + Math.cos(ang) * d2, -r * 0.6 + Math.sin(ang) * d2);
          ctx.stroke();
        }}
        ctx.restore();
      }}

      // -------------------------------------------------------- Cute Static Sparks while Carried
      if (isCarried) {{
        ctx.save();
        ctx.fillStyle = 'rgba(255, 240, 80, 0.85)';
        for (let s = 0; s < 3; s++) {{
          const spPhase = (t * 5 + s * 1.1) % 1;
          const spX = r * (0.35 + Math.sin(s * 2.5 + t * 8) * 0.3);
          const spY = -r * (0.8 + spPhase * 0.6);
          ctx.beginPath();
          ctx.arc(spX, spY, r * (0.05 + (1 - spPhase) * 0.04), 0, Math.PI * 2);
          ctx.fill();
        }}
        ctx.restore();
      }}

      // -------------------------------------------------------- Sprite Rendering
      if (sprite && sprite.complete && sprite.naturalWidth > 0) {{
        ctx.save();
        ctx.imageSmoothingEnabled = false; // crisp pixel art
        const sw = sprite.naturalWidth;
        const sh = sprite.naturalHeight;
        const drawScale = (r * 2.35) / baseRefW;
        const dw = sw * drawScale;
        const dh = sh * drawScale;
        ctx.drawImage(sprite, -dw / 2, -dh * yAlign, dw, dh);
        ctx.restore();
      }} else {{
        // Vector fallback
        ctx.fillStyle = '#ffdd00';
        ctx.beginPath();
        ctx.arc(0, -r * 0.8, r * 0.75, 0, Math.PI * 2);
        ctx.fill();
        // Red cheeks
        ctx.fillStyle = '#ff3333';
        ctx.beginPath();
        ctx.arc(r * 0.45, -r * 0.7, r * 0.18, 0, Math.PI * 2);
        ctx.arc(-r * 0.45, -r * 0.7, r * 0.18, 0, Math.PI * 2);
        ctx.fill();
      }}

      // -------------------------------------------------------- Berry / Snack Eating Overlay
      if (pet.chew > 0 && !isCarried) {{
        ctx.save();
        ctx.translate(r * 0.25, -r * 0.55);
        ctx.rotate(0.12 + Math.sin(t * 14) * 0.1);

        // Oran Berry (blue berry with green leaves)
        ctx.fillStyle = '#2980b9';
        ctx.beginPath();
        ctx.arc(0, 0, r * 0.18, 0, Math.PI * 2);
        ctx.fill();
        // Berry leaves
        ctx.fillStyle = '#27ae60';
        ctx.beginPath();
        ctx.ellipse(0, -r * 0.16, r * 0.08, r * 0.05, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }}

      // -------------------------------------------------------- Sleeping Zzz
      if (asleep) {{
        ctx.save();
        ctx.fillStyle = '#ffffff';
        ctx.font = `bold ${{Math.max(10, r * 0.38)}}px sans-serif`;
        const zOff = (t * 0.8) % 1;
        ctx.globalAlpha = 1 - zOff;
        ctx.fillText('Z', r * 0.35 + zOff * 10, -r * 1.3 - zOff * 18);
        ctx.fillText('z', r * 0.55 + zOff * 10, -r * 1.5 - zOff * 22);
        ctx.restore();
      }}

      ctx.restore();
    }});
  }}

  function drawKaiju() {{'''

    if "function drawPikachu()" not in content:
        assert draw_kaiju_needle in content, "draw_kaiju_needle not found"
        content = content.replace(draw_kaiju_needle, draw_pikachu, 1)
        print("Added drawPikachu implementation!")

    bitling_path.write_text(content, encoding="utf-8")
    print(f"Updated {bitling_path} successfully! New length: {len(content)}")

if __name__ == "__main__":
    main()
