import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

async function withPage(t, fn) {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-goku-enemies-test-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__gokuEnemyTest = {
    pet, state, draw, drawGoku, drawBugs, drawGokuEnemy, ctx, canvas, petR, species, SPECIES,
    updatePet, updateBugs, bugs, spawnBug, squashBug, GOKU_ENEMIES, gokuEnemyClass, gokuEnemyPool,
    getGokuSnapshot,
  };
  // ---------------------------------------------------------------- boot`,
    );
    const page = await browser.newPage({ viewport: { width: 320, height: 360 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.addInitScript(() => {
      window.requestAnimationFrame = () => 0;
      window.__hostMessages = [];
      window.webkit = { messageHandlers: { pet: { postMessage: (message) => window.__hostMessages.push(message) } } };
      window.__petSavedState = JSON.stringify({ species: 'goku', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
    });
    await page.route('**/*', (route) => (route.request().url() === 'http://bitling.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort()));
    await page.goto('http://bitling.test/');
    const result = await page.evaluate(fn);
    assert.deepEqual(errors, [], `page errors: ${errors.join(', ')}`);
    return result;
  } finally {
    await browser.close();
    await rm(directory, { recursive: true, force: true });
  }
}

test('Goku is registered with his own enemy pack, distinct from the shared beetle', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__gokuEnemyTest;
    return {
      enemyPack: api.SPECIES.goku.enemyPack,
      // Mario has since earned his own pack too (see mario-enemies.test.mjs) - only species
      // that still fight the shared beetle belong in this list.
      otherPacksUndefined: ['robot', 'thor', 'spiderman', 'dragon'].every((id) => api.SPECIES[id].enemyPack === undefined),
      marioHasOwnDistinctPack: api.SPECIES.mario.enemyPack === 'mario',
      classIds: Object.keys(api.GOKU_ENEMIES).sort(),
    };
  });
  assert.equal(result.enemyPack, 'goku');
  assert.ok(result.otherPacksUndefined, 'no other species should have picked up an enemy pack');
  assert.ok(result.marioHasOwnDistinctPack, "Mario's pack must be its own, not Goku's");
  assert.deepEqual(result.classIds, ['boss', 'elite', 'fast', 'fighter', 'flying']);
});

test('each Goku enemy class spawns with a distinct identity, renders without error, and is not a beetle', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__gokuEnemyTest;
    window.__bitling.gokuForceForm(3); // Super Saiyan 2, so every class is unlockable
    window.__bitling.advance(0.1);
    const failures = [];
    const spawned = [];
    for (const kind of ['fighter', 'flying', 'fast', 'elite', 'boss']) {
      api.bugs.length = 0;
      window.__bitling.gokuSpawnEnemy(kind);
      const b = api.bugs[0];
      if (!b || b.enemyId !== kind) { failures.push(`${kind} did not spawn with enemyId ${kind}`); continue; }
      spawned.push({ kind, hp: b.hp, maxHp: b.maxHp, boss: b.boss, grounded: api.gokuEnemyClass(kind).grounded, altitude: b.altitude });
      api.ctx.clearRect(0, 0, 320, 360);
      Object.assign(api.pet, { x: 160, y: 220 });
      try {
        api.drawBugs();
      } catch (e) {
        failures.push(`${kind} threw while drawing: ${e.message}`);
        continue;
      }
      const { width, height } = api.canvas;
      const pixels = api.ctx.getImageData(0, 0, width, height).data;
      let opaque = 0;
      for (let i = 3; i < pixels.length; i += 4) if (pixels[i] > 100) opaque++;
      if (opaque < 40) failures.push(`${kind} rendered too few pixels: ${opaque}`);
    }
    return { failures, spawned };
  });
  assert.deepEqual(result.failures, []);
  const byKind = Object.fromEntries(result.spawned.map((s) => [s.kind, s]));
  assert.equal(byKind.fighter.hp, 1, 'a common fighter should die in one hit even at higher forms');
  assert.equal(byKind.flying.grounded, false, 'the flying class must be marked airborne');
  assert.ok(byKind.flying.altitude > 0, 'a flying enemy must spawn above ground level');
  assert.ok(byKind.elite.hp >= 3, 'an elite must take more than one hit');
  assert.ok(byKind.boss.hp >= 6 && byKind.boss.boss, 'the boss class must be flagged boss and have real health');
});

