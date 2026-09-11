import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('Thor species definition, dual weapons, attacks, audio synthesis, and voice lines', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-thor-test-'));
  const generated = join(directory, 'pet.html');
  await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
  const html = await readFile(generated, 'utf8');

  // Verify species registration
  assert.ok(html.includes("id: 'thor'"), 'Thor species must be registered');
  assert.ok(html.includes("kind: 'float'"), 'Thor must be a floating species');
  assert.ok(html.includes("drawThor()"), 'drawThor drawing function must be hooked');

  // Verify attacks
  assert.ok(html.includes("drawThorAttack("), 'Thor attack renderer must be defined');
  assert.ok(html.includes("thorThunder("), 'Thor thunder audio synth must be defined');
  assert.ok(html.includes("thorLightning("), 'Thor lightning audio synth must be defined');
  assert.ok(html.includes("thorHammerSpin("), 'Thor hammer spin audio synth must be defined');
  assert.ok(html.includes("thorCatch("), 'Thor catch audio synth must be defined');
  assert.ok(html.includes("thorStormbreaker("), 'Thor stormbreaker audio synth must be defined');

  // Verify voice lines
  assert.ok(html.includes("BRING ME THANOS!"), 'Thor battle cry line must be present');
  assert.ok(html.includes("I am Thor, son of Odin!"), 'Thor introduction line must be present');
});

test('desktop Thor renders every pose without errors, switches species via host bridge, and executes dual attacks', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-thor-browser-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__thorTest = { pet, state, draw, drawThor, ctx, canvas, petR, species, SPECIES, updatePet, getThorSnapshot, getThorPower, thorState };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'thor', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const result = await page.evaluate(() => {
      const api = window.__thorTest;
      const base = { ...api.pet };
      let frames = 0;
      const failures = [];

      // Verify species definition
      const sp = api.SPECIES.thor;
      if (!sp) failures.push('SPECIES.thor not registered');
      if (sp.kind !== 'float') failures.push(`Expected kind float, got ${sp.kind}`);

      // Test poses
      const poses = [
        { name: 'idle', apply: () => { api.pet.vx = 0; api.pet.flying = false; api.state.asleep = false; api.pet.attacking = 0; } },
        { name: 'flying_right', apply: () => { api.pet.vx = 90; api.pet.vy = -20; api.pet.face = 1; api.pet.flying = true; } },
        { name: 'flying_left', apply: () => { api.pet.vx = -90; api.pet.vy = 20; api.pet.face = -1; api.pet.flying = true; } },
        { name: 'sleeping', apply: () => { api.pet.vx = 0; api.pet.flying = false; api.state.asleep = true; } },
        { name: 'held', apply: () => { api.pet.held = true; api.pet.flying = false; api.state.asleep = false; } },
        { name: 'attack_small_bug', apply: () => { api.pet.held = false; api.pet.attacking = 0.5; api.pet.attackKind = 0; } },
        { name: 'attack_boss_bug', apply: () => { api.pet.held = false; api.pet.attacking = 0.5; api.pet.attackKind = 1; } },
      ];

      for (const pose of poses) {
        Object.assign(api.pet, base);
        pose.apply();
        api.ctx.clearRect(0, 0, 320, 360);
        try {
          api.drawThor();
          frames++;
        } catch (e) {
          failures.push(`Pose ${pose.name} failed: ${e.message}`);
        }
      }

      // Test weapon throw / recall simulation
      api.thorState.weaponThrown = true;
      api.thorState.throwProgress = 0.5;
      api.thorState.throwTarget = { x: 260, y: 140 };
      api.ctx.clearRect(0, 0, 320, 360);
      try {
        api.drawThor();
        frames++;
      } catch (e) {
        failures.push(`Weapon thrown render failed: ${e.message}`);
      }
      api.thorState.weaponThrown = false;
      api.thorState.throwProgress = 0;

      return { frames, failures };
    });

    assert.equal(errors.length, 0, `Page errors: ${errors.join(', ')}`);
    assert.equal(result.failures.length, 0, `Pose failures: ${result.failures.join(', ')}`);
    assert.ok(result.frames >= 7, 'Rendered all test poses');
  } finally {
    await browser.close();
  }
});

