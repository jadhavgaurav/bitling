import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

test('every pet rests, takes one bounded trip, and rests again', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-calm-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace('  // ---------------------------------------------------------------- boot',
      `window.__calm = { pet, state, update, doIdle, handleFlight, release, SPECIES, shenron, ronaldoBall, snack };
  // ---------------------------------------------------------------- boot`);
    for (const id of ['robot', 'dragon', 'rider', 'goku', 'pikachu', 'ironman', 'kaiju', 'ronaldo', 'naruto', 'mario']) {
      const page = await browser.newPage({ viewport: { width: id === 'dragon' ? 1440 : 320, height: id === 'dragon' ? 900 : 360 } });
      await page.addInitScript(({ id }) => {
        window.requestAnimationFrame = () => 0;
        window.__messages = [];
        window.webkit = { messageHandlers: { pet: { postMessage: message => window.__messages.push(message) } } };
        window.__petSavedState = JSON.stringify({ species: id, hatched: true, sound: false, born: Date.now(), lastSeen: Date.now(), full: 90, energy: 90, joy: 90 });
      }, { id });
      await page.route('**/*', route => route.request().url() === 'http://calm.test/'
        ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
      await page.goto('http://calm.test/');
      const result = await page.evaluate(() => {
        const { pet, state, update, handleFlight, SPECIES } = window.__calm;
        const tick = seconds => { for (let i = 0; i < seconds * 20; i++) update(0.05); };
        const travel = () => window.__messages.filter(m => ['fly', 'walk', 'roam'].includes(m.type));
        if (SPECIES[state.species].kind === 'float') handleFlight('hover');
        tick(1); // settle initial geometry
        const origin = { x: pet.x, y: pet.y };
        window.__messages.length = 0;
        tick(60);
        const initialDistance = Math.hypot(pet.x - origin.x, pet.y - origin.y);
        const initialTrips = travel().length;
        // Let the natural rest expire; compact-window host acknowledges arrival.
        tick(130);
        const trips = travel().length;
        if (state.species !== 'dragon') {
          if (SPECIES[state.species].kind === 'float') handleFlight('hover');
          else window.petNative.walking(0);
        }
        const parked = { x: pet.x, y: pet.y };
        window.__messages.length = 0;
        tick(60);
        return { initialDistance, initialTrips, trips, restTrips: travel().length,
          restDistance: Math.hypot(pet.x - parked.x, pet.y - parked.y) };
      });
      if (id !== 'dragon') assert.ok(result.initialDistance < 1, `${id} moved ${result.initialDistance}px during initial rest`);
      if (id !== 'dragon') assert.equal(result.initialTrips, 0, `${id} requested travel during initial rest`);
      if (id !== 'dragon') assert.equal(result.trips, 1, `${id} must take exactly one brief trip after resting`);
      if (id !== 'dragon') assert.equal(result.restTrips, 0, `${id} requested another trip before resting`);
      if (id !== 'dragon') assert.ok(result.restDistance < 1, `${id} did not stay parked after travel`);
      await page.close();
    }
  } finally { await browser.close(); await rm(directory, { recursive: true, force: true }); }
});

