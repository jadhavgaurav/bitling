#!/usr/bin/env python3
"""Inject Iron Man assets, audio, species, and renderer into web/bitling.html."""
import json
from pathlib import Path

DATA_FILE = Path('/tmp/ironman_data.json')
HTML_FILE = Path('/Users/a12345/Desktop/AI/Bitling/web/bitling.html')

with open(DATA_FILE) as f:
    data = json.load(f)

sprites = data['sprites']
audio_data = data['audio']

html = HTML_FILE.read_text(encoding='utf-8')

# 1. Insert IRONMAN_AUDIO right after PIKA_AUDIO
ironman_audio_block = """
  const IRONMAN_AUDIO = {
    iroRepulsor: '""" + audio_data['iroRepulsor'] + """',
    iroUnibeam: '""" + audio_data['iroUnibeam'] + """',
    jarvisAsYouWish: '""" + audio_data['jarvisAsYouWish'] + """',
    jarvisOnline: '""" + audio_data['jarvisOnline'] + """',
    repulsorHum: '""" + audio_data['repulsorHum'] + """',
  };

  const ironmanBuffers = {};
  function getIronManBuffer(key) {
    if (ironmanBuffers[key]) return Promise.resolve(ironmanBuffers[key]);
    if (!audio.ctx || !IRONMAN_AUDIO[key]) return Promise.resolve(null);
    try {
      const b64 = IRONMAN_AUDIO[key].split(',')[1];
      const binary = atob(b64);
      const len = binary.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
      const arrayBuf = bytes.buffer.slice(0);
      return new Promise((resolve) => {
        const p = audio.ctx.decodeAudioData(
          arrayBuf,
          (buf) => { ironmanBuffers[key] = buf; resolve(buf); },
          () => resolve(null)
        );
        if (p && typeof p.then === 'function') {
          p.then((buf) => { ironmanBuffers[key] = buf; resolve(buf); }).catch(() => resolve(null));
        }
      });
    } catch (_) {
      return Promise.resolve(null);
    }
  }
"""

anchor_audio = "  // ---------------------------------------------------------------- audio"
if "const IRONMAN_AUDIO =" not in html:
    assert anchor_audio in html, f"anchor_audio not found"
    html = html.replace(anchor_audio, ironman_audio_block + "\n" + anchor_audio, 1)

# 2. Add playIronMan and IronMan methods to audio object
ironman_audio_methods = """    playIronMan(key, vol = 0.95) {
      if (!state.sound) return;
      this.ensure();
      const now = performance.now();
      if (this._lastIronManKey === key && now - (this._lastIronManTime || 0) < 300) return;
      this._lastIronManKey = key;
      this._lastIronManTime = now;
      getIronManBuffer(key).then((buf) => {
        if (buf && this.ctx) {
          try {
            if (this._ironManSrc && (key === 'iroUnibeam' || key === 'jarvisOnline')) {
              try { this._ironManSrc.stop(); } catch (_) {}
              this._ironManSrc = null;
            }
            const src = this.ctx.createBufferSource();
            src.buffer = buf;
            const g = this.ctx.createGain();
            g.gain.setValueAtTime(vol, this.ctx.currentTime);
            src.connect(g).connect(this.ctx.destination);
            src.start(0);
            this._ironManSrc = src;
            src.onended = () => { if (this._ironManSrc === src) this._ironManSrc = null; };
            return;
          } catch (_) {}
        }
        try {
          if (IRONMAN_AUDIO[key]) {
            const snd = new Audio(IRONMAN_AUDIO[key]);
            snd.volume = vol;
            snd.play().catch(() => {});
          }
        } catch (_) {}
      });
    },
    preloadIronMan() {
      if (typeof window !== 'undefined' && window.atob) {
        Object.keys(IRONMAN_AUDIO).forEach((k) => getIronManBuffer(k));
      }
    },
    iroRepulsor() { this.playIronMan('iroRepulsor', 0.95); },
    iroUnibeam() { this.playIronMan('iroUnibeam', 0.98); },
    jarvisOnline() { this.playIronMan('jarvisOnline', 0.95); },
    jarvisAsYouWish() { this.playIronMan('jarvisAsYouWish', 0.92); },
    repulsorHum() { this.playIronMan('repulsorHum', 0.75); },
"""

