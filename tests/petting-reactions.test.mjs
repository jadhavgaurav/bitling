import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';
const run = promisify(execFile);

test('each species has a distinct petting reaction profile and visual state', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-petting-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['Tools/make_pet_html.py', 'web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace('  // ---------------------------------------------------------------- boot',
      `window.__petting = { pet, state, petTap, update, SPECIES };
  // ---------------------------------------------------------------- boot`);
    const page = await browser.newPage({ viewport: { width: 360, height: 400 } });
    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
      window.__petSavedState = JSON.stringify({ species: 'robot', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now(), full: 90, energy: 90, joy: 90 });
    });
    await page.route('**/*', route => route.request().url() === 'http://pet.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
    await page.goto('http://pet.test/');
    const reactions = await page.evaluate(() => {
      const { pet, state, petTap, update, SPECIES } = window.__petting;
      const output = {};
      for (const id of Object.keys(SPECIES)) {
        state.species = id; pet.reaction = ''; pet.reactionT = 0; pet.happy = 0; pet.surprise = 0; pet.tilt = 0; pet.knee = 0;
        petTap();
        output[id] = { reaction: pet.reaction, duration: pet.reactionT, happy: pet.happy, surprise: pet.surprise, tilt: pet.tilt, knee: pet.knee };
        update(0.2);
      }
      return output;
    });
    const distinctIds = Object.keys(reactions).filter(id => id !== 'dragon');
    const names = distinctIds.map(id => reactions[id].reaction);
    assert.equal(new Set(names).size, distinctIds.length, 'non-Shenron species reactions must be distinct');
    for (const [id, reaction] of Object.entries(reactions)) {
      assert.ok(reaction.duration > 0, `${id} reaction must have a duration`);
      assert.ok(reaction.happy > 0 || reaction.surprise > 0 || reaction.tilt !== 0 || reaction.knee !== 0, `${id} needs visible feedback`);
    }
  } finally { await browser.close(); await rm(directory, { recursive: true, force: true }); }
});
