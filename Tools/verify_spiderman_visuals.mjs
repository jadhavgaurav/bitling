import { readFileSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const rawHtml = readFileSync(new URL('../Resources/pet.html', import.meta.url), 'utf8');
const html = rawHtml.replace(
  '  // ---------------------------------------------------------------- boot',
  `window.__spideyVisuals = { pet, state, draw, drawSpiderman, drawSpidermanWebAttack, ctx, canvas, petR, species, SPECIES, groundY };
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
      species: 'spiderman',
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
  await page.waitForTimeout(500);

  const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/f8f3c39d-54d9-4f31-a36d-c26a9c9f0cb8';

  const states = [
    {
      name: 'spiderman_idle',
      setup: (api) => {
        api.pet.walking = false; api.pet.carried = false; api.pet.held = false;
        api.state.asleep = false; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = api.groundY; api.pet.facing = 1;
      }
    },
    {
      name: 'spiderman_crawl',
      setup: (api) => {
        api.pet.walking = true; api.pet.walkDir = 1; api.pet.carried = false;
        api.state.asleep = false; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = api.groundY; api.pet.facing = 1;
      }
    },
    {
      name: 'spiderman_swing',
      setup: (api) => {
        api.pet.walking = false; api.pet.spideySwinging = true; api.pet.carried = false;
        api.state.asleep = false; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = 240; api.pet.facing = 1;
        api.pet.dragVx = 120;
      }
    },
    {
      name: 'spiderman_web_shoot',
      setup: (api) => {
        api.pet.walking = false; api.pet.spideySwinging = false; api.pet.carried = false;
        api.state.asleep = false; api.pet.zapCharge = 0; api.pet.zap = 0.5; api.pet.zapBoss = false;
        api.pet.x = 140; api.pet.y = api.groundY; api.pet.facing = 1;
      },
      postDraw: (api) => {
        api.drawSpidermanWebAttack(44, 0.4, false, 'webThwip');
      }
    },
    {
      name: 'spiderman_slingshot_strike',
      setup: (api) => {
        api.pet.walking = false; api.pet.spideySwinging = false; api.pet.carried = false;
        api.state.asleep = false; api.pet.zapCharge = 0; api.pet.zap = 0.5; api.pet.zapBoss = true;
        api.pet.x = 150; api.pet.y = api.groundY; api.pet.facing = 1;
      },
      postDraw: (api) => {
        api.drawSpidermanWebAttack(44, 0.4, true, 'slingshotDive');
      }
    },
    {
      name: 'spiderman_sleep',
      setup: (api) => {
        api.pet.walking = false; api.pet.spideySwinging = false; api.pet.carried = false;
        api.state.asleep = true; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = api.groundY;
      }
    },
    {
      name: 'spiderman_dangle',
      setup: (api) => {
        api.pet.walking = false; api.pet.spideySwinging = false; api.pet.carried = true; api.pet.held = true;
        api.state.asleep = false; api.pet.zapCharge = 0; api.pet.zap = 0;
        api.pet.x = 170; api.pet.y = 240;
      }
    }
  ];

  for (const st of states) {
    await page.evaluate((stateName) => {
      const api = window.__spideyVisuals;
      api.ctx.clearRect(0, 0, 340, 380);
    }, st.name);

    await page.evaluate((stObj) => {
      const api = window.__spideyVisuals;
      // invoke setup
    });

    await page.evaluate(`
      (() => {
        const api = window.__spideyVisuals;
        const stateDef = ${st.setup.toString()};
        stateDef(api);
        api.draw();
        ${st.postDraw ? `(${st.postDraw.toString()})(api);` : ''}
      })()
    `);

    await page.waitForTimeout(100);
    const shotPath = `${artifactDir}/${st.name}.png`;
    await page.screenshot({ path: shotPath, omitBackground: false });
    console.log(`Saved screenshot: ${shotPath}`);
  }

  await browser.close();
  console.log('All Spider-Man visual verifications captured successfully!');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
