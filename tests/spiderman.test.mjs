import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('Spider-Man species definition, web attacks, audio synthesis, and voice lines', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-spiderman-test-'));
  const generated = join(directory, 'pet.html');
  await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
  const html = await readFile(generated, 'utf8');

  // Verify species registration
  assert.ok(html.includes("id: 'spiderman'"), 'Spider-Man species must be registered');
  assert.ok(html.includes("kind: 'ground'"), 'Spider-Man must be a ground walking/perching species');
  assert.ok(html.includes("drawSpiderman()"), 'drawSpiderman drawing function must be hooked');

  // Verify attacks & webs
  assert.ok(html.includes("drawSpidermanWebAttack("), 'Spider-Man web attack renderer must be defined');
  assert.ok(html.includes("drawWebSplat("), 'Web splat generator must be defined');
  assert.ok(html.includes("if (isCarried && !asleep && !spidermanState.sleepAnchor)"), 'Carried dangling web cord must only be active when awake and not anchored in sleep');
  assert.ok(html.includes("spideyThwip("), 'spideyThwip audio synth must be defined');
  assert.ok(html.includes("spideyZip("), 'spideyZip audio synth must be defined');
  assert.ok(html.includes("spideySense("), 'spideySense audio synth must be defined');
  assert.ok(html.includes("spideyWham("), 'spideyWham audio synth must be defined');

  // Verify voice lines
  assert.ok(html.includes("friendly neighborhood Spider-Man"), 'Spider-Man signature greeting must be present');
  assert.ok(html.includes("With great code comes great responsibility!"), 'Spider-Man motto must be present');
  assert.ok(html.includes("Pizza time!"), 'Spider-Man pizza line must be present');
});

test('desktop Spider-Man renders every pose without errors, switches species via host bridge, and executes dual attacks', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-spiderman-browser-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__spidermanTest = { pet, state, draw, drawSpiderman, drawSpidermanWebAttack, ctx, canvas, petR, species, SPECIES, setSpideyRooftops, setSpideyUserActive };
  // ---------------------------------------------------------------- boot`
    );

    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));

    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'spiderman', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });

    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());

    await page.goto('http://bitling.test/');

    const result = await page.evaluate(() => {
      const api = window.__spidermanTest;
      const base = { ...api.pet };
      let frames = 0;
      const failures = [];

      // Verify species definition
      const sp = api.SPECIES.spiderman;
      if (!sp) failures.push('SPECIES.spiderman not registered');
      if (sp.kind !== 'ground') failures.push(`Expected kind ground, got ${sp.kind}`);

      // Test poses
      const poses = [
        { name: 'idle_perch', apply: () => { api.pet.walking = false; api.pet.carried = false; api.state.asleep = false; api.pet.zap = 0; api.pet.zapCharge = 0; } },
        { name: 'crawl_walk', apply: () => { api.pet.walking = true; api.pet.walkDir = 1; api.pet.carried = false; api.state.asleep = false; } },
        { name: 'crawl_walk_left', apply: () => { api.pet.walking = true; api.pet.walkDir = -1; api.pet.carried = false; api.state.asleep = false; } },
        { name: 'swinging', apply: () => { api.pet.walking = false; api.pet.spideySwinging = true; api.pet.carried = false; } },
        { name: 'dangle_carried', apply: () => { api.pet.walking = false; api.pet.carried = true; api.pet.held = true; api.pet.spideySwinging = false; } },
        { name: 'shooting_web', apply: () => { api.pet.carried = false; api.pet.zapCharge = 0.5; api.pet.zap = 0; } },
        { name: 'firing_web', apply: () => { api.pet.carried = false; api.pet.zapCharge = 0; api.pet.zap = 0.5; api.pet.zapBoss = false; } },
        { name: 'firing_slingshot_boss', apply: () => { api.pet.carried = false; api.pet.zapCharge = 0; api.pet.zap = 0.5; api.pet.zapBoss = true; } },
        { name: 'eating_pizza', apply: () => { api.pet.carried = false; api.pet.chew = 1.0; } },
        { name: 'sleeping_hammock', apply: () => { api.pet.carried = false; api.state.asleep = true; } },
      ];

      for (const pose of poses) {
        Object.assign(api.pet, base);
        pose.apply();
        api.ctx.clearRect(0, 0, 320, 360);
        try {
          api.drawSpiderman();
          frames++;
        } catch (e) {
          failures.push(`Pose ${pose.name} failed: ${e.message}`);
        }
      }

      // Test Web attack renderer
      try {
        api.ctx.clearRect(0, 0, 320, 360);
        api.drawSpidermanWebAttack(44, 0.5, false, 'webThwip');
        frames++;
      } catch (e) {
        failures.push(`Standard web attack failed: ${e.message}`);
      }

      try {
        api.ctx.clearRect(0, 0, 320, 360);
        api.drawSpidermanWebAttack(44, 0.5, true, 'slingshotDive');
        frames++;
      } catch (e) {
        failures.push(`Slingshot boss web attack failed: ${e.message}`);
      }

      // Test host bridge rooftop and user active reporting
      try {
        window.petNative.setWindowRooftops([{ x: 100, y: 300, w: 600, h: 400 }]);
        window.petNative.setUserActive(true);
        window.petNative.setUserActive(false);
      } catch (e) {
        failures.push(`Host bridge rooftop/userActive failed: ${e.message}`);
      }

      return { frames, failures };
    });

    assert.equal(errors.length, 0, `Page errors: ${errors.join(', ')}`);
    assert.equal(result.failures.length, 0, `Evaluation failures: ${result.failures.join('; ')}`);
    assert.ok(result.frames >= 12, `Expected at least 12 rendered frames, got ${result.frames}`);
  } finally {
    await browser.close();
  }
});
