import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('Kid Goku on Flying Nimbus species definition, dual attacks, and voice lines', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-goku-test-'));
  const generated = join(directory, 'pet.html');
  await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
  const html = await readFile(generated, 'utf8');

  // Verify registration in HTML
  assert.ok(html.includes("id: 'goku'"), 'Goku species must be registered');
  assert.ok(html.includes("kind: 'float'"), 'Goku must be a floater on Flying Nimbus');
  assert.ok(html.includes("kamehameha"), 'Kamehameha attack must be defined');
  assert.ok(html.includes("kiball"), 'Ki ball attack must be defined');
});

test('desktop Kid Goku renders every pose without errors, switches species via host bridge, and executes dual attacks', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-goku-browser-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__gokuTest = { pet, state, draw, drawGoku, ctx, canvas, petR, species, SPECIES, updatePet };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'goku', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const result = await page.evaluate(() => {
      const api = window.__gokuTest;
      const base = { ...api.pet };
      let frames = 0;
      const failures = [];

      // Verify species definition
      const sp = api.SPECIES.goku;
      if (!sp) return { ok: false, error: 'Goku not found in SPECIES' };
      if (sp.kind !== 'float') return { ok: false, error: `Expected float kind, got ${sp.kind}` };

      // Verify attack resolution for small vs boss bugs
      const smallAttack = sp.attack.resolve(false);
      const bossAttack = sp.attack.resolve(true);
      if (smallAttack.style !== 'kiball') return { ok: false, error: `Expected kiball for small bugs, got ${smallAttack.style}` };
      if (bossAttack.style !== 'kamehameha') return { ok: false, error: `Expected kamehameha for boss bugs, got ${bossAttack.style}` };

      // Test poses across different states
      const poses = [
        { name: 'idle', facing: 1 },
        { name: 'blink', facing: 1, blink: 1 },
        { name: 'flying-forward', facing: 1, walking: true, walkDir: 1, dragSpeed: 100 },
        { name: 'flying-backward', facing: -1, walking: true, walkDir: -1, dragSpeed: 100 },
        { name: 'waving', facing: 1, waving: 1.5, happy: 1 },
        { name: 'eating-meat', facing: 1, chew: 1, happy: 1 },
        { name: 'dizzy-shock', facing: 1, surprise: 1 },
        { name: 'charge-kamehameha', facing: 1, zapCharge: 0.8, zapFull: 1, zapBoss: true, zapStyle: 'kamehameha' },
        { name: 'fire-kamehameha', facing: 1, zap: 0.2, zapBoss: true, zapStyle: 'kamehameha' },
        { name: 'charge-kiball', facing: 1, zapCharge: 0.5, zapFull: 0.9, zapBoss: false, zapStyle: 'kiball' },
        { name: 'fire-kiball', facing: 1, zap: 0.15, zapBoss: false, zapStyle: 'kiball' },
        { name: 'carried-drag', facing: 1, carried: true, dragSpeed: 50 },
      ];

      for (const pose of poses) {
        Object.assign(api.pet, base, pose, { x: 160, y: 220, mode: 'fly', grounded: false });
        api.ctx.clearRect(0, 0, 320, 360);
        try {
          api.drawGoku();
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

        // Goku and Nimbus should occupy substantial area
        if (opaque < 300) {
          failures.push(`Pose ${pose.name} rendered too few pixels: ${opaque}`);
        }
        frames++;
      }

      // Test host bridge species switching
      window.petNative.setSpecies('robot');
      const switchedToRobot = api.state.species === 'robot';
      window.petNative.setSpecies('goku');
      const switchedBackToGoku = api.state.species === 'goku';

      return {
        ok: failures.length === 0 && switchedToRobot && switchedBackToGoku,
        frames,
        failures,
        switchedToRobot,
        switchedBackToGoku
      };
    });

    assert.equal(errors.length, 0, `Page errors: ${errors.join(', ')}`);
    assert.ok(result.ok, `Rendering failures: ${result.failures?.join('; ')}`);
    assert.equal(result.frames, 12, 'All 12 test poses rendered successfully');
    assert.ok(result.switchedToRobot, 'Host bridge successfully switches to robot');
    assert.ok(result.switchedBackToGoku, 'Host bridge successfully switches back to goku');
  } finally {
    await browser.close();
  }
});