anchor_methods = "    pikaThunder() {"
if "playIronMan(key, vol = 0.95)" not in html:
    assert anchor_methods in html, f"anchor_methods not found"
    html = html.replace(anchor_methods, ironman_audio_methods + anchor_methods, 1)

# 3. Wire say(text) for ironman
anchor_say = "    if (state.species === 'pikachu') {"
ironman_say = """    if (state.species === 'ironman') {
      const up = (text || '').toUpperCase();
      if (up.includes('ONLINE') || up.includes('READY') || up.includes('UPLOADED') || up.includes('I AM IRON MAN')) {
        audio.jarvisOnline();
      } else if (up.includes('AS YOU WISH') || up.includes('NOMINAL') || up.includes('WELCOME') || up.includes('INTEGRITY') || up.includes('SENSORS') || up.includes('CRUSHED')) {
        audio.jarvisAsYouWish();
      }
    }
"""
if "state.species === 'ironman'" not in html:
    assert anchor_say in html, f"anchor_say not found"
    html = html.replace(anchor_say, ironman_say + anchor_say, 1)

# 4. Wire attack shotStyle in updateBugs
anchor_shot = """          } else if (shotStyle === 'electroball') {
            audio.electroBall();
            if (state.species === 'pikachu') audio.pikaPika();
          }"""
ironman_shot = """          } else if (shotStyle === 'electroball') {
            audio.electroBall();
            if (state.species === 'pikachu') audio.pikaPika();
          } else if (shotStyle === 'unibeam') {
            audio.iroUnibeam();
          } else if (shotStyle === 'repulsor') {
            audio.iroRepulsor();
          }"""
if "shotStyle === 'unibeam'" not in html:
    assert anchor_shot in html, f"anchor_shot not found"
    html = html.replace(anchor_shot, ironman_shot, 1)

anchor_hue = "          const sparkHue = state.species === 'pikachu' ? 52 : state.species === 'kaiju' ? 185 : state.species === 'goku' ? (shotStyle === 'kamehameha' ? 195 : 45) : 8;"
new_hue = "          const sparkHue = state.species === 'pikachu' ? 52 : state.species === 'kaiju' ? 185 : state.species === 'goku' ? (shotStyle === 'kamehameha' ? 195 : 45) : state.species === 'ironman' ? (shotStyle === 'unibeam' ? 190 : 180) : 8;"
if "state.species === 'ironman' ?" not in html:
    assert anchor_hue in html, f"anchor_hue not found"
    html = html.replace(anchor_hue, new_hue, 1)

