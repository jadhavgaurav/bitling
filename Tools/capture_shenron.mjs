import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const directory = resolve(process.argv[2] || 'artifacts/shenron');
await mkdir(directory, { recursive: true });
const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
try {
  for (const [name, width, height] of [['desktop', 1440, 900], ['compact', 300, 340]]) {
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
      window.__petSavedState = JSON.stringify({ species: 'dragon', hatched: true, sound: false,
        born: Date.now() - 3 * 86400000, lastSeen: Date.now(), full: 95, energy: 95, joy: 95, care: 440 });
    });
    await page.goto(`file://${resolve('Resources/pet.html')}`);
    await page.waitForFunction(() => window.__bitling.shenronReady());
    await page.evaluate(() => { window.petNative.stageSize(1); window.petNative.advance(1); window.__bitling.say('I am Shenron. State your wish.', 60000); window.petNative.advance(0.1); });
    await page.screenshot({ path: resolve(directory, `${name}.png`), omitBackground: true });
    if (name === 'desktop') {
      await page.evaluate(() => { window.__bitling.hideBubble(); window.petNative.advance(1.5); });
      await page.screenshot({ path: resolve(directory, 'desktop-phase-2.png'), omitBackground: true });
      await page.evaluate(() => window.petNative.advance(1.5));
      await page.screenshot({ path: resolve(directory, 'desktop-phase-3.png'), omitBackground: true });
      await page.evaluate(() => {
        window.__bitling.steerShenron(Math.PI * 0.75);
        window.petNative.advance(3.5);
      });
      await page.screenshot({ path: resolve(directory, 'desktop-turn.png'), omitBackground: true });
    }
    const timing = await page.evaluate(() => {
      const start = performance.now();
      for (let i = 0; i < 120; i++) window.petNative.advance(1 / 60);
      return (performance.now() - start) / 120;
    });
    console.log(`${name}: ${timing.toFixed(2)}ms per simulation/render`);
    await page.close();
  }
} finally { await browser.close(); }
