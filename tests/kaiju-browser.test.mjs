import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);
test('desktop Godzilla renders every pose inside its window and uses the real host bridge', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-browser-test-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__kaijuTest = { pet, state, draw, drawKaiju, ctx, canvas, kaijuMouth, petR, species, updatePet };
  // ---------------------------------------------------------------- boot`,
    );
    const page = await browser.newPage({ viewport: { width: 300, height: 340 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: message => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'kaiju', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });
    await page.route('**/*', route => route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
    await page.goto('http://bitling.test/');
    const result = await page.evaluate(() => {
      const api = window.__kaijuTest;
      const base = { ...api.pet };
      let frames = 0;
      const failures = [];
      const poses = [
        {}, { zapCharge: 0.45, zapFull: 0.9 }, { zap: 0.2 }, { carried: true },
        { mode: 'fly', grounded: false }, { sleeping: true }, { chew: 1 },
        ...Array.from({ length: 24 }, (_, i) => ({ walking: true, gaitBlend: 1, stride: i / 24 * Math.PI * 2 })),
        ...Array.from({ length: 12 }, (_, i) => ({ thrown: true, grounded: false, spin: i / 12 * Math.PI * 2 })),
      ];
      for (const days of [0, 2, 8]) {
        api.state.born = Date.now() - days * 86400000; api.state.care = 150;
        for (const facing of [-1, 1]) {
          for (const pose of poses) {
            Object.assign(api.pet, base, pose, { facing, x: 150, y: 306, ax: 150 });
            api.state.asleep = !!pose.sleeping;
            api.ctx.clearRect(0, 0, 300, 340);
            api.drawKaiju();
            const { width, height } = api.canvas;
            const pixels = api.ctx.getImageData(0, 0, width, height).data;
            let opaque = 0, edge = 0;
            for (let y = 0; y < height; y++) {
              for (let x = 0; x < width; x++) {
                if (pixels[(y * width + x) * 4 + 3] < 200) continue;
                opaque++;
                if (x === 0 || y === 0 || x === width - 1 || y === height - 1) edge++;
              }
            }
            if (opaque < 1000 || edge) failures.push({ days, facing, pose, opaque, edge });
            frames++;
          }
        }
      }
      Object.assign(api.pet, base, { x: 150, y: 306, ax: 150, stride: 0, gaitBlend: 1 });
      api.state.asleep = false;
      window.petNative.walking(1);
      api.updatePet(1 / 60);
      const stride = api.pet.stride;
      const expected = (32 / 60) / (api.petR() * 0.72 / 0.62) * Math.PI * 2;
      window.petNative.walking(0);
      api.updatePet(1 / 60);
      const stopped = !api.pet.walking;
      const style = api.species().attack.style;
      const mouth = api.kaijuMouth(api.petR());
      window.petNative.setSpecies('robot'); window.__bitling.advance(0.1);
      window.petNative.setSpecies('kaiju'); window.__bitling.advance(0.1);
      window.petNative.action('feed'); window.__bitling.advance(0.1);
      window.petNative.gitEvent({ kind: 'test-failed', count: 2, tests: ['godzilla_test'] });
      window.__bitling.advance(1);
      return { frames, failures, stride, expected, stopped, style, mouth };
    });
    assert.deepEqual(errors, []);
    assert.deepEqual(result.failures, [], 'opaque character pixels must never clip the desktop window');
    assert.equal(result.style, 'atomic');
    assert.ok(Math.abs(result.stride - result.expected) < 1e-8, 'native travel must drive stride');
    assert.ok(result.stopped, 'a native stop must end walking');
    assert.ok(Number.isFinite(result.mouth.x) && Number.isFinite(result.mouth.y));
    console.log(`Verified ${result.frames} rendered desktop poses, host walking, species switching and event actions.`);
  } finally {
    await browser.close();
    await rm(directory, { recursive: true, force: true });
  }
});
