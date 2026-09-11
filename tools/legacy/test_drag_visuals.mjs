import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

async function main() {
  const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';
  const petHtmlPath = join(process.cwd(), 'Resources', 'pet.html');
  const petHtml = await readFile(petHtmlPath, 'utf8');

  const browser = await chromium.launch({
    channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome'
  });

  const page = await browser.newPage({
    viewport: { width: 420, height: 440 },
    deviceScaleFactor: 2
  });

  await page.addInitScript(() => {
    window.__hostMessages = [];
    window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
    window.__petSavedState = JSON.stringify({
      species: 'goku',
      hatched: true,
      sound: false
    });
  });

  await page.route('**/*', route => {
    if (route.request().url() === 'http://bitling.preview/') {
      return route.fulfill({ contentType: 'text/html', body: petHtml });
    }
    return route.abort();
  });

  await page.goto('http://bitling.preview/');
  await page.waitForTimeout(600);

  // Switch to Goku if not already
  await page.evaluate(() => {
    if (window.petNative) {
      window.petNative.setSpecies('goku');
    }
  });
  await page.waitForTimeout(400);

  const canvas = page.locator('canvas#stage');
  const box = await canvas.boundingBox();

  // Test 1: Grab and drag to the right
  const startX = box.x + box.width / 2;
  const startY = box.y + box.height / 2;

  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.waitForTimeout(100);

  // Move right rapidly
  for (let i = 1; i <= 8; i++) {
    await page.mouse.move(startX + i * 15, startY - i * 4);
    await page.waitForTimeout(20);
  }
  await page.screenshot({ path: join(artifactDir, 'goku_drag_right.png') });
  console.log('Captured goku_drag_right.png');

  // Move left rapidly (should smoothly turn around, face left, bank into flight)
  for (let i = 1; i <= 14; i++) {
    await page.mouse.move(startX + 120 - i * 18, startY - 32 + i * 5);
    await page.waitForTimeout(20);
  }
  await page.screenshot({ path: join(artifactDir, 'goku_drag_left.png') });
  console.log('Captured goku_drag_left.png');

  // Drag down steeply (dive)
  for (let i = 1; i <= 8; i++) {
    await page.mouse.move(startX - 130 + i * 4, startY + 38 + i * 12);
    await page.waitForTimeout(20);
  }
  await page.screenshot({ path: join(artifactDir, 'goku_drag_dive.png') });
  console.log('Captured goku_drag_dive.png');

  // Release mouse
  await page.mouse.up();
  await page.waitForTimeout(600);
  await page.screenshot({ path: join(artifactDir, 'goku_after_release.png') });
  console.log('Captured goku_after_release.png');

  await browser.close();
}

main().catch(console.error);
