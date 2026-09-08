import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';

async function capture() {
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  const page = await browser.newPage({ viewport: { width: 360, height: 380 }, deviceScaleFactor: 2 });

  const html = (await readFile('Resources/pet.html', 'utf8')).replace(
    '  // ---------------------------------------------------------------- boot',
    `window.__pikaTest = { pet, state, draw, drawPikachu, ctx, canvas, petR, species, SPECIES, updatePet };
  // ---------------------------------------------------------------- boot`
  );

  await page.addInitScript(() => {
    window.requestAnimationFrame = () => 0;
    window.__hostMessages = [];
    window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
    window.__petSavedState = JSON.stringify({ species: 'pikachu', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
  });

  await page.route('**/*', route => route.fulfill({ contentType: 'text/html', body: html }));
  await page.goto('http://bitling.test/');

  // Wait for sprites to load
  await page.waitForTimeout(300);

  const defaultY = await page.evaluate(() => window.__pikaTest.pet.y || 320);

  const captureState = async (filename, setupFn) => {
    await page.evaluate(setupFn, defaultY);
    await page.screenshot({ path: join(artifactDir, filename) });
    console.log(`Saved ${filename}`);
  };

  // 1. Alert Idle
  await captureState('pikachu_live_idle.png', (gy) => {
    const api = window.__pikaTest;
    api.pet.x = 180; api.pet.y = gy; api.pet.facing = 1;
    api.pet.walking = false; api.pet.carried = false; api.pet.zap = 0; api.pet.zapCharge = 0;
    api.ctx.clearRect(0, 0, 360, 380);
    api.drawPikachu();
  });

  // 2. Scamper Run
  await captureState('pikachu_live_run.png', (gy) => {
    const api = window.__pikaTest;
    api.pet.x = 180; api.pet.y = gy; api.pet.facing = 1;
    api.pet.walking = true; api.pet.walkDir = 1; api.pet.dragSpeed = 75;
    api.pet.carried = false; api.pet.zap = 0; api.pet.zapCharge = 0;
    api.ctx.clearRect(0, 0, 360, 380);
    api.drawPikachu();
  });

  // 3. Carried / Scruff-Dangle Dragging (Facing Right)
  await captureState('pikachu_live_dangle_right.png', () => {
    const api = window.__pikaTest;
    api.pet.x = 180; api.pet.y = 220; api.pet.facing = 1;
    api.pet.walking = false; api.pet.carried = true; api.pet.dragVx = 50;
    api.pet.zap = 0; api.pet.zapCharge = 0;
    api.ctx.clearRect(0, 0, 360, 380);
    api.drawPikachu();
  });

  // 4. Carried / Scruff-Dangle Dragging (Facing Left)
  await captureState('pikachu_live_dangle_left.png', () => {
    const api = window.__pikaTest;
    api.pet.x = 180; api.pet.y = 220; api.pet.facing = -1;
    api.pet.walking = false; api.pet.carried = true; api.pet.dragVx = -50;
    api.pet.zap = 0; api.pet.zapCharge = 0;
    api.ctx.clearRect(0, 0, 360, 380);
    api.drawPikachu();
  });

  // 5. Charging Electro Ball
  await captureState('pikachu_live_charge_electroball.png', (gy) => {
    const api = window.__pikaTest;
    api.pet.x = 180; api.pet.y = gy; api.pet.facing = 1;
    api.pet.walking = false; api.pet.carried = false;
    api.pet.zapCharge = 0.2; api.pet.zapFull = 0.24; api.pet.zapBoss = false; api.pet.zapStyle = 'electroball';
    api.ctx.clearRect(0, 0, 360, 380);
    api.drawPikachu();
  });

  // 6. Firing Electro Ball at Bug
  await captureState('pikachu_live_fire_electroball.png', (gy) => {
    const api = window.__pikaTest;
    api.pet.x = 120; api.pet.y = gy; api.pet.facing = 1;
    api.pet.walking = false; api.pet.carried = false;
    api.pet.zap = 0.18; api.pet.zapBoss = false; api.pet.zapStyle = 'electroball';
    api.pet.zapX = 300; api.pet.zapY = gy - 12;
    api.ctx.clearRect(0, 0, 360, 380);
    api.drawPikachu();
    // Render the electroball attack projectile
    api.SPECIES.pikachu.attack.draw(api.petR(), 0.9, false, 'electroball');
  });

  // 7. Charging 100,000-Volt Thunderbolt
  await captureState('pikachu_live_charge_thunderbolt.png', (gy) => {
    const api = window.__pikaTest;
    api.pet.x = 180; api.pet.y = gy; api.pet.facing = 1;
    api.pet.walking = false; api.pet.carried = false;
    api.pet.zapCharge = 0.85; api.pet.zapFull = 0.95; api.pet.zapBoss = true; api.pet.zapStyle = 'thunderbolt';
    api.ctx.clearRect(0, 0, 360, 380);
    api.drawPikachu();
  });

  // 8. 100,000-Volt Thunderbolt Crashing from Sky
  await captureState('pikachu_live_fire_thunderbolt.png', (gy) => {
    const api = window.__pikaTest;
    api.pet.x = 100; api.pet.y = gy; api.pet.facing = 1;
    api.pet.walking = false; api.pet.carried = false;
    api.pet.zap = 0.3; api.pet.zapBoss = true; api.pet.zapStyle = 'thunderbolt';
    api.pet.zapX = 270; api.pet.zapY = gy;
    api.ctx.clearRect(0, 0, 360, 380);
    api.drawPikachu();
    // Render the thunderbolt attack
    api.SPECIES.pikachu.attack.draw(api.petR(), 0.9, true, 'thunderbolt');
  });

  // 9. Oran Berry Snack
  await captureState('pikachu_live_eating_berry.png', (gy) => {
    const api = window.__pikaTest;
    api.pet.x = 180; api.pet.y = gy; api.pet.facing = 1;
    api.pet.walking = false; api.pet.carried = false;
    api.pet.zap = 0; api.pet.zapCharge = 0;
    api.pet.chew = 1; api.pet.happy = 1;
    api.ctx.clearRect(0, 0, 360, 380);
    api.drawPikachu();
  });

  await browser.close();
  console.log('All visual captures completed!');
}

capture().catch(err => {
  console.error(err);
  process.exit(1);
});
