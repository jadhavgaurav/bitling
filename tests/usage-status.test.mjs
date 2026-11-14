import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';
const run = promisify(execFile);

test('the menu bar colours match the pet page, stop for stop and in between', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-usage-color-'));
  try {
    const probe = join(directory, 'main.swift');
    await writeFile(probe, `
for percent in [-5.0, 0, 12, 60, 72, 85, 100, 140] {
    print(percent, UsageColor.rgb(for: percent).map(String.init).joined(separator: ","))
}
`);
    const binary = join(directory, 'probe');
    await run('swiftc', ['-O', '-swift-version', '5', 'apps/macos/Sources/SystemMonitor.swift', probe, '-o', binary]);
    const native = new Map((await run(binary)).stdout.trim().split('\n').map(line => {
      const [percent, rgb] = line.split(' ');
      return [Number(percent), rgb];
    }));

    // The page's own function, read from the shipped source so the two cannot drift apart.
    const source = await readFile('apps/macos/web/bitling.html', 'utf8');
    const start = source.indexOf('const USAGE_STOPS');
    const end = source.indexOf('function paintSystemRow');
    assert.ok(start > 0 && end > start, 'the page colour function is where the test expects it');
    const usageRgb = new Function(`${source.slice(start, end)}; return usageRgb;`)();
    for (const [percent, rgb] of native) {
      const expected = usageRgb(percent).match(/\d+/g).join(',');
      assert.equal(rgb, expected, `${percent}% is the same colour in the menu bar and on the pet`);
    }
    assert.equal(native.get(0), '34,197,94', 'idle is green');
    assert.equal(native.get(60), '245,158,11', '60% is amber');
    assert.equal(native.get(140), '239,68,68', 'anything past the last stop stays red');
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('a Claude reading older than 15 minutes counts as stale, so the menu bar cannot show it as live', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-stale-'));
  try {
    const probe = join(directory, 'main.swift');
    await writeFile(probe, `
import Foundation
let now = Date()
func window(minutesOld: Double) -> QuotaWindow {
    QuotaWindow(usedPercent: 14, resetsAt: nil, asOf: (now.timeIntervalSince1970 - minutesOld * 60) * 1000)
}
for minutes in [0.0, 14, 16, 600, -5] {
    print(minutes, window(minutesOld: minutes).isStale(at: now))
}
`);
    const binary = join(directory, 'probe');
    await run('swiftc', ['-O', '-swift-version', '5', 'apps/macos/Sources/QuotaWatcher.swift', probe, '-o', binary]);
    const out = new Map((await run(binary)).stdout.trim().split('\n').map(line => line.split(' ')));
    assert.equal(out.get('0.0'), 'false', 'a fresh reading is live');
    assert.equal(out.get('14.0'), 'false', 'still live just under 15 minutes');
    assert.equal(out.get('16.0'), 'true', 'stale past 15 minutes');
    assert.equal(out.get('600.0'), 'true', 'stale after hours');
    assert.equal(out.get('-5.0'), 'false', 'a reading stamped in the future is not stale');
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('the pet HUD stays shut until the menu bar item turns it on', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-hud-switch-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace('  // ---------------------------------------------------------------- boot',
      'window.__hud = { showQuotaHud };\n  // ---------------------------------------------------------------- boot');
    const page = await browser.newPage({ viewport: { width: 360, height: 560 } });
    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
      window.__petSavedState = JSON.stringify({ species: 'robot', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now(), full: 90, energy: 90, joy: 90 });
    });
    await page.route('**/*', route => route.request().url() === 'http://hud.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
    await page.goto('http://hud.test/');
    const result = await page.evaluate(() => {
      const hidden = () => document.querySelector('#quotaHud').hidden;
      const out = {};
      window.petNative.systemUpdate({ cpu: 30, memory: 40 });
      window.petNative.hudEnabled(false);
      window.__hud.showQuotaHud(60000);
      out.offStaysShut = hidden();
      window.petNative.hudEnabled(true);
      window.__hud.showQuotaHud(60000);
      out.onOpens = !hidden();
      window.petNative.hudEnabled(false);
      out.offClosesAnOpenOne = hidden();
      return out;
    });
    assert.equal(result.offStaysShut, true, 'a tap on the pet opens nothing while the HUD is off');
    assert.equal(result.onOpens, true, 'turning it on brings the HUD back');
    assert.equal(result.offClosesAnOpenOne, true, 'turning it off closes an open HUD');
  } finally {
    await browser.close();
    await rm(directory, { recursive: true, force: true });
  }
});
