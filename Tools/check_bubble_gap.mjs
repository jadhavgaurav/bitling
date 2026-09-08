#!/usr/bin/env node
/**
 * Every pet must hold the speech bubble the same distance above its head.
 *
 * The gap is not a constant, it is derived: a species declares `reach`, how far it draws
 * above its own feet in radii, and the bubble is placed from that. Declare it too small
 * and the bubble sits on the creature's horns; too large and it floats with a hole under
 * it. Neither is visible from the code, so this measures the rendered result.
 *
 * For each species it shows a line, then for every frame of a short animation compares the
 * topmost painted pixel with the bottom of the bubble's tail, and keeps the worst case.
 *
 *   node Tools/check_bubble_gap.mjs            # all species
 *   node Tools/check_bubble_gap.mjs kaiju      # one
 *
 * Fixing a failure: gap changes by r * delta-reach, so if a pet is 20px too generous and
 * its radius is 40, subtract 0.5 from its reach. Re-run to confirm.
 */
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const PAGE = resolve(HERE, '..', 'Resources', 'pet.html');
const MIN = 8;      // any less and the bubble crowds the head
const MAX = 24;     // any more and there is a visible hole under it

const SEED = {
  v: 1, name: 'Pet', species: 'robot', hatched: true, taps: 3,
  born: Date.now() - 3 * 86400000, lastSeen: Date.now(),
  full: 92, energy: 95, joy: 95, care: 440, sound: false, asleep: false,
  meals: 1, games: 0, pets: 63, stageSeen: 2,
  commits: 72, pushes: 196, bugs: 233, prompts: 109,
};

const wanted = process.argv.slice(2);
// Use the installed Chrome, as the repo's other browser test does, rather than
// requiring a separate playwright browser download.
const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
const page = await browser.newPage({ viewport: { width: 300, height: 340 }, deviceScaleFactor: 2 });
await page.addInitScript((seed) => {
  window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
  window.__petSavedState = JSON.stringify(seed);
}, SEED);
await page.goto(`file://${PAGE}`);   // load it the way the app does, so layout matches
await page.waitForFunction(() => window.petNative && window.petNative.debug);

const species = await page.evaluate(() => window.petNative.debug().speciesList
  || ['robot', 'dragon', 'rider', 'goku', 'pikachu', 'kaiju']);
const list = wanted.length ? wanted : species;

const results = await page.evaluate(async (ids) => {
  const c = document.getElementById('stage');
  const ctx = c.getContext('2d');
  const dpr = c.width / c.clientWidth;
  const bubble = document.querySelector('.bubble');
  bubble.style.animation = 'none';
  const worst = (id, msg) => {
    window.petNative.setSpecies(id);
    window.petNative.advance(1);
    window.petNative.gitEvent({ kind: 'say', message: msg });
    window.petNative.advance(0.4);
    let min = Infinity;
    for (let k = 0; k < 25; k++) {
      window.petNative.advance(0.04);
      if (bubble.hidden) continue;
      const data = ctx.getImageData(0, 0, c.width, c.height).data;
      let top = -1;
      for (let y = 0; y < c.height && top < 0; y++) {
        for (let x = 0; x < c.width; x++) if (data[(y * c.width + x) * 4 + 3] > 8) { top = y; break; }
      }
      if (top < 0) continue;
      const cr = c.getBoundingClientRect(), br = bubble.getBoundingClientRect();
      min = Math.min(min, top / dpr - (br.bottom - cr.top + 6));
    }
    return Math.round(min);
  };
  const out = {};
  for (const id of ids) {
    out[id] = {
      short: worst(id, 'hi'),
      long: worst(id, 'that commit touched an awful lot of files today'),
      r: Number(window.petNative.debug().r.toFixed(1)),
    };
  }
  return out;
}, list);

await browser.close();

let bad = 0;
for (const [id, r] of Object.entries(results)) {
  const gap = Math.min(r.short, r.long);
  const ok = gap >= MIN && gap <= MAX;
  if (!ok) bad++;
  const hint = gap < MIN ? `raise reach by ~${((MIN + 4 - gap) / r.r).toFixed(2)}`
    : gap > MAX ? `lower reach by ~${((gap - MAX + 4) / r.r).toFixed(2)}` : '';
  console.log(`${ok ? 'ok  ' : 'FAIL'}  ${id.padEnd(9)} gap ${String(gap).padStart(3)}px  `
    + `(short ${r.short}, long ${r.long}, r ${r.r})  ${hint}`);
}
console.log(bad ? `\n${bad} species outside ${MIN}..${MAX}px` : `\nall ${list.length} species within ${MIN}..${MAX}px`);
process.exit(bad ? 1 : 0);
