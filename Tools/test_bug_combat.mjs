import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

async function main() {
  const artifactDir = '/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758';
  const petHtmlPath = join(process.cwd(), 'Resources', 'pet.html');
  const petHtml = await readFile(petHtmlPath, 'utf8');

  const browser = await chromium.launch({
    channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome'
  });

  const page = await browser.newPage({
    viewport: { width: 440, height: 440 },
    deviceScaleFactor: 2
  });

  await page.addInitScript(() => {
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
      return route.fulfill({ contentType: 'text/html', body: petHtml });
    }
    return route.abort();
  });

  await page.goto('http://bitling.preview/');
  await page.waitForTimeout(500);

  // 1. Trigger Small Bug Ki Blast Attack
  console.log('Testing Small Bug Attack...');
  await page.evaluate(() => {
    window.petNative.setSpecies('goku');
    // Spawn 2 bugs
    window.petNative.gitEvent({
      kind: 'test-failed',
      count: 2,
      name: 'auth_test',
      tests: ['test_login', 'test_token']
    });
  });

  // Wait a moment for Goku to aim and charge Ki Blast
  await page.waitForTimeout(350);
  await page.screenshot({ path: join(artifactDir, 'goku_kiball_charge_live.png') });
  console.log('Captured goku_kiball_charge_live.png');

  // Wait for Ki Blast firing
  await page.waitForTimeout(250);
  await page.screenshot({ path: join(artifactDir, 'goku_kiball_fire_live.png') });
  console.log('Captured goku_kiball_fire_live.png');

  // Wait for bug extermination
  await page.waitForTimeout(600);
  await page.screenshot({ path: join(artifactDir, 'goku_bugs_cleared.png') });
  console.log('Captured goku_bugs_cleared.png');

  // 2. Trigger Boss Bug Kamehameha Attack
  console.log('Testing Boss Bug Kamehameha...');
  await page.evaluate(() => {
    window.petNative.gitEvent({
      kind: 'test-failed',
      count: 8,
      name: 'database_cluster',
      tests: ['boss_cluster_deadlock', 'test2', 'test3', 'test4', 'test5', 'test6', 'test7', 'test8']
    });
  });

  // Wait for Kamehameha charging with cyan Ki aura and electric sparks
  await page.waitForTimeout(500);
  await page.screenshot({ path: join(artifactDir, 'goku_kame_charge_live.png') });
  console.log('Captured goku_kame_charge_live.png');

  // Wait for massive Kamehameha beam firing
  await page.waitForTimeout(450);
  await page.screenshot({ path: join(artifactDir, 'goku_kame_fire_live.png') });
  console.log('Captured goku_kame_fire_live.png');

  await browser.close();
  console.log('Combat tests finished!');
}

main().catch(console.error);