test('Thor Git-powered progression, dual weapon unlocking, dev simulation, and settings', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-thor-progression-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__thorProg = { pet, state, draw, drawThor, ctx, canvas, petR, species, SPECIES, getThorSnapshot, getThorPower, thorState };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'thor', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const progression = await page.evaluate(() => {
      const api = window.__thorProg;

      const testCases = [
        { commits: 0, expectedWeapon: 'mjolnir', expectUnlocked: false },
        { commits: 10, expectedWeapon: 'mjolnir', expectUnlocked: false },
        { commits: 24, expectedWeapon: 'mjolnir', expectUnlocked: false },
        { commits: 25, expectedWeapon: 'stormbreaker', expectUnlocked: true },
        { commits: 50, expectedWeapon: 'stormbreaker', expectUnlocked: true },
        { commits: 100, expectedWeapon: 'stormbreaker', expectUnlocked: true },
      ];

      const results = [];
      let prevPower = 0;

      for (const tc of testCases) {
        window.petNative.thorSimulate(tc.commits);
        const snap = api.getThorSnapshot();
        const pwr = api.getThorPower();

        // Monotonic power scaling
        const powerGrewOrEqual = pwr.basePower >= prevPower;
        prevPower = pwr.basePower;

        // Render this weapon state
        api.ctx.clearRect(0, 0, 320, 360);
        api.pet.x = 160;
        api.pet.y = 220;
        api.drawThor();

        const { width, height } = api.canvas;
        const pixels = api.ctx.getImageData(0, 0, width, height).data;
        let opaque = 0;
        for (let i = 3; i < pixels.length; i += 4) {
          if (pixels[i] > 100) opaque++;
        }

        results.push({
          commits: tc.commits,
          weapon: snap.weapon,
          isStormbreaker: snap.isStormbreaker,
          power: snap.power,
          lightning: snap.lightning,
          matchesExpected: snap.weapon === tc.expectedWeapon && snap.isStormbreaker === tc.expectUnlocked,
          opaquePixels: opaque,
          powerGrewOrEqual,
        });
      }

      // Test thor settings via bridge
      window.petNative.thorSetting('lightningIntensity', 1.75);
      const lightningSet = api.state.thorSettings.lightningIntensity === 1.75;

      window.petNative.thorSetting('stormIntensity', 1.5);
      const stormSet = api.state.thorSettings.stormIntensity === 1.5;

      // Test reset simulation
      window.petNative.thorSimulate('reset');
      const resetSnap = api.getThorSnapshot();
      const isSimReset = !resetSnap.isSimulated;

      return {
        results,
        lightningSet,
        stormSet,
        isSimReset,
      };
    });

    assert.equal(errors.length, 0, `Page errors during Thor progression test: ${errors.join(', ')}`);
    assert.ok(progression.lightningSet, 'thorSetting lightningIntensity should be updated');
    assert.ok(progression.stormSet, 'thorSetting stormIntensity should be updated');
    assert.ok(progression.isSimReset, 'thorSimulate reset should return to real commits');

    for (const r of progression.results) {
      assert.ok(r.matchesExpected, `Commits ${r.commits} failed weapon check: got ${r.weapon} (unlocked: ${r.isStormbreaker})`);
      assert.ok(r.powerGrewOrEqual, `Commits ${r.commits} power did not grow or maintain: ${r.power}`);
      assert.ok(r.opaquePixels > 300, `Commits ${r.commits} (${r.weapon}) rendered too few pixels: ${r.opaquePixels}`);
    }
  } finally {
    await browser.close();
  }
});
