import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdir, mkdtemp, readFile, rm, utimes, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';
const run = promisify(execFile);

async function openPet(browser, directory, viewport) {
  const generated = join(directory, 'pet.html');
  await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
  const html = (await readFile(generated, 'utf8')).replace('  // ---------------------------------------------------------------- boot',
    `window.__quota = { update, say, showQuotaHud, paintQuota, hudUntil: () => quotaHudUntil, expire: () => { quotaHudUntil = performance.now() - 1; } };
  // ---------------------------------------------------------------- boot`);
  const page = await browser.newPage({ viewport });
  await page.addInitScript(() => {
    window.requestAnimationFrame = () => 0;
    window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
    window.__petSavedState = JSON.stringify({ species: 'robot', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now(), full: 90, energy: 90, joy: 90 });
  });
  await page.route('**/*', route => route.request().url() === 'http://quota.test/'
    ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
  await page.goto('http://quota.test/');
  return page;
}

test('the HUD shows only what was recorded, labels stale readings and counts down real resets', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-quota-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const page = await openPet(browser, directory, { width: 360, height: 560 });
    const hud = await page.evaluate(() => {
      const now = Date.now(), minute = 60000;
      window.petNative.quotaUpdate({
        showClaude: true, showCodex: true,
        claude: { plan: 'Max 20x',
          fiveHour: { usedPercent: 94, asOf: now - 2 * minute },
          weekly: { usedPercent: 40, asOf: now - 120 * minute } },
        codex: { plan: 'Plus',
          fiveHour: { usedPercent: 20, resetsAt: now + 130 * minute + 20000, asOf: now - minute },
          weekly: undefined },
      });
      window.__quota.showQuotaHud(3000);
      const text = id => document.querySelector(id).textContent;
      const cls = id => [...document.querySelector(id).classList];
      return {
        hidden: document.querySelector('#quotaHud').hidden,
        claudePlan: text('#quotaClaudePlan'), codexPlan: text('#quotaCodexPlan'),
        claude5hVal: text('#quotaClaude5hVal'), claude5hSub: text('#quotaClaude5hSub'), claude5hCls: cls('#quotaClaude5hFill'),
        claudeWkVal: text('#quotaClaudeWkVal'), claudeWkSub: text('#quotaClaudeWkSub'), claudeWkCls: cls('#quotaClaudeWkFill'),
        codex5hVal: text('#quotaCodex5hVal'), codex5hSub: text('#quotaCodex5hSub'),
        codexWkVal: text('#quotaCodexWkVal'), codexWkSub: text('#quotaCodexWkSub'), codexWkWidth: document.querySelector('#quotaCodexWkFill').style.width,
        all: document.querySelector('#quotaHud').textContent,
      };
    });
    assert.equal(hud.hidden, false);
    assert.equal(hud.claudePlan, 'Max 20x');
    assert.equal(hud.codexPlan, 'Plus');
    assert.equal(hud.claude5hVal, '6%');
    assert.equal(hud.claude5hSub, '6% left', 'a fresh reading carries no age label');
    assert.ok(hud.claude5hCls.includes('critical'), 'under 10% left is critical');
    assert.equal(hud.claudeWkVal, '60%');
    assert.equal(hud.claudeWkSub, '60% left · logged 2h 0m ago', 'a two hour old sample is labelled as old');
    assert.equal(hud.codex5hVal, '80%');
    assert.equal(hud.codex5hSub, '80% left · resets in 2h 10m');
    assert.equal(hud.codexWkVal, '--');
    assert.equal(hud.codexWkSub, 'no recent data', 'a window nobody recorded is not shown as 100% left');
    assert.equal(hud.codexWkWidth, '0%');
    assert.ok(!/NaN|undefined|null|turns|gpt-/i.test(hud.all), `no stray placeholder text: ${hud.all}`);
  } finally {
    await browser.close();
    await rm(directory, { recursive: true, force: true });
  }
});

