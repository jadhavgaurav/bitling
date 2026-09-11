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

  const petHtmlPath = 'file:///Users/a12345/Desktop/AI/Bitling/Resources/pet.html';
  console.log(`Loading ${petHtmlPath}...`);
  await page.goto(petHtmlPath, { waitUntil: 'networkidle' });

  await page.waitForTimeout(600);

  // Set species to Goku
  await page.evaluate(() => {
    const s = window.__bitling.rawState();
    const p = window.__bitling.pet();
    s.species = 'goku';
    s.hatched = true;
    s.asleep = false;
    p.facing = 1;
    p.x = 220;
    p.y = 350;
    p.carried = false;
    p.held = false;
    p.walking = false;
    p.gokuSpeed = 0;
    window.__bitling.draw();
  });
  await page.waitForTimeout(200);

  // 1. Idle Screenshot
  await page.evaluate(() => {
    const p = window.__bitling.pet();
    p.carried = false;
    p.held = false;
    p.walking = false;
    p.gokuSpeed = 0;
    p.zapCharge = 0;
    p.zap = 0;
    p.zapAim = null;
    window.__bitling.draw();
  });
  await page.waitForTimeout(100);
  const idleBuf = await page.screenshot();
  await writeFile(join(artifactDir, 'test_goku_idle.png'), idleBuf);
  console.log('Saved test_goku_idle.png');

  // 2. Flying / Dragging Screenshot
  await page.evaluate(() => {
    const p = window.__bitling.pet();
    p.carried = true;
    p.dragVx = 120;
    p.dragVy = -20;
    p.gokuSpeed = 120;
    p.facing = 1;
    p.gokuPitch = 0.08;
    p.zapCharge = 0;
    p.zap = 0;
    p.zapAim = null;
    window.__bitling.draw();
  });
  await page.waitForTimeout(100);
  const flyBuf = await page.screenshot();
  await writeFile(join(artifactDir, 'test_goku_flying.png'), flyBuf);
  console.log('Saved test_goku_flying.png');

  // 3. Kamehameha Charging against Boss Bug
  await page.evaluate(() => {
    const p = window.__bitling.pet();
    p.carried = false;
    p.held = false;
    p.walking = false;
    p.gokuSpeed = 0;
    p.zapAim = { bug: { alive: true, x: 450, y: 220 } };
    p.zapCharge = 5.0; // plenty of time to not expire
    p.zapFull = 5.0;
    p.zapBoss = true;
    p.zapStyle = 'kamehameha';
    p.zap = 0;
    p.facing = 1;
    window.__bitling.say("KA... ME... HA... ME...", 5000);
    window.__bitling.draw();
  });
  await page.waitForTimeout(100);
  const kameChargeBuf = await page.screenshot();
  await writeFile(join(artifactDir, 'test_goku_kame_charge.png'), kameChargeBuf);
  console.log('Saved test_goku_kame_charge.png');

  // 4. Kamehameha Firing against Boss Bug
  await page.evaluate(() => {
    const p = window.__bitling.pet();
    p.carried = false;
    p.held = false;
    p.walking = false;
    p.gokuSpeed = 0;
    p.zapCharge = 0;
    p.zap = 2.0; // plenty of time to not expire
    p.zapBoss = true;
    p.zapStyle = 'kamehameha';
    p.zapX = 460;
    p.zapY = 220;
    p.facing = 1;
    window.__bitling.say("HA---!", 4000);
    window.__bitling.draw();
  });
  await page.waitForTimeout(100);
  const kameFireBuf = await page.screenshot();
  await writeFile(join(artifactDir, 'test_goku_kame_fire.png'), kameFireBuf);
  console.log('Saved test_goku_kame_fire.png');

  // 5. Ki Blast Firing against Small Bug
  await page.evaluate(() => {
    const p = window.__bitling.pet();
    p.carried = false;
    p.held = false;
    p.walking = false;
    p.gokuSpeed = 0;
    p.zapCharge = 0;
    p.zap = 2.0; // plenty of time
    p.zapBoss = false;
    p.zapStyle = 'kiball';
    p.zapX = 440;
    p.zapY = 240;
    p.facing = 1;
    window.__bitling.say("Ha!", 4000);
    window.__bitling.draw();
  });
  await page.waitForTimeout(100);
  const kiBlastBuf = await page.screenshot();
  await writeFile(join(artifactDir, 'test_goku_ki_blast.png'), kiBlastBuf);
  console.log('Saved test_goku_ki_blast.png');

  await browser.close();
  console.log('Captured all 5 combat states successfully!');
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
