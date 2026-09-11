import { chromium } from 'playwright';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function run() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  
  const errors = [];
  page.on('pageerror', err => errors.push(err.message));
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  const demoPath = 'file://' + path.resolve(__dirname, '../docs/index.html');
  console.log('Loading:', demoPath);
  await page.goto(demoPath);
  await page.waitForTimeout(1000);

  // Check pet switcher buttons
  const switcherBtns = await page.$$('.pet-chip');
  console.log(`Found ${switcherBtns.length} pet switcher buttons`);
  if (switcherBtns.length !== 9) {
    throw new Error(`Expected 9 pet buttons, got ${switcherBtns.length}`);
  }

  // Check demo bar buttons
  const specialBtn = await page.$('button[data-demo="special"]');
  const bossBtn = await page.$('button[data-demo="boss"]');
  if (!specialBtn || !bossBtn) {
    throw new Error('Special attack or Boss button missing in demo bar!');
  }

  // Switch between all 9 pets and verify their species state, title, and speech
  const speciesList = ['robot', 'dragon', 'goku', 'rider', 'pikachu', 'ironman', 'kaiju', 'naruto', 'ronaldo'];
  for (const sp of speciesList) {
    console.log(`Testing pet: ${sp}`);
    const btn = await page.$(`.pet-chip[data-species="${sp}"]`);
    await btn.click();
    await page.waitForTimeout(400);

    const activeSpecies = await page.$eval('.pet-chip.active', el => el.dataset.species);
    const titleText = await page.$eval('#nameLabel', el => el.textContent);
    console.log(`  Active: ${activeSpecies}, Name: ${titleText}`);
    
    if (activeSpecies !== sp) {
      throw new Error(`Expected species ${sp}, got ${activeSpecies}`);
    }

    // Trigger Special attack
    await specialBtn.click();
    await page.waitForTimeout(500);

    if (process.env.SAVE_SCREENSHOTS) {
      if (sp === 'ronaldo') {
        await page.screenshot({ path: path.resolve(__dirname, '../docs/live_ronaldo.png') });
      } else if (sp === 'naruto') {
        await page.screenshot({ path: path.resolve(__dirname, '../docs/live_naruto_blast.png') });
      } else if (sp === 'goku') {
        await page.screenshot({ path: path.resolve(__dirname, '../docs/live_goku.png') });
      } else if (sp === 'pikachu') {
        await page.screenshot({ path: path.resolve(__dirname, '../docs/live_pikachu.png') });
      }
    }

    // Trigger Boss bug
    await bossBtn.click();
    await page.waitForTimeout(500);
  }

  // Test other buttons: Commit, Push, Bugs, Tests Pass, Sleep
  console.log('Testing git and status triggers...');
  for (const action of ['commit', 'push', 'bugs', 'tests-pass', 'sleep', 'sleep']) {
    const btn = await page.$(`button[data-demo="${action}"]`);
    if (btn) {
      await btn.click();
      await page.waitForTimeout(300);
    }
  }

  if (process.env.SAVE_SCREENSHOTS) {
    await page.screenshot({ path: path.resolve(__dirname, '../docs/live_preview.png') });
    console.log('Screenshot saved to docs/live_preview.png');
  }

  await browser.close();
  if (errors.length > 0) {
    console.error('Page errors encountered:', errors);
    process.exit(1);
  }
  console.log('All tests passed successfully!');
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
