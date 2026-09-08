import { chromium } from 'playwright';
import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

async function testSprite() {
  const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';
  const idleB64 = (await readFile(join(artifactDir, 'goku_pristine_idle.png'))).toString('base64');
  const flyB64 = (await readFile(join(artifactDir, 'goku_pristine_fly.png'))).toString('base64');

  const browser = await chromium.launch({
    channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome'
  });

  const page = await browser.newPage({
    viewport: { width: 400, height: 400 },
    deviceScaleFactor: 2
  });

  const html = `<!DOCTYPE html>
<html>
<head>
<style>
  body { margin: 0; background: #201e2e; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
  canvas { background: transparent; image-rendering: pixelated; }
</style>
</head>
<body>
<canvas id="c" width="400" height="400"></canvas>
<script>
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');

  const imgIdle = new Image();
  imgIdle.src = 'data:image/png;base64,${idleB64}';

  const imgFly = new Image();
  imgFly.src = 'data:image/png;base64,${flyB64}';

  window.__imagesLoaded = new Promise(resolve => {
    let count = 0;
    const check = () => { if (++count === 2) resolve(); };
    imgIdle.onload = check;
    imgFly.onload = check;
  });

  window.__drawPet = function(opts = {}) {
    ctx.clearRect(0, 0, 400, 400);

    const cx = opts.x || 200;
    const cy = opts.y || 220;
    const scale = opts.scale || 1.8;
    const facing = opts.facing || 1;
    const t = opts.t || 0;
    const state = opts.state || 'idle'; // 'idle', 'fly', 'charge', 'fire', 'kiblast', 'wave', 'eat'

    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(facing * scale, scale);

    // Nimbus floating bob
    const bob = Math.sin(t * 2.4) * 4;
    ctx.translate(0, bob);

    // Authentic Dragon Ball Golden Crescent Speed Trail behind Nimbus
    if (state === 'fly' || opts.speed > 50) {
      ctx.save();
      ctx.fillStyle = 'rgba(255, 235, 70, 0.7)';
      ctx.strokeStyle = '#e69f0a';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      // Curving golden ribbon arching up and back (matching DBZ anime references!)
      ctx.moveTo(-15, 22);
      ctx.bezierCurveTo(-45, 18, -75, -5, -60, -35);
      ctx.bezierCurveTo(-55, -45, -45, -55, -35, -52);
      ctx.bezierCurveTo(-48, -45, -58, -32, -52, -15);
      ctx.bezierCurveTo(-46, 5, -28, 18, -10, 26);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Trailing cloud puff specks
      ctx.fillStyle = '#ffea60';
      ctx.beginPath();
      ctx.arc(-65, -8, 4.5, 0, Math.PI * 2);
      ctx.arc(-82, -22, 3, 0, Math.PI * 2);
      ctx.arc(-42, -58, 2.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // Kamehameha Aura
    if (state === 'charge' || state === 'fire') {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const rad = 55 + Math.sin(t * 18) * 8;
      const glow = ctx.createRadialGradient(0, -10, 8, 0, -10, rad);
      glow.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
      glow.addColorStop(0.35, 'rgba(100, 225, 255, 0.6)');
      glow.addColorStop(0.7, 'rgba(0, 140, 255, 0.25)');
      glow.addColorStop(1, 'rgba(0, 70, 220, 0)');
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.ellipse(0, -10, rad * 1.15, rad * 1.35, 0, 0, Math.PI * 2);
      ctx.fill();

      // Electric spark arcs
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.6;
      for (let i = 0; i < 6; i++) {
        const ang = (i / 6) * Math.PI * 2 + Math.sin(t * 12 + i) * 0.4;
        const r1 = 20, r2 = rad * 0.85;
        ctx.beginPath();
        ctx.moveTo(Math.cos(ang) * r1, -10 + Math.sin(ang) * r1);
        ctx.lineTo(Math.cos(ang + 0.2) * (r1 + r2) * 0.5, -10 + Math.sin(ang + 0.2) * (r1 + r2) * 0.5);
        ctx.lineTo(Math.cos(ang) * r2, -10 + Math.sin(ang) * r2);
        ctx.stroke();
      }
      ctx.restore();
    }

    // Ki Blast Golden Aura
    if (state === 'kiblast') {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const rad = 45 + Math.sin(t * 22) * 6;
      const glow = ctx.createRadialGradient(15, -8, 5, 15, -8, rad);
      glow.addColorStop(0, '#ffffff');
      glow.addColorStop(0.4, 'rgba(255, 240, 90, 0.7)');
      glow.addColorStop(0.8, 'rgba(255, 150, 0, 0.3)');
      glow.addColorStop(1, 'rgba(255, 90, 0, 0)');
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(15, -8, rad, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // Select sprite
    const sprite = (state === 'fly') ? imgFly : imgIdle;
    const sw = sprite.width;
    const sh = sprite.height;

    // Draw sprite centered at origin
    // For idle: width 66, height 90
    // Center point should be roughly at waist/cloud connection
    ctx.imageSmoothingEnabled = false; // keep pixel-perfect crispness
    ctx.drawImage(sprite, -sw / 2, -sh * 0.62, sw, sh);

    // Overlays for specific actions:
    // Waving Hand
    if (state === 'wave') {
      ctx.save();
      const waveAngle = Math.sin(t * 9) * 0.35;
      ctx.translate(14, -26);
      ctx.rotate(0.5 + waveAngle);

      // Arm
      ctx.fillStyle = '#fedebb';
      ctx.fillRect(-2.5, -14, 5, 14);

      // Red wristband
      ctx.fillStyle = '#c9302c';
      ctx.fillRect(-3.5, -14, 7, 5);

      // Open hand with fingers
      ctx.fillStyle = '#fedebb';
      ctx.beginPath();
      ctx.arc(0, -18, 5, 0, Math.PI * 2);
      ctx.fill();
      for (let f = -2; f <= 2; f++) {
        ctx.beginPath();
        ctx.arc(f * 2, -22, 1.6, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    }

    // Eating Roast Meat Bone
    if (state === 'eat') {
      ctx.save();
      ctx.translate(2, -22);
      ctx.rotate(0.15 + Math.sin(t * 12) * 0.05);

      // Bone ends
      ctx.fillStyle = '#f5f5f5';
      ctx.beginPath();
      ctx.arc(-14, -2.5, 3, 0, Math.PI * 2);
      ctx.arc(-14, 2.5, 3, 0, Math.PI * 2);
      ctx.arc(14, -2.5, 3, 0, Math.PI * 2);
      ctx.arc(14, 2.5, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillRect(-13, -1.8, 26, 3.6);

      // Juicy roast meat
      ctx.fillStyle = '#9e472a';
      ctx.strokeStyle = '#632511';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.ellipse(0, 0, 9.5, 7.5, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }

    // Charging Kamehameha Ki Sphere
    if (state === 'charge') {
      ctx.save();
      const pulse = 10 + Math.sin(t * 30) * 3;
      const kg = ctx.createRadialGradient(16, -2, 2, 16, -2, pulse);
      kg.addColorStop(0, '#ffffff');
      kg.addColorStop(0.35, '#85f0ff');
      kg.addColorStop(0.7, 'rgba(0, 160, 255, 0.7)');
      kg.addColorStop(1, 'rgba(0, 80, 255, 0)');
      ctx.fillStyle = kg;
      ctx.beginPath();
      ctx.arc(16, -2, pulse, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // Firing Kamehameha beam start
    if (state === 'fire') {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      // Muzzle flash
      const mrad = 32 + Math.sin(t * 40) * 5;
      const mg = ctx.createRadialGradient(24, -4, 2, 24, -4, mrad);
      mg.addColorStop(0, '#ffffff');
      mg.addColorStop(0.35, '#95f5ff');
      mg.addColorStop(0.75, 'rgba(0, 180, 255, 0.8)');
      mg.addColorStop(1, 'rgba(0, 90, 255, 0)');
      ctx.fillStyle = mg;
      ctx.beginPath();
      ctx.arc(24, -4, mrad, 0, Math.PI * 2);
      ctx.fill();

      // Energy wave beam shooting right
      ctx.fillStyle = 'rgba(210, 250, 255, 0.95)';
      ctx.fillRect(24, -14, 180, 20);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(24, -8, 180, 8);
      ctx.restore();
    }

    // Firing Ki Blast orb
    if (state === 'kiblast') {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const krad = 18 + Math.sin(t * 30) * 3;
      const kg = ctx.createRadialGradient(28, -6, 2, 28, -6, krad);
      kg.addColorStop(0, '#ffffff');
      kg.addColorStop(0.35, '#fff066');
      kg.addColorStop(0.75, 'rgba(255, 160, 0, 0.8)');
      kg.addColorStop(1, 'rgba(255, 80, 0, 0)');
      ctx.fillStyle = kg;
      ctx.beginPath();
      ctx.arc(28, -6, krad, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    ctx.restore();
  };
</script>
</body>
</html>`;

  await page.setContent(html);
  await page.evaluate(() => window.__imagesLoaded);

  const testStates = [
    { name: 'sprite_goku_idle', state: 'idle' },
    { name: 'sprite_goku_fly', state: 'fly' },
    { name: 'sprite_goku_charge', state: 'charge' },
    { name: 'sprite_goku_fire', state: 'fire' },
    { name: 'sprite_goku_kiblast', state: 'kiblast' },
    { name: 'sprite_goku_wave', state: 'wave' },
    { name: 'sprite_goku_eat', state: 'eat' },
  ];

  for (const s of testStates) {
    await page.evaluate(st => window.__drawPet({ state: st, t: 2.0, scale: 2.2 }), s.state);
    const buf = await page.screenshot();
    await writeFile(join(artifactDir, `${s.name}.png`), buf);
    console.log(`Saved ${s.name}.png`);
  }

  await browser.close();
}

testSprite().catch(console.error);