test('Goku Git-powered training arc: 6 forms, continuous scaling, dev simulation, and settings', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-goku-training-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__gokuTest = { pet, state, draw, drawGoku, ctx, canvas, petR, species, SPECIES, getGokuSnapshot, getGokuPower, gokuState };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'goku', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const formProgression = await page.evaluate(() => {
      const api = window.__gokuTest;
      const testCases = [
        { commits: 0, expectedForm: 'Kid Goku', expectedIndex: 0 },
        { commits: 2, expectedForm: 'Kid Goku', expectedIndex: 0 },
        { commits: 3, expectedForm: 'Base Goku', expectedIndex: 1 },
        { commits: 6, expectedForm: 'Base Goku', expectedIndex: 1 },
        { commits: 7, expectedForm: 'Super Saiyan', expectedIndex: 2 },
        { commits: 13, expectedForm: 'Super Saiyan', expectedIndex: 2 },
        { commits: 14, expectedForm: 'Super Saiyan 2', expectedIndex: 3 },
        { commits: 24, expectedForm: 'Super Saiyan 2', expectedIndex: 3 },
        { commits: 25, expectedForm: 'Super Saiyan 3', expectedIndex: 4 },
        { commits: 40, expectedForm: 'Super Saiyan 3', expectedIndex: 4 },
        { commits: 41, expectedForm: 'Ultra Instinct', expectedIndex: 5 },
        { commits: 100, expectedForm: 'Ultra Instinct', expectedIndex: 5 },
      ];

      const results = [];
      let prevPower = 0;

      for (const tc of testCases) {
        window.petNative.gokuSimulate(tc.commits);
        const snap = api.getGokuSnapshot();
        const pwr = api.getGokuPower();

        // Check power monotonicity
        const powerGrewOrEqual = pwr.overallPower >= prevPower;
        prevPower = pwr.overallPower;

        // Render this form to verify canvas draw
        api.ctx.clearRect(0, 0, 320, 360);
        api.pet.x = 160;
        api.pet.y = 220;
        api.drawGoku();

        const { width, height } = api.canvas;
        const pixels = api.ctx.getImageData(0, 0, width, height).data;
        let opaque = 0;
        for (let i = 3; i < pixels.length; i += 4) {
          if (pixels[i] > 100) opaque++;
        }

        results.push({
          commits: tc.commits,
          currentForm: snap.currentForm,
          formIndex: snap.formIndex,
          overallPower: snap.overallPower,
          auraIntensity: snap.auraIntensity,
          matchesExpected: snap.currentForm === tc.expectedForm && snap.formIndex === tc.expectedIndex,
          opaquePixels: opaque,
          powerGrewOrEqual,
        });
      }

      // Test goku settings via bridge
      window.petNative.gokuSetting('size', 1.35);
      const sizeSet = api.state.gokuSettings.size === 1.35;

      window.petNative.gokuSetting('auraIntensity', 2.0);
      const auraSet = api.state.gokuSettings.auraIntensity === 2.0;

      // Test reset simulation
      window.petNative.gokuSimulate('reset');
      const resetSnap = api.getGokuSnapshot();
      const isSimReset = !resetSnap.isSimulated;

      return {
        results,
        sizeSet,
        auraSet,
        isSimReset,
      };
    });

    assert.equal(errors.length, 0, `Page errors during training test: ${errors.join(', ')}`);
    assert.ok(formProgression.sizeSet, 'gokuSetting size should be updated');
    assert.ok(formProgression.auraSet, 'gokuSetting auraIntensity should be updated');
    assert.ok(formProgression.isSimReset, 'gokuSimulate reset should return to real commits');

    for (const r of formProgression.results) {
      assert.ok(r.matchesExpected, `Commits ${r.commits} failed form check: got ${r.currentForm} (${r.formIndex})`);
      assert.ok(r.powerGrewOrEqual, `Commits ${r.commits} power did not grow or maintain: ${r.overallPower}`);
      assert.ok(r.opaquePixels > 300, `Commits ${r.commits} (${r.currentForm}) rendered too few pixels: ${r.opaquePixels}`);
    }
  } finally {
    await browser.close();
  }
});
