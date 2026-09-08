import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('Cristiano Ronaldo species definition, dual attacks, and soccer audio synth', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-ronaldo-test-'));
  const generated = join(directory, 'pet.html');
  await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
  const html = await readFile(generated, 'utf8');

  // Verify registration in HTML
  assert.ok(html.includes("id: 'ronaldo'"), 'Ronaldo species must be registered');
  assert.ok(html.includes("kind: 'ground'"), 'Ronaldo must be a grounded walker');
  assert.ok(html.includes("knuckleball"), 'Knuckleball attack must be defined');
  assert.ok(html.includes("siuuu"), 'SIUUUU attack must be defined');
  assert.ok(html.includes("ronaldoWhistle"), 'ronaldoWhistle audio synth must be defined');
  assert.ok(html.includes("ronaldoKick"), 'ronaldoKick audio synth must be defined');
  assert.ok(html.includes("ronaldoSiuuu"), 'ronaldoSiuuu audio synth must be defined');
  assert.ok(html.includes("ronaldoChirp"), 'ronaldoChirp audio synth must be defined');
  assert.ok(html.includes("SIUUUU"), 'SIUUUU voice lines must be included');
  assert.ok(html.toLowerCase().includes("bicho") || html.toLowerCase().includes("calma"), 'Iconic CR7 voice lines must be included');
});

test('desktop Ronaldo renders every sprite pose without errors, switches species via host bridge, and executes dual attacks', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-ronaldo-browser-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__ronaldoTest = { pet, state, draw, drawRonaldo, drawRonaldoAttack, ctx, canvas, petR, species, SPECIES, updatePet };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'ronaldo', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const result = await page.evaluate(() => {
      const api = window.__ronaldoTest;
      const base = { ...api.pet };
      let frames = 0;
      const failures = [];

      // Verify species definition
      const sp = api.SPECIES.ronaldo;
      if (!sp) return { ok: false, error: 'Ronaldo not found in SPECIES' };
      if (sp.kind !== 'ground') return { ok: false, error: `Expected ground kind, got ${sp.kind}` };

      // Verify attack resolution for small vs boss bugs
      const smallAttack = sp.attack.resolve(false);
      const bossAttack = sp.attack.resolve(true);
      if (smallAttack.style !== 'knuckleball') return { ok: false, error: `Expected knuckleball for small bugs, got ${smallAttack.style}` };
      if (bossAttack.style !== 'siuuu') return { ok: false, error: `Expected siuuu for boss bugs, got ${bossAttack.style}` };

      // Test poses across different states
      const poses = [
        { name: 'idle-with-ball', facing: 1 },
        { name: 'blink', facing: 1, blink: 1 },
        { name: 'dribble-sprint-forward', facing: 1, walking: true, walkDir: 1, vx: 50 },
        { name: 'dribble-sprint-backward', facing: -1, walking: true, walkDir: -1, vx: -50 },
        { name: 'waving-thumbs-up', facing: 1, waving: 1.5, happy: 1 },
        { name: 'eating-snack', facing: 1, chew: 1, happy: 1 },
        { name: 'dizzy-confusion', facing: 1, surprise: 1 },
        { name: 'wide-stance-charge-boss', facing: 1, zapCharge: 0.8, zapFull: 1, zapBoss: true, zapStyle: 'siuuu' },
        { name: 'fire-siuuu-celebration', facing: 1, zap: 0.25, zapBoss: true, zapStyle: 'siuuu', zapX: 160, zapY: 200, zapTargetX: 300, zapTargetY: 200 },
        { name: 'knuckleball-charge', facing: 1, zapCharge: 0.4, zapFull: 0.8, zapBoss: false, zapStyle: 'knuckleball' },
        { name: 'fire-knuckleball', facing: 1, zap: 0.15, zapBoss: false, zapStyle: 'knuckleball', zapX: 160, zapY: 200, zapTargetX: 280, zapTargetY: 200 },
        { name: 'carried-scruff', facing: 1, carried: true, dragSpeed: 50 },
      ];

      for (const pose of poses) {
        Object.assign(api.pet, base, pose, { x: 160, y: 220, mode: 'walk', grounded: true });
        api.ctx.clearRect(0, 0, 320, 360);
        try {
          api.drawRonaldo();
          if (pose.zap > 0) {
            api.drawRonaldoAttack(pose.zapStyle, pose.zapBoss, pose.zap);
          }
        } catch (e) {
          failures.push(`Pose ${pose.name} threw error: ${e.message}`);
          continue;
        }

        const { width, height } = api.canvas;
        const pixels = api.ctx.getImageData(0, 0, width, height).data;
        let opaque = 0;
        for (let i = 3; i < pixels.length; i += 4) {
          if (pixels[i] > 100) opaque++;
        }

        // Ronaldo should occupy substantial area
        if (opaque < 250) {
          failures.push(`Pose ${pose.name} rendered too few pixels: ${opaque}`);
        }
        frames++;
      }

      // Test host bridge species switching
      window.petNative.setSpecies('robot');
      const switchedToRobot = api.state.species === 'robot';
      window.petNative.setSpecies('ronaldo');
      const switchedBackToRonaldo = api.state.species === 'ronaldo';

      return {
        ok: failures.length === 0 && switchedToRobot && switchedBackToRonaldo,
        frames,
        failures,
        switchedToRobot,
        switchedBackToRonaldo
      };
    });

    assert.equal(errors.length, 0, `Page errors: ${errors.join(', ')}`);
    assert.ok(result.ok, `Rendering failures: ${result.failures?.join('; ')}`);
    assert.equal(result.frames, 12, 'All 12 test poses rendered successfully');
    assert.ok(result.switchedToRobot, 'Host bridge successfully switches to robot');
    assert.ok(result.switchedBackToRonaldo, 'Host bridge successfully switches back to ronaldo');
  } finally {
    await browser.close();
  }
});

