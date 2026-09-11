import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('Pikachu species definition, electric audio synthesis, dual attacks, and voice lines', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-pika-test-'));
  const generated = join(directory, 'pet.html');
  await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
  const html = await readFile(generated, 'utf8');

  // Verify registration in HTML
  assert.ok(html.includes("id: 'pikachu'"), 'Pikachu species must be registered');
  assert.ok(html.includes("kind: 'ground'"), 'Pikachu must be a ground kind');
  assert.ok(html.includes("thunderbolt"), 'Thunderbolt attack must be defined');
  assert.ok(html.includes("electroball"), 'Electro ball attack must be defined');
  assert.ok(html.includes("pikaPika()"), 'pikaPika audio synthesis must be defined');
  assert.ok(html.includes("pikaChuuu()"), 'pikaChuuu audio synthesis must be defined');
  assert.ok(html.includes("pikaChu()"), 'pikaChu audio synthesis must be defined');
  assert.ok(html.includes("pikaQuestion()"), 'pikaQuestion audio synthesis must be defined');
});

test('desktop Pikachu renders every pose without errors, switches species via host bridge, and executes dual electric attacks', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-pika-browser-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__pikaTest = { pet, state, draw, drawPikachu, ctx, canvas, petR, species, SPECIES, updatePet };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'pikachu', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const result = await page.evaluate(() => {
      const api = window.__pikaTest;
      const base = { ...api.pet };
      let frames = 0;
      const failures = [];

      // Verify species definition
      const sp = api.SPECIES.pikachu;
      if (!sp) return { ok: false, error: 'Pikachu not found in SPECIES' };
      if (sp.kind !== 'ground') return { ok: false, error: `Expected ground kind, got ${sp.kind}` };

      // Verify attack resolution for small vs boss bugs
      const smallAttack = sp.attack.resolve(false);
      const bossAttack = sp.attack.resolve(true);
      if (smallAttack.style !== 'electroball') return { ok: false, error: `Expected electroball for small bugs, got ${smallAttack.style}` };
      if (bossAttack.style !== 'thunderbolt') return { ok: false, error: `Expected thunderbolt for boss bugs, got ${bossAttack.style}` };
      if (smallAttack.sound !== 'pikaPika') return { ok: false, error: `Expected pikaPika sound for small bugs, got ${smallAttack.sound}` };
      if (bossAttack.sound !== 'pikaChuuu') return { ok: false, error: `Expected pikaChuuu sound for boss bugs, got ${bossAttack.sound}` };

      // Test poses across different states
      const poses = [
        { name: 'idle', facing: 1 },
        { name: 'idle-left', facing: -1 },
        { name: 'scamper-right', facing: 1, walking: true, walkDir: 1, dragSpeed: 60 },
        { name: 'scamper-left', facing: -1, walking: true, walkDir: -1, dragSpeed: 60 },
        { name: 'eating-berry', facing: 1, chew: 1, happy: 1 },
        { name: 'charge-electroball', facing: 1, zapCharge: 0.2, zapFull: 0.24, zapBoss: false, zapStyle: 'electroball' },
        { name: 'fire-electroball', facing: 1, zap: 0.18, zapBoss: false, zapStyle: 'electroball' },
        { name: 'charge-thunderbolt', facing: 1, zapCharge: 0.8, zapFull: 0.95, zapBoss: true, zapStyle: 'thunderbolt' },
        { name: 'fire-thunderbolt', facing: 1, zap: 0.3, zapBoss: true, zapStyle: 'thunderbolt' },
        { name: 'carried-dangle-right', facing: 1, carried: true, dragSpeed: 40 },
        { name: 'carried-dangle-left', facing: -1, carried: true, dragSpeed: 40 },
      ];

      for (const pose of poses) {
        Object.assign(api.pet, base, pose, { x: 160, y: 220, mode: 'walk', grounded: true });
        api.ctx.clearRect(0, 0, 320, 360);
        try {
          api.drawPikachu();
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

        // Pikachu should occupy substantial area
        if (opaque < 250) {
          failures.push(`Pose ${pose.name} rendered too few pixels: ${opaque}`);
        }
        frames++;
      }

      // Test host bridge species switching
      window.petNative.setSpecies('robot');
      const switchedToRobot = api.state.species === 'robot';
      window.petNative.setSpecies('pikachu');
      const switchedBackToPika = api.state.species === 'pikachu';

      return {
        ok: failures.length === 0 && switchedToRobot && switchedBackToPika,
        frames,
        failures,
        switchedToRobot,
        switchedBackToPika
      };
    });

    assert.equal(errors.length, 0, `Page errors: ${errors.join(', ')}`);
    assert.ok(result.ok, `Rendering failures: ${result.failures?.join('; ')}`);
    assert.equal(result.frames, 11, 'All 11 test poses rendered successfully');
    assert.ok(result.switchedToRobot, 'Host bridge successfully switches to robot');
    assert.ok(result.switchedBackToPika, 'Host bridge successfully switches back to pikachu');
  } finally {
    await browser.close();
  }
});