test('placement, species switching, busy states and reduced motion preserve quiet time', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-calm-interaction-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace('  // ---------------------------------------------------------------- boot',
      `window.__calm = { pet, state, updateAmbientMovement, updatePet, doIdle, comeDown, snack, SPECIES };
  // ---------------------------------------------------------------- boot`);
    for (const reducedMotion of ['no-preference', 'reduce']) {
      const page = await browser.newPage({ viewport: { width: 320, height: 360 }, reducedMotion });
      await page.addInitScript(() => {
        window.requestAnimationFrame = () => 0;
        window.__messages = [];
        window.webkit = { messageHandlers: { pet: { postMessage: message => window.__messages.push(message) } } };
        window.__petSavedState = JSON.stringify({ species: 'robot', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
      });
      await page.route('**/*', route => route.request().url() === 'http://calm.test/'
        ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
      await page.goto('http://calm.test/');
      const results = await page.evaluate(reduced => {
        const { pet, state, updateAmbientMovement, doIdle, comeDown, snack, SPECIES } = window.__calm;
        const travel = () => window.__messages.filter(m => ['walk', 'roam', 'fly'].includes(m.type)).length;
        const results = [];
        for (const id of Object.keys(SPECIES)) {
          if (id === 'dragon') continue;
          window.petNative.setSpecies(id);
          if (SPECIES[id].kind === 'float') window.petNative.flight('hover');
          for (const blocker of ['asleep', 'working', 'carried', 'snack']) {
            state.asleep = blocker === 'asleep'; pet.working = blocker === 'working';
            pet.carried = blocker === 'carried'; snack.active = blocker === 'snack';
            pet.restUntil = 0; window.__messages.length = 0;
            updateAmbientMovement();
            results.push({ name: `${id}/${blocker}`, valid: travel() === 0 && pet.restUntil > pet.t + 60 });
          }
          state.asleep = false; pet.working = false; pet.carried = false;
          snack.active = true; pet.ambientTravelUntil = pet.t + 8;
          pet.ax = pet.x + 20; window.__messages.length = 0;
          updateAmbientMovement();
          results.push({ name: `${id}/care-interrupts-travel`, valid:
            window.__messages.some(m => m.type === 'rest') && pet.ax === pet.x + 20 });
          snack.active = false; pet.ax = pet.x;
          pet.restUntil = 0; window.petNative.release(); window.__messages.length = 0;
          for (let i = 0; i < 60; i++) { pet.t += 1; updateAmbientMovement(); doIdle(); }
          results.push({ name: `${id}/release`, valid: travel() === 0 });
          if (SPECIES[id].kind === 'float') {
            comeDown();
            results.push({ name: `${id}/hover-expiry`, valid: travel() === 0 && pet.hoverUntil === 0 });
          }
          if (reduced) {
            pet.restUntil = 0; window.__messages.length = 0;
            updateAmbientMovement();
            results.push({ name: `${id}/reduced`, valid: travel() === 0 });
          }
        }
        return results;
      }, reducedMotion === 'reduce');
      for (const result of results) assert.ok(result.valid, result.name);
      await page.close();
    }
  } finally { await browser.close(); await rm(directory, { recursive: true, force: true }); }
});

test('browser pets finish a nearby trip and remain parked, including floating species', async () => {
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const html = (await readFile('apps/macos/web/bitling.html', 'utf8')).replace('  // ---------------------------------------------------------------- boot',
      `window.__calm = { pet, state, update, selectSpecies, SPECIES };
  // ---------------------------------------------------------------- boot`);
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.addInitScript(() => { window.requestAnimationFrame = () => 0; });
    await page.route('**/*', route => route.request().url() === 'http://calm.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
    await page.goto('http://calm.test/');
    const results = await page.evaluate(() => {
      const { pet, state, update, selectSpecies, SPECIES } = window.__calm;
      const tick = seconds => { for (let i = 0; i < seconds * 60; i++) update(1 / 60); };
      return Object.keys(SPECIES).map(id => {
        selectSpecies(id, false); state.sound = false;
        tick(1);
        const origin = { x: pet.x, y: pet.y };
        pet.restUntil = pet.t;
        tick(12);
        const parked = { x: pet.x, y: pet.y };
        const tripDistance = Math.hypot(pet.x - origin.x, pet.y - origin.y);
        tick(60);
        return { id, tripDistance, restDistance: Math.hypot(pet.x - parked.x, pet.y - parked.y) };
      });
    });
    for (const result of results) {
      if (result.id !== 'dragon') assert.ok(result.tripDistance > 10 && result.tripDistance <= 200, `${result.id} trip distance ${result.tripDistance}`);
      if (result.id !== 'dragon') assert.ok(result.restDistance < 1, `${result.id} kept moving after arrival: ${result.restDistance}`);
    }
  } finally { await browser.close(); }
});
