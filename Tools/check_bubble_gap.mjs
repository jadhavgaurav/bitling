#!/usr/bin/env node
/**
 * Every pet must hold the speech bubble the same distance above its head.
 *
 * The gap is not a constant, it is derived: a species declares `reach`, how far it draws
 * above its own feet in radii, and the bubble is placed from that. Declare it too small
 * and the bubble sits on the creature's horns; too large and it floats with a hole under
 * it. Neither is visible from the code, so this measures the rendered result.
 *
 * Each species gets its own fresh page. Idle timers, chatter cadence and particle state
 * accumulate over elapsed sim time, and measuring several species in one shared page
 * carried that state between them: the same species, tested twice, could measure ten
 * pixels apart depending on what had built up before it was switched to. A fresh page
 * per species removes that as a variable entirely, rather than guessing at which timer
 * was responsible.
 *
 *   node Tools/check_bubble_gap.mjs            # all species
 *   node Tools/check_bubble_gap.mjs kaiju      # one
 *   node Tools/check_bubble_gap.mjs --debug    # print every sampled frame
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

const args = process.argv.slice(2);
const debug = args.includes('--debug');
const wanted = args.filter((a) => !a.startsWith('--'));

const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });

// One throwaway page just to read the roster off the live SPECIES registry, so the list
// checked here can never quietly fall behind the species the page actually defines.
const rosterPage = await browser.newPage();
await rosterPage.goto(`file://${PAGE}`);
await rosterPage.waitForFunction(() => window.__speciesOrder && window.__speciesOrder.length);
const roster = await rosterPage.evaluate(() => window.__speciesOrder);
await rosterPage.close();
const list = wanted.length ? wanted : roster;

async function measure(id) {
  const page = await browser.newPage({ viewport: { width: 300, height: 340 }, deviceScaleFactor: 2 });
  if (debug) page.on('console', (m) => console.log('[page]', m.text()));
  await page.addInitScript((seed) => {
    window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
    window.__petSavedState = JSON.stringify({ ...seed, species: seed.species });
  }, { ...SEED, species: id });
  await page.goto(`file://${PAGE}`);
  await page.waitForFunction(() => window.petNative && window.petNative.debug);

  const result = await page.evaluate(async ({ id, debugOn }) => {
    const c = document.getElementById('stage');
    const ctx = c.getContext('2d');
    const dpr = c.width / c.clientWidth;
    const bubble = document.querySelector('.bubble');
    bubble.style.animation = 'none';
    const worst = (msg) => {
      window.petNative.advance(1);
      window.petNative.gitEvent({ kind: 'say', message: msg });
      window.petNative.advance(0.6);
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
        const g = top / dpr - (br.bottom - cr.top + 6);
        if (debugOn) console.log(msg.slice(0, 12), 'k', k, 'gap', Math.round(g));
        min = Math.min(min, g);
      }
      return Math.round(min);
    };
    return {
      short: worst('hi'),
      long: worst('that commit touched an awful lot of files today'),
      r: Number(window.petNative.debug().r.toFixed(1)),
    };
  }, { id, debugOn: debug });

  await page.close();
  return result;
}

const results = {};
for (const id of list) results[id] = await measure(id);
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
