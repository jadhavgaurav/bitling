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
        logos: [...document.querySelectorAll('#quotaHud img.quota-logo')].map(i => ({ ok: i.complete && i.naturalWidth === 64, provider: i.closest('.quota-sec').id })),
      };
    });
    assert.deepEqual(hud.logos, [{ ok: true, provider: 'quotaClaudeSec' }, { ok: true, provider: 'quotaCodexSec' }],
      'each provider shows its own logo, and both images decode');
    assert.ok(!/[\u26A1\u{1F300}]/u.test(hud.all), 'the emoji stand-ins are gone');
    assert.equal(hud.hidden, false);
    assert.equal(hud.claudePlan, 'Max 20x');
    assert.equal(hud.codexPlan, 'Plus');
    assert.equal(hud.claude5hVal, '94%');
    assert.equal(hud.claude5hSub, '94% used', 'a fresh reading carries no age label');
    assert.ok(hud.claude5hCls.includes('critical'), '90% or more used is critical');
    assert.equal(hud.claudeWkVal, '40%');
    assert.equal(hud.claudeWkSub, '40% used · logged 2h 0m ago', 'a two hour old sample is labelled as old');
    assert.equal(hud.codex5hVal, '20%');
    assert.equal(hud.codex5hSub, '20% used · resets in 2h 10m');
    assert.equal(hud.codexWkVal, '--');
    assert.equal(hud.codexWkSub, 'no recent data', 'a window nobody recorded is not shown as 0% used');
    assert.equal(hud.codexWkWidth, '0%');
    assert.ok(!/NaN|undefined|null|turns|gpt-/i.test(hud.all), `no stray placeholder text: ${hud.all}`);

    const stale = await page.evaluate(() => {
      const now = Date.now(), hour = 3600000;
      window.petNative.quotaUpdate({ showClaude: true, showCodex: true,
        claude: { plan: 'Max 20x', liveStatus: 'claude did not answer', fiveHour: { usedPercent: 10, asOf: now - 2 * hour } },
        codex: { plan: 'Plus', weekly: { usedPercent: 16, resetsAt: now + 5 * 24 * hour, asOf: now - 50 * hour } } });
      window.__quota.showQuotaHud(3000);
      const text = id => document.querySelector(id).textContent;
      return { codexWk: text('#quotaCodexWkSub'), claudeNote: text('#quotaClaudeNote'),
               claudeNoteHidden: document.querySelector('#quotaClaudeNote').hidden,
               codexNoteHidden: document.querySelector('#quotaCodexNote').hidden };
    });
    assert.equal(stale.codexWk, '16% used · logged 2d 2h ago',
      'a reset time out of a two day old log must not be shown as a live countdown');
    assert.equal(stale.claudeNote, 'Not live: claude did not answer');
    assert.equal(stale.claudeNoteHidden, false);
    assert.equal(stale.codexNoteHidden, true, 'no note when nothing is wrong');
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
func json(_ object: Any) -> String { String(decoding: try! JSONSerialization.data(withJSONObject: object, options: [.sortedKeys]), as: UTF8.self) }
func window(_ w: QuotaWindow?) -> Any {
    guard let w else { return NSNull() }
    return ["used": w.usedPercent, "resetsAt": w.resetsAt as Any? ?? NSNull(), "asOf": w.asOf]
}
let args = CommandLine.arguments
let now = Date(timeIntervalSince1970: 1_791_790_000)
switch args[1] {
case "files":
    print(String(decoding: try! enc.encode(QuotaReader.read(home: URL(fileURLWithPath: args[2]))), as: UTF8.self))
case "claude-usage":
    let text = try! String(contentsOf: URL(fileURLWithPath: args[2]), encoding: .utf8)
    if let r = ClaudeUsageTextParser.parse(text, fetchedAt: now) { print(json(["fiveHour": window(r.fiveHour), "weekly": window(r.weekly)])) } else { print("nil") }
case "codex-usage":
    let data = try! Data(contentsOf: URL(fileURLWithPath: args[2]))
    let object = try! JSONSerialization.jsonObject(with: data) as! [String: Any]
    if let r = CodexUsageParser.parse(object, fetchedAt: now) { print(json(["plan": r.plan as Any? ?? NSNull(), "fiveHour": window(r.fiveHour), "weekly": window(r.weekly)])) } else { print("nil") }
default: print("unknown mode")
}
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
    const read = async home => JSON.parse((await run(binary, ['files', home])).stdout);
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

