import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

async function capture() {
  const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';
  const petHtmlPath = join(process.cwd(), 'Resources', 'pet.html');
  const petHtml = await readFile(petHtmlPath, 'utf8');

  const injectedHtml = petHtml.replace(
    '  // ---------------------------------------------------------------- boot',
    `window.__gokuPreview = { pet, state, drawGoku, ctx, canvas, petR, species };
  // ---------------------------------------------------------------- boot`
  );

  const browser = await chromium.launch({
    channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome'
  });

  const page = await browser.newPage({
    viewport: { width: 400, height: 400 },
    deviceScaleFactor: 2
  });

  await page.addInitScript(() => {
    window.requestAnimationFrame = () => 0;
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
      return route.fulfill({ contentType: 'text/html', body: injectedHtml });
    }
    return route.abort();
  });

  await page.goto('http://bitling.preview/');
  await page.waitForTimeout(500);

  // 1. Idle Kid Goku floating on Flying Nimbus
  await page.evaluate(() => {
    const api = window.__gokuPreview;
    api.state.species = 'goku';
    Object.assign(api.pet, {
      x: 200,
      y: 220,
      t: 1.2,
      facing: 1,
      mode: 'fly',
      grounded: false,
      walking: false,
      chew: 0,
      waving: 0,
      zapCharge: 0,
      zap: 0
    });
    api.ctx.clearRect(0, 0, 400, 400);
    api.drawGoku();
  });
  await page.screenshot({ path: join(artifactDir, 'goku_nimbus_idle.png') });

  // 2. Kid Goku charging Kamehameha with Aura
  await page.evaluate(() => {
    const api = window.__gokuPreview;
    Object.assign(api.pet, {
      x: 200,
      y: 220,
      t: 3.5,
      facing: 1,
      mode: 'fly',
      grounded: false,
      walking: false,
      zapCharge: 0.9,
      zapFull: 1,
      zapBoss: true,
      zapStyle: 'kamehameha'
    });
    api.ctx.clearRect(0, 0, 400, 400);
    api.drawGoku();
  });
  await page.screenshot({ path: join(artifactDir, 'goku_kamehameha_charge.png') });

  // 3. Kid Goku waving cheerfully
  await page.evaluate(() => {
    const api = window.__gokuPreview;
    Object.assign(api.pet, {
      x: 200,
      y: 220,
      t: 2.0,
      facing: 1,
      mode: 'fly',
      grounded: false,
      walking: false,
      waving: 1.6,
      happy: 1,
      zapCharge: 0,
      zap: 0
    });
    api.ctx.clearRect(0, 0, 400, 400);
    api.drawGoku();
  });
  await page.screenshot({ path: join(artifactDir, 'goku_waving.png') });

  // 4. Kid Goku eating meat bone
  await page.evaluate(() => {
    const api = window.__gokuPreview;
    Object.assign(api.pet, {
      x: 200,
      y: 220,
      t: 2.5,
      facing: 1,
      mode: 'fly',
      grounded: false,
      walking: false,
      chew: 1,
      happy: 1,
      waving: 0
    });
    api.ctx.clearRect(0, 0, 400, 400);
    api.drawGoku();
  });
  await page.screenshot({ path: join(artifactDir, 'goku_eating.png') });

  await browser.close();
  console.log('Saved preview screenshots to artifact directory.');
}

capture().catch(console.error);
