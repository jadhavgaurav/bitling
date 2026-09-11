import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';

async function testIronManVisuals() {
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

  const outDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';

  // 1. Capture Front-View Idle Hover
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.state.species = 'ironman';
    api.state.asleep = false;
    api.pet.mode = 'fly';
    api.pet.grounded = false;
    api.pet.carried = false;
    api.pet.held = false;
    api.pet.walking = false;
    api.pet.ironmanSpeed = 0;
    api.pet.dragSpeed = 0;
    api.pet.dragVx = 0;
    api.pet.dragVy = 0;
    api.pet.zap = 0;
    api.pet.zapCharge = 0;
    api.pet.facing = 1;
    api.pet.x = 190;
    api.pet.y = 280;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
  });
  await page.screenshot({ path: `${outDir}/test_ironman_idle_front.png` });
  console.log('Saved test_ironman_idle_front.png');

  // 2. Capture Supersonic Flight
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.state.asleep = false;
    api.pet.carried = false;
    api.pet.held = false;
    api.pet.ironmanSpeed = 120;
    api.pet.dragSpeed = 120;
    api.pet.dragVx = 120;
    api.pet.dragVy = -20;
    api.pet.walking = true;
    api.pet.facing = 1;
    api.pet.zap = 0;
    api.pet.zapCharge = 0;
    api.pet.x = 180;
    api.pet.y = 260;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
  });
  await page.screenshot({ path: `${outDir}/test_ironman_flying.png` });
  console.log('Saved test_ironman_flying.png');

  // 2b. Capture Supersonic Flight (Moving Left - verifies flare opposite to direction)
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.state.asleep = false;
    api.pet.carried = false;
    api.pet.held = false;
    api.pet.ironmanSpeed = 120;
    api.pet.dragSpeed = 120;
    api.pet.dragVx = -120;
    api.pet.dragVy = -20;
    api.pet.walking = true;
    api.pet.facing = -1;
    api.pet.zap = 0;
    api.pet.zapCharge = 0;
    api.pet.x = 200;
    api.pet.y = 260;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
  });
  await page.screenshot({ path: `${outDir}/test_ironman_flying_left.png` });
  console.log('Saved test_ironman_flying_left.png');

  // 2c. Capture Inspect / Working Stance
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.state.asleep = false;
    api.pet.carried = false;
    api.pet.held = false;
    api.pet.walking = false;
    api.pet.working = true;
    api.pet.ironmanSpeed = 0;
    api.pet.dragSpeed = 0;
    api.pet.dragVx = 0;
    api.pet.dragVy = 0;
    api.pet.facing = 1;
    api.pet.zap = 0;
    api.pet.zapCharge = 0;
    api.pet.x = 190;
    api.pet.y = 280;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
  });
  await page.screenshot({ path: `${outDir}/test_ironman_inspect.png` });
  console.log('Saved test_ironman_inspect.png');

  // 3. Capture Palm Repulsor Blast
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.state.asleep = false;
    api.pet.carried = false;
    api.pet.held = false;
    api.pet.ironmanSpeed = 0;
    api.pet.walking = false;
    api.pet.dragSpeed = 0;
    api.pet.dragVx = 0;
    api.pet.dragVy = 0;
    api.pet.facing = 1;
    api.pet.zap = 0.25;
    api.pet.zapCharge = 0;
    api.pet.zapBoss = false;
    api.pet.zapStyle = 'repulsor';
    api.pet.zapLocal = true;
    api.pet.zapX = 350;
    api.pet.zapY = 160;
    api.pet.x = 130;
    api.pet.y = 290;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
    api.species().attack.draw(api.petR(), 0.85, false, 'repulsor');
  });
  await page.screenshot({ path: `${outDir}/test_ironman_repulsor.png` });
  console.log('Saved test_ironman_repulsor.png');

  // 4. Capture Chest Arc Reactor Unibeam Charge
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.state.asleep = false;
    api.pet.carried = false;
    api.pet.held = false;
    api.pet.ironmanSpeed = 0;
    api.pet.walking = false;
    api.pet.dragSpeed = 0;
    api.pet.dragVx = 0;
    api.pet.dragVy = 0;
    api.pet.zap = 0;
    api.pet.zapBoss = true;
    api.pet.zapStyle = 'unibeam';
    api.pet.zapCharge = 0.5;
    api.pet.zapFull = 0.95;
    api.pet.facing = 1;
    api.pet.x = 170;
    api.pet.y = 280;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
  });
  await page.screenshot({ path: `${outDir}/test_ironman_unibeam_charge.png` });
  console.log('Saved test_ironman_unibeam_charge.png');

  // 5. Capture Chest Arc Reactor Unibeam Fire
  await page.evaluate(() => {
    window.__pauseLoop = true;
    const api = window.__ironmanTest;
    api.state.asleep = false;
    api.pet.carried = false;
    api.pet.held = false;
    api.pet.ironmanSpeed = 0;
    api.pet.walking = false;
    api.pet.dragSpeed = 0;
    api.pet.dragVx = 0;
    api.pet.dragVy = 0;
    api.pet.zapCharge = 0;
    api.pet.zap = 0.35;
    api.pet.zapBoss = true;
    api.pet.zapStyle = 'unibeam';
    api.pet.zapLocal = true;
    api.pet.zapX = 360;
    api.pet.zapY = 200;
    api.pet.facing = 1;
    api.pet.x = 110;
    api.pet.y = 290;
    api.ctx.clearRect(0, 0, 380, 420);
    api.drawIronMan();
    api.species().attack.draw(api.petR(), 0.95, true, 'unibeam');
  });
  await page.screenshot({ path: `${outDir}/test_ironman_unibeam_fire.png` });
  console.log('Saved test_ironman_unibeam_fire.png');

  await browser.close();
  console.log('All visual screenshots captured successfully!');
}

testIronManVisuals().catch(err => {
  console.error(err);
  process.exit(1);
});
