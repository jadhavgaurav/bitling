import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const PAGE = resolve(HERE, '..', 'Resources', 'pet.html');

test('Spider-Man upside-down hanging sleep mode, elastic web dragging, bungee physics, and somersault wake', async () => {
  try {
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  const page = await browser.newPage({ viewport: { width: 400, height: 450 } });

  await page.addInitScript(() => {
    window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
    window.__petSavedState = JSON.stringify({
      v: 1, name: 'Spidey', species: 'spiderman', hatched: true,
      sound: false, asleep: false, full: 90, energy: 90, joy: 90
    });
  });

  await page.goto(`file://${PAGE}`);
  await page.waitForFunction(() => window.petNative && window.petNative.debug);

  const initial = await page.evaluate(() => window.petNative.debug());
  assert.equal(initial.species, 'spiderman');

  // 1. Put Spider-Man to sleep
  await page.evaluate(() => {
    window.petNative.action('sleep');
  });

  const sleepState = await page.evaluate(() => {
    window.petNative.advance(0.1);
    const d = window.petNative.debug();
    return {
      asleep: d.asleep,
      x: d.x,
      y: d.y,
    };
  });

  assert.equal(sleepState.asleep, true, 'Spider-Man must be asleep');
  assert(sleepState.y > 100, `Spider-Man should hang down from top anchor, got ${sleepState.y}`);

  // 2. Test elastic dragging in sleep
  await page.evaluate(() => {
    window.petNative.stageDrag(40, 80);
    window.petNative.advance(0.05);
  });

  const dragged = await page.evaluate(() => {
    const d = window.petNative.debug();
    return { x: d.x, y: d.y };
  });
  assert(dragged.y > sleepState.y, 'Spider-Man position should move downwards with drag');

  // 3. Test release and bungee spring return
  await page.evaluate(() => {
    window.petNative.release();
    window.petNative.advance(1.2);
  });

  const postBungee = await page.evaluate(() => {
    const d = window.petNative.debug();
    return { x: d.x, y: d.y, asleep: d.asleep };
  });
  assert.equal(postBungee.asleep, true, 'Spider-Man should remain asleep after bungee bounce');

  // 4. Test wake-up somersault flip
  await page.evaluate(() => {
    window.petNative.action('sleep'); // toggleSleep wakes him
  });

  const wakeState = await page.evaluate(() => {
    const d = window.petNative.debug();
    window.petNative.advance(0.5);
    const d2 = window.petNative.debug();
    return {
      beforeFlipAsleep: d.asleep,
      afterFlipGrounded: d2.grounded,
      y: d2.y,
    };
  });

  assert.equal(wakeState.beforeFlipAsleep, false, 'Spider-Man should be awake');
  assert.equal(wakeState.afterFlipGrounded, true, 'Spider-Man should land on feet after somersault');

  await browser.close();
  } catch (err) {
    console.error("TEST ERROR:", err);
    throw err;
  }
});