test('a non-boss, non-elite Goku enemy staggers with knockback on a partial hit and only dies on the killing blow, with a themed death animation', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__gokuEnemyTest;
    // Kid Goku (default, unforced) so the elite's hp is exactly its unscaled base of 3.
    api.bugs.length = 0;
    window.__bitling.gokuSpawnEnemy('elite');
    const b = api.bugs[0];
    b.x = 160; // clear of both world edges, so the boundary clamp can't mask the knockback
    const hpBefore = b.hp;
    const xBefore = b.x;
    api.squashBug(b, false, true); // first hit: should stagger, not kill
    const afterFirstHit = { alive: b.alive, hp: b.hp, hurtT: b.hurtT, knockVx: b.knockVx };
    // drive a few frames so the knockback actually displaces it
    for (let i = 0; i < 6; i++) api.updateBugs(1 / 60);
    const movedWhileStaggered = b.x !== xBefore;
    // finish it off
    while (b.alive && b.hp > 0) api.squashBug(b, false, true);
    const afterKill = { alive: b.alive, squash: b.squash, state: b.state };
    // it should linger (not be spliced) for its themed death animation, then actually
    // render its death pose without throwing
    api.ctx.clearRect(0, 0, 320, 360);
    let drawError = null;
    try { api.drawGokuEnemy(b); } catch (e) { drawError = e.message; }
    return { hpBefore, afterFirstHit, movedWhileStaggered, afterKill, stillInArray: api.bugs.includes(b), drawError };
  });
  assert.equal(result.hpBefore, 3, 'elite should start with more than one hit point (form-scaled)');
  assert.equal(result.afterFirstHit.alive, true, 'a partial hit must not kill an elite outright');
  assert.equal(result.afterFirstHit.hp, 2);
  assert.ok(result.afterFirstHit.hurtT > 0, 'a partial hit must set a stagger timer');
  assert.notEqual(result.afterFirstHit.knockVx, 0, 'a partial hit must set knockback velocity');
  assert.ok(result.movedWhileStaggered, 'knockback velocity must actually displace the enemy over subsequent frames');
  assert.equal(result.afterKill.alive, false);
  assert.equal(result.afterKill.state, 'dying');
  assert.ok(result.afterKill.squash > 0.45, 'an elite death should linger longer than the generic 0.45s squash');
  assert.ok(result.stillInArray, 'a dying enemy must not be spliced out immediately - it needs its death animation frames');
  assert.equal(result.drawError, null, 'the death pose must render without throwing');
});

test("Goku's attack resolution depends on the target's enemy class, not just boss/non-boss", async (t) => {
  const result = await withPage(t, () => {
    const api = window.__gokuEnemyTest;
    const attack = api.species('goku').attack;
    return {
      fighter: attack.resolve(false, { enemyId: 'fighter' }),
      fast: attack.resolve(false, { enemyId: 'fast' }),
      elite: attack.resolve(false, { enemyId: 'elite' }),
      boss: attack.resolve(true, { enemyId: 'boss', boss: true }),
      noTarget: attack.resolve(false, null),
    };
  });
  assert.equal(result.boss.style, 'kamehameha', 'only an actual boss should earn the full Kamehameha');
  assert.equal(result.elite.style, 'kiball');
  assert.ok(result.elite.charge > result.fighter.charge, 'an elite should get a stronger, longer-charged blast than a common fighter');
  assert.ok(result.fast.charge < result.fighter.charge, 'a fast enemy should get a quicker, snappier response');
  assert.equal(result.noTarget.style, 'kiball', 'resolve must stay safe with no target (every non-Goku species calls it with one argument)');
});