test('live readings are parsed from the real output shapes', async (t) => {
  if (!(await swiftAvailable())) return t.skip('swiftc is not installed');
  const directory = await mkdtemp(join(tmpdir(), 'bitling-quota-live-'));
  try {
    await writeFile(join(directory, 'main.swift'), DRIVER);
    const binary = join(directory, 'reader');
    await run('swiftc', ['-O', '-swift-version', '5', 'apps/macos/Sources/QuotaWatcher.swift', join(directory, 'main.swift'), '-o', binary]);
    const ask = async (mode, body) => {
      const file = join(directory, `${mode}.json`);
      await writeFile(file, JSON.stringify(body));
      const out = (await run(binary, [mode, file])).stdout.trim();
      return out === 'nil' ? null : JSON.parse(out);
    };
    const fetchedAt = 1_791_790_000_000;

    // Claude: the text `claude -p /usage` prints. Resets are in the zone the CLI names.
    const askText = async text => {
      const file = join(directory, 'claude.txt');
      await writeFile(file, text);
      const out = (await run(binary, ['claude-usage', file])).stdout.trim();
      return out === 'nil' ? null : JSON.parse(out);
    };
    let r = await askText(`You are currently using your subscription to power your Claude Code usage

Current session: 7% used · resets Oct 12 at 1:20pm (Asia/Calcutta)
Current week (all models): 82% used · resets Oct 18 at 5:30am (Asia/Calcutta)
Current week (Fable): 0% used · resets Oct 18 at 5:30am (Asia/Calcutta)
`);
    assert.equal(r.fiveHour.used, 7);
    assert.equal(r.weekly.used, 82, 'the all-models week, not the per-model one');
    assert.equal(r.fiveHour.resetsAt, Date.UTC(2026, 9, 12, 7, 50), '1:20pm IST');
    assert.equal(r.weekly.resetsAt, Date.UTC(2026, 9, 18, 0, 0), '5:30am IST on the 18th');
    assert.equal(r.fiveHour.asOf, 1_791_790_000_000, 'a live reading is dated when it was fetched');
    r = await askText('Current session: 0% used\nCurrent week (all models): 140% used · resets Jan 3 at 9am (UTC)\n');
    assert.equal(r.fiveHour.used, 0);
    assert.equal(r.fiveHour.resetsAt, null, 'an untouched window has no reset');
    assert.equal(r.weekly.used, 100, 'clamped');
    assert.equal(r.weekly.resetsAt, Date.UTC(2027, 0, 3, 9, 0), 'a date already past rolls to next year');
    assert.equal(await askText('Not logged in\n'), null, 'an unrecognised output is a failure, not zeros');

    // Codex: the shape account/rateLimits/read really returned, with the "codex" bucket chosen.
    const bucket = (limitId, p, s) => ({ limitId, limitName: null,
      primary: { usedPercent: p, windowDurationMins: 300, resetsAt: 1791791842 },
      secondary: { usedPercent: s, windowDurationMins: 10080, resetsAt: 1792378642 },
      credits: { hasCredits: false, unlimited: false, balance: '0' }, planType: 'plus', rateLimitReachedType: null });
    r = await ask('codex-usage', { rateLimits: bucket('codex', 4, 1), rateLimitsByLimitId: { codex: bucket('codex', 4, 1) }, rateLimitResetCredits: { availableCount: 0, credits: [] } });
    assert.equal(r.plan, 'Plus');
    assert.equal(r.fiveHour.used, 4);
    assert.equal(r.weekly.used, 1);
    assert.equal(r.fiveHour.resetsAt, 1791791842000, 'seconds become ms');
    assert.equal(r.weekly.resetsAt, 1792378642000);
    r = await ask('codex-usage', { rateLimits: bucket('premium', 90, 90), rateLimitsByLimitId: { premium: bucket('premium', 90, 90), codex: bucket('codex', 4, 1) } });
    assert.equal(r.fiveHour.used, 4, 'the codex bucket wins when several are present');
    r = await ask('codex-usage', { rateLimits: bucket('codex', 7, 2) });
    assert.equal(r.fiveHour.used, 7, 'the single-bucket form still works');
    assert.equal(await ask('codex-usage', { rateLimits: bucket('premium', 90, 90) }), null, 'a non-codex bucket alone is not codex usage');
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('the hook ignores Bitling\'s own usage probe', async () => {
  // --- the hook: a probe run must not tell the pet anything, a real session must
  const directory = await mkdtemp(join(tmpdir(), 'bitling-quota-hook-'));
  try {
    const bin = join(directory, 'bin'), log = join(directory, 'opened.txt');
    await mkdir(bin);
    await writeFile(join(bin, 'open'), `#!/bin/bash\necho "$@" >> '${log}'\n`, { mode: 0o755 });
    const env = extra => ({ ...process.env, PATH: `${bin}:${process.env.PATH}`, ...extra });
    const fire = (extra) => new Promise((resolve, reject) => {
      const child = execFile('/bin/bash', ['apps/macos/Resources/bitling', 'claude'], { env: env(extra) }, err => err ? reject(err) : resolve());
      child.stdin.end(JSON.stringify({ hook_event_name: 'Stop', cwd: '/tmp/some-project' }));
    });
    await fire({ BITLING_PROBE: '1' });
    const probed = await readFile(log, 'utf8').catch(() => '');
    assert.equal(probed, '', 'a probe run must not reach the pet');
    await fire({});
    const real = await readFile(log, 'utf8').catch(() => '');
    assert.match(real, /bitling:\/\/claude-done\?name=some-project/, 'a real session still reaches the pet');
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('the menu logos ship in the bundle: valid 64px PNGs that the code and the build both point at', async () => {
  for (const name of ['claude', 'codex']) {
    const png = await readFile(`apps/macos/Resources/logos/${name}.png`);
    assert.equal(png.subarray(1, 4).toString(), 'PNG', `${name}.png is a PNG`);
    assert.deepEqual([png.readUInt32BE(16), png.readUInt32BE(20)], [64, 64], `${name}.png is 64x64`);
    assert.match(await readFile('apps/macos/Sources/main.swift', 'utf8'), new RegExp(`menuLogo\\("${name}"\\)`), `${name} is attached to its menu item`);
  }
  assert.match(await readFile('apps/macos/build.sh', 'utf8'), /cp -R Resources\/logos/, 'build.sh copies the logos into the app');
});
