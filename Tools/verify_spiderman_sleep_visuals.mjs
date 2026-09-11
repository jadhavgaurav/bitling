import { chromium } from 'playwright';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const PAGE = resolve(HERE, '..', 'Resources', 'pet.html');

async function main() {
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  const page = await browser.newPage({ viewport: { width: 420, height: 480 }, deviceScaleFactor: 2 });

  await page.addInitScript(() => {
    window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
    window.__petSavedState = JSON.stringify({
      v: 1, name: 'Spidey', species: 'spiderman', hatched: true,
      sound: false, asleep: false, full: 90, energy: 90, joy: 90
    });
  });

  await page.goto(`file://${PAGE}`);
  await page.waitForFunction(() => window.petNative && window.petNative.debug);

  // 1. Capture Normal Standing / Perch
  await page.evaluate(() => window.petNative.advance(0.1));
  await page.screenshot({ path: '/tmp/spiderman_perch_preview.png' });

  // 2. Put into Sleep Mode (shoots web to window header, hangs upside down)
  await page.evaluate(() => {
    window.petNative.action('sleep');
    window.petNative.advance(3.2); // allow initial speech bubble to hide cleanly
  });
  await page.screenshot({ path: '/tmp/spiderman_hanging_sleep.png' });

  // 3. Drag downwards & sideways to show elastic web stretching & thinning
  await page.evaluate(() => {
    window.petNative.stageDrag(50, 110);
    window.petNative.advance(0.05);
  });
  await page.screenshot({ path: '/tmp/spiderman_sleep_stretched.png' });

  // 4. Release and let bungee spring settle
  await page.evaluate(() => {
    window.petNative.release();
    window.petNative.advance(1.5);
  });
  await page.screenshot({ path: '/tmp/spiderman_sleep_bungee_settled.png' });

  // 5. Wake up (cuts web strand, somersault flip landing on feet)
  await page.evaluate(() => {
    window.petNative.action('sleep');
    window.petNative.advance(0.5);
  });
  await page.screenshot({ path: '/tmp/spiderman_wake_landed.png' });

  await browser.close();
  console.log('Visual screenshots saved to /tmp/ successfully!');
}

main().catch(console.error);
