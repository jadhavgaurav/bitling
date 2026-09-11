#!/usr/bin/env python3
import json

with open("/tmp/spiderman_poses/spiderman_all_poses_b64.json", "r") as f:
    sprites = json.load(f)

with open("web/bitling.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add audio synthesizers to `audio` object
audio_anchor = "    thorStormbreaker() {\n"
audio_idx = content.find(audio_anchor)
assert audio_idx != -1, "thorStormbreaker not found in bitling.html"
storm_end = content.find("    },\n", audio_idx)
assert storm_end != -1, "end of thorStormbreaker not found"

spiderman_audio = """
    spideyThwip() {
      this.tone(1900, 600, 0.08, 'sawtooth', 0.12);
      setTimeout(() => this.tone(950, 260, 0.09, 'triangle', 0.14), 25);
    },
    spideyZip() {
      this.tone(480, 1300, 0.18, 'sine', 0.08);
      setTimeout(() => this.tone(1300, 680, 0.14, 'triangle', 0.07), 60);
    },
    spideySense() {
      this.tone(880, 1760, 0.15, 'sine', 0.08);
      setTimeout(() => this.tone(1174, 2349, 0.15, 'triangle', 0.07), 40);
      setTimeout(() => this.tone(1396, 2793, 0.15, 'sine', 0.06), 80);
    },
    spideyWham() {
      this.tone(180, 45, 0.22, 'triangle', 0.16);
      setTimeout(() => this.tone(340, 90, 0.12, 'square', 0.09), 30);
      setTimeout(() => this.splat(), 70);
    },"""

insert_pos_audio = storm_end + len("    },\n")
content = content[:insert_pos_audio] + spiderman_audio + content[insert_pos_audio:]

# 2. Add defineSpecies for Spider-Man before `petHalfWidth`
species_anchor = "  // How far the drawing actually reaches sideways from pet.x:"
species_idx = content.find(species_anchor)
assert species_idx != -1, "petHalfWidth anchor not found in bitling.html"

spiderman_species_def = """  defineSpecies({
    id: 'spiderman',
    name: 'Spider-Man',
    kind: 'ground',
    blurb: "Your friendly neighborhood Spider-Man! Authentic 3D suit, skyline window swinging, expressive eye shutters, and Spidey-Sense bug combat.",
    accent: '#e23636',
    radius: [44, 42, 50, 58],
    reach: () => 2.62,
    half: (r) => r * 1.85,
    draw: () => drawSpiderman(),
    trail: null,
    attack: {
      style: 'web',
      behind: false,
      charge: 0.35,
      resolve(isBoss) {
        return {
          style: isBoss ? 'slingshotDive' : 'webThwip',
          charge: isBoss ? 0.6 : 0.25,
          sound: isBoss ? 'spideyWham' : 'spideyThwip'
        };
      },
      origin(r) {
        return [{
          x: Math.round(pet.x + (pet.facing || 1) * r * 0.45),
          y: Math.round(pet.y - r * 0.85)
        }];
      },
      draw(r, k, isBoss, style) {
        drawSpidermanWebAttack(r, k, isBoss, style);
      }
    },
    voice: {
      hello: ["Just your friendly neighborhood Spider-Man!", "Hey everyone!", "Ready to swing into action!", "Spider-Man is on patrol!"],
      happy: ["With great code comes great responsibility!", "Woohoo! Nailed the landing!", "I love this neighborhood!", "Another clean commit!"],
      hungry: ["Pizza time!", "Anyone order extra mozzarella?", "Swinging works up an appetite!", "Need some New York pizza!"],
      sleepy: ["Zzz... catching 40 winks in my web hammock...", "Resting on the fire escape...", "Wake me if the Sinister Six shows up..."],
      bored: ["No bank heists? No rogue bugs?", "Waiting for the police scanner to light up...", "Think I'll practice some web flips..."],
      petted: ["Hey, thanks buddy!", "Spider-hug!", "Friendly neighborhood affection!"],
      eat: ["Mmm, pizza time! Best slice in Queens!", "Delicious!", "*nom nom* Fuel for web-slinging!"],
      zapped: ["THWIP THWIP! Bug webbed up!", "Web shooter direct hit!", "Caught in the spider's web!", "WHAM! Slingshot kick!"],
      play: ["Check out this flip!", "Look ma, no hands!", "Acrobatic layout!"],
      working: ["Patrolling the desktop skyline...", "Monitoring the network perimeter...", "Scanning open windows for threats..."],
      done: ["All clear on the desktop! Neighborhood is safe!", "Bug neutralized and tagged!"],
      testFail: ["My Spidey-Sense is tingling... issue on line 42!", "Test failure detected! Webbing up the bug!", "Hang on, I've got this!"],
      testPass: ["ALL TESTS PASSED! Clean as a whistle!", "Shipped with great responsibility!"],
      shipped: ["Pushed straight to production! Thwip thwip!"],
      held: ["Whoa! Don't drop me!", "Hey, only I do the swinging here!"],
      landed: ["Superhero landing! Hard on the knees, but looks cool!"],
      night: ["The city is quiet tonight. Spider-Man standing guard.", "Sleep tight, neighborhood."]
    }
  });

"""

content = content[:species_idx] + spiderman_species_def + content[species_idx:]

# 3. Add Spider-Man sprites, state, and drawSpiderman() renderer before `function drawKaiju()`
kaiju_anchor = "  function drawKaiju() {"
kaiju_idx = content.find(kaiju_anchor)
assert kaiju_idx != -1, "drawKaiju anchor not found in bitling.html"

spiderman_renderer = f"""  // ---------------------------------------------------------------- Spider-Man (Authentic 3D Living Desktop Pet)
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
      pet.facing = pet.walkDir < 0 ? -1 : 1;
    }}
    const f = pet.facing || 1;

    // Aerodynamic banking / pitch
    let targetPitch = 0;
    if (isCarried) {{
      targetPitch = clamp((vx * f / 700) + (vy / 900), -0.28, 0.28);
    }} else if (pet.walking) {{
      targetPitch = 0.03;
    }} else if (pet.spideySwinging) {{
      targetPitch = clamp(vx * f / 500, -0.35, 0.35);
    }}
    pet.spideyPitch = (pet.spideyPitch || 0) * 0.78 + targetPitch * 0.22;

    stageBody({{
      shadow: !isCarried && !asleep,
      bob: isCarried ? 0.02 : (pet.walking ? 0.07 : (asleep ? 0.01 : 0.035)),
      bobRate: pet.walking ? 8.5 : (asleep ? 1.4 : 2.6),
      sway: (isCarried || asleep) ? 0 : 0.02
    }}, (r, t) => {{
      ctx.save();

      // Neutralize stage squash/stretch so the pristine 3D art stays undistorted
      const sx = (1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6);
      const sy = (1 + pet.sq) * (1 + pet.stretch);
      if (Math.abs(sx) > 0.05 && Math.abs(sy) > 0.05) {{
        ctx.scale(1 / sx, 1 / sy);
      }}

      // Facing scale and tilt
      ctx.scale(f, 1);
      ctx.rotate(pet.spideyPitch);

      // Select high-definition 3D pose
      let sprite = spideyImgIdle;
      let targetH = r * 2.38;
      let yOffset = 0.94;

      if (asleep) {{
        sprite = spideyImgSleep;
        targetH = r * 2.25;
        yOffset = 0.92;
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
      }} else if (pet.spideySwinging) {{
        const swingPhase = (t * 4) % 3;
        if (swingPhase < 1) sprite = spideyImgSwingDown;
        else if (swingPhase < 2) sprite = spideyImgSwingUp;
        else sprite = spideyImgFlip;
        targetH = r * 2.50;
        yOffset = 0.92;
      }} else if (pet.walking) {{
        sprite = spideyImgCrawl;
        targetH = r * 2.35;
        yOffset = 0.94;
      }}

      // -------------------------------------------------------- Spidey-Sense Ditko Lightning Halo
      const isNearbyThreat = (bugs && bugs.length > 0 && Math.hypot(bugs[0].x - pet.x, bugs[0].y - pet.y) < 320);
      if (charging || firing || isNearbyThreat || (pet.spideySense && pet.spideySense > 0)) {{
        ctx.save();
        ctx.strokeStyle = Math.floor(t * 22) % 2 === 0 ? '#ffe600' : '#e23636';
        ctx.lineWidth = Math.max(1.8, r * 0.045);
        ctx.shadowColor = '#ffe600';
        ctx.shadowBlur = 8;
        const headX = 0;
        const headY = -targetH * 0.82;
        const numWaves = 6;
        for (let i = 0; i < numWaves; i++) {{
          const ang = -Math.PI * 0.85 + (i / (numWaves - 1)) * Math.PI * 0.7;
          const r1 = r * 0.45;
          const r2 = r * (0.8 + Math.sin(t * 25 + i) * 0.22);
          const r3 = r2 + r * 0.28;
          ctx.beginPath();
          ctx.moveTo(headX + Math.cos(ang) * r1, headY + Math.sin(ang) * r1);
          ctx.lineTo(headX + Math.cos(ang + 0.12) * r2, headY + Math.sin(ang + 0.12) * r2);
          ctx.lineTo(headX + Math.cos(ang - 0.08) * r3, headY + Math.sin(ang - 0.08) * r3);
          ctx.stroke();
        }}
        ctx.restore();
      }}

      // -------------------------------------------------------- Dangle Web Strand when Carried
      if (isCarried) {{
        ctx.save();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = Math.max(1.5, r * 0.04);
        ctx.shadowColor = 'rgba(255, 255, 255, 0.7)';
        ctx.shadowBlur = 3;
        ctx.beginPath();
        ctx.moveTo(0, -targetH * 0.9);
        ctx.lineTo(0, -targetH * 1.8);
        ctx.stroke();
        ctx.restore();
      }}

      // -------------------------------------------------------- High-Definition 3D Sprite Rendering
      if (sprite && sprite.complete && sprite.naturalWidth > 0) {{
        ctx.save();
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        const sw = sprite.naturalWidth;
        const sh = sprite.naturalHeight;
        const targetW = targetH * (sw / sh);
        ctx.drawImage(sprite, -targetW / 2, -targetH * yOffset, targetW, targetH);
        ctx.restore();
      }} else {{
        // Vector fallback
        ctx.fillStyle = '#e23636';
        ctx.beginPath();
        ctx.arc(0, -r * 0.85, r * 0.75, 0, Math.PI * 2);
        ctx.fill();
        // Eye lenses
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.ellipse(-r * 0.22, -r * 0.9, r * 0.16, r * 0.24, -0.2, 0, Math.PI * 2);
        ctx.ellipse(r * 0.22, -r * 0.9, r * 0.16, r * 0.24, 0.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#1a1a1a';
        ctx.lineWidth = 2;
        ctx.stroke();
      }}

      // -------------------------------------------------------- Pepperoni Pizza Eating Overlay
      if (pet.chew > 0 && !isCarried && !asleep) {{
        ctx.save();
        ctx.translate(r * 0.22, -targetH * 0.72);
        ctx.rotate(0.22 + Math.sin(t * 14) * 0.12);
        // Pizza slice crust & cheese
        ctx.fillStyle = '#f6ad55';
        ctx.beginPath();
        ctx.moveTo(-r * 0.25, -r * 0.25);
        ctx.lineTo(r * 0.25, -r * 0.25);
        ctx.lineTo(0, r * 0.35);
        ctx.closePath();
        ctx.fill();
        // Crust edge
        ctx.fillStyle = '#d69e2e';
        ctx.beginPath();
        ctx.rect(-r * 0.27, -r * 0.32, r * 0.54, r * 0.08);
        ctx.fill();
        // Pepperoni slices
        ctx.fillStyle = '#c53030';
        ctx.beginPath();
        ctx.arc(-r * 0.06, -r * 0.08, r * 0.055, 0, Math.PI * 2);
        ctx.arc(r * 0.08, 0, r * 0.048, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }}

      // -------------------------------------------------------- Web Hammock & Sleep Particles
      if (asleep) {{
        ctx.save();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
        ctx.lineWidth = 1.5;
        const hw = r * 1.25;
        ctx.beginPath();
        ctx.moveTo(-hw, -r * 0.95);
        ctx.quadraticCurveTo(0, -r * 0.05, hw, -r * 0.95);
        ctx.stroke();
        for (let s = -3; s <= 3; s++) {{
          ctx.beginPath();
          ctx.moveTo(s * (hw / 3.5), -r * (0.95 - Math.abs(s) * 0.12));
          ctx.lineTo(s * (hw / 4.5), -r * 0.22);
          ctx.stroke();
        }}
        // Floating Zzz
        ctx.fillStyle = '#ffffff';
        ctx.font = `bold ${{Math.max(10, r * 0.35)}}px sans-serif`;
        for (let z = 0; z < 3; z++) {{
          const zPhase = (t * 1.3 + z * 0.33) % 1;
          const zx = r * 0.35 + zPhase * r * 0.65;
          const zy = -r * 0.85 - zPhase * r * 0.85;
          ctx.globalAlpha = Math.sin(zPhase * Math.PI) * 0.85;
          ctx.fillText('Z', zx, zy);
        }}
        ctx.restore();
      }}

      ctx.restore();
    }});
  }}

  function drawSpidermanWebAttack(r, k, isBoss, style) {{
    ctx.save();
    const f = pet.facing || 1;
    const ox = pet.x + f * r * 0.45;
    const oy = pet.y - r * 0.85;

    let targetX = pet.x + f * r * 4.5;
    let targetY = pet.y - r * 0.85;
    if (bugs && bugs.length > 0) {{
      targetX = bugs[0].x;
      targetY = bugs[0].y;
    }}

    const curX = ox + (targetX - ox) * (1 - k);
    const curY = oy + (targetY - oy) * (1 - k);

    if (style === 'slingshotDive' || isBoss) {{
      // Slingshot Dual-Web Dive Kick: twin web lines anchor behind him, diving forward
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = Math.max(2.2, r * 0.07);
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

content = content[:kaiju_idx] + spiderman_renderer + content[kaiju_idx:]

# 4. Add window.__bitling methods for Spider-Man
bitling_anchor = "    selectSpecies(id) { selectSpecies(id, true); },\n"
bitling_idx = content.find(bitling_anchor)
assert bitling_idx != -1, "selectSpecies anchor not found in window.__bitling"

spiderman_bitling = """    setWindowRooftops(list) { setSpideyRooftops(list); },
    setUserActive(active) { setSpideyUserActive(active); },
"""

content = content[:bitling_idx + len(bitling_anchor)] + spiderman_bitling + content[bitling_idx + len(bitling_anchor):]

with open("web/bitling.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully injected Spider-Man into web/bitling.html!")