test('an empty or partial update never paints junk, and the per-provider switches are honoured', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-quota-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const page = await openPet(browser, directory, { width: 360, height: 560 });
    const result = await page.evaluate(() => {
      const q = window.__quota, nq = window.petNative.quotaUpdate;
      const state = () => ({
        hidden: document.querySelector('#quotaHud').hidden,
        claude: document.querySelector('#quotaClaudeSec').hidden,
        codex: document.querySelector('#quotaCodexSec').hidden,
        divider: document.querySelector('#quotaDivider').hidden,
        text: document.querySelector('#quotaHud').textContent,
      });
      const out = {};
      q.showQuotaHud(3000);
      out.beforeAnyData = document.querySelector('#quotaHud').hidden;          // nothing to show yet
      nq({ showClaude: true, showCodex: true });                                 // flags only, no readings
      q.showQuotaHud(3000); out.flagsOnly = state();
      nq({ showClaude: true, showCodex: false, claude: { fiveHour: { usedPercent: 10, asOf: Date.now() } }, codex: {} });
      q.showQuotaHud(3000); out.claudeOnly = state();
      nq({ showClaude: false, showCodex: true, claude: {}, codex: { fiveHour: { usedPercent: 10, asOf: Date.now() } } });
      q.showQuotaHud(3000); out.codexOnly = state();
      nq({ showClaude: false, showCodex: false });
      q.showQuotaHud(3000); out.bothOff = state();
      return out;
    });
    assert.equal(result.beforeAnyData, true, 'with no reading yet there is no HUD to show');
    assert.ok(!/NaN|undefined|null/.test(result.flagsOnly.text), result.flagsOnly.text);
    assert.equal(result.flagsOnly.hidden, false);
    assert.equal(result.claudeOnly.claude, false);
    assert.equal(result.claudeOnly.codex, true);
    assert.equal(result.claudeOnly.divider, true, 'no divider with a single provider');
    assert.equal(result.codexOnly.claude, true);
    assert.equal(result.codexOnly.codex, false);
    assert.equal(result.bothOff.hidden, true, 'switching both off hides the HUD entirely');
  } finally {
    await browser.close();
    await rm(directory, { recursive: true, force: true });
  }
});

test('the HUD expires, and sits above the speech bubble instead of covering it', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-quota-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const page = await openPet(browser, directory, { width: 360, height: 640 });
    const layout = await page.evaluate(() => {
      const q = window.__quota;
      window.petNative.quotaUpdate({ showClaude: true, showCodex: true,
        claude: { plan: 'Max 20x', fiveHour: { usedPercent: 30, asOf: Date.now() }, weekly: { usedPercent: 30, asOf: Date.now() } },
        codex: { plan: 'Plus', fiveHour: { usedPercent: 30, asOf: Date.now() }, weekly: { usedPercent: 30, asOf: Date.now() } } });
      q.showQuotaHud(3000);
      q.update(0.016);
      const alone = document.querySelector('#quotaHud').getBoundingClientRect();
      q.say('stacking check', 4000);
      q.update(0.016);
      const bubble = document.querySelector('#bubble').getBoundingClientRect();
      const withBubble = document.querySelector('#quotaHud').getBoundingClientRect();
      q.expire();
      q.update(0.016);
      return {
        aloneBottom: alone.bottom, bubbleTop: bubble.top, bubbleHeight: bubble.height,
        hudBottomWithBubble: withBubble.bottom, hudTop: withBubble.top,
        hiddenAfterExpiry: document.querySelector('#quotaHud').hidden,
      };
    });
    assert.ok(layout.bubbleHeight > 0, 'the bubble rendered');
    assert.ok(layout.hudBottomWithBubble <= layout.bubbleTop + 1,
      `HUD bottom ${layout.hudBottomWithBubble} must clear the bubble top ${layout.bubbleTop}`);
    assert.ok(layout.hudTop >= 0, 'the HUD stays inside the window');
    assert.equal(layout.hiddenAfterExpiry, true, 'the HUD hides once its time is up');
  } finally {
    await browser.close();
    await rm(directory, { recursive: true, force: true });
  }
});

// The reader that feeds the HUD is native code, so compile the real file against fixture
// homes instead of re-implementing its rules here.
const DRIVER = `import Foundation
let enc = JSONEncoder(); enc.outputFormatting = [.sortedKeys]
let data = QuotaReader.read(home: URL(fileURLWithPath: CommandLine.arguments[1]))
print(String(decoding: try! enc.encode(data), as: UTF8.self))
`;

async function swiftAvailable() {
  try { await run('swiftc', ['--version']); return true; } catch { return false; }
}

