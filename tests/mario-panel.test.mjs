import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { chromium } from 'playwright';

// Same shape as goku-panel.test.mjs: locks in the Mario World control-room block this
// task adds - the stats readout, the stage presets and the enemy-spawn dev buttons all
// relay through the same `send('action', ...)` channel every other species block uses.
test("the control room's Mario block shows form/coins/power and the enemy-pack readout", async () => {
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
          species: 'mario', hatched: true, name: 'Mario',
          mario: {
            stage: 2, currentForm: 'Fire Mario', power: 67, coins: 12,
            enemyPack: 'Mario World', currentEnemy: 'Shellback (+1)', enemiesDefeated: 24, bossState: 'Engaged: King Koopa (5/9)',
          },
        },
        today: {}, lifetime: {}, watch: {}, events: [],
      });
      const text = (id) => document.getElementById(id)?.textContent;
      const before = {
        hidden: document.getElementById('marioControls').hidden,
        form: text('mFormName'), coins: text('mCoins'), power: text('mPower'),
        pack: text('mEnemyPack'), enemy: text('mCurrentEnemy'), defeated: text('mEnemiesDefeated'), boss: text('mBossState'),
        stageActive: document.querySelector('[data-mariostage="2"]').classList.contains('active'),
      };

      document.querySelector('[data-mariospawn="shell"]').click();
      document.querySelector('[data-mariostage="3"]').click();

      // switching away must hide the block again, same as every other species block
      window.panel.update({ pet: { species: 'goku', hatched: true }, today: {}, lifetime: {}, watch: {}, events: [] });
      const hiddenForOtherSpecies = document.getElementById('marioControls').hidden;

      return { before, sent: window.__sent, hiddenForOtherSpecies };
    });

    assert.deepEqual(errors, [], `page errors: ${errors.join(', ')}`);
    assert.equal(result.before.hidden, false);
    assert.equal(result.before.form, 'Fire Mario');
    assert.equal(result.before.coins, '12');
    assert.equal(result.before.power, '67%');
    assert.equal(result.before.pack, 'Mario World');
    assert.equal(result.before.enemy, 'Shellback (+1)');
    assert.equal(result.before.defeated, '24');
    assert.equal(result.before.boss, 'Engaged: King Koopa (5/9)');
    assert.equal(result.before.stageActive, true, 'the current stage preset must be highlighted as active');
    const actionsSent = result.sent.filter((m) => m.type === 'action');
    assert.deepEqual(actionsSent, [
      { type: 'action', value: 'mario:spawn:shell' },
      { type: 'action', value: 'mario:stage:3' },
    ], 'clicking a dev preset must relay through the same action channel as every other species control');
    assert.equal(result.hiddenForOtherSpecies, true, "switching species away from Mario must hide his block, like every other species' block");
  } finally {
    await browser.close();
  }
});
