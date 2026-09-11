import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('Iron Man species definition, arcade audio buffers, dual attacks, and Jarvis voice lines', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-ironman-test-'));
  const generated = join(directory, 'pet.html');
  await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
  const html = await readFile(generated, 'utf8');

  // Verify registration in HTML
  assert.ok(html.includes("id: 'ironman'"), 'Iron Man species must be registered');
  assert.ok(html.includes("name: 'Iron Man'"), 'Iron Man name must be registered');
  assert.ok(html.includes("kind: 'float'"), 'Iron Man must be a floating kind');
  assert.ok(html.includes("accent: '#ff2222'"), 'Iron Man must have Stark crimson accent');
  assert.ok(html.includes("unibeam"), 'Unibeam attack must be defined');
  assert.ok(html.includes("repulsor"), 'Repulsor attack must be defined');
  assert.ok(html.includes("iroRepulsor()"), 'iroRepulsor audio method must be defined');
  assert.ok(html.includes("iroUnibeam()"), 'iroUnibeam audio method must be defined');
  assert.ok(html.includes("jarvisOnline()"), 'jarvisOnline audio method must be defined');
  assert.ok(html.includes("jarvisAsYouWish()"), 'jarvisAsYouWish audio method must be defined');
});

test('desktop Iron Man renders every pose without errors, switches species via host bridge, and executes dual repulsor/unibeam attacks', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-ironman-browser-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__ironmanTest = { pet, state, draw, drawIronMan, ctx, canvas, petR, species, SPECIES, updatePet };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'ironman', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const result = await page.evaluate(() => {
      const api = window.__ironmanTest;
      const base = { ...api.pet };
      let frames = 0;
      const failures = [];

      // Verify species definition
      const sp = api.SPECIES.ironman;
      if (!sp) return { ok: false, error: 'Iron Man not found in SPECIES' };
      if (sp.kind !== 'float') return { ok: false, error: `Expected float kind, got ${sp.kind}` };
      if (sp.accent !== '#ff2222') return { ok: false, error: `Expected #ff2222 accent, got ${sp.accent}` };

      // Verify dual attack resolution for small vs boss bugs
      const smallAttack = sp.attack.resolve(false);
      const bossAttack = sp.attack.resolve(true);
      if (smallAttack.style !== 'repulsor') return { ok: false, error: `Expected repulsor for small bugs, got ${smallAttack.style}` };
      if (bossAttack.style !== 'unibeam') return { ok: false, error: `Expected unibeam for boss bugs, got ${bossAttack.style}` };
      if (smallAttack.sound !== 'iroRepulsor') return { ok: false, error: `Expected iroRepulsor sound for small bugs, got ${smallAttack.sound}` };
      if (bossAttack.sound !== 'iroUnibeam') return { ok: false, error: `Expected iroUnibeam sound for boss bugs, got ${bossAttack.sound}` };

      // Test poses across different states
      const poses = [
        { name: 'idle-hover-right', facing: 1 },
        { name: 'idle-hover-left', facing: -1 },
        { name: 'flight-bank-right', facing: 1, walking: true, walkDir: 1, dragSpeed: 60, ironmanSpeed: 80 },
        { name: 'flight-bank-left', facing: -1, walking: true, walkDir: -1, dragSpeed: 60, ironmanSpeed: 80 },
        { name: 'charge-repulsor', facing: 1, zapCharge: 0.2, zapFull: 0.22, zapBoss: false, zapStyle: 'repulsor' },
        { name: 'fire-repulsor', facing: 1, zap: 0.18, zapBoss: false, zapStyle: 'repulsor' },
        { name: 'charge-unibeam', facing: 1, zapCharge: 0.8, zapFull: 0.95, zapBoss: true, zapStyle: 'unibeam' },
        { name: 'fire-unibeam', facing: 1, zap: 0.3, zapBoss: true, zapStyle: 'unibeam' },
        { name: 'carried-dangle-right', facing: 1, carried: true, dragSpeed: 40 },
        { name: 'carried-dangle-left', facing: -1, carried: true, dragSpeed: 40 },
        { name: 'inspect-gauntlet', facing: 1, working: true },
      ];

      for (const pose of poses) {
        Object.assign(api.pet, base, pose, { x: 160, y: 220, mode: 'fly', grounded: false });
        api.ctx.clearRect(0, 0, 320, 360);
        try {
          api.drawIronMan();
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

        // Iron Man should occupy substantial area
        if (opaque < 250) {
          failures.push(`Pose ${pose.name} rendered too few pixels: ${opaque}`);
        }
        frames++;
      }

      // Test host bridge species switching
      window.petNative.setSpecies('robot');
      const switchedToRobot = api.state.species === 'robot';
      window.petNative.setSpecies('ironman');
      const switchedBackToIronMan = api.state.species === 'ironman';

      return {
        ok: failures.length === 0 && switchedToRobot && switchedBackToIronMan,
        frames,
        failures,
        switchedToRobot,
        switchedBackToIronMan
      };
    });

    assert.equal(errors.length, 0, `Page errors: ${errors.join(', ')}`);
    assert.ok(result.ok, `Rendering failures: ${result.failures?.join('; ')}`);
    assert.equal(result.frames, 11, 'All 11 test poses rendered successfully');
    assert.ok(result.switchedToRobot, 'Host bridge successfully switches to robot');
    assert.ok(result.switchedBackToIronMan, 'Host bridge successfully switches back to ironman');
  } finally {
    await browser.close();
  }
});
