import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';

const outDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';

async function testDrag() {
  const browser = await chromium.launch({
    channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome',
    headless: true
  });
  const page = await browser.newPage({
    viewport: { width: 380, height: 420 },
    deviceScaleFactor: 2
  });

  const html = (await readFile('Resources/pet.html', 'utf8'))
    .replace(
      '  function frame(t) {',
      `  function frame(t) {
    if (window.__pauseLoop) { requestAnimationFrame(frame); return; }`
    )
    .replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__ironmanTest = { pet, state, draw, drawIronMan, ctx, canvas, petR, species, SPECIES, updatePet };
  // ---------------------------------------------------------------- boot`
    );

  await page.addInitScript(() => {
    window.__hostMessages = [];
    window.webkit = {
      messageHandlers: {
        pet: {
          postMessage: msg => window.__hostMessages.push(msg)
        }
      }
    };
    window.__petSavedState = JSON.stringify({
      species: 'ironman',
      hatched: true,
      sound: false,
      born: Date.now(),
      lastSeen: Date.now()
    });
  });

  await page.route('**/*', route => {
    if (route.request().url() === 'http://bitling.test/') {
      route.fulfill({ contentType: 'text/html', body: html });
    } else {
      route.abort();
    }
  });

  await page.goto('http://bitling.test/');
  await page.waitForTimeout(500);

  // Test 1: Dragging moving right (vx = 150, vy = 0)
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.pet.carried = true;
    api.pet.held = true;
    api.pet.dragSpeed = 150;
    api.pet.dragVx = 150;
    api.pet.dragVy = 0;
    api.pet.vx = 150;
    api.pet.vy = 0;
    api.pet.facing = 1;
    api.pet.x = 190;
    api.pet.y = 250;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
  });
  await page.screenshot({ path: `${outDir}/test_drag_right.png` });

  // Test 2: Dragging moving left (vx = -150, vy = 0)
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.pet.carried = true;
    api.pet.held = true;
    api.pet.dragSpeed = 150;
    api.pet.dragVx = -150;
    api.pet.dragVy = 0;
    api.pet.vx = -150;
    api.pet.vy = 0;
    api.pet.facing = -1;
    api.pet.x = 190;
    api.pet.y = 250;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
  });
  await page.screenshot({ path: `${outDir}/test_drag_left.png` });

  // Test 3: Dragging held stationary / slow (vx = 0, vy = 0)
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.pet.carried = true;
    api.pet.held = true;
    api.pet.dragSpeed = 0;
    api.pet.dragVx = 0;
    api.pet.dragVy = 0;
    api.pet.vx = 0;
    api.pet.vy = 0;
    api.pet.ironmanSpeed = 0;
    api.pet.facing = 1;
    api.pet.x = 190;
    api.pet.y = 250;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
  });
  await page.screenshot({ path: `${outDir}/test_drag_still.png` });

  // Test 4: Dragging moving upward (vx = 0, vy = -150)
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.pet.carried = true;
    api.pet.held = true;
    api.pet.dragSpeed = 150;
    api.pet.dragVx = 0;
    api.pet.dragVy = -150;
    api.pet.vx = 0;
    api.pet.vy = -150;
    api.pet.facing = 1;
    api.pet.x = 190;
    api.pet.y = 250;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
  });
  await page.screenshot({ path: `${outDir}/test_drag_up.png` });

  await browser.close();
  console.log('Drag tests completed successfully!');
}

testDrag().catch(console.error);
