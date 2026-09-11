import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { chromium } from 'playwright';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);

async function generate() {
  console.log('Generating OpenPets-compatible Kid Goku spritesheet...');
  const petHtmlPath = join(process.cwd(), 'Resources', 'pet.html');
  const petHtml = await readFile(petHtmlPath, 'utf8');

  // Inject hook to capture context & control rendering
  const injectedHtml = petHtml.replace(
    '  // ---------------------------------------------------------------- boot',
    `window.__gokuExport = { pet, state, drawGoku, ctx, canvas, petR, species };
  // ---------------------------------------------------------------- boot`
  );

  const browser = await chromium.launch({
    channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage({
    viewport: { width: 1536, height: 1872 },
    deviceScaleFactor: 1
  });

  await page.addInitScript(() => {
    window.requestAnimationFrame = () => 0;
    window.__hostMessages = [];
    window.webkit = { messageHandlers: { pet: { postMessage: () => {} } } };
    window.__petSavedState = JSON.stringify({
      species: 'goku',
      hatched: true,
      sound: false,
      name: 'Goku',
      stage: 'Saiyan'
    });
  });

  await page.route('**/*', route => {
    if (route.request().url() === 'http://bitling.openpets/') {
      return route.fulfill({ contentType: 'text/html', body: injectedHtml });
    }
    return route.abort();
  });

  await page.goto('http://bitling.openpets/');
  await page.waitForTimeout(600);

  // Render the 8-column x 9-row spritesheet in browser
  const pngBase64 = await page.evaluate(async () => {
    const api = window.__gokuExport;
    api.state.species = 'goku';

    const sheetCanvas = document.createElement('canvas');
    sheetCanvas.width = 1536;
    sheetCanvas.height = 1872;
    const sctx = sheetCanvas.getContext('2d');

    const frameW = 192;
    const frameH = 208;
    const cols = 8;
    const rows = 9;

    // Save standard pet state
    const basePet = { ...api.pet };

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const frameIdx = c;
        const prog = c / 8;
        const t = r * 10 + c * 0.35;

        // Reset
        Object.assign(api.pet, basePet, {
          x: 96,
          y: 148,
          t: t,
          facing: 1,
          mode: 'fly',
          grounded: false,
          walking: false,
          walkDir: 0,
          waving: 0,
          chew: 0,
          happy: 0,
          surprise: 0,
          stretch: 0,
          sq: 0,
          blink: 0,
          zap: 0,
          zapCharge: 0,
          zapFull: 0,
          zapBoss: false,
          zapStyle: 'kiball'
        });
        api.state.asleep = false;
        api.state.species = 'goku';

        // Specific animation rows:
        // 0: idle, 1: running-right, 2: running-left, 3: waving, 4: jumping, 5: failed, 6: waiting, 7: running, 8: review
        switch (r) {
          case 0: // idle
            api.pet.facing = 1;
            if (c === 3 || c === 4) api.pet.blink = 1;
            break;

          case 1: // running-right
            api.pet.facing = 1;
            api.pet.walking = true;
            api.pet.walkDir = 1;
            api.pet.dragSpeed = 120;
            break;

          case 2: // running-left
            api.pet.facing = -1;
            api.pet.walking = true;
            api.pet.walkDir = -1;
            api.pet.dragSpeed = 120;
            break;

          case 3: // waving
            api.pet.facing = 1;
            api.pet.waving = 1 + Math.sin(prog * Math.PI * 2) * 0.6;
            api.pet.happy = 1;
            break;

          case 4: // jumping (aerial acrobatics / power pole ready)
            api.pet.facing = 1;
            api.pet.y = 148 - Math.sin(prog * Math.PI) * 22;
            api.pet.stretch = Math.sin(prog * Math.PI * 2) * 0.15;
            break;

          case 5: // failed (swirly / dizzy shock)
            api.pet.facing = 1;
            api.pet.surprise = 1;
            api.state.screen = 'error';
            break;

          case 6: // waiting (eating anime roast meat bone)
            api.pet.facing = 1;
            api.pet.chew = 1;
            api.pet.happy = 1;
            break;

          case 7: // running (high speed forward rush)
            api.pet.facing = 1;
            api.pet.walking = true;
            api.pet.walkDir = 1;
            api.pet.dragSpeed = 240;
            break;

          case 8: // review (Kamehameha charge aura)
            api.pet.facing = 1;
            api.pet.zapCharge = 0.3 + 0.7 * (c / 7);
            api.pet.zapFull = 1;
            api.pet.zapBoss = true;
            api.pet.zapStyle = 'kamehameha';
            break;
        }

        // Render Goku onto page canvas (192 x 208)
        api.canvas.width = frameW;
        api.canvas.height = frameH;
        api.ctx.clearRect(0, 0, frameW, frameH);
        api.drawGoku();

        // Blit into main spritesheet canvas
        sctx.drawImage(api.canvas, c * frameW, r * frameH);
      }
    }

    return sheetCanvas.toDataURL('image/png').split(',')[1];
  });

  await browser.close();

  // Write PNG then convert to WebP
  const outputDir = join(process.cwd(), 'Resources', 'pets', 'goku');
  await mkdir(outputDir, { recursive: true });

  const tempPng = join(outputDir, 'spritesheet.png');
  const destWebp = join(outputDir, 'spritesheet.webp');
  await writeFile(tempPng, Buffer.from(pngBase64, 'base64'));

  // Use python PIL to convert PNG to high quality WebP
  await exec('python3', [
    '-c',
    `from PIL import Image; img = Image.open("${tempPng}"); img.save("${destWebp}", "WEBP", quality=95, method=6)`
  ]);
  await exec('rm', [tempPng]);

  // Create OpenPets pet.json
  const petJson = {
    id: 'goku',
    displayName: 'Kid Goku',
    description: 'Kid Goku flying on the Flying Nimbus (Kintoun) with his Power Pole, Turtle School Gi, and Kamehameha attacks.',
    spritesheetPath: 'spritesheet.webp'
  };

  const petJsonPath = join(outputDir, 'pet.json');
  await writeFile(petJsonPath, JSON.stringify(petJson, null, 2) + '\n');
  console.log(`Wrote ${petJsonPath} and ${destWebp}`);

  // Also install to ~/.codex/pets/goku if ~/.codex/pets exists
  const codexPetsDir = join(homedir(), '.codex', 'pets', 'goku');
  await mkdir(codexPetsDir, { recursive: true });
  await writeFile(join(codexPetsDir, 'pet.json'), JSON.stringify(petJson, null, 2) + '\n');
  await exec('cp', [destWebp, join(codexPetsDir, 'spritesheet.webp')]);
  console.log(`Installed to ${codexPetsDir}`);
}

generate().catch(err => {
  console.error(err);
  process.exit(1);
});
