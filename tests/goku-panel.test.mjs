import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { chromium } from 'playwright';

// panel.html has no prior test coverage at all - this both locks in the fix (the Goku
// block was reading goku.overallPower/effectiveCommits/isSimulated, fields
// getGokuSnapshot() in bitling.html never actually sends, so Power/Commits/the
// simulated-commits flag always showed their fallback values) and the new enemy-pack
// readout this task adds alongside it.
test("the control room's Goku block shows real power/commits/simulated state and the new enemy-pack readout", async () => {
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const html = await readFile('apps/macos/web/panel.html', 'utf8');
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.addInitScript(() => {
      window.__sent = [];
      window.webkit = { messageHandlers: { panel: { postMessage: (m) => window.__sent.push(m) } } };
    });
    await page.route('**/*', (route) => (route.request().url() === 'http://panel.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort()));
    await page.goto('http://panel.test/');

    const result = await page.evaluate(() => {
      window.panel.update({
        pet: {
          species: 'goku', hatched: true, name: 'Goku',
          goku: {
            currentForm: 'Super Saiyan 2', power: 74, commitsToday: 18, formProgress: 42, simulated: true,
            enemyPack: 'Goku Combat', currentEnemy: 'Brute (+1)', enemiesDefeated: 5, bossState: 'Engaged: Warlord (4/8)',
          },
        },
        today: {}, lifetime: {}, watch: {}, events: [],
      });
      const text = (id) => document.getElementById(id)?.textContent;
      const before = {
        hidden: document.getElementById('gokuControls').hidden,
        form: text('gFormName'), power: text('gPowerMult'), commits: text('gCommits'),
        progress: text('gFormProgress'), pack: text('gEnemyPack'), enemy: text('gCurrentEnemy'),
        defeated: text('gEnemiesDefeated'), boss: text('gBossState'),
      };

      document.querySelector('[data-spawn="elite"]').click();

      // switching away must hide the block again, same as every other species block
      window.panel.update({ pet: { species: 'thor', hatched: true }, today: {}, lifetime: {}, watch: {}, events: [] });
      const hiddenForOtherSpecies = document.getElementById('gokuControls').hidden;

      return { before, sent: window.__sent, hiddenForOtherSpecies };
    });

    assert.deepEqual(errors, [], `page errors: ${errors.join(', ')}`);
    assert.equal(result.before.hidden, false);
    assert.equal(result.before.form, 'Super Saiyan 2');
    assert.equal(result.before.power, '0.7x', 'power must be read from the real "power" field (0-100), not the never-sent "overallPower"');
    assert.equal(result.before.commits, '18 (sim)', 'commits must be read from "commitsToday" and the simulated flag from "simulated"');
    assert.equal(result.before.progress, '42%', 'formProgress from the snapshot is already a 0-100 percentage, not a 0-1 fraction to re-multiply');
    assert.equal(result.before.pack, 'Goku Combat');
    assert.equal(result.before.enemy, 'Brute (+1)');
    assert.equal(result.before.defeated, '5');
    assert.equal(result.before.boss, 'Engaged: Warlord (4/8)');
    const actionsSent = result.sent.filter((m) => m.type === 'action');
    assert.deepEqual(actionsSent, [{ type: 'action', value: 'goku:spawn:elite' }],
      'clicking a spawn preset must relay the enemy class through the same action channel as every other dev control');
    assert.equal(result.hiddenForOtherSpecies, true, "switching species away from Goku must hide his block, like every other species' block");
  } finally {
    await browser.close();
  }
});
