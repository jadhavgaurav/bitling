import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const html = readFileSync(new URL('../Resources/pet.html', import.meta.url), 'utf8').replace(
  '  // ---------------------------------------------------------------- boot',
  `window.__pikachuVerify = { pet, state, ctx, canvas, drawPikachu };
  // ---------------------------------------------------------------- boot`
);

async function main() {
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  const page = await browser.newPage({ viewport: { width: 340, height: 380 }, deviceScaleFactor: 2 });

  await page.addInitScript(() => {
    window.requestAnimationFrame = () => 0;
    window.__hostMessages = [];
    window.webkit = { messageHandlers: { pet: { postMessage: m => window.__hostMessages.push(m) } } };
    window.__petSavedState = JSON.stringify({
      species: 'pikachu',
      hatched: true,
      sound: false,
      born: Date.now(),
      lastSeen: Date.now(),
      joy: 100,
      energy: 100,
      full: 100,
    });
  });

  await page.route('**/*', route => {
    if (route.request().url() === 'http://bitling.test/') {
      return route.fulfill({ contentType: 'text/html', body: html });
    }
    return route.abort();
  });

  await page.goto('http://bitling.test/');

  const poses = [
    { name: 'idle', pet: {} },
    { name: 'run', pet: { walking: true, walkDir: 1 } },
    { name: 'charge', pet: { zapCharge: 0.2, zapFull: 0.5 } },
    { name: 'attack', pet: { zap: 0.2 } },
    { name: 'dangle', pet: { carried: true, dragSpeed: 100 } },
    { name: 'sleep', pet: {}, asleep: true },
  ];

  const artifactDir = process.env.BITLING_ARTIFACT_DIR || '/tmp/bitling-pikachu-poses';
  mkdirSync(artifactDir, { recursive: true });

  for (const pose of poses) {
    await page.evaluate((pose) => {
      const { pet, state, ctx, canvas, drawPikachu } = window.__pikachuVerify;
      Object.assign(pet, { vx: 0, walking: false, walkDir: 0, held: false, carried: false,
        dragSpeed: 0, zapCharge: 0, zap: 0, zapStyle: 'thunderbolt' }, pose.pet);
      state.asleep = !!pose.asleep;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      drawPikachu();
    }, pose);

    const shotPath = `${artifactDir}/pikachu_pose_${pose.name}.png`;
    const buffer = await page.screenshot({ clip: { x: 50, y: 70, width: 240, height: 260 }, omitBackground: false });
    writeFileSync(shotPath, buffer);
    console.log(`Saved screenshot: ${shotPath}`);
  }

  await browser.close();
}

main().catch(console.error);
