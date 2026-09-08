import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('Naruto Uzumaki species definition, dual attacks, and ninja sound synth', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-naruto-test-'));
  const generated = join(directory, 'pet.html');
  await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
  const html = await readFile(generated, 'utf8');

  // Verify registration in HTML
  assert.ok(html.includes("id: 'naruto'"), 'Naruto species must be registered');
  assert.ok(html.includes("kind: 'ground'"), 'Naruto must be a grounded walker');
  assert.ok(html.includes("rasenshuriken"), 'Rasenshuriken attack must be defined');
  assert.ok(html.includes("shuriken"), 'Shuriken attack must be defined');
  assert.ok(html.includes("narutoShuriken"), 'narutoShuriken audio synth must be defined');
  assert.ok(html.includes("narutoRasengan"), 'narutoRasengan audio synth must be defined');
  assert.ok(html.includes("narutoChirp"), 'narutoChirp audio synth must be defined');
  assert.ok(html.toLowerCase().includes("ramen"), 'Ramen developer lines must be included');
  assert.ok(html.toLowerCase().includes("hokage"), 'Hokage developer lines must be included');
});

test('desktop Naruto renders every sprite pose without errors, switches species via host bridge, and executes dual attacks', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-naruto-browser-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__narutoTest = { pet, state, draw, drawNaruto, drawNarutoAttack, ctx, canvas, petR, species, SPECIES, updatePet };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'naruto', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const result = await page.evaluate(() => {
      const api = window.__narutoTest;
      const base = { ...api.pet };
      let frames = 0;
      const failures = [];

      // Verify species definition
      const sp = api.SPECIES.naruto;
      if (!sp) return { ok: false, error: 'Naruto not found in SPECIES' };
      if (sp.kind !== 'ground') return { ok: false, error: `Expected ground kind, got ${sp.kind}` };

      // Verify attack resolution for small vs boss bugs
      const smallAttack = sp.attack.resolve(false);
      const bossAttack = sp.attack.resolve(true);
      if (smallAttack.style !== 'shuriken') return { ok: false, error: `Expected shuriken for small bugs, got ${smallAttack.style}` };
      if (bossAttack.style !== 'rasenshuriken') return { ok: false, error: `Expected rasenshuriken for boss bugs, got ${bossAttack.style}` };

      // Test poses across different states
      const poses = [
        { name: 'idle', facing: 1 },
        { name: 'blink', facing: 1, blink: 1 },
        { name: 'ninja-sprint-forward', facing: 1, walking: true, walkDir: 1, vx: 50 },
        { name: 'ninja-sprint-backward', facing: -1, walking: true, walkDir: -1, vx: -50 },
        { name: 'waving-thumbs-up', facing: 1, waving: 1.5, happy: 1 },
        { name: 'eating-ramen', facing: 1, chew: 1, happy: 1 },
        { name: 'dizzy-confusion', facing: 1, surprise: 1 },
        { name: 'chakra-charge-boss', facing: 1, zapCharge: 0.8, zapFull: 1, zapBoss: true, zapStyle: 'rasenshuriken' },
        { name: 'fire-rasenshuriken', facing: 1, zap: 0.25, zapBoss: true, zapStyle: 'rasenshuriken', zapX: 160, zapY: 200, zapTargetX: 300, zapTargetY: 200 },
        { name: 'chakra-charge-shuriken', facing: 1, zapCharge: 0.4, zapFull: 0.8, zapBoss: false, zapStyle: 'shuriken' },
        { name: 'fire-shuriken', facing: 1, zap: 0.15, zapBoss: false, zapStyle: 'shuriken', zapX: 160, zapY: 200, zapTargetX: 280, zapTargetY: 200 },
        { name: 'carried-scruff', facing: 1, carried: true, dragSpeed: 50 },
      ];

      for (const pose of poses) {
        Object.assign(api.pet, base, pose, { x: 160, y: 220, mode: 'walk', grounded: true });
        api.ctx.clearRect(0, 0, 320, 360);
        try {
          api.drawNaruto();
          if (pose.zap > 0) {
            api.drawNarutoAttack(pose.zapStyle, pose.zapBoss, pose.zap);
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

        // Naruto should occupy substantial area
        if (opaque < 250) {
          failures.push(`Pose ${pose.name} rendered too few pixels: ${opaque}`);
        }
        frames++;
      }

      // Test host bridge species switching
      window.petNative.setSpecies('robot');
      const switchedToRobot = api.state.species === 'robot';
      window.petNative.setSpecies('naruto');
      const switchedBackToNaruto = api.state.species === 'naruto';

      return {
        ok: failures.length === 0 && switchedToRobot && switchedBackToNaruto,
        frames,
        failures,
        switchedToRobot,
        switchedBackToNaruto
      };
    });

    assert.equal(errors.length, 0, `Page errors: ${errors.join(', ')}`);
    assert.ok(result.ok, `Rendering failures: ${result.failures?.join('; ')}`);
    assert.equal(result.frames, 12, 'All 12 test poses rendered successfully');
    assert.ok(result.switchedToRobot, 'Host bridge successfully switches to robot');
    assert.ok(result.switchedBackToNaruto, 'Host bridge successfully switches back to naruto');
  } finally {
    await browser.close();
  }
});
