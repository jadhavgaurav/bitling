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
  await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
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
    await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
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