# 5. Define ironman species
ironman_species_block = """  defineSpecies({
    id: 'ironman', name: 'Iron Man', kind: 'float',
    blurb: 'The Armored Avenger in classic Mark III red & gold armor. Hovers with pulse repulsor thrusters, fires palm Repulsor Blasts at small bugs, and unleashes the chest Arc Reactor Unibeam on boss bugs!',
    accent: '#ff2222',
    radius: [46, 44, 52, 60],
    reach: () => 2.45,
    half: (r) => r * 1.6,
    draw: () => drawIronMan(),
    trail: 'flamejet',
    attack: {
      style: 'unibeam',
      behind: false,
      charge: 0.95,
      resolve(isBoss) {
        if (isBoss) {
          return { style: 'unibeam', charge: 0.95, sound: 'iroUnibeam' };
        }
        return { style: 'repulsor', charge: 0.22, sound: 'iroRepulsor' };
      },
      origin: (r) => {
        const isBoss = (pet.zapBoss || (pet.zapStyle === 'unibeam'));
        if (isBoss) {
          return [{ x: Math.round(pet.x + pet.facing * r * 0.25), y: Math.round(pet.y - r * 0.95) }];
        }
        return [{ x: Math.round(pet.x + pet.facing * r * 0.72), y: Math.round(pet.y - r * 0.92) }];
      },
      draw(r, k, isBoss, style) {
        const ox = pet.x + pet.facing * r * (isBoss ? 0.25 : 0.72);
        const oy = pet.y - r * (isBoss ? 0.95 : 0.92);
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';

        if (style === 'unibeam' || isBoss) {
          // ------------------------------------------------ Chest Arc Reactor Unibeam
          const tx = pet.zapX, ty = pet.zapY;
          const len = Math.hypot(tx - ox, ty - oy);
          const ang = Math.atan2(ty - oy, tx - ox);
          ctx.translate(ox, oy);
          ctx.rotate(ang);

          // Wide outer photon beam
          const beamW = Math.max(8, r * (0.45 + k * 0.35));
          const grad = ctx.createLinearGradient(0, 0, len, 0);
          grad.addColorStop(0, `rgba(255, 255, 255, ${0.98 * k})`);
          grad.addColorStop(0.15, `rgba(0, 240, 255, ${0.95 * k})`);
          grad.addColorStop(0.65, `rgba(0, 150, 255, ${0.75 * k})`);
          grad.addColorStop(1, `rgba(0, 100, 255, ${0.4 * k})`);
          ctx.fillStyle = grad;
          ctx.beginPath();
          ctx.roundRect(0, -beamW, len, beamW * 2, beamW * 0.5);
          ctx.fill();

          // Intense pure white core beam
          ctx.fillStyle = `rgba(255, 255, 255, ${0.98 * k})`;
          ctx.beginPath();
          ctx.roundRect(0, -beamW * 0.35, len, beamW * 0.7, beamW * 0.2);
          ctx.fill();

          // Concentric energy rings traveling along beam
          ctx.strokeStyle = `rgba(180, 245, 255, ${0.85 * k})`;
          ctx.lineWidth = Math.max(2, r * 0.05);
          for (let i = 1; i <= 4; i++) {
            const pos = ((i / 4) * len + pet.t * 300) % len;
            const ringR = beamW * (0.8 + Math.sin(pet.t * 20 + i) * 0.25);
            ctx.beginPath();
            ctx.ellipse(pos, 0, ringR * 0.35, ringR, 0, 0, Math.PI * 2);
            ctx.stroke();
          }

          // Arc Reactor muzzle flash
          const muzzleR = beamW * 1.8;
          const mg = ctx.createRadialGradient(0, 0, 2, 0, 0, muzzleR);
          mg.addColorStop(0, '#ffffff');
          mg.addColorStop(0.4, 'rgba(0, 240, 255, 0.95)');
          mg.addColorStop(1, 'rgba(0, 150, 255, 0)');
          ctx.fillStyle = mg;
          ctx.beginPath(); ctx.arc(0, 0, muzzleR, 0, Math.PI * 2); ctx.fill();

          // Target impact shockwave
          const impR = r * (0.9 + k * 1.2);
          const ig = ctx.createRadialGradient(len, 0, 2, len, 0, impR);
          ig.addColorStop(0, '#ffffff');
          ig.addColorStop(0.4, 'rgba(0, 240, 255, 0.9)');
          ig.addColorStop(1, 'rgba(0, 100, 255, 0)');
          ctx.fillStyle = ig;
          ctx.beginPath(); ctx.arc(len, 0, impR, 0, Math.PI * 2); ctx.fill();

        } else {
          // ------------------------------------------------ Palm Repulsor Blast
          const len = Math.hypot(pet.zapX - ox, pet.zapY - oy);
          const ang = Math.atan2(pet.zapY - oy, pet.zapX - ox);
          ctx.translate(ox, oy);
          ctx.rotate(ang);

          // Fast high-velocity repulsor ray
          ctx.strokeStyle = `rgba(0, 240, 255, ${0.92 * k})`;
          ctx.lineWidth = Math.max(3, r * 0.12);
          ctx.beginPath();
          ctx.moveTo(0, 0);
          ctx.lineTo(len, 0);
          ctx.stroke();

          // Core beam
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = Math.max(1.5, r * 0.05);
          ctx.beginPath();
          ctx.moveTo(0, 0);
          ctx.lineTo(len, 0);
          ctx.stroke();

          // Traveling repulsor plasma ring
          const ringR = r * (0.24 + Math.sin(pet.t * 30) * 0.05);
          ctx.strokeStyle = `rgba(0, 240, 255, ${0.95 * k})`;
          ctx.lineWidth = 2.2;
          ctx.beginPath();
          ctx.ellipse(len * 0.65, 0, ringR * 0.4, ringR, 0, 0, Math.PI * 2);
          ctx.stroke();

          // Target impact burst
          const ballR = r * (0.32 + Math.sin(pet.t * 40) * 0.08);
          const bg = ctx.createRadialGradient(len, 0, 2, len, 0, ballR);
          bg.addColorStop(0, '#ffffff');
          bg.addColorStop(0.5, 'rgba(0, 240, 255, 0.95)');
          bg.addColorStop(1, 'rgba(0, 150, 255, 0)');
          ctx.fillStyle = bg;
          ctx.beginPath(); ctx.arc(len, 0, ballR, 0, Math.PI * 2); ctx.fill();

          // Electric repulsor arcs at target
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.6;
          for (let i = 0; i < 5; i++) {
            const spAng = (i / 5) * Math.PI * 2 + pet.t * 20;
            const dist = ballR * 1.4;
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
      hello: ["I am Iron Man.", "Jarvis: 'We're online and ready, sir.'", "Jarvis: 'Welcome home, sir.'"],
      happy: ["Suit integrity at 100%.", "Jarvis: 'All systems nominal, sir.'", "Repulsors fully calibrated.", "Tony: 'Looking good in red and gold.'"],
      hungry: ["Power grid at 12%. Need an Arc Reactor charge.", "Jarvis: 'Power reserves depleted, sir.'", "Tony: 'Who forgot to order shawarma?'"],
      sleepy: ["Entering low power standby mode.", "Jarvis: 'Powering down non-essential systems.'", "Armor entering sleep protocol."],
      bored: ["Jarvis, find me something to blow up.", "Running telemetry diagnostics...", "Stark Industries: always innovating."],
      petted: ["Jarvis: 'Sensors detect user physical contact.'", "Careful, that gold-titanium alloy is polished.", "Tony: 'Yeah, I know. It's an awesome suit.'"],
      eat: ["Arc Reactor charged to 100%!", "Jarvis: 'Power restored to maximum output.'", "Shawarma secured! Energy restored!"],
      zapped: ["Jarvis: 'Target neutralized.'", "Repulsor beam: direct hit.", "Bug vaporized. You're welcome.", "Jarvis: 'Threat eliminated, sir.'"],
      bossDown: ["MAXIMUM POWER UNIBEAM!", "Jarvis: 'Critical target destroyed.'", "Arc Reactor Unibeam: total disintegration!"],
      squash: ["Jarvis: 'Target crushed underfoot.'", "Squashed.", "Clean hit."],
      play: ["Flight test sequence initiated!", "Jarvis: 'Engaging supersonic thrusters.'", "Hold on to your coffee cups!"],
      working: ["Jarvis: 'Calibrating targeting telemetry...'", "Charging repulsor capacitors...", "Arc Reactor flaring..."],
      done: ["Code compiled, bugs exterminated.", "Jarvis: 'Workspace clear of hostile anomalies, sir.'", "Stark Industries software quality assured."],
      testFail: ["Jarvis: 'Sir, multiple test failures detected!'", "Red alerts on HUD! Failing tests in sector 4!", "Targeting bug swarm!"],
      testPass: ["Jarvis: 'All tests passing, sir. Build is green.'", "Flawless execution.", "Green across the board."],
      shipped: ["Jarvis: 'Payload deployed to production.'", "Super-sonic orbital launch!", "Shipped. Mark III out."],
      held: ["Jarvis: 'Warning: external gravitational displacement.'", "Tony: 'Hey! Watch the paint job!'", "Thrusters compensating for drag!"],
      night: ["Jarvis: 'Activating night stealth visor protocol.'", "Arc Reactor glowing in the dark.", "City patrol duty active."],
    },
  });
"""

