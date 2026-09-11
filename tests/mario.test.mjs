import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('Super Mario species definition, audio synths, and evolution mechanics', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-mario-test-'));
  const generated = join(directory, 'pet.html');
  await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
  const html = await readFile(generated, 'utf8');

  // Verify registration in HTML
  assert.ok(html.includes("id: 'mario'"), 'Mario species must be registered');
  assert.ok(html.includes("name: 'Mario'"), 'Mario species name must be Mario');
  assert.ok(html.includes("kind: 'ground'"), 'Mario must be a grounded walker');
  assert.ok(html.includes("stomp"), 'Stomp attack must be defined');
  assert.ok(html.includes("fireball"), 'Fireball attack must be defined');
  assert.ok(html.includes("marioJump"), 'marioJump audio synth must be defined');
  assert.ok(html.includes("marioCoin"), 'marioCoin audio synth must be defined');
  assert.ok(html.includes("marioPowerUp"), 'marioPowerUp audio synth must be defined');
  assert.ok(html.includes("marioPowerDown"), 'marioPowerDown audio synth must be defined');
  assert.ok(html.includes("marioFireball"), 'marioFireball audio synth must be defined');
  assert.ok(html.includes("marioPipe"), 'marioPipe audio synth must be defined');
  assert.ok(html.includes("marioStomp"), 'marioStomp audio synth must be defined');
  assert.ok(html.includes("marioClear"), 'marioClear audio synth must be defined');
  assert.ok(html.includes("It's-a me, Mario!"), 'Mario iconic voice line must be included');
  assert.ok(html.includes("Mamma mia"), 'Mamma mia voice line must be included');
  assert.ok(html.includes("triggerMarioCommitPowerUp"), 'Commit power-up trigger must be defined');
  assert.ok(html.includes("scoreMarioWarpPipe"), 'Warp pipe course clear must be defined');
});

test('desktop Mario renders sprite poses across all stages, sizes and attacks in browser', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-mario-browser-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__marioTest = { pet, state, marioState, triggerMarioCommitPowerUp, scoreMarioWarpPipe, updateMarioSimulation, drawMario, drawMarioAttack, ctx, canvas, petR, species, SPECIES, updatePet };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'mario', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const result = await page.evaluate(() => {
      const api = window.__marioTest;
      const base = { ...api.pet };
      const failures = [];

      // 1. Verify species definition
      const sp = api.SPECIES.mario;
      if (!sp) return { ok: false, error: 'Mario not found in SPECIES' };
      if (sp.kind !== 'ground') return { ok: false, error: `Expected ground kind, got ${sp.kind}` };

      // 2. Verify evolution stages attack resolution
      api.marioState.stage = 0; // Small Mario
      const smallAttack = sp.attack.resolve(false);
      if (smallAttack.style !== 'stomp') failures.push(`Expected stomp for small Mario, got ${smallAttack.style}`);

      api.marioState.stage = 2; // Fire Mario
      const fireAttack = sp.attack.resolve(false);
      if (fireAttack.style !== 'fireball') failures.push(`Expected fireball for Fire Mario, got ${fireAttack.style}`);

      const bossAttack = sp.attack.resolve(true);
      if (bossAttack.style !== 'fireball') failures.push(`Expected fireball for boss attack, got ${bossAttack.style}`);

      // 3. Test rendering all evolution stages across all poses
      const stages = [0, 1, 2, 3]; // Small, Super, Fire, Star
      const poses = [
        { name: 'idle', walking: false, vy: 0, vx: 0 },
        { name: 'walk', walking: true, vy: 0, vx: 30 },
        { name: 'sprint', walking: true, vy: 0, vx: 80 },
        { name: 'jump', walking: false, vy: -60, vx: 0 },
        { name: 'throw', walking: false, vy: 0, vx: 0, zap: 0.5, zapStyle: 'fireball' },
        { name: 'asleep', walking: false, vy: 0, vx: 0, asleep: true }
      ];

      // 4. Test across multiple pet sizes (0.8, 1.0, 1.2, 1.6)
      const testSizes = [0.8, 1.0, 1.2, 1.6];

      for (const size of testSizes) {
        api.state.petSize = size;
        for (const st of stages) {
          api.marioState.stage = st;
          for (const pose of poses) {
            Object.assign(api.pet, base, {
              x: 160,
              y: 220,
              mode: pose.walking ? 'walk' : 'idle',
              grounded: !pose.vy,
              facing: 1,
              walking: pose.walking,
              vx: pose.vx,
              vy: pose.vy,
              zap: pose.zap || 0,
              zapStyle: pose.zapStyle || null,
              asleep: pose.asleep || false
            });
            api.ctx.clearRect(0, 0, 320, 360);
            try {
              api.drawMario();
            } catch (e) {
              failures.push(`Render failure [size=${size}, stage=${st}, pose=${pose.name}]: ${e.message}`);
            }
          }
        }
      }

      // 5. Test attacks execution across sizes
      for (const size of testSizes) {
        api.state.petSize = size;
        try {
          api.drawMarioAttack(api.petR(), 1, false, 'stomp');
          api.drawMarioAttack(api.petR(), 1, true, 'fireball');
        } catch (e) {
          failures.push(`Attack execution error at size ${size}: ${e.message}`);
        }
      }

      // 6. Test commit power-up & warp pipe triggers
      try {
        api.triggerMarioCommitPowerUp();
        if (!api.marioState.qblockActive) failures.push('QBlock should be active after commit trigger');
        api.scoreMarioWarpPipe('Course Clear test');
        if (!api.marioState.pipeActive) failures.push('Warp pipe should be active after push score');
      } catch (e) {
        failures.push(`Trigger error: ${e.message}`);
      }

      // 7. Test simulation step
      try {
        api.updateMarioSimulation(0.016);
      } catch (e) {
        failures.push(`updateMarioSimulation error: ${e.message}`);
      }

      return {
        ok: failures.length === 0,
        failures,
        stage: api.marioState.stage,
        qblockActive: api.marioState.qblockActive,
        pipeActive: api.marioState.pipeActive
      };
    });

    assert.equal(errors.length, 0, `Page errors: ${errors.join('; ')}`);
    assert.ok(result.ok, `Simulation failures: ${result.failures.join('; ')}`);
    assert.ok(result.qblockActive, 'Question block must be active');
    assert.ok(result.pipeActive, 'Warp pipe must be active');
  } finally {
    await browser.close();
  }
});