test('enemy difficulty is gated by Goku\'s current form and he remains dominant (low HP) even at max power', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__gokuEnemyTest;
    window.__bitling.gokuForceForm(0); // Kid Goku
    window.__bitling.advance(0.1);
    const kidPoolIds = api.gokuEnemyPool().map((e) => e.id).sort();
    window.__bitling.gokuForceForm(5); // Ultra Instinct
    window.__bitling.advance(0.1);
    const uiPoolIds = api.gokuEnemyPool().map((e) => e.id).sort();
    api.bugs.length = 0;
    window.__bitling.gokuSpawnEnemy('elite');
    const eliteHpAtUI = api.bugs[0].hp;
    api.bugs.length = 0;
    window.__bitling.gokuSpawnEnemy('boss');
    const bossHpAtUI = api.bugs[0].hp;
    return { kidPoolIds, uiPoolIds, eliteHpAtUI, bossHpAtUI };
  });
  assert.ok(!result.kidPoolIds.includes('fast') && !result.kidPoolIds.includes('elite'),
    'Kid Goku should only face the easy classes');
  assert.ok(result.uiPoolIds.includes('fast') && result.uiPoolIds.includes('elite'),
    'a fully-powered Goku should face the harder classes too');
  assert.ok(result.eliteHpAtUI <= 4, 'even at max power an elite must stay a handful of hits, not a wall');
  assert.ok(result.bossHpAtUI <= 9, 'even at max power the boss must stay finite - Goku must remain able to win');
});

test('spawning a Goku enemy triggers his notice/alert reaction, and other species are unaffected by the whole pack system', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__gokuEnemyTest;
    Object.assign(api.pet, { zapCharge: 0, zap: 0, reactionT: 0, held: false, carried: false });
    api.state.asleep = false;
    api.bugs.length = 0;
    window.__bitling.gokuSpawnEnemy('fighter');
    const alerted = api.pet.reaction === 'alert' && api.pet.reactionT > 0;

    window.petNative.setSpecies('robot');
    window.__bitling.advance(0.1);
    api.bugs.length = 0;
    api.spawnBug();
    const robotBug = api.bugs[0];
    const robotUnaffected = robotBug.enemyId === undefined && robotBug.hp === 1;
    // a generic bug must still die in exactly one hit for a non-Goku species
    api.squashBug(robotBug, false, true);
    const robotDiedInOneHit = robotBug.alive === false;

    window.petNative.setSpecies('goku');
    window.__bitling.advance(0.1);
    api.bugs.length = 0;

    return { alerted, robotUnaffected, robotDiedInOneHit };
  });
  assert.ok(result.alerted, 'Goku should react to a freshly spawned enemy while idle');
  assert.ok(result.robotUnaffected, 'switching species must not leak enemyId/hp changes onto the generic beetle');
  assert.ok(result.robotDiedInOneHit, "the generic beetle's one-hit-kill behavior must be unchanged");
});

test("the control room snapshot reports the enemy pack, current enemy, kill count and boss state", async (t) => {
  const result = await withPage(t, () => {
    const api = window.__gokuEnemyTest;
    api.bugs.length = 0;
    window.__bitling.gokuSpawnEnemy('fighter');
    const before = api.getGokuSnapshot();
    api.squashBug(api.bugs[0], false, true);
    const after = api.getGokuSnapshot();
    api.bugs.length = 0;
    window.__bitling.gokuSpawnEnemy('boss');
    const withBoss = api.getGokuSnapshot();
    return { before, after, withBoss };
  });
  assert.equal(result.before.enemyPack, 'Goku Combat');
  assert.equal(result.before.currentEnemy, 'Scrapper');
  assert.equal(result.before.bossState, 'None');
  assert.equal(result.after.currentEnemy, 'None');
  assert.ok(result.after.enemiesDefeated >= 1, 'defeating an enemy must increment the day-stamped counter the panel shows');
  assert.match(result.withBoss.bossState, /^Engaged: /);
});