anchor_species = "  defineSpecies({\n    id: 'kaiju',"
if "id: 'ironman'" not in html:
    assert anchor_species in html, f"anchor_species not found"
    html = html.replace(anchor_species, ironman_species_block + "\n" + anchor_species, 1)

# 6. Insert IRONMAN_SPRITES and drawIronMan()
ironman_sprites_and_renderer = """
  // ---------------------------------------------------------------- Iron Man sprites & renderer
  const IRONMAN_SPRITES = {
    idle: '""" + sprites['idle'] + """',
    fly: '""" + sprites['fly'] + """',
    stance: '""" + sprites['stance'] + """',
    charge: '""" + sprites['charge'] + """',
    inspect: '""" + sprites['inspect'] + """',
    salute: '""" + sprites['salute'] + """',
  };

  const ironmanImgIdle = new Image(); ironmanImgIdle.src = IRONMAN_SPRITES.idle;
  const ironmanImgFly = new Image(); ironmanImgFly.src = IRONMAN_SPRITES.fly;
  const ironmanImgStance = new Image(); ironmanImgStance.src = IRONMAN_SPRITES.stance;
  const ironmanImgCharge = new Image(); ironmanImgCharge.src = IRONMAN_SPRITES.charge;
  const ironmanImgInspect = new Image(); ironmanImgInspect.src = IRONMAN_SPRITES.inspect;
  const ironmanImgSalute = new Image(); ironmanImgSalute.src = IRONMAN_SPRITES.salute;

  function drawIronMan() {
    const asleep = state.asleep;
    const charging = pet.zapCharge > 0 && !asleep;
    const firing = pet.zap > 0;
    const isBoss = pet.zapBoss || false;
    const isCarried = !!(pet.carried || pet.held);
    const vx = (pet.held ? pet.vx : (pet.dragVx || 0));
    const vy = (pet.held ? pet.vy : (pet.dragVy || 0));
    const rawSpeed = Math.hypot(vx, vy) || (pet.dragSpeed || 0);

    // Exponential smoothing on velocity
    pet.ironmanSpeed = (pet.ironmanSpeed || 0) * 0.84 + rawSpeed * 0.16;

    // Immediately face the drag / pull direction
    if (isCarried && Math.abs(vx) > 12) {
      pet.facing = vx < 0 ? -1 : 1;
    }
    const f = pet.facing || 1;

    // Aerodynamic banking / pitch in local coordinates
    const forwardV = vx * f;
    const targetPitch = isCarried
      ? clamp((forwardV / 700) + (vy / 950), -0.26, 0.26)
      : (pet.walking ? 0.05 : 0);
    pet.ironmanPitch = (pet.ironmanPitch || 0) * 0.82 + targetPitch * 0.18;

    const isFlying = isCarried || pet.walking || pet.ironmanSpeed > 30;

    // Sprite selection based on action state
    let sprite = ironmanImgIdle;
    let baseRefW = 89;
    let yAlign = 0.88;

    if (isCarried) {
      sprite = ironmanImgIdle;
      baseRefW = 89;
      yAlign = 0.85;
    } else if (charging || firing) {
      sprite = ironmanImgCharge;
      baseRefW = 104;
      yAlign = 0.90;
    } else if (pet.working || (typeof snack !== 'undefined' && snack.active)) {
      sprite = ironmanImgInspect;
      baseRefW = 60;
      yAlign = 0.88;
    } else if (isFlying) {
      sprite = ironmanImgFly;
      baseRefW = 89;
      yAlign = 0.86;
    }

    stageBody({ shadow: !isCarried, bob: isCarried ? 0.01 : 0.04, bobRate: 2.2, sway: isCarried ? 0 : 0.015 }, (r, t) => {
      ctx.save();

      // Neutralize squash/stretch deformation so pixel art stays crisp
      const sx = (1 - pet.sq * 0.85) * (1 - pet.stretch * 0.6);
      const sy = (1 + pet.sq) * (1 + pet.stretch);
      if (Math.abs(sx) > 0.05 && Math.abs(sy) > 0.05) {
        ctx.scale(1 / sx, 1 / sy);
      }

      // Flip for facing direction
      ctx.scale(f, 1);

      // Aerodynamic pitch
      ctx.rotate(pet.ironmanPitch);

      // -------------------------------------------------------- Supersonic Plasma Slipstream & Exhaust
      if (isFlying) {
        const speedRatio = clamp((pet.ironmanSpeed || 0) / 240, isCarried ? 0.5 : 0.4, 1.4);
        const trailLen = r * (1.5 + speedRatio * 1.6);

        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        // Supersonic plasma exhaust stream behind boots (-X is behind Iron Man)
        const grad = ctx.createLinearGradient(-r * 0.35, r * 0.25, -r * 0.35 - trailLen, r * 0.25);
        grad.addColorStop(0, 'rgba(0, 240, 255, 0.95)');
        grad.addColorStop(0.35, 'rgba(0, 150, 255, 0.6)');
        grad.addColorStop(0.7, 'rgba(255, 100, 0, 0.3)');
        grad.addColorStop(1, 'rgba(255, 50, 0, 0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(-r * 0.3, r * 0.1);
        ctx.bezierCurveTo(-r * 0.8, r * 0.18, -r * 0.5 - trailLen * 0.7, r * 0.22, -r * 0.35 - trailLen, r * 0.25);
        ctx.bezierCurveTo(-r * 0.5 - trailLen * 0.7, r * 0.28, -r * 0.8, r * 0.35, -r * 0.3, r * 0.4);
        ctx.closePath();
        ctx.fill();

        // Trailing plasma sparks
        for (let i = 0; i < 4; i++) {
          const phase = (t * 4.2 + i * 0.75) % 1;
          const sparkDist = r * 0.4 + phase * trailLen;
          const sparkY = r * 0.25 + Math.sin(t * 18 + i) * r * 0.08;
          ctx.fillStyle = `rgba(${i % 2 === 0 ? '0, 240, 255' : '255, 180, 50'}, ${0.85 * (1 - phase)})`;
          ctx.beginPath();
          ctx.arc(-sparkDist, sparkY, r * (0.04 + (1 - phase) * 0.05), 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }

      // -------------------------------------------------------- Boot Repulsor Thruster Flames (Hover Jets)
      if (!asleep) {
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const pulse = Math.sin(t * 28) * 0.15;
        const thrusterLen = r * (0.45 + (isFlying ? 0.35 : 0) + pulse);
        const bootX = -r * 0.08;
        const bootY = r * 0.32;

        // Outer fiery flame
        const fg = ctx.createLinearGradient(bootX, bootY, bootX - (isFlying ? r * 0.2 : 0), bootY + thrusterLen);
        fg.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
        fg.addColorStop(0.25, 'rgba(0, 240, 255, 0.9)');
        fg.addColorStop(0.65, 'rgba(255, 140, 0, 0.7)');
        fg.addColorStop(1, 'rgba(255, 50, 0, 0)');
        ctx.fillStyle = fg;
        ctx.beginPath();
        ctx.moveTo(bootX - r * 0.14, bootY);
        ctx.quadraticCurveTo(bootX, bootY + thrusterLen * 1.1, bootX + (isFlying ? -r * 0.25 : 0), bootY + thrusterLen);
        ctx.quadraticCurveTo(bootX, bootY + thrusterLen * 0.7, bootX + r * 0.14, bootY);
        ctx.closePath();
        ctx.fill();

        // Inner core plasma needle
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.moveTo(bootX - r * 0.05, bootY);
        ctx.lineTo(bootX + (isFlying ? -r * 0.15 : 0), bootY + thrusterLen * 0.6);
        ctx.lineTo(bootX + r * 0.05, bootY);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }

      // -------------------------------------------------------- Render Sprite
      const drawW = r * 2.35 * (baseRefW / 89);
      const drawH = drawW * (sprite.height / sprite.width);
      const drawX = -drawW * 0.48;
      const drawY = -drawH * yAlign;

      ctx.drawImage(sprite, drawX, drawY, drawW, drawH);

      // -------------------------------------------------------- Glowing Cyan Eye Visors & Chest Arc Reactor
      if (!asleep) {
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';

        // Chest Arc Reactor glow
        const reactorX = r * 0.12;
        const reactorY = -r * 0.68;
        const arcPulse = 0.85 + Math.sin(t * 6) * 0.15;
        const arcR = r * (0.16 * arcPulse);
        const arcGrad = ctx.createRadialGradient(reactorX, reactorY, 1, reactorX, reactorY, arcR * 2.4);
        arcGrad.addColorStop(0, '#ffffff');
        arcGrad.addColorStop(0.35, 'rgba(0, 240, 255, 0.9)');
        arcGrad.addColorStop(0.7, 'rgba(0, 160, 255, 0.4)');
        arcGrad.addColorStop(1, 'rgba(0, 160, 255, 0)');
        ctx.fillStyle = arcGrad;
        ctx.beginPath();
        ctx.arc(reactorX, reactorY, arcR * 2.4, 0, Math.PI * 2);
        ctx.fill();

        // Helmet Eye Visor glow
        const eyeX = r * 0.22;
        const eyeY = -r * 1.05;
        ctx.fillStyle = 'rgba(0, 240, 255, 0.85)';
        ctx.beginPath();
        ctx.ellipse(eyeX, eyeY, r * 0.08, r * 0.035, 0.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.ellipse(eyeX, eyeY, r * 0.04, r * 0.018, 0.2, 0, Math.PI * 2);
        ctx.fill();

        // Energy Gathering Aura during Attack Charge
        if (charging || firing) {
          const auraX = (sprite === ironmanImgCharge) ? r * 0.22 : reactorX;
          const auraY = (sprite === ironmanImgCharge) ? -r * 1.45 : reactorY;
          const auraR = r * (isBoss ? 1.6 : 1.1) * (0.9 + Math.sin(t * 35) * 0.15);
          const ag = ctx.createRadialGradient(auraX, auraY, 2, auraX, auraY, auraR);
          ag.addColorStop(0, '#ffffff');
          ag.addColorStop(0.4, 'rgba(0, 240, 255, 0.95)');
          ag.addColorStop(0.75, 'rgba(0, 140, 255, 0.45)');
          ag.addColorStop(1, 'rgba(0, 140, 255, 0)');
          ctx.fillStyle = ag;
          ctx.beginPath();
          ctx.arc(auraX, auraY, auraR, 0, Math.PI * 2);
          ctx.fill();

          // Electrical sparks dancing around charge center
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.8;
          const arcs = isBoss ? 6 : 3;
          for (let i = 0; i < arcs; i++) {
            const aAng = (i / arcs) * Math.PI * 2 + t * 25;
            const dist = auraR * 0.9;
            ctx.beginPath();
            ctx.moveTo(auraX, auraY);
            ctx.lineTo(auraX + Math.cos(aAng) * dist, auraY + Math.sin(aAng) * dist);
            ctx.stroke();
          }
        }

        ctx.restore();
      }

      ctx.restore();
    });
  }
"""

anchor_draw = "  function drawKaiju() {"
if "function drawIronMan()" not in html:
    assert anchor_draw in html, f"anchor_draw not found"
    html = html.replace(anchor_draw, ironman_sprites_and_renderer + "\n" + anchor_draw, 1)

HTML_FILE.write_text(html, encoding='utf-8')
print("Successfully patched web/bitling.html with Iron Man!")
