import { readFileSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const rawHtml = readFileSync(new URL('../Resources/pet.html', import.meta.url), 'utf8');
const html = rawHtml.replace(
  '  // ---------------------------------------------------------------- boot',
  `window.__thorTest = { pet, state, draw, drawThor, ctx, canvas, petR, species, SPECIES, updatePet };
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
      species: 'thor',
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
  await page.waitForTimeout(400);

  const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/f8f3c39d-54d9-4f31-a36d-c26a9c9f0cb8';

  const states = [
    {
      name: 'idle',
      setup: (api) => {
        window.petNative.thorSimulate(5);
        api.pet.vx = 0; api.pet.vy = 0; api.pet.flying = false; api.pet.walking = false;
        api.state.asleep = false; api.pet.held = false; api.pet.carried = false;
        api.pet.attacking = 0; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = 230;
      }
    },
    {
      name: 'fly',
      setup: (api) => {
        window.petNative.thorSimulate(5);
        api.pet.vx = 140; api.pet.vy = -30; api.pet.facing = 1;
        api.pet.flying = true; api.pet.walking = false;
        api.state.asleep = false; api.pet.held = false; api.pet.carried = false;
        api.pet.attacking = 0; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = 210;
      }
    },
    {
      name: 'charge',
      setup: (api) => {
        window.petNative.thorSimulate(10);
        api.pet.vx = 0; api.pet.vy = 0; api.pet.flying = false; api.pet.walking = false;
        api.state.asleep = false; api.pet.held = false; api.pet.carried = false;
        api.pet.attacking = 0.2; api.pet.zapCharge = 0.3; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = 230;
      }
    },
    {
      name: 'attack',
      setup: (api) => {
        window.petNative.thorSimulate(15);
        api.pet.vx = 0; api.pet.vy = 0; api.pet.flying = false; api.pet.walking = false;
        api.state.asleep = false; api.pet.held = false; api.pet.carried = false;
        api.pet.attacking = 0.7; api.pet.zap = 0.5;
        api.pet.x = 170; api.pet.y = 230;
      }
    },
    {
      name: 'dangle',
      setup: (api) => {
        window.petNative.thorSimulate(8);
        api.pet.vx = 0; api.pet.vy = 0; api.pet.flying = false; api.pet.walking = false;
        api.state.asleep = false; api.pet.held = true; api.pet.carried = true;
        api.pet.attacking = 0; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = 215;
      }
    },
    {
      name: 'drag_flight',
      setup: (api) => {
        window.petNative.thorSimulate(8);
        api.pet.vx = 220; api.pet.vy = -60; api.pet.dragSpeed = 220;
        api.pet.flying = false; api.pet.walking = false;
        api.state.asleep = false; api.pet.held = true; api.pet.carried = true;
        api.pet.attacking = 0; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = 210;
      }
    },
    {
      name: 'sleep',
      setup: (api) => {
        window.petNative.thorSimulate(12);
        api.pet.vx = 0; api.pet.vy = 0; api.pet.flying = false; api.pet.walking = false;
        api.state.asleep = true; api.pet.held = false; api.pet.carried = false;
        api.pet.attacking = 0; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = 230;
      }
    },
    {
      name: 'stormbreaker',
      setup: (api) => {
        window.petNative.thorSimulate(35);
        api.pet.vx = 0; api.pet.vy = 0; api.pet.flying = false; api.pet.walking = false;
        api.state.asleep = false; api.pet.held = false; api.pet.carried = false;
        api.pet.attacking = 0; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = 230;
      }
    }
  ];

  for (const s of states) {
    await page.evaluate((setupFuncStr) => {
      const api = window.__thorTest;
      const fn = new Function('api', `(${setupFuncStr})(api)`);
      fn(api);
      api.ctx.clearRect(0, 0, api.canvas.width, api.canvas.height);
      api.drawThor();
    }, s.setup.toString());

    const shotPath = `${artifactDir}/thor_${s.name}.png`;
    const buffer = await page.screenshot({ clip: { x: 40, y: 50, width: 260, height: 280 }, omitBackground: false });
    writeFileSync(shotPath, buffer);
    console.log(`Saved screenshot: ${shotPath}`);
  }

  await browser.close();
}

main().catch(console.error);
