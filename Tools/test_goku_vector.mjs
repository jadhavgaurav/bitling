import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';

async function testGoku() {
  const browser = await chromium.launch({ channel: 'chrome' });
  const page = await browser.newPage({ viewport: { width: 500, height: 500 }, deviceScaleFactor: 2 });

  const html = `<!DOCTYPE html>
<html>
<head>
<style>
  body { margin: 0; background: #232232; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
  canvas { background: transparent; }
</style>
</head>
<body>
<canvas id="c" width="400" height="400"></canvas>
<script>
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');

  function drawGokuReal(opts = {}) {
    const cx = opts.x || 200;
    const cy = opts.y || 225;
    const r = opts.r || 52;
    const scale = (r / 48) * (opts.scale || 1.0);
    const t = opts.t || 0;
    const facing = opts.facing || 1;
    const state = opts.state || 'idle'; // 'idle', 'fly', 'charge', 'fire', 'wave', 'eat', 'asleep'

    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(facing * scale, scale);

    // Subtle cloud bobbing
    const bob = Math.sin(t * 2.2) * 2.5;
    ctx.translate(0, bob);

    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    // Anime accurate Toriyama Kid Goku Palette
    const skin = '#fedebb', skinShade = '#f0b080', skinBlush = 'rgba(244, 114, 182, 0.4)';
    const hair = '#111217', hairLit = '#282e4a', hairRim = '#3f476e';
    const gi = '#4d3f84', giShade = '#372a66', giLit = '#6554a8';
    const belt = '#f4f4f6', beltShade = '#c8c8ce';
    const strap = '#deb887', strapShade = '#b08b58';
    const wrist = '#e11d48', wristShade = '#9f1239';
    const pole = '#d32222', poleShade = '#941010', poleGold = '#fbc02d', poleGoldShade = '#d97706';
    const tail = '#78350f', tailShade = '#451a03';
    const shoe = '#3d4052', shoeTrim = '#ececf0';
    const ink = '#111217';

    // -------------------------------------------------------------
    // 0. CHARGE AURA (Kamehameha Charge or Fire)
    // -------------------------------------------------------------
    if (state === 'charge' || state === 'fire') {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const p = state === 'fire' ? 1.0 : (opts.chargeProgress || 0.85);
      const rad = 72 + Math.sin(t * 22) * 7;
      const grad = ctx.createRadialGradient(0, -32, 8, 0, -32, rad * 1.25);
      grad.addColorStop(0, 'rgba(224, 252, 255, 0.9)');
      grad.addColorStop(0.35, 'rgba(56, 189, 248, 0.65)');
      grad.addColorStop(0.7, 'rgba(14, 116, 144, 0.3)');
      grad.addColorStop(1, 'rgba(14, 116, 144, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.ellipse(0, -32, rad * 1.15, rad * 1.35, 0, 0, Math.PI * 2);
      ctx.fill();

      // Electric arcs
      ctx.strokeStyle = '#e0f2fe';
      ctx.lineWidth = 1.8;
      for (let i = 0; i < 6; i++) {
        const ang = (i / 6) * Math.PI * 2 + Math.sin(t * 14 + i) * 0.45;
        const r1 = 26 + Math.cos(t * 11 + i * 2) * 7;
        const r2 = rad * (0.8 + Math.sin(t * 13 + i) * 0.2);
        ctx.beginPath();
        ctx.moveTo(Math.cos(ang) * r1, -32 + Math.sin(ang) * r1);
        ctx.lineTo(Math.cos(ang + 0.22) * (r1 + r2) * 0.5, -32 + Math.sin(ang + 0.22) * (r1 + r2) * 0.5);
        ctx.lineTo(Math.cos(ang) * r2, -32 + Math.sin(ang) * r2);
        ctx.stroke();
      }
      ctx.restore();
    }

    // -------------------------------------------------------------
    // 1. POWER POLE (Slung across back pointing up-left)
    // -------------------------------------------------------------
    ctx.save();
    ctx.translate(-10, -22);
    ctx.rotate(-0.72);

    // Pole / Sheath
    ctx.fillStyle = pole;
    ctx.beginPath();
    ctx.roundRect(-3.5, -50, 7, 82, 2);
    ctx.fill();
    ctx.fillStyle = poleShade;
    ctx.fillRect(0.5, -50, 3, 82);

    // Gold Caps top and bottom
    ctx.fillStyle = poleGold;
    ctx.beginPath(); ctx.roundRect(-4.5, -54, 9, 6, 1.5); ctx.fill();
    ctx.beginPath(); ctx.roundRect(-4.5, 30, 9, 6, 1.5); ctx.fill();
    ctx.fillStyle = poleGoldShade;
    ctx.fillRect(0.5, -54, 4, 6);
    ctx.fillRect(0.5, 30, 4, 6);
    ctx.restore();

    // -------------------------------------------------------------
    // 2. MONKEY TAIL (Curling out from back-right)
    // -------------------------------------------------------------
    ctx.save();
    const tailWag = Math.sin(t * 3.6) * 0.12;
    ctx.strokeStyle = tail;
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.moveTo(11, -4);
    // Graceful curve up and around matching user screenshot
    ctx.bezierCurveTo(24, -8, 38 + tailWag * 12, -22, 42 + tailWag * 14, -8);
    ctx.bezierCurveTo(46 + tailWag * 14, 6, 32, 10, 23, 5);
    ctx.stroke();

    // Shadow underside
    ctx.strokeStyle = tailShade;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(12, -2);
    ctx.bezierCurveTo(24, -6, 36 + tailWag * 12, -18, 40 + tailWag * 14, -6);
    ctx.stroke();
    ctx.restore();

    // -------------------------------------------------------------
    // 3. FLYING NIMBUS (Kintoun) - Big Fluffy Spherical Golden Cloud
    // -------------------------------------------------------------
    ctx.save();
    ctx.translate(0, 20);

    // Trailing streamer when flying
    if (state === 'fly' || opts.speed > 25) {
      ctx.save();
      const spd = Math.min(1.5, (opts.speed || 50) / 100);
      const fl = ctx.createLinearGradient(0, 0, -85 * spd, 0);
      fl.addColorStop(0, 'rgba(255, 235, 59, 0.75)');
      fl.addColorStop(0.5, 'rgba(255, 214, 0, 0.4)');
      fl.addColorStop(1, 'rgba(255, 171, 0, 0)');
      ctx.fillStyle = fl;
      ctx.beginPath();
      ctx.moveTo(-34, -8);
      ctx.quadraticCurveTo(-60 * spd, -18, -95 * spd, -2);
      ctx.quadraticCurveTo(-55 * spd, 16, -30, 14);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }

    // Helper for cloud puffs with 3D volume
    function cloudBall(cx, cy, rx, ry, cFill, cLit, cDark) {
      if (cDark) {
        ctx.fillStyle = cDark;
        ctx.beginPath(); ctx.ellipse(cx, cy + ry * 0.22, rx, ry * 0.95, 0, 0, Math.PI * 2); ctx.fill();
      }
      ctx.fillStyle = cFill;
      ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2); ctx.fill();
      if (cLit) {
        ctx.fillStyle = cLit;
        ctx.beginPath(); ctx.ellipse(cx - rx * 0.16, cy - ry * 0.25, rx * 0.65, ry * 0.52, -0.2, 0, Math.PI * 2); ctx.fill();
      }
    }

    const cDeep = '#c87a00', cShd = '#e89e0e', cMid = '#fed732', cLit = '#fff59d', cTop = '#fffde7';

    // Nimbus bottom hemisphere (rich amber-gold shadow lobes)
    cloudBall(0, 16, 44, 22, cShd, null, cDeep);
    cloudBall(-25, 14, 28, 19, cShd, null, cDeep);
    cloudBall(25, 14, 28, 19, cShd, null, cDeep);
    cloudBall(-13, 22, 24, 15, cShd, null, cDeep);
    cloudBall(13, 22, 24, 15, cShd, null, cDeep);
    cloudBall(0, 26, 26, 14, cShd, null, cDeep);

    // Nimbus middle body lobes (bright sunny golden yellow)
    cloudBall(-36, 6, 20, 16, cMid, cLit, cShd);
    cloudBall(36, 6, 20, 16, cMid, cLit, cShd);
    cloudBall(-24, 4, 28, 20, cMid, cLit, cShd);
    cloudBall(24, 4, 28, 20, cMid, cLit, cShd);
    cloudBall(0, 6, 44, 24, cMid, cLit, cShd);

    // Nimbus top puffy rim where Goku sits
    cloudBall(-15, -4, 28, 17, cMid, cTop, cShd);
    cloudBall(15, -4, 28, 17, cMid, cTop, cShd);
    cloudBall(0, -6, 30, 15, cLit, cTop, null);
    cloudBall(-30, -1, 18, 14, cMid, cTop, null);
    cloudBall(30, -1, 18, 14, cMid, cTop, null);

    // Traditional Japanese / Dragon Ball Cloud Swirl Engravings
    ctx.strokeStyle = '#8a5202';
    ctx.lineWidth = 1.6;
    function swirl(sx, sy, s = 1, flip = false) {
      ctx.save();
      ctx.translate(sx, sy);
      if (flip) ctx.scale(-1, 1);
      ctx.beginPath();
      ctx.arc(0, 0, 7.5 * s, 0, Math.PI * 1.3, false);
      ctx.arc(-2 * s, 1 * s, 4 * s, Math.PI * 1.3, Math.PI * 2.2, false);
      ctx.stroke();
      ctx.restore();
    }
    swirl(-22, 10, 1.0);
    swirl(22, 10, 1.0, true);
    swirl(0, 18, 0.95);
    swirl(-32, 6, 0.8);
    swirl(32, 6, 0.8, true);

    ctx.restore(); // end Nimbus

    // -------------------------------------------------------------
    // 4. LOWER BODY & LEGS (Cross-Legged on Cloud)
    // -------------------------------------------------------------
    ctx.save();

    // Purple pants mass
    ctx.fillStyle = giShade;
    ctx.beginPath(); ctx.ellipse(0, 8, 30, 14, 0, 0, Math.PI * 2); ctx.fill();

    // Left folded knee
    ctx.fillStyle = gi;
    ctx.strokeStyle = giShade;
    ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.ellipse(-16, 6, 14.5, 9.5, -0.22, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    // Highlight
    ctx.fillStyle = giLit;
    ctx.beginPath(); ctx.ellipse(-17, 4.5, 9, 5, -0.22, 0, Math.PI * 2); ctx.fill();

    // Right folded knee
    ctx.fillStyle = gi;
    ctx.beginPath(); ctx.ellipse(16, 6, 14.5, 9.5, 0.22, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    // Highlight
    ctx.fillStyle = giLit;
    ctx.beginPath(); ctx.ellipse(17, 4.5, 9, 5, 0.22, 0, Math.PI * 2); ctx.fill();

    // Slippers / Shoes tucked inward
    function slipper(sx, sy, ang) {
      ctx.save();
      ctx.translate(sx, sy);
      ctx.rotate(ang);
      ctx.fillStyle = shoe;
      ctx.strokeStyle = '#181924';
      ctx.lineWidth = 1.3;
      ctx.beginPath(); ctx.ellipse(0, 0, 9, 6.2, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      // White sole trim
      ctx.fillStyle = shoeTrim;
      ctx.beginPath(); ctx.ellipse(0, 1.5, 7, 4, 0, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
    slipper(-6.5, 9.5, -0.3);
    slipper(6.5, 9.5, 0.3);

    // White Obi / Belt Sash
    ctx.fillStyle = belt;
    ctx.strokeStyle = beltShade;
    ctx.lineWidth = 1.3;
    ctx.beginPath(); ctx.rect(-13, -4, 26, 6.5); ctx.fill(); ctx.stroke();

    // Center knot
    ctx.beginPath(); ctx.arc(0, -0.8, 4.2, 0, Math.PI * 2); ctx.fill(); ctx.stroke();

    // Sash tails hanging down
    ctx.beginPath();
    ctx.moveTo(-2, 2); ctx.lineTo(-6, 14); ctx.lineTo(-1.5, 14); ctx.lineTo(1, 2); ctx.fill(); ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(1, 2); ctx.lineTo(4, 15); ctx.lineTo(8, 14); ctx.lineTo(3, 2); ctx.fill(); ctx.stroke();

    ctx.restore(); // end legs

    // -------------------------------------------------------------
    // 5. TORSO & GI (Sleeveless V-Neck)
    // -------------------------------------------------------------
    ctx.save();

    // Torso base
    ctx.fillStyle = gi;
    ctx.strokeStyle = giShade;
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(-13.5, -20); ctx.lineTo(13.5, -20); ctx.lineTo(12, -3); ctx.lineTo(-12, -3);
    ctx.closePath();
    ctx.fill(); ctx.stroke();

    // Left side highlight
    ctx.fillStyle = giLit;
    ctx.beginPath();
    ctx.moveTo(-13.5, -20); ctx.lineTo(-6, -20); ctx.lineTo(-5, -3); ctx.lineTo(-12, -3);
    ctx.closePath();
    ctx.fill();

    // Bare chest V-neck
    ctx.fillStyle = skin;
    ctx.beginPath();
    ctx.moveTo(-7, -20); ctx.lineTo(7, -20); ctx.lineTo(0, -9); ctx.closePath();
    ctx.fill();

    // V-neck border line
    ctx.strokeStyle = giShade;
    ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(-7, -20); ctx.lineTo(0, -9); ctx.lineTo(7, -20); ctx.stroke();

    // Diagonal Power Pole strap
    ctx.strokeStyle = strap;
    ctx.lineWidth = 3.6;
    ctx.beginPath(); ctx.moveTo(-10, -19); ctx.lineTo(9, -3); ctx.stroke();
    ctx.strokeStyle = strapShade;
    ctx.lineWidth = 1.1;
    ctx.beginPath(); ctx.moveTo(-9, -19); ctx.lineTo(10, -3); ctx.stroke();

    ctx.restore(); // end torso

    // -------------------------------------------------------------
    // 6. ARMS & HANDS
    // -------------------------------------------------------------
    ctx.save();

    if (state === 'charge') {
      // Kamehameha Charge: Hands cupped at right hip with glowing Ki sphere
      ctx.fillStyle = skin;
      ctx.strokeStyle = skinShade;
      ctx.lineWidth = 1.4;

      // Right arm pulled back
      ctx.beginPath();
      ctx.moveTo(10, -17); ctx.quadraticCurveTo(22, -10, 18, 0); ctx.lineTo(12, 0); ctx.quadraticCurveTo(15, -9, 8, -14);
      ctx.fill(); ctx.stroke();

      // Right wristband
      ctx.fillStyle = wrist;
      ctx.beginPath(); ctx.roundRect(13, -3, 8, 6, 2); ctx.fill();

      // Left arm crossing over
      ctx.fillStyle = skin;
      ctx.beginPath();
      ctx.moveTo(-10, -17); ctx.quadraticCurveTo(5, -12, 14, -4); ctx.lineTo(10, -1); ctx.quadraticCurveTo(0, -8, -8, -14);
      ctx.fill(); ctx.stroke();

      // Left wristband
      ctx.fillStyle = wrist;
      ctx.beginPath(); ctx.roundRect(9, -6, 7, 5.5, 2); ctx.fill();

      // Glowing Cyan Ki Sphere
      const kiRad = 13 + Math.sin(t * 24) * 3;
      const kg = ctx.createRadialGradient(20, -2, 2, 20, -2, kiRad);
      kg.addColorStop(0, '#ffffff');
      kg.addColorStop(0.35, '#a5f3fc');
      kg.addColorStop(0.7, 'rgba(14, 165, 233, 0.8)');
      kg.addColorStop(1, 'rgba(14, 165, 233, 0)');
      ctx.fillStyle = kg;
      ctx.beginPath(); ctx.arc(20, -2, kiRad, 0, Math.PI * 2); ctx.fill();

    } else if (state === 'fire') {
      // Kamehameha Fire: Palms thrust forward
      ctx.fillStyle = skin;
      ctx.strokeStyle = skinShade;
      ctx.lineWidth = 1.3;

      ctx.beginPath(); ctx.moveTo(4, -17); ctx.lineTo(26, -11); ctx.lineTo(26, -5); ctx.lineTo(6, -11); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-4, -16); ctx.lineTo(24, -7); ctx.lineTo(24, -1); ctx.lineTo(-2, -10); ctx.fill(); ctx.stroke();

      ctx.fillStyle = wrist;
      ctx.beginPath(); ctx.roundRect(17, -12, 6.5, 6, 2); ctx.fill();
      ctx.beginPath(); ctx.roundRect(15, -7, 6.5, 6, 2); ctx.fill();

      ctx.fillStyle = skin;
      ctx.beginPath(); ctx.arc(27, -7, 6, 0, Math.PI * 2); ctx.fill();

    } else if (state === 'wave') {
      // Waving
      ctx.fillStyle = skin;
      ctx.beginPath(); ctx.ellipse(-13, 2, 5, 7, 0.3, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = wrist;
      ctx.beginPath(); ctx.roundRect(-16, -4, 7, 5, 1.5); ctx.fill();

      const waveAng = Math.sin(t * 9) * 0.28;
      ctx.save();
      ctx.translate(12, -18);
      ctx.rotate(0.55 + waveAng);
      ctx.fillStyle = skin;
      ctx.beginPath(); ctx.roundRect(0, -16, 7, 16, 3); ctx.fill();
      ctx.fillStyle = wrist;
      ctx.beginPath(); ctx.roundRect(-1, -16, 9, 6, 2); ctx.fill();
      ctx.fillStyle = skin;
      ctx.beginPath(); ctx.arc(3.5, -20, 6, 0, Math.PI * 2); ctx.fill();
      for (let f = -2; f <= 2; f++) {
        ctx.beginPath(); ctx.arc(3.5 + f * 2.2, -25, 1.8, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();

    } else if (state === 'eat') {
      // Eating
      ctx.fillStyle = skin;
      ctx.beginPath(); ctx.ellipse(-12, 1, 5, 7, 0.2, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = wrist;
      ctx.beginPath(); ctx.roundRect(-16, -5, 7, 5, 1.5); ctx.fill();

      ctx.fillStyle = skin;
      ctx.beginPath(); ctx.moveTo(11, -17); ctx.lineTo(8, -25); ctx.lineTo(2, -23); ctx.lineTo(7, -13); ctx.fill();
      ctx.fillStyle = wrist;
      ctx.beginPath(); ctx.roundRect(4, -26, 6, 5, 1.5); ctx.fill();

      // Bone & Meat
      ctx.save();
      ctx.translate(0, -27); ctx.rotate(0.2);
      ctx.fillStyle = '#f8fafc';
      ctx.beginPath();
      ctx.arc(-16, -3, 3.5, 0, Math.PI * 2); ctx.arc(-16, 3, 3.5, 0, Math.PI * 2);
      ctx.arc(16, -3, 3.5, 0, Math.PI * 2); ctx.arc(16, 3, 3.5, 0, Math.PI * 2); ctx.fill();
      ctx.fillRect(-15, -2, 30, 4);
      ctx.fillStyle = '#9e472a';
      ctx.strokeStyle = '#6d2b14';
      ctx.lineWidth = 1.3;
      ctx.beginPath(); ctx.ellipse(0, 0, 11, 8.5, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.restore();

    } else {
      // Idle: Hands resting on knees (Exact match to user screenshot)
      // Left arm
      ctx.fillStyle = skin;
      ctx.strokeStyle = skinShade;
      ctx.lineWidth = 1.3;
      ctx.beginPath();
      ctx.moveTo(-13, -18); ctx.quadraticCurveTo(-20, -6, -11, 2); ctx.lineTo(-6, 2); ctx.quadraticCurveTo(-14, -7, -8, -18);
      ctx.closePath(); ctx.fill(); ctx.stroke();

      // Left wristband
      ctx.fillStyle = wrist;
      ctx.beginPath(); ctx.roundRect(-15, -4, 7.5, 6, 2); ctx.fill();

      // Left hand on knee
      ctx.fillStyle = skin;
      ctx.beginPath(); ctx.ellipse(-9, 3, 5, 4.5, -0.2, 0, Math.PI * 2); ctx.fill();

      // Right arm
      ctx.fillStyle = skin;
      ctx.beginPath();
      ctx.moveTo(13, -18); ctx.quadraticCurveTo(20, -6, 11, 2); ctx.lineTo(6, 2); ctx.quadraticCurveTo(14, -7, 8, -18);
      ctx.closePath(); ctx.fill(); ctx.stroke();

      // Right wristband
      ctx.fillStyle = wrist;
      ctx.beginPath(); ctx.roundRect(8, -4, 7.5, 6, 2); ctx.fill();

      // Right hand on knee
      ctx.fillStyle = skin;
      ctx.beginPath(); ctx.ellipse(9, 3, 5, 4.5, 0.2, 0, Math.PI * 2); ctx.fill();
    }

    ctx.restore(); // end arms

    // -------------------------------------------------------------
    // 7. HEAD & CHUBBY 3/4 FACE
    // -------------------------------------------------------------
    ctx.save();
    ctx.translate(0, -32);

    // 3/4 Head base: Left cheek swells out chubbily, right jaw slopes to ear
    ctx.fillStyle = skin;
    ctx.beginPath();
    ctx.moveTo(-15, -12);
    ctx.bezierCurveTo(-22, -6, -21, 6, -12, 13);
    ctx.bezierCurveTo(-5, 17, 6, 17, 13, 11.5);
    ctx.bezierCurveTo(18, 5, 18, -6, 15, -12);
    ctx.closePath();
    ctx.fill();

    // Chin shadow
    ctx.fillStyle = skinShade;
    ctx.beginPath();
    ctx.moveTo(-9, 14.5); ctx.quadraticCurveTo(0, 17.5, 9, 13.5); ctx.quadraticCurveTo(0, 15, -9, 14.5);
    ctx.fill();

    // Cute blush ovals on cheeks
    ctx.fillStyle = skinBlush;
    ctx.beginPath(); ctx.ellipse(-11, 4, 4.8, 2.8, 0.1, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(11, 4, 4.8, 2.8, -0.1, 0, Math.PI * 2); ctx.fill();

    // Toriyama Anime Ear on right
    ctx.fillStyle = skin;
    ctx.strokeStyle = skinShade;
    ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.ellipse(17, -1, 6.5, 9.2, 0.15, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    // Ear inner swirl
    ctx.strokeStyle = skinShade;
    ctx.lineWidth = 1.3;
    ctx.beginPath(); ctx.arc(17, -1, 3.8, -Math.PI * 0.5, Math.PI * 0.6); ctx.stroke();

    // Left ear rim
    ctx.fillStyle = skin;
    ctx.beginPath(); ctx.ellipse(-17, -1, 3.5, 7, -0.15, 0, Math.PI * 2); ctx.fill();

    // -------------------------------------------------------------
    // 8. EYES & EXPRESSION
    // -------------------------------------------------------------
    const isAsleep = (state === 'asleep');

    if (state === 'eat' || isAsleep) {
      ctx.strokeStyle = ink;
      ctx.lineWidth = 2.2;
      ctx.beginPath(); ctx.arc(-8, -2, 5, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();
      ctx.beginPath(); ctx.arc(6, -2, 4.5, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();

      if (isAsleep) {
        ctx.strokeStyle = ink; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(-3, 8); ctx.lineTo(3, 8); ctx.stroke();
      } else {
        ctx.fillStyle = '#be123c';
        ctx.beginPath(); ctx.arc(0, 7.5, 5, 0, Math.PI * 2); ctx.fill();
      }
    } else {
      // Left Eye (3/4 perspective: larger)
      ctx.save();
      ctx.translate(-8, -1);
      // Sclera
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.moveTo(-6.5, 2); ctx.quadraticCurveTo(-5.5, -6, 1, -6); ctx.quadraticCurveTo(6, -5, 5, 3); ctx.quadraticCurveTo(0, 4.5, -6.5, 2);
      ctx.closePath(); ctx.fill();

      // Pupil
      ctx.fillStyle = ink;
      ctx.beginPath(); ctx.ellipse(0, -1, 3.2, 4.5, 0, 0, Math.PI * 2); ctx.fill();

      // Catchlight
      ctx.fillStyle = '#ffffff';
      ctx.beginPath(); ctx.arc(1.1, -2.4, 1.4, 0, Math.PI * 2); ctx.fill();

      // Upper Eyeliner
      ctx.strokeStyle = ink;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(-6.8, 1); ctx.quadraticCurveTo(-5, -6.5, 1.5, -6.5); ctx.quadraticCurveTo(5, -5.5, 6, -1);
      ctx.stroke();

      // Lower tick
      ctx.lineWidth = 1.3;
      ctx.beginPath(); ctx.moveTo(-2.5, 3.8); ctx.lineTo(3, 4.1); ctx.stroke();
      ctx.restore();

      // Right Eye
      ctx.save();
      ctx.translate(6, -1);
      // Sclera
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.moveTo(-5, 2); ctx.quadraticCurveTo(-4, -5.5, 1, -5.5); ctx.quadraticCurveTo(5, -5, 5, 2.5); ctx.quadraticCurveTo(0, 4, -5, 2);
      ctx.closePath(); ctx.fill();

      // Pupil
      ctx.fillStyle = ink;
      ctx.beginPath(); ctx.ellipse(0.5, -1, 2.8, 4.2, 0, 0, Math.PI * 2); ctx.fill();

      // Catchlight
      ctx.fillStyle = '#ffffff';
      ctx.beginPath(); ctx.arc(1.3, -2.4, 1.2, 0, Math.PI * 2); ctx.fill();

      // Upper Eyeliner
      ctx.strokeStyle = ink;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(-5, 1); ctx.quadraticCurveTo(-3, -6, 1.5, -6); ctx.quadraticCurveTo(4.5, -5, 5.5, -1);
      ctx.stroke();

      // Lower tick
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(-2, 3.6); ctx.lineTo(2.8, 3.8); ctx.stroke();
      ctx.restore();

      // Eyebrows
      ctx.strokeStyle = ink;
      ctx.lineWidth = 1.8;
      if (state === 'charge' || state === 'fire') {
        ctx.beginPath(); ctx.moveTo(-13, -8); ctx.lineTo(-4.5, -5.8); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(3, -5.8); ctx.lineTo(11, -8); ctx.stroke();
      } else {
        ctx.beginPath(); ctx.moveTo(-13, -7.5); ctx.quadraticCurveTo(-8, -9.5, -3.5, -6.5); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(3, -6.5); ctx.quadraticCurveTo(7, -9.5, 11.5, -7.5); ctx.stroke();
      }

      // Nose: Cute button tick
      ctx.fillStyle = ink;
      ctx.beginPath(); ctx.arc(-0.5, 3.5, 1.2, 0, Math.PI * 2); ctx.fill();

      // Mouth
      if (state === 'charge' || state === 'fire') {
        ctx.fillStyle = '#881337';
        ctx.strokeStyle = ink;
        ctx.lineWidth = 1.6;
        ctx.beginPath(); ctx.ellipse(0, 8, 5, 4.5, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(-3.5, 5.5, 7, 2.2); // teeth
        ctx.fillStyle = '#f43f5e';
        ctx.beginPath(); ctx.arc(0, 9.5, 3, Math.PI, Math.PI * 2); ctx.fill(); // tongue
      } else if (state === 'wave') {
        ctx.fillStyle = '#881337';
        ctx.strokeStyle = ink;
        ctx.lineWidth = 1.6;
        ctx.beginPath(); ctx.moveTo(-6.5, 7); ctx.quadraticCurveTo(0, 13, 6.5, 7); ctx.closePath();
        ctx.fill(); ctx.stroke();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(-4.5, 7, 9, 2.2);
        ctx.fillStyle = '#f43f5e';
        ctx.beginPath(); ctx.arc(0, 11, 3.2, Math.PI, Math.PI * 2); ctx.fill();
      } else {
        // Confident, sweet Toriyama smirk
        ctx.strokeStyle = ink;
        ctx.lineWidth = 1.8;
        ctx.beginPath(); ctx.moveTo(-5, 7); ctx.quadraticCurveTo(0, 9.5, 5, 7); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(4.5, 6.5); ctx.lineTo(6, 7.5); ctx.stroke();
      }
    }

    // -------------------------------------------------------------
    // 9. THE SIGNATURE TORIYAMA GOKU HAIRSTYLE (Exact DB Silhouette)
    // -------------------------------------------------------------
    ctx.fillStyle = hair;
    ctx.strokeStyle = ink;
    ctx.lineWidth = 1.8;

    ctx.beginPath();
    ctx.moveTo(15, -10);

    // Right ear tuft
    ctx.lineTo(21, -12);
    ctx.lineTo(17, -18);

    // Spike 4: Lower-right horizontal tuft
    ctx.lineTo(31, -16);
    ctx.lineTo(21, -24);

    // Spike 3: Big sharp middle-right spike
    ctx.lineTo(38, -28);
    ctx.lineTo(24, -36);

    // Spike 2: Giant sweeping upper-right spike
    ctx.lineTo(33, -48);
    ctx.lineTo(15, -45);

    // Spike 1: Crown peak pointing up-right
    ctx.lineTo(12, -58);
    ctx.lineTo(1, -49);

    // Left crown spike
    ctx.lineTo(-7, -54);
    ctx.lineTo(-11, -45);

    // Spike 5: Upper-left spike
    ctx.lineTo(-24, -46);
    ctx.lineTo(-18, -35);

    // Spike 6: Middle-left spike
    ctx.lineTo(-28, -30);
    ctx.lineTo(-18, -22);

    // Spike 7: Lower-left ear spike
    ctx.lineTo(-24, -14);
    ctx.lineTo(-16, -10);

    // Hairline & Bangs framing face
    ctx.lineTo(-12, -15);
    ctx.lineTo(-10, -7); // left bang
    ctx.lineTo(-6, -14);
    ctx.lineTo(-2, -5);  // center prominent bang
    ctx.lineTo(2, -14);
    ctx.lineTo(7, -8);   // right bang
    ctx.lineTo(11, -13);
    ctx.lineTo(15, -10);

    ctx.closePath();
    ctx.fill(); ctx.stroke();

    // Dark Indigo Specular Hair Sheen along primary spike ridges
    ctx.strokeStyle = hairLit;
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.moveTo(12, -54); ctx.lineTo(7, -47);
    ctx.moveTo(28, -44); ctx.lineTo(19, -39);
    ctx.moveTo(33, -27); ctx.lineTo(24, -25);
    ctx.moveTo(-19, -42); ctx.lineTo(-14, -36);
    ctx.stroke();

    ctx.restore(); // end head

    ctx.restore(); // end Goku
  }

  window.__render = function(st) {
    ctx.clearRect(0, 0, 400, 400);
    drawGokuReal({ x: 200, y: 220, r: 52, scale: 1.4, t: 1.5, state: st });
  };
</script>
</body>
</html>`;

  await page.setContent(html);
  const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';

  const testStates = [
    { name: 'goku_real_idle', state: 'idle' },
    { name: 'goku_real_charge', state: 'charge' },
    { name: 'goku_real_fire', state: 'fire' },
    { name: 'goku_real_wave', state: 'wave' },
  ];

  for (const s of testStates) {
    await page.evaluate(st => window.__render(st), s.state);
    const buf = await page.screenshot();
    await writeFile(join(artifactDir, `${s.name}.png`), buf);
    console.log(`Saved ${s.name}.png`);
  }

  await browser.close();
}

testGoku().catch(console.error);
