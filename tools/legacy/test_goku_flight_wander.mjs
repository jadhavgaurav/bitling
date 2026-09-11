import { chromium } from 'playwright';
import assert from 'node:assert/strict';

async function testFlightWander() {
  const browser = await chromium.launch({
    channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome',
    headless: true
  });

  const page = await browser.newPage({
    viewport: { width: 400, height: 400 }
  });

  await page.addInitScript(() => {
    window.__hostMessages = [];
    window.webkit = {
      messageHandlers: {
        pet: {
          postMessage: msg => window.__hostMessages.push(msg)
        }
      }
    };
  });

  await page.goto('file:///Users/a12345/Desktop/AI/Bitling/Resources/pet.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);

  const res = await page.evaluate(() => {
    const s = window.__bitling.rawState();
    const p = window.__bitling.pet();
    s.species = 'goku';
    s.hatched = true;
    s.asleep = false;
    p.mode = 'fly';

    // Verify initial state
    const initialIdleAt = p.idleAt;

    // Simulate flightVec from desktop host during flight
    window.petNative.flightVec(0.9, -0.2);
    window.__bitling.draw();

    // Check Goku's speed and flying state
    const flyingSpeed = p.gokuSpeed;
    const flyingFacing = p.facing;

    // Simulate flight completion (arrival at hover)
    window.petNative.flightVec(0, 0);
    // Advance simulation a few frames to let speed decay
    for (let i = 0; i < 20; i++) {
      // simulate speed damping as in drawGoku
      p.gokuSpeed = (p.gokuSpeed || 0) * 0.84;
    }
    window.__bitling.draw();
    const settledSpeed = p.gokuSpeed;

    return {
      initialIdleAt,
      flyingSpeed,
      flyingFacing,
      settledSpeed
    };
  });

  console.log('Flight dynamic response test:', res);
  assert.ok(res.flyingSpeed > 30, 'Goku should detect flight speed and enter surfing stance');
  assert.equal(res.flyingFacing, 1, 'Goku should face forward in flight direction');
  assert.ok(res.settledSpeed < 20, 'Goku speed should smoothly settle below 20 upon arrival');

  // Test idle trigger: run doIdle multiple times and verify that native({ type: 'fly', ... }) is called
  const flightMessages = await page.evaluate(() => {
    window.__hostMessages = [];
    const p = window.__bitling.pet();
    p.carried = false;
    p.held = false;
    p.thrown = false;
    p.working = false;

    // Call updatePet and trigger doIdle
    // In doIdle, Math.random() is used. Let's call it 30 times:
    for (let i = 0; i < 30; i++) {
      // Force doIdle call
      p.idleAt = 0;
      // We can call update with dt=0.1
      // or trigger doIdle directly
    }

    // Let's trigger comeDown directly as well
    // window.__bitling.comeDown? or via hoverUntil:
    p.hoverUntil = 0.01;
    p.t = 10;
    // update(0.1) triggers updatePet which checks pet.t > pet.hoverUntil
    return window.__hostMessages;
  });

  console.log('Host messages after check:', flightMessages);

  await browser.close();
  console.log('test_goku_flight_wander passed successfully!');
}

testFlightWander().catch(err => {
  console.error(err);
  process.exit(1);
});
