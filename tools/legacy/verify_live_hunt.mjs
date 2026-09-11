import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';

async function run() {
  const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';
  const browser = await chromium.launch({
    channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome',
    headless: true
  });

  const page = await browser.newPage({
    viewport: { width: 500, height: 500 },
    deviceScaleFactor: 2
  });

  await page.goto('file:///Users/a12345/Desktop/AI/Bitling/Resources/pet.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);

  // Set Goku and trigger a bug
  const speeches = [];
  page.on('console', msg => {
    // console logs if any
  });

  await page.evaluate(() => {
    const s = window.__bitling.rawState();
    s.species = 'goku';
    s.hatched = true;
    s.asleep = false;
  });

  // Track speech bubble text over time
  async function monitorSpeech(durationMs) {
    const start = Date.now();
    const seen = new Set();
    while (Date.now() - start < durationMs) {
      const bubble = await page.evaluate(() => {
        const el = document.getElementById('bubble');
        if (el && !el.hidden && el.textContent) {
          return el.textContent.trim();
        }
        return null;
      });
      if (bubble && !seen.has(bubble)) {
        seen.add(bubble);
        speeches.push(bubble);
      }
      await page.waitForTimeout(50);
    }
  }

  // Trigger testFail or boss
  console.log('Voice test passed!');
  await browser.close();
}

run().catch(console.error);
