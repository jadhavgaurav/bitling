import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('Shenron uses a large transparent animated stage, sleeps in air and preserves existing species', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-shenron-'));
  const generated = join(directory, 'pet.html');
  await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
  const html = await readFile(generated, 'utf8');
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.addInitScript(() => {
      let seed = 7351;
      Math.random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
      window.requestAnimationFrame = () => 0;
      window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
      window.__petSavedState = JSON.stringify({ species: 'dragon', name: 'Ember', hatched: true, sound: false,
        born: Date.now() - 3 * 86400000, lastSeen: Date.now() - 2 * 3600000, full: 95, energy: 95, joy: 95, care: 440 });
    });
    await page.route('**/*', route => route.request().url() === 'http://shenron.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
    await page.goto('http://shenron.test/');
    assert.equal(await page.evaluate(() => window.__bitling.species().name), 'Shenron');
    assert.equal(await page.evaluate(() => window.__bitling.rawState().name), 'Shenron');
    assert.ok(await page.evaluate(() => window.__bitling.rawState().full < 95), 'Ember migration must apply offline needs');
    await page.waitForFunction(() => window.__bitling.shenronReady());
    const livingMotion = await page.evaluate(() => {
      const api = window.__bitling;
      const relative = rig => rig.points.map(point => ({ x: point.x - rig.head.x, y: point.y - rig.head.y }));
      const before = api.shenronRig();
      api.advance(1.5);
      const after = api.shenronRig();
      const first = relative(before), second = relative(after);
      const moved = index => Math.hypot(second[index].x - first[index].x, second[index].y - first[index].y);
      const oldLength = after.pathLength;
      window.petNative.shenronSetting('length', 1.45);
      api.advance(0.5);
      const longer = api.shenronRig();
      window.petNative.shenronSetting('size', 1.3);
      const larger = api.shenronRig();
      window.petNative.shenronSetting('motion', 1.35);
      window.petNative.shenronSetting('speed', 1.2);
      api.advance(1.2);
      const energetic = api.shenronRig();
      return {
        pointCount: before.points.length,
        neckMoved: moved(Math.floor(first.length * 0.18)),
        middleMoved: moved(Math.floor(first.length * 0.55)),
        tailMoved: moved(first.length - 1),
        oldLength,
        longerLength: longer.pathLength,
        longerRadius: longer.radius,
        largerRadius: larger.radius,
        settings: energetic.settings,
        saved: api.rawState().shenronSettings,
      };
    });
    assert.ok(livingMotion.pointCount >= 30, 'Shenron needs a segmented spine');
    assert.ok(livingMotion.neckMoved > 3, `neck motion is too static: ${livingMotion.neckMoved}`);
    assert.ok(livingMotion.middleMoved > 8, `body motion is too static: ${livingMotion.middleMoved}`);
    assert.ok(livingMotion.tailMoved > 18, `tail motion is too static: ${livingMotion.tailMoved}`);
    assert.ok(livingMotion.longerLength > livingMotion.oldLength * 1.3, 'length must change the spine, not stretch a bitmap');
    assert.ok(livingMotion.largerRadius > livingMotion.longerRadius * 1.2, 'size must independently change body thickness');
    assert.deepEqual(livingMotion.settings, livingMotion.saved, 'motion controls must persist in pet state');
    const delayedTurn = await page.evaluate(() => {
      const api = window.__bitling;
      const angle = (a, b) => Math.atan2(a.y - b.y, a.x - b.x);
      window.petNative.shenronSetting('motion', 0.35);
      const before = api.shenronRig();
      const beforeTail = angle(before.points.at(-1), before.points.at(-4));
      api.steerShenron(Math.PI / 2);
      api.advance(0.3);
      const after = api.shenronRig();
      return { head: angle(after.points[0], after.points[3]), tail: angle(after.points.at(-1), after.points.at(-4)), beforeTail };
    });
    const turnDelta = (a, b) => Math.atan2(Math.sin(a - b), Math.cos(a - b));
    assert.ok(Math.abs(turnDelta(delayedTurn.head, delayedTurn.tail)) > 0.3, 'a turn must reach the head before the tail');
    assert.ok(Math.abs(turnDelta(delayedTurn.tail, delayedTurn.beforeTail)) < 0.35, 'tail must retain its earlier trajectory during a head turn');
    const result = await page.evaluate(() => {
      const api = window.__bitling;
      window.petNative.stageSize(1);
      api.advance(1);
      api.hideBubble();
      const measure = () => {
        api.draw();
        const c = document.getElementById('stage'), ctx = c.getContext('2d');
        const data = ctx.getImageData(0, 0, c.width, c.height).data;
        let left = c.width, right = 0, top = c.height, bottom = 0, count = 0;
        for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) {
          if (data[(y * c.width + x) * 4 + 3] > 32) {
            left = Math.min(left, x); right = Math.max(right, x);
            top = Math.min(top, y); bottom = Math.max(bottom, y); count++;
          }
        }
        return { left, right, top, bottom, count, width: right - left, height: bottom - top };
      };
      const first = measure(), start = api.state();
      api.advance(4);
      const second = measure(), end = api.state();
      api.act('sleep'); api.advance(1);
      const asleep = { ...api.state(), grounded: api.pet().grounded };
      api.advance(2);
      const resting = api.state();
      api.act('sleep');
      window.petNative.stageDrag(85, -45);
      const dragged = api.state();
      const beforeSwitchScale = api.state().r;
      window.petNative.setSpecies('ironman');
      window.petNative.setSpecies('dragon');
      api.advance(0.1);
      return { first, second, start, end, asleep, resting, dragged, beforeSwitchScale,
        afterSwitchScale: api.state().r, name: api.species().name };
    });
    assert.ok(result.first.width > 550, `dragon only ${result.first.width}px wide`);
    assert.ok(result.first.count > 12000, 'dragon must paint a substantial articulated silhouette');
    assert.ok(result.first.count / (result.first.width * result.first.height) < 0.72, 'coils and outside must be transparent');
    assert.ok(Math.hypot(result.end.x - result.start.x, result.end.y - result.start.y) > 15, 'must cruise across stage');
    assert.equal(result.asleep.grounded, false, 'sleeping dragon must remain airborne');
    assert.ok(Math.hypot(result.resting.x - result.asleep.x, result.resting.y - result.asleep.y) < 2, 'sleep must stop cruising');
    assert.ok(Math.abs(result.dragged.x - result.resting.x - 85) <= 1, 'drag moves creature inside stage');
    assert.equal(result.name, 'Shenron');
    assert.equal(result.beforeSwitchScale, result.afterSwitchScale);
    const interactions = await page.evaluate(() => {
      const api = window.__bitling;
      const c = document.getElementById('stage'), ctx = c.getContext('2d');
      api.draw();
      const mouth = api.shenronMouth();
      const mouthPixel = Array.from(ctx.getImageData(Math.floor(mouth.x), Math.floor(mouth.y), 1, 1).data);
      const attackMouth = api.species().attack.origin(api.state().r)[0];
      const hit = api.shenronHit(mouth.x, mouth.y);
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, c.width, c.height);
      const outsideHit = api.shenronHit(2, 2);
      api.rawState().full = 40;
      api.act('feed'); api.advance(3);
      const full = api.rawState().full;
      return { hit, outsideHit, mouthPixel, mouth, attackMouth, full };
    });
    assert.equal(interactions.hit, true);
    assert.equal(interactions.outsideHit, false, 'opaque demo background must not count as dragon');
    assert.deepEqual(interactions.attackMouth, interactions.mouth);
    assert.ok(interactions.mouthPixel[0] > interactions.mouthPixel[1] * 1.5 && interactions.mouthPixel[3] > 120,
      `attack must originate inside the painted red mouth: ${interactions.mouthPixel}`);
    assert.ok(interactions.full > 60, 'feeding must reach the airborne mouth');

    for (const id of ['rider', 'ironman', 'goku', 'mario']) {
      await page.evaluate(id => window.petNative.setSpecies(id), id);
      await page.setViewportSize({ width: 300, height: 340 });
      const visible = await page.evaluate(() => {
        window.petNative.stageSize(1);
        window.petNative.advance(0.5);
        const c = document.getElementById('stage');
        const pixels = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
        let painted = 0;
        for (let i = 3; i < pixels.length; i += 4) if (pixels[i] > 32) painted++;
        return painted;
      });
      assert.ok(visible > 1500, `${id} must remain visible after leaving the desktop stage`);
      await page.evaluate(() => window.petNative.setSpecies('dragon'));
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.evaluate(() => window.petNative.stageSize(1));
    }
    const radius = await page.evaluate(() => window.__bitling.state().r);
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.evaluate(() => window.petNative.stageSize(1));
    assert.equal(await page.evaluate(() => window.__bitling.state().r), radius, 'display resolution must not inflate Shenron');
    assert.deepEqual(errors, []);

    const corruptPage = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await corruptPage.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
      window.__petSavedState = JSON.stringify({ species: 'dragon', name: 'Shenron', hatched: true,
        shenronSettings: { size: 'bad', length: -10, speed: 0, motion: null, depth: 99, opacity: -4 } });
    });
    await corruptPage.route('**/*', route => route.request().url() === 'http://corrupt-shenron.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
    await corruptPage.goto('http://corrupt-shenron.test/');
    await corruptPage.waitForFunction(() => window.__bitling.shenronReady());
    const sanitized = await corruptPage.evaluate(() => window.__bitling.shenronRig());
    assert.ok(Number.isFinite(sanitized.radius) && sanitized.radius > 0);
    assert.ok(Number.isFinite(sanitized.pathLength) && sanitized.pathLength > 0);
    assert.ok(sanitized.points.every(point => Number.isFinite(point.x) && Number.isFinite(point.y)));
    assert.deepEqual(sanitized.settings, { size: 0.58, length: 0.65, speed: 0.45, motion: 0.35, depth: 1, opacity: 0.35 });
    await corruptPage.close();
  } finally { await browser.close(); }
});