test('free soccer ball physics, interactive kicking, bug striking, and theatrical goal push celebration', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-ronaldo-ball-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__ronaldoTest = { pet, state, draw, drawRonaldo, ronaldoBall, ronaldoGoal, scoreRonaldoGoal, updateRonaldoBall, bugs, groundY, W };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'ronaldo', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const result = await page.evaluate(() => {
      const api = window.__ronaldoTest;
      const b = api.ronaldoBall;
      if (!b) return { ok: false, error: 'ronaldoBall not found' };
      if (!b.active) return { ok: false, error: 'ronaldoBall should be active' };
      if (b.radius !== 13) return { ok: false, error: `Expected radius 13, got ${b.radius}` };

      // Test free ball movement and gravity
      b.x = 100;
      b.y = 50;
      b.vx = 80;
      b.vy = 0;
      api.updateRonaldoBall(0.05);
      if (b.x <= 100 || b.y <= 50) return { ok: false, error: 'Ball did not update with velocity and gravity' };

      // Test bug killing strike
      const bug = { id: 999, x: 180, y: api.groundY - 10, alive: true, hp: 1, maxHp: 1 };
      api.bugs.push(bug);
      b.x = 120;
      b.y = api.groundY - b.radius;
      b.vx = 400;
      b.vy = 0;
      b.state = 'strike';
      b.strikeStyle = 'knuckleball';
      b.strikeTimer = 0;
      b.targetBug = bug;

      // Update simulation step: ball hits the bug
      api.updateRonaldoBall(0.15);
      const bugKilled = !bug.alive;
      const ballRebounded = b.state === 'idle' && b.vy < 0; // popped up with backspin

      // Test goal push celebration
      api.scoreRonaldoGoal("TEST GOAL!");
      const goalActive = api.ronaldoGoal.active;
      const goalShooting = b.state === 'goal_shot';

      // Advance goal simulation to score into net
      for (let step = 0; step < 20; step++) {
        api.updateRonaldoBall(0.05);
      }
      const netHit = b.state === 'in_net' || api.ronaldoGoal.netBulge > 0;

      return {
        ok: bugKilled && ballRebounded && goalActive && goalShooting && netHit,
        bugKilled,
        ballRebounded,
        goalActive,
        goalShooting,
        netHit
      };
    });

    assert.equal(errors.length, 0, `Page errors: ${errors.join(', ')}`);
    assert.ok(result.ok, `Soccer ball simulation failure: ${JSON.stringify(result)}`);
    assert.ok(result.bugKilled, 'Striking ball killed the bug');
    assert.ok(result.ballRebounded, 'Ball rebounded off the bug with pop-up trajectory');
    assert.ok(result.goalActive, 'Goal event activated');
    assert.ok(result.goalShooting, 'Ball shot towards goal net');
    assert.ok(result.netHit, 'Ball bulged the net upon goal');
  } finally {
    await browser.close();
  }
});

