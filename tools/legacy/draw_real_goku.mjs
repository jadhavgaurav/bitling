import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';

async function testRender() {
  const browser = await chromium.launch({
    channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome'
  });

  const page = await browser.newPage({
    viewport: { width: 800, height: 800 },
    deviceScaleFactor: 2
  });

  const html = `<!DOCTYPE html>
<html>
<head>
<style>
  body { margin: 0; background: #201e2e; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
  canvas { background: transparent; }
</style>
</head>
<body>
<canvas id="c" width="400" height="400"></canvas>
<script>
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');

  // Realistic Toriyama Kid Goku on Flying Nimbus renderer
  function drawRealGoku(opts = {}) {
    const cx = opts.x || 200;
    const cy = opts.y || 230;
    const scale = opts.scale || 1.3;
    const t = opts.t || 0;
    const facing = opts.facing || 1; // 1 = right, -1 = left
    const state = opts.state || 'idle'; // 'idle', 'fly', 'charge', 'fire', 'kiblast', 'wave', 'eat'

    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(scale * facing, scale);

    // Subtle cloud bobbing & breathing
    const bob = Math.sin(t * 2.2) * 4;
    ctx.translate(0, bob);

    // Color Palette matching Dragon Ball anime & manga references
    const PALETTE = {
      // Skin
      skin: '#fedebb',
      skinShadow: '#f0b080',
      skinBlush: '#f99e82',
      // Hair
      hair: '#111217',
      hairSheen: '#282f48',
      hairLine: '#08090c',
      // Gi (Iconic Purple/Indigo from original DB anime & user screenshot)
      gi: opts.orangeGi ? '#ff5400' : '#4d3f84',
      giShadow: opts.orangeGi ? '#cb3b00' : '#372a66',
      giHighlight: opts.orangeGi ? '#ff7e38' : '#6554a8',
      // Belts & Straps
      belt: opts.orangeGi ? '#1c1c24' : '#f4f4f6',
      beltShadow: opts.orangeGi ? '#0f0f14' : '#c8c8ce',
      strap: '#e8dcbe',
      strapShadow: '#bfae8c',
      // Wristbands
      wrist: '#c9302c',
      wristShadow: '#8e1b18',
      // Power Pole (Nyoi-bo)
      pole: '#d32222',
      poleGold: '#fbc02d',
      poleShadow: '#941010',
      // Tail
      tail: '#79411d',
      tailShadow: '#52290d',
      // Shoes
      shoe: '#3d4052',
      shoeLight: '#656b87',
      shoeTrim: '#ececf0',
      // Nimbus Cloud
      cloudMain: '#fed732',
      cloudLight: '#ffec6e',
      cloudShadow: '#e89e0e',
      cloudDeep: '#bf7604',
      cloudLine: '#8a5202'
    };

    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    // -------------------------------------------------------------
    // 0. AURA (During Kamehameha Charge or Fire)
    // -------------------------------------------------------------
    if (state === 'charge' || state === 'fire') {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const auraPulse = 1 + Math.sin(t * 18) * 0.12;
      const auraRad = 85 * auraPulse;

      const grad = ctx.createRadialGradient(0, -35, 10, 0, -35, auraRad);
      grad.addColorStop(0, 'rgba(230, 255, 255, 0.85)');
      grad.addColorStop(0.35, 'rgba(80, 210, 255, 0.55)');
      grad.addColorStop(0.7, 'rgba(20, 140, 255, 0.25)');
      grad.addColorStop(1, 'rgba(10, 80, 240, 0)');

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.ellipse(0, -35, auraRad * 1.15, auraRad * 1.35, 0, 0, Math.PI * 2);
      ctx.fill();

      // Electric Ki bolts
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      for (let i = 0; i < 5; i++) {
        const seed = t * 12 + i * 2.1;
        const ang = (i / 5) * Math.PI * 2 + Math.sin(seed) * 0.4;
        const r1 = 30 + Math.cos(seed * 2) * 10;
        const r2 = auraRad * (0.75 + Math.sin(seed * 3) * 0.2);
        const x1 = Math.cos(ang) * r1, y1 = -35 + Math.sin(ang) * r1;
        const mx = Math.cos(ang + 0.2) * (r1 + r2) * 0.5, my = -35 + Math.sin(ang + 0.2) * (r1 + r2) * 0.5;
        const x2 = Math.cos(ang) * r2, y2 = -35 + Math.sin(ang) * r2;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(mx, my);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }
      ctx.restore();
    }

    // -------------------------------------------------------------
    // 1. POWER POLE (Back layer: sticks up-left behind Goku)
    // -------------------------------------------------------------
    ctx.save();
    // Sheath / pole angled diagonally across back
    const poleTilt = -0.65;
    ctx.translate(-8, -25);
    ctx.rotate(poleTilt);

    // Sheath strap cylinder
    ctx.fillStyle = PALETTE.pole;
    ctx.strokeStyle = PALETTE.poleShadow;
    ctx.lineWidth = 1.2;

    // Pole top sticking out
    ctx.beginPath();
    ctx.rect(-3.5, -46, 7, 24);
    ctx.fill();
    ctx.stroke();

    // Gold cap top
    ctx.fillStyle = PALETTE.poleGold;
    ctx.beginPath();
    ctx.rect(-4.5, -50, 9, 5);
    ctx.fill();
    ctx.stroke();

    // Sheath body
    ctx.fillStyle = '#9b1818';
    ctx.beginPath();
    ctx.rect(-4.5, -22, 9, 42);
    ctx.fill();
    ctx.stroke();

    // Gold cap bottom
    ctx.fillStyle = PALETTE.poleGold;
    ctx.beginPath();
    ctx.rect(-4.5, 20, 9, 5);
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    // -------------------------------------------------------------
    // 2. MONKEY TAIL (Curving out from back-right)
    // -------------------------------------------------------------
    ctx.save();
    const tailWag = Math.sin(t * 3.5) * 0.15;
    ctx.strokeStyle = PALETTE.tail;
    ctx.lineWidth = 7.5;
    ctx.beginPath();
    ctx.moveTo(12, -8);
    // Graceful curve up and around
    ctx.bezierCurveTo(24, -12, 38 + tailWag * 10, -22, 42 + tailWag * 12, -10);
    ctx.bezierCurveTo(45 + tailWag * 14, 2, 34, 10, 26, 4);
    ctx.stroke();

    // Tail shadow underside
    ctx.strokeStyle = PALETTE.tailShadow;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(13, -6);
    ctx.bezierCurveTo(24, -10, 36 + tailWag * 10, -18, 40 + tailWag * 12, -8);
    ctx.stroke();
    ctx.restore();

    // -------------------------------------------------------------
    // 3. FLYING NIMBUS (Kintoun) - Volumetric Fluffy Golden Cloud
    // -------------------------------------------------------------
    ctx.save();
    ctx.translate(0, 18);

    // Nimbus trailing speed trail if moving fast
    if (state === 'fly' || opts.speed > 0) {
      ctx.save();
      ctx.fillStyle = 'rgba(255, 225, 60, 0.4)';
      ctx.beginPath();
      ctx.moveTo(-35, -5);
      ctx.quadraticCurveTo(-65, -15, -90, -4);
      ctx.quadraticCurveTo(-60, 10, -32, 12);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }

    // Cloud Base Puffs (Rich 3D golden cloud with shadows and highlights)
    function drawCloudPuff(x, y, rx, ry, col) {
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    // Underside deep amber shading
    drawCloudPuff(0, 12, 46, 20, PALETTE.cloudDeep);
    drawCloudPuff(-24, 10, 26, 17, PALETTE.cloudDeep);
    drawCloudPuff(25, 10, 26, 17, PALETTE.cloudDeep);

    // Mid warm amber shading
    drawCloudPuff(0, 8, 48, 22, PALETTE.cloudShadow);
    drawCloudPuff(-26, 6, 28, 18, PALETTE.cloudShadow);
    drawCloudPuff(26, 6, 28, 18, PALETTE.cloudShadow);
    drawCloudPuff(-15, 16, 24, 14, PALETTE.cloudShadow);
    drawCloudPuff(15, 16, 24, 14, PALETTE.cloudShadow);

    // Main golden yellow puffs
    drawCloudPuff(0, 2, 45, 20, PALETTE.cloudMain);
    drawCloudPuff(-25, 0, 26, 17, PALETTE.cloudMain);
    drawCloudPuff(25, 0, 26, 17, PALETTE.cloudMain);
    drawCloudPuff(-38, 2, 16, 13, PALETTE.cloudMain);
    drawCloudPuff(38, 2, 16, 13, PALETTE.cloudMain);
    drawCloudPuff(-12, -6, 26, 15, PALETTE.cloudMain);
    drawCloudPuff(14, -6, 26, 15, PALETTE.cloudMain);

    // Top pillowy light puffs
    drawCloudPuff(-8, -4, 28, 14, PALETTE.cloudLight);
    drawCloudPuff(12, -4, 26, 13, PALETTE.cloudLight);
    drawCloudPuff(0, -7, 24, 11, PALETTE.cloudLight);

    // Traditional Japanese / Dragon Ball cloud swirl lines
    ctx.strokeStyle = PALETTE.cloudLine;
    ctx.lineWidth = 1.4;

    function drawCloudSwirl(x, y, scale = 1, flip = false) {
      ctx.save();
      ctx.translate(x, y);
      if (flip) ctx.scale(-1, 1);
      ctx.beginPath();
      ctx.arc(0, 0, 8 * scale, 0, Math.PI * 1.3, false);
      ctx.arc(-2 * scale, 1 * scale, 4 * scale, Math.PI * 1.3, Math.PI * 2.2, false);
      ctx.stroke();
      ctx.restore();
    }

    drawCloudSwirl(-22, 6, 0.9);
    drawCloudSwirl(22, 6, 0.9, true);
    drawCloudSwirl(0, 14, 0.85);
    drawCloudSwirl(-32, 2, 0.7);
    drawCloudSwirl(32, 2, 0.7, true);

    ctx.restore(); // end Nimbus

    // -------------------------------------------------------------
    // 4. LOWER BODY & LEGS (Seated Cross-Legged on Cloud)
    // -------------------------------------------------------------
    ctx.save();

    // Purple pants folded cross-legged
    ctx.fillStyle = PALETTE.giShadow;
    ctx.beginPath();
    ctx.ellipse(0, 8, 30, 14, 0, 0, Math.PI * 2);
    ctx.fill();

    // Left folded leg
    ctx.fillStyle = PALETTE.gi;
    ctx.strokeStyle = PALETTE.giShadow;
    ctx.lineWidth = 1.5;

    ctx.beginPath();
    ctx.ellipse(-16, 7, 14, 9, -0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Right folded leg
    ctx.beginPath();
    ctx.ellipse(16, 7, 14, 9, 0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Shoes / Kung-fu slippers (cross-legged soles facing inward/forward)
    function drawSlipper(x, y, ang) {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(ang);
      // Dark slipper base
      ctx.fillStyle = PALETTE.shoe;
      ctx.strokeStyle = '#22242f';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.ellipse(0, 0, 8.5, 6, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      // White sole bottom
      ctx.fillStyle = PALETTE.shoeTrim;
      ctx.beginPath();
      ctx.ellipse(0, 1.2, 6.5, 4, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    drawSlipper(-7, 10, -0.3);
    drawSlipper(7, 10, 0.3);

    // White tied belt sash at waist
    ctx.fillStyle = PALETTE.belt;
    ctx.strokeStyle = PALETTE.beltShadow;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.rect(-13, -3, 26, 6);
    ctx.fill();
    ctx.stroke();

    // Belt knot & hanging tails
    ctx.beginPath();
    ctx.arc(0, 0, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Tails draping down
    ctx.beginPath();
    ctx.moveTo(-2, 2);
    ctx.lineTo(-5, 14);
    ctx.lineTo(-1, 14);
    ctx.lineTo(1, 2);
    ctx.fill();
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(1, 2);
    ctx.lineTo(4, 15);
    ctx.lineTo(8, 14);
    ctx.lineTo(3, 2);
    ctx.fill();
    ctx.stroke();

    ctx.restore(); // end legs/belt

    // -------------------------------------------------------------
    // 5. TORSO & GI (Sleeveless V-Neck with Chest Skin)
    // -------------------------------------------------------------
    ctx.save();

    // Torso base shape
    ctx.fillStyle = PALETTE.gi;
    ctx.strokeStyle = PALETTE.giShadow;
    ctx.lineWidth = 1.5;

    ctx.beginPath();
    ctx.moveTo(-14, -20);
    ctx.lineTo(14, -20);
    ctx.lineTo(12, -2);
    ctx.lineTo(-12, -2);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // V-Neck opening showing chest skin
    ctx.fillStyle = PALETTE.skin;
    ctx.beginPath();
    ctx.moveTo(-7, -20);
    ctx.lineTo(7, -20);
    ctx.lineTo(0, -9);
    ctx.closePath();
    ctx.fill();

    // V-neck border collar
    ctx.strokeStyle = PALETTE.giShadow;
    ctx.lineWidth = 1.3;
    ctx.beginPath();
    ctx.moveTo(-7, -20);
    ctx.lineTo(0, -9);
    ctx.lineTo(7, -20);
    ctx.stroke();

    // Diagonal strap across chest for power pole
    ctx.strokeStyle = PALETTE.strap;
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.moveTo(-11, -19);
    ctx.lineTo(9, -2);
    ctx.stroke();

    ctx.strokeStyle = PALETTE.strapShadow;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(-10, -19);
    ctx.lineTo(10, -2);
    ctx.stroke();

    ctx.restore(); // end torso

    // -------------------------------------------------------------
    // 6. ARMS & HANDS (Articulated based on state)
    // -------------------------------------------------------------
    ctx.save();

    if (state === 'charge') {
      // Kamehameha charging: Both hands pulled back to the right hip, cupped!
      // Right arm pulled deep back
      ctx.fillStyle = PALETTE.skin;
      ctx.strokeStyle = PALETTE.skinShadow;
      ctx.lineWidth = 1.2;

      // Arm
      ctx.beginPath();
      ctx.moveTo(10, -17);
      ctx.quadraticCurveTo(22, -10, 18, 0);
      ctx.lineTo(12, 0);
      ctx.quadraticCurveTo(15, -9, 8, -14);
      ctx.fill();

      // Red wristband
      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(13, -3, 8, 6);

      // Left arm crossing over
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.moveTo(-10, -17);
      ctx.quadraticCurveTo(5, -12, 14, -4);
      ctx.lineTo(10, -1);
      ctx.quadraticCurveTo(0, -8, -8, -14);
      ctx.fill();

      // Left red wristband
      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(9, -6, 7, 5);

      // Glowing Ki Sphere between cupped hands
      const kiGlow = 14 + Math.sin(t * 25) * 3;
      const kg = ctx.createRadialGradient(20, -2, 2, 20, -2, kiGlow);
      kg.addColorStop(0, '#ffffff');
      kg.addColorStop(0.4, '#a2f5ff');
      kg.addColorStop(0.8, 'rgba(0, 180, 255, 0.6)');
      kg.addColorStop(1, 'rgba(0, 120, 255, 0)');
      ctx.fillStyle = kg;
      ctx.beginPath();
      ctx.arc(20, -2, kiGlow, 0, Math.PI * 2);
      ctx.fill();

    } else if (state === 'fire') {
      // Kamehameha firing: Both arms thrust forward to the right!
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.moveTo(4, -17);
      ctx.lineTo(26, -11);
      ctx.lineTo(26, -5);
      ctx.lineTo(6, -11);
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(-4, -16);
      ctx.lineTo(24, -7);
      ctx.lineTo(24, -1);
      ctx.lineTo(-2, -10);
      ctx.fill();

      // Wristbands
      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(18, -12, 6, 6);
      ctx.fillRect(16, -7, 6, 6);

      // Cupped palms firing forward
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.arc(28, -7, 6, 0, Math.PI * 2);
      ctx.fill();

    } else if (state === 'kiblast') {
      // Single hand thrust forward with golden Ki orb
      // Left hand on knee
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.ellipse(-12, -4, 5, 8, 0.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(-16, -9, 8, 5);

      // Right arm thrusting forward
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.moveTo(10, -17);
      ctx.lineTo(28, -12);
      ctx.lineTo(28, -6);
      ctx.lineTo(8, -11);
      ctx.fill();

      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(20, -13, 7, 6);

      // Open palm
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.ellipse(30, -9, 5, 6, 0, 0, Math.PI * 2);
      ctx.fill();

      // Golden Ki blast orb
      const kg = ctx.createRadialGradient(38, -9, 2, 38, -9, 15);
      kg.addColorStop(0, '#ffffff');
      kg.addColorStop(0.4, '#ffee55');
      kg.addColorStop(0.8, 'rgba(255, 170, 0, 0.7)');
      kg.addColorStop(1, 'rgba(255, 100, 0, 0)');
      ctx.fillStyle = kg;
      ctx.beginPath();
      ctx.arc(38, -9, 15, 0, Math.PI * 2);
      ctx.fill();

    } else if (state === 'wave') {
      // Waving: Right arm up high waving!
      // Left arm resting on knee
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.ellipse(-13, 2, 5, 7, 0.3, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(-17, -4, 7, 5);

      // Right arm reaching up
      const waveAngle = Math.sin(t * 8) * 0.25;
      ctx.save();
      ctx.translate(12, -18);
      ctx.rotate(0.6 + waveAngle);

      // Upper arm
      ctx.fillStyle = PALETTE.skin;
      ctx.fillRect(0, -16, 7, 16);

      // Red wristband
      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(-1, -16, 9, 6);

      // Hand with spread waving fingers
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.arc(3.5, -20, 6, 0, Math.PI * 2);
      ctx.fill();
      // Fingers
      for (let f = -2; f <= 2; f++) {
        ctx.beginPath();
        ctx.arc(3.5 + f * 2.2, -25, 1.8, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();

    } else if (state === 'eat') {
      // Holding anime roast meat bone
      // Left arm resting
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.ellipse(-12, 1, 5, 7, 0.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(-16, -5, 7, 5);

      // Right arm holding meat to mouth
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.moveTo(11, -17);
      ctx.lineTo(8, -25);
      ctx.lineTo(2, -23);
      ctx.lineTo(7, -13);
      ctx.fill();

      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(4, -26, 6, 5);

      // Giant Anime Meat Bone
      ctx.save();
      ctx.translate(0, -27);
      ctx.rotate(0.2);
      // Bone ends
      ctx.fillStyle = '#f5f5f5';
      ctx.beginPath();
      ctx.arc(-16, -3, 3.5, 0, Math.PI * 2);
      ctx.arc(-16, 3, 3.5, 0, Math.PI * 2);
      ctx.arc(16, -3, 3.5, 0, Math.PI * 2);
      ctx.arc(16, 3, 3.5, 0, Math.PI * 2);
      ctx.fill();
      // White bone shaft
      ctx.fillRect(-15, -2, 30, 4);
      // Roast meat cylinder
      ctx.fillStyle = '#9e472a';
      ctx.strokeStyle = '#6d2b14';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.ellipse(0, 0, 11, 8.5, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.restore();

    } else {
      // Default: Idle resting hands on knees (matching user screenshot goku_crop.png!)
      // Left arm
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.moveTo(-13, -18);
      ctx.quadraticCurveTo(-20, -6, -11, 2);
      ctx.lineTo(-6, 2);
      ctx.quadraticCurveTo(-14, -7, -8, -18);
      ctx.fill();

      // Left red wristband
      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(-15, -4, 7, 6);

      // Left hand on knee with fingers
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.ellipse(-9, 3, 5, 4.5, -0.2, 0, Math.PI * 2);
      ctx.fill();

      // Right arm
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.moveTo(13, -18);
      ctx.quadraticCurveTo(20, -6, 11, 2);
      ctx.lineTo(6, 2);
      ctx.quadraticCurveTo(14, -7, 8, -18);
      ctx.fill();

      // Right red wristband
      ctx.fillStyle = PALETTE.wrist;
      ctx.fillRect(8, -4, 7, 6);

      // Right hand on knee with fingers
      ctx.fillStyle = PALETTE.skin;
      ctx.beginPath();
      ctx.ellipse(9, 3, 5, 4.5, 0.2, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.restore(); // end arms

    // -------------------------------------------------------------
    // 7. HEAD & FACE (The Real Toriyama Son Goku!)
    // -------------------------------------------------------------
    ctx.save();
    ctx.translate(0, -32);

    // Head base - soft round chibi anime jaw
    ctx.fillStyle = PALETTE.skin;
    ctx.strokeStyle = PALETTE.skinShadow;
    ctx.lineWidth = 1;

    ctx.beginPath();
    // 3/4 perspective: cheek swells out gently on left, ear on right
    ctx.moveTo(-16, -12);
    ctx.bezierCurveTo(-21, -6, -20, 6, -12, 12);
    ctx.bezierCurveTo(-5, 16, 5, 16, 12, 11);
    ctx.bezierCurveTo(18, 5, 18, -6, 15, -12);
    ctx.closePath();
    ctx.fill();

    // Chin shadow under jaw
    ctx.fillStyle = PALETTE.skinShadow;
    ctx.beginPath();
    ctx.moveTo(-8, 14);
    ctx.quadraticCurveTo(0, 17, 8, 13);
    ctx.quadraticCurveTo(0, 14.5, -8, 14);
    ctx.fill();

    // Big Toriyama Anime Ear on the right
    ctx.fillStyle = PALETTE.skin;
    ctx.strokeStyle = PALETTE.skinShadow;
    ctx.lineWidth = 1.3;
    ctx.beginPath();
    ctx.ellipse(17, -1, 6.5, 9, 0.15, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Inner ear cartilage swirl
    ctx.strokeStyle = PALETTE.skinShadow;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.arc(17, -1, 4, -Math.PI * 0.5, Math.PI * 0.6);
    ctx.stroke();

    // Left ear (smaller, edge visible)
    ctx.fillStyle = PALETTE.skin;
    ctx.beginPath();
    ctx.ellipse(-17, -1, 3.5, 7, -0.15, 0, Math.PI * 2);
    ctx.fill();

    // -------------------------------------------------------------
    // 8. EYES & FACIAL EXPRESSIONS (Authentic Toriyama Eyes!)
    // -------------------------------------------------------------
    const isBlink = opts.blink || false;

    if (state === 'eat') {
      // Happy eating closed eyes (^ ^)
      ctx.strokeStyle = '#111217';
      ctx.lineWidth = 2.2;
      // Left eye arc
      ctx.beginPath();
      ctx.arc(-8, -2, 5, Math.PI * 1.1, Math.PI * 1.9);
      ctx.stroke();
      // Right eye arc
      ctx.beginPath();
      ctx.arc(6, -2, 4.5, Math.PI * 1.1, Math.PI * 1.9);
      ctx.stroke();

      // Cheerful open mouth chewing
      ctx.fillStyle = '#a62424';
      ctx.beginPath();
      ctx.arc(0, 7, 5, 0, Math.PI * 2);
      ctx.fill();

    } else if (isBlink) {
      // Blinking lines
      ctx.strokeStyle = '#111217';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(-13, 0);
      ctx.lineTo(-4, 0);
      ctx.moveTo(2, 0);
      ctx.lineTo(10, 0);
      ctx.stroke();

    } else {
      // Authentic DBZ Almond Eyes
      // Left Eye
      ctx.save();
      ctx.translate(-8, -1);

      // White Sclera
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.moveTo(-7, 2);
      ctx.quadraticCurveTo(-6, -6, 1, -6);
      ctx.quadraticCurveTo(6, -5, 5, 3);
      ctx.quadraticCurveTo(0, 4.5, -7, 2);
      ctx.closePath();
      ctx.fill();

      // Black Pupil (Vertical Ellipse)
      ctx.fillStyle = '#111217';
      ctx.beginPath();
      ctx.ellipse(0, -1, 3.2, 4.5, 0, 0, Math.PI * 2);
      ctx.fill();

      // Crisp White Specular Catchlight
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(1, -2.5, 1.4, 0, Math.PI * 2);
      ctx.fill();

      // Thick Toriyama upper eyeliner
      ctx.strokeStyle = '#111217';
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(-7, 1);
      ctx.quadraticCurveTo(-5, -6.5, 1.5, -6.5);
      ctx.quadraticCurveTo(5, -5.5, 6, -1);
      ctx.stroke();

      // Lower eye tick
      ctx.lineWidth = 1.3;
      ctx.beginPath();
      ctx.moveTo(-3, 3.8);
      ctx.lineTo(3, 4.2);
      ctx.stroke();

      ctx.restore();

      // Right Eye (Slightly smaller in 3/4 perspective)
      ctx.save();
      ctx.translate(6, -1);

      // White Sclera
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.moveTo(-5, 2);
      ctx.quadraticCurveTo(-4, -5.5, 1, -5.5);
      ctx.quadraticCurveTo(5, -5, 5, 2.5);
      ctx.quadraticCurveTo(0, 4, -5, 2);
      ctx.closePath();
      ctx.fill();

      // Black Pupil
      ctx.fillStyle = '#111217';
      ctx.beginPath();
      ctx.ellipse(0.5, -1, 2.8, 4.2, 0, 0, Math.PI * 2);
      ctx.fill();

      // Specular Catchlight
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(1.3, -2.5, 1.2, 0, Math.PI * 2);
      ctx.fill();

      // Upper eyeliner
      ctx.strokeStyle = '#111217';
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(-5, 1);
      ctx.quadraticCurveTo(-3, -6, 1.5, -6);
      ctx.quadraticCurveTo(4.5, -5, 5.5, -1);
      ctx.stroke();

      // Lower tick
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(-2, 3.6);
      ctx.lineTo(3, 3.8);
      ctx.stroke();

      ctx.restore();

      // Eyebrows
      ctx.strokeStyle = '#111217';
      ctx.lineWidth = 1.8;

      if (state === 'charge' || state === 'fire') {
        // Fierce battle angled brows
        ctx.beginPath();
        ctx.moveTo(-14, -8);
        ctx.lineTo(-5, -6);
        ctx.moveTo(3, -6);
        ctx.lineTo(11, -8);
        ctx.stroke();
      } else {
        // Friendly curved Toriyama brows
        ctx.beginPath();
        ctx.moveTo(-14, -7);
        ctx.quadraticCurveTo(-8, -9.5, -4, -6.5);
        ctx.moveTo(3, -6.5);
        ctx.quadraticCurveTo(7, -9.5, 12, -7.5);
        ctx.stroke();
      }

      // Nose: Cute tiny anime tick
      ctx.fillStyle = '#111217';
      ctx.beginPath();
      ctx.arc(-0.5, 3.5, 1.1, 0, Math.PI * 2);
      ctx.fill();

      // Mouth
      if (state === 'charge' || state === 'fire') {
        // Wide open shouting mouth!
        ctx.fillStyle = '#8b1e1e';
        ctx.strokeStyle = '#111217';
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.ellipse(0, 8, 5, 4.5, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        // White upper teeth bar
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(-3.5, 5.5, 7, 2.2);
        // Pink tongue
        ctx.fillStyle = '#e86a7a';
        ctx.beginPath();
        ctx.arc(0, 9.5, 3, Math.PI, Math.PI * 2);
        ctx.fill();
      } else if (state === 'wave') {
        // Big happy toothy grin!
        ctx.fillStyle = '#8b1e1e';
        ctx.strokeStyle = '#111217';
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(-7, 7);
        ctx.quadraticCurveTo(0, 13, 7, 7);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        // Teeth
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(-5, 7, 10, 2.2);
        // Tongue
        ctx.fillStyle = '#e86a7a';
        ctx.beginPath();
        ctx.arc(0, 11, 3.2, Math.PI, Math.PI * 2);
        ctx.fill();
      } else {
        // Confident, pleasant boy smirk (Toriyama smile)
        ctx.strokeStyle = '#111217';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.moveTo(-5, 7);
        ctx.quadraticCurveTo(0, 9.5, 5, 7);
        ctx.stroke();
        // Corner tick
        ctx.beginPath();
        ctx.moveTo(4.5, 6.5);
        ctx.lineTo(6, 7.5);
        ctx.stroke();
      }
    }

    // -------------------------------------------------------------
    // 9. THE ICONIC TORIYAMA KID GOKU HAIRSTYLE (Exact Silhouette!)
    // -------------------------------------------------------------
    ctx.fillStyle = PALETTE.hair;
    ctx.strokeStyle = PALETTE.hairLine;
    ctx.lineWidth = 1.8;

    ctx.beginPath();
    // Start at forehead above right ear
    ctx.moveTo(15, -10);

    // Ear tuft
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

    // --- Forehead hairline & bangs ---
    // Left forehead temple
    ctx.lineTo(-12, -15);
    // Bang 1 (left framing tuft)
    ctx.lineTo(-10, -7);
    ctx.lineTo(-6, -14);
    // Bang 2 (Prominent Center Bang curving between eyes)
    ctx.lineTo(-2, -5);
    ctx.lineTo(2, -14);
    // Bang 3 (Right framing tuft)
    ctx.lineTo(7, -8);
    ctx.lineTo(11, -13);
    ctx.lineTo(15, -10);

    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Dark Indigo Specular Hair Sheen along primary spikes
    ctx.strokeStyle = PALETTE.hairSheen;
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    // Highlights along right spike ridges
    ctx.moveTo(12, -54);
    ctx.lineTo(7, -47);
    ctx.moveTo(28, -44);
    ctx.lineTo(19, -39);
    ctx.moveTo(33, -27);
    ctx.lineTo(24, -25);
    ctx.moveTo(-19, -42);
    ctx.lineTo(-14, -36);
    ctx.stroke();

    ctx.restore(); // end head

    ctx.restore(); // end whole Goku
  }

  // Draw 6 states
  const states = ['idle', 'fly', 'charge', 'fire', 'kiblast', 'wave'];
  window.__renderState = function(st) {
    ctx.clearRect(0, 0, 400, 400);
    drawRealGoku({ x: 200, y: 220, scale: 2.2, t: 2.0, state: st });
  };
</script>
</body>
</html>`;

  await page.setContent(html);

  const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';

  const testStates = [
    { name: 'real_goku_idle', state: 'idle' },
    { name: 'real_goku_charge', state: 'charge' },
    { name: 'real_goku_fire', state: 'fire' },
    { name: 'real_goku_kiblast', state: 'kiblast' },
    { name: 'real_goku_wave', state: 'wave' },
    { name: 'real_goku_eat', state: 'eat' },
  ];

  for (const s of testStates) {
    await page.evaluate(st => window.__renderState(st), s.state);
    const buf = await page.screenshot();
    await writeFile(join(artifactDir, `${s.name}.png`), buf);
    console.log(`Saved ${s.name}.png`);
  }

  await browser.close();
}

testRender().catch(console.error);