test('the native reader returns only recorded figures: right bucket, right account, no stale or invented data', async (t) => {
  if (!(await swiftAvailable())) return t.skip('swiftc is not installed');
  const directory = await mkdtemp(join(tmpdir(), 'bitling-quota-swift-'));
  try {
    await writeFile(join(directory, 'main.swift'), DRIVER);
    const binary = join(directory, 'reader');
    await run('swiftc', ['-O', '-swift-version', '5', 'apps/macos/Sources/QuotaWatcher.swift', join(directory, 'main.swift'), '-o', binary]);
    const read = async home => JSON.parse((await run(binary, [home])).stdout);
    const now = Date.now(), sec = Math.floor(now / 1000), minute = 60000, hour = 3600000;

    // ---- Claude: matched to the signed-in organisation, newest sample, no invented reset
    const claudeHome = join(directory, 'claude-home');
    await mkdir(join(claudeHome, 'Library/Application Support/Claude'), { recursive: true });
    await writeFile(join(claudeHome, '.claude.json'), JSON.stringify({ oauthAccount: { organizationUuid: 'org-A', organizationRateLimitTier: 'default_claude_max_5x' } }));
    const history = samples => writeFile(join(claudeHome, 'Library/Application Support/Claude/plan-usage-history.json'), JSON.stringify({ version: 1, samples }));
    await history([
      { t: now - 90 * minute, org: 'org-A', u: { fh: 11, sd: 5 } },
      { t: now - 30 * minute, org: 'org-A', u: { fh: 30, sd: 10 } },
      { t: now - 5 * minute, org: 'org-B', u: { fh: 99, sd: 99 } },
    ]);
    let r = await read(claudeHome);
    assert.equal(r.claude.plan, 'Max 5x', 'the multiple comes from the tier, not a hardcoded 20x');
    assert.equal(r.claude.fiveHour.usedPercent, 30, "another account's newer sample must not be used");
    assert.equal(r.claude.weekly.usedPercent, 10);
    assert.equal(r.claude.fiveHour.resetsAt, undefined, 'Claude records no reset time, so none is reported');
    assert.equal(r.claude.weekly.resetsAt, undefined);

    await history([{ t: now - 6 * hour, org: 'org-A', u: { fh: 80, sd: 55 } }]);
    r = await read(claudeHome);
    assert.equal(r.claude.fiveHour, undefined, 'a reading older than the 5 hour window says nothing about the open one');
    assert.equal(r.claude.weekly.usedPercent, 55, 'the weekly figure is still good, and keeps its age');

    await history([{ t: now - 8 * 24 * hour, org: 'org-A', u: { fh: 80, sd: 55 } }]);
    r = await read(claudeHome);
    assert.equal(r.claude.fiveHour, undefined);
    assert.equal(r.claude.weekly, undefined, 'older than a week is no reading at all');

    // ---- Codex: the "codex" bucket only, newest file wins, rolled-over windows are untouched
    const codexHome = join(directory, 'codex-home');
    const day = join(codexHome, '.codex/sessions/2026/10/12'), older = join(codexHome, '.codex/sessions/2026/10/11');
    await mkdir(day, { recursive: true }); await mkdir(older, { recursive: true });
    const line = (bucket, p, s, when) => JSON.stringify({ timestamp: new Date(when).toISOString(), type: 'event_msg', payload: { type: 'token_count', rate_limits: {
      limit_id: bucket, plan_type: 'plus',
      primary: { used_percent: p.used, window_minutes: 300, resets_at: Math.floor(p.reset / 1000) },
      secondary: { used_percent: s.used, window_minutes: 10080, resets_at: Math.floor(s.reset / 1000) } } } });
    const stale = line('codex', { used: 77, reset: now + hour }, { used: 77, reset: now + 24 * hour }, now - 20 * hour);
    const current = line('codex', { used: 40, reset: now + 2 * hour }, { used: 15, reset: now + 5 * 24 * hour }, now - 10 * minute);
    const premium = line('premium', { used: 1, reset: now + hour }, { used: 2, reset: now + 24 * hour }, now - minute);
    const olderFile = join(older, 'rollout-2026-10-11T08-00-00-aaa.jsonl'), newerFile = join(day, 'rollout-2026-10-12T08-00-00-bbb.jsonl');
    await writeFile(olderFile, `${stale}\n`); await utimes(olderFile, new Date(now - 20 * hour), new Date(now - 20 * hour));
    await writeFile(newerFile, `${current}\n{"timestamp":"x","type":"other"}\n${premium}\n{"truncated`);
    r = await read(codexHome);
    assert.equal(r.codex.plan, 'Plus');
    assert.equal(r.codex.fiveHour.usedPercent, 40, 'the later "premium" line must not replace the codex bucket');
    assert.equal(r.codex.weekly.usedPercent, 15, 'the newest file wins over an older day');
    assert.ok(Math.abs(r.codex.fiveHour.resetsAt - (now + 2 * hour)) < 2000, 'the reset time is the recorded one, in ms');
    assert.ok(Math.abs(r.codex.weekly.resetsAt - (now + 5 * 24 * hour)) < 2000);

    const rolled = line('codex', { used: 94, reset: now - hour }, { used: 15, reset: now + 24 * hour }, now - 3 * hour);
    await writeFile(newerFile, `${rolled}\n`);
    r = await read(codexHome);
    assert.equal(r.codex.fiveHour.usedPercent, 0, 'a window that reset after the last logged turn is untouched');
    assert.equal(r.codex.fiveHour.resetsAt, undefined, 'and has no countdown');
    assert.ok(Math.abs(r.codex.fiveHour.asOf - (now - hour)) < 2000, 'its reading is dated at the reset itself');
    assert.equal(r.codex.weekly.usedPercent, 15, 'the other window is unaffected');

    // ---- nothing installed: nothing invented
    const empty = join(directory, 'empty-home'); await mkdir(empty);
    r = await read(empty);
    assert.deepEqual(r, { claude: {}, codex: {} }, 'no tools, no plan, no windows');
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
