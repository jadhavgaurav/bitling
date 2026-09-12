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
  const directory = await mkdtemp(join(tmpdir(), 'bitling-mario-enemies-test-'));
  const browser = await chromium.launch({ channel: process.env.BITLING_BROWSER_CHANNEL || 'chrome' });
  try {
    const generated = join(directory, 'pet.html');
    await run('python3', ['packages/pet-engine/scripts/make_pet_html.py', 'apps/macos/web/bitling.html', generated]);
    const html = (await readFile(generated, 'utf8')).replace(
      '  // ---------------------------------------------------------------- boot',
      `window.__marioEnemyTest = {
    pet, state, marioState, draw, drawMario, drawBugs, drawMarioEnemy, ctx, canvas, petR, species, SPECIES,
    updatePet, updateBugs, bugs, spawnBug, squashBug, MARIO_ENEMIES, marioEnemyClass, marioEnemyPool,
    getMarioSnapshot, groundY: () => groundY, scale: () => scale,
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
      window.__petSavedState = JSON.stringify({ species: 'mario', hatched: true, sound: false, born: Date.now(), lastSeen: Date.now() });
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

test('Mario is registered with his own enemy pack, distinct from the shared beetle and from Goku\'s pack', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    return {
      enemyPack: api.SPECIES.mario.enemyPack,
      otherPacksUnaffected: ['robot', 'goku', 'thor', 'spiderman', 'dragon'].every((id) => api.SPECIES[id].enemyPack !== 'mario'),
      classIds: Object.keys(api.MARIO_ENEMIES).sort(),
    };
  });
  assert.equal(result.enemyPack, 'mario');
  assert.ok(result.otherPacksUnaffected, 'no other species should report the Mario pack');
  assert.deepEqual(result.classIds, ['ambush', 'boss', 'elite', 'flying', 'jumping', 'shell', 'walker']);
});

test('each Mario enemy class spawns with a distinct identity, is tagged to the Mario pack, and renders without error', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    window.__bitling.marioForceStage(3); // Star Mario, so every class is unlockable
    window.__bitling.advance(0.1);
    const failures = [];
    const spawned = [];
    for (const kind of ['walker', 'shell', 'flying', 'jumping', 'ambush', 'elite', 'boss']) {
      api.bugs.length = 0;
      window.__bitling.marioSpawnEnemy(kind);
      const b = api.bugs[0];
      if (!b || b.enemyId !== kind || b.pack !== 'mario') { failures.push(`${kind} did not spawn as a tagged Mario enemy`); continue; }
      spawned.push({ kind, hp: b.hp, maxHp: b.maxHp, boss: b.boss, grounded: api.marioEnemyClass(kind).grounded, altitude: b.altitude });
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
  assert.equal(byKind.walker.hp, 1, 'a common walker should die in one hit even at higher stages');
  assert.equal(byKind.flying.grounded, false, 'the flying class must be marked airborne');
  assert.ok(byKind.flying.altitude > 0, 'a flying enemy must spawn above ground level');
  assert.ok(byKind.elite.hp >= 3, 'an elite must take more than one hit');
  assert.ok(byKind.boss.hp >= 7 && byKind.boss.boss, 'the boss class must be flagged boss and have real health');
});

test('a shell retracts on the first stomp, auto-slides after its delay, and chain-reacts into another enemy', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 1; // not Star Mario - the shell gimmick applies
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('shell');
    const shell = api.bugs[0];
    shell.x = 140;
    const stateBeforeStomp = shell.shellState;
    api.squashBug(shell, true, false); // first stomp: retract, do not kill
    const afterFirstStomp = { alive: shell.alive, shellState: shell.shellState, vx: shell.vx };

    // drive time forward past the shell delay so it auto-slides without a second stomp
    for (let i = 0; i < 90; i++) api.updateBugs(1 / 60);
    const afterDelay = { shellState: shell.shellState, sliding: Math.abs(shell.vx) > 0 };

    // pin it to a known spot moving in a known direction, then place a second, ordinary
    // enemy directly in its path so the chain reaction is deterministic to test
    shell.x = 150; shell.vx = 200; shell.shellHitCd = 0;
    window.__bitling.marioSpawnEnemy('walker');
    const walker = api.bugs[api.bugs.length - 1];
    walker.x = 158;
    walker.hp = 1;
    let chained = false;
    for (let i = 0; i < 60 && !chained; i++) {
      api.updateBugs(1 / 60);
      if (!walker.alive) chained = true;
    }
    return { stateBeforeStomp, afterFirstStomp, afterDelay, chained, stillInArray: api.bugs.includes(shell) };
  });
  assert.equal(result.stateBeforeStomp, 'walk');
  assert.equal(result.afterFirstStomp.alive, true, 'the first stomp must retract the shell, not kill it');
  assert.equal(result.afterFirstStomp.shellState, 'shelled');
  assert.equal(result.afterFirstStomp.vx, 0, 'a freshly shelled Koopa should sit still');
  assert.equal(result.afterDelay.shellState, 'sliding', 'the shell must auto-slide once its delay elapses');
  assert.ok(result.afterDelay.sliding, 'a sliding shell must have real horizontal velocity');
  assert.ok(result.chained, 'a sliding shell must be able to defeat another enemy in its path');
});

test('a second stomp while shelled kicks it into sliding immediately, and only a strong hit destroys a sliding shell', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 1;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('shell');
    const shell = api.bugs[0];
    shell.x = 150;
    api.squashBug(shell, true, false); // -> shelled
    api.squashBug(shell, true, false); // -> kicked into sliding
    const afterKick = { shellState: shell.shellState, vx: shell.vx, alive: shell.alive };
    api.squashBug(shell, true, false); // a bare stomp into a sliding shell should just bounce off
    const afterBump = { alive: shell.alive, shellState: shell.shellState };
    api.squashBug(shell, false, true); // a strong (laser/fireball) hit should finish it
    const afterStrongHit = { alive: shell.alive, state: shell.state };
    return { afterKick, afterBump, afterStrongHit };
  });
  assert.equal(result.afterKick.shellState, 'sliding');
  assert.notEqual(result.afterKick.vx, 0);
  assert.equal(result.afterKick.alive, true);
  assert.equal(result.afterBump.alive, true, 'walking into a sliding shell must not destroy it');
  assert.equal(result.afterStrongHit.alive, false, 'a strong hit must destroy a sliding shell');
  assert.equal(result.afterStrongHit.state, 'dying');
});

test('Star Mario one-shots even multi-hit enemies with a bigger knockback, but the boss still takes real damage', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 3;
    api.marioState.invincibleT = 10;

    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('elite');
    const elite = api.bugs[0];
    elite.x = 160;
    const eliteHpBefore = elite.hp; // >1 at every stage - would normally take multiple hits
    api.squashBug(elite, false, true);
    const eliteAfterOneHit = { alive: elite.alive, knockVx: elite.knockVx };

    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('shell');
    const shell = api.bugs[0];
    api.squashBug(shell, true, false); // a single hit, not the usual retract-then-kick dance
    const shellAfterOneHit = { alive: shell.alive };

    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('boss');
    const boss = api.bugs[0];
    const bossHpBefore = boss.hp;
    api.squashBug(boss, false, true);
    const bossAfterOneHit = { alive: boss.alive, hp: boss.hp };

    return { eliteHpBefore, eliteAfterOneHit, shellAfterOneHit, bossHpBefore, bossAfterOneHit };
  });
  assert.ok(result.eliteHpBefore > 1, 'this test needs an elite that would normally survive one hit');
  assert.equal(result.eliteAfterOneHit.alive, false, 'Star Mario must down a multi-hit enemy in a single hit');
  assert.ok(Math.abs(result.eliteAfterOneHit.knockVx) > 0, 'the kill must still carry knockback');
  assert.equal(result.shellAfterOneHit.alive, false, 'Star Mario must blow straight through the shell gimmick too');
  assert.ok(result.bossHpBefore > 1, 'this test needs a boss with real health');
  assert.equal(result.bossAfterOneHit.alive, true, 'the boss must still take real, gradual damage even from Star Mario');
  assert.equal(result.bossAfterOneHit.hp, result.bossHpBefore - 1);
});

test('a jumping enemy uses a real gravity arc, not a teleport, and squashes on landing', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('jumping');
    const b = api.bugs[0];
    b.jumpCd = 0; // force the next update to launch it
    const altitudes = [];
    for (let i = 0; i < 90; i++) {
      api.updateBugs(1 / 60);
      altitudes.push(b.altitude);
    }
    const rose = altitudes.some((a) => a > 5);
    const cameBackDown = altitudes[altitudes.length - 1] <= altitudes[Math.floor(altitudes.length / 2)] || altitudes[altitudes.length - 1] === 0;
    // monotonic teleport would jump straight from 0 to a large value in a single 1/60s
    // step; a real arc changes altitude smoothly, so no single step should be huge.
    let maxStep = 0;
    for (let i = 1; i < altitudes.length; i++) maxStep = Math.max(maxStep, Math.abs(altitudes[i] - altitudes[i - 1]));
    return { rose, cameBackDown, maxStep };
  });
  assert.ok(result.rose, 'the jumping enemy must actually leave the ground');
  assert.ok(result.cameBackDown, 'the jumping enemy must come back down under its own gravity');
  assert.ok(result.maxStep < 30, `altitude should change smoothly frame to frame, not teleport (max step ${result.maxStep})`);
});

test('a flying enemy cannot be stomped by ordinary ground contact, but can be hit while Mario is airborne over it', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('flying');
    const b = api.bugs[0];
    b.x = 160; b.altitude = 90;
    Object.assign(api.pet, { x: 160, grounded: true, held: false, carried: false });
    api.state.asleep = false;
    api.updateBugs(1 / 60);
    const survivedGroundContact = b.alive;

    const by = api.groundY() - 9 * api.scale() - b.altitude;
    Object.assign(api.pet, { x: 160, y: by + api.petR() * 1.6, grounded: false });
    api.updateBugs(1 / 60);
    return { survivedGroundContact, aliveAfterAirborneContact: b.alive };
  });
  assert.ok(result.survivedGroundContact, 'walking under a flier on the ground must not stomp it');
  assert.equal(result.aliveAfterAirborneContact, false, 'jumping right on top of a flier must stomp it');
});

test("Mario's attack resolution depends on his stage and the target's enemy class, not just boss/non-boss", async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    const attack = api.species('mario').attack;
    api.marioState.stage = 0;
    const small = attack.resolve(false);
    api.marioState.stage = 2;
    const fireVsWalker = attack.resolve(false, { pack: 'mario', enemyId: 'walker' });
    const fireVsFlying = attack.resolve(false, { pack: 'mario', enemyId: 'flying' });
    api.marioState.stage = 3;
    const star = attack.resolve(false);
    const bossFromStar = attack.resolve(true);
    api.marioState.stage = 0;
    const noTarget = attack.resolve(false, null);
    return { small, fireVsWalker, fireVsFlying, star, bossFromStar, noTarget };
  });
  assert.equal(result.small.style, 'stomp');
  assert.equal(result.fireVsWalker.style, 'fireball');
  assert.equal(result.fireVsFlying.style, 'fireball');
  assert.ok(result.fireVsFlying.charge < result.fireVsWalker.charge, 'a dodging flier should earn a quicker throw');
  assert.equal(result.star.style, 'starpower', 'Star Mario should not just be a faster fireball, it should be its own style');
  assert.equal(result.bossFromStar.style, 'fireball', 'a boss fight must stay a fireball even while Star Mario is active');
  assert.equal(result.noTarget.style, 'stomp', 'resolve must stay safe with no target (every non-Mario species calls it with one argument)');
});

test('enemy difficulty is gated by Mario\'s current stage and he remains dominant (low HP) even at Star Mario', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    window.__bitling.marioForceStage(0); // Small Mario
    window.__bitling.advance(0.1);
    const smallPoolIds = api.marioEnemyPool().map((e) => e.id).sort();
    window.__bitling.marioForceStage(3); // Star Mario
    window.__bitling.advance(0.1);
    const starPoolIds = api.marioEnemyPool().map((e) => e.id).sort();
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('elite');
    const eliteHpAtStar = api.bugs[0].hp;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('boss');
    const bossHpAtStar = api.bugs[0].hp;
    return { smallPoolIds, starPoolIds, eliteHpAtStar, bossHpAtStar };
  });
  assert.ok(!result.smallPoolIds.includes('shell') && !result.smallPoolIds.includes('elite'),
    'Small Mario should only face the easy classes');
  assert.ok(result.starPoolIds.includes('shell') && result.starPoolIds.includes('elite'),
    'a fully-grown Mario should face the harder classes too');
  assert.ok(result.eliteHpAtStar <= 4, 'even at Star Mario an elite must stay a handful of hits, not a wall');
  assert.ok(result.bossHpAtStar <= 9, 'even at Star Mario the boss must stay finite - Mario must remain able to win');
});

test('spawning a Mario enemy triggers his notice/alert reaction, and other species are unaffected by the whole pack system', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    Object.assign(api.pet, { zapCharge: 0, zap: 0, reactionT: 0, held: false, carried: false });
    api.state.asleep = false;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('walker');
    const alerted = api.pet.reaction === 'alert' && api.pet.reactionT > 0;

    window.petNative.setSpecies('robot');
    window.__bitling.advance(0.1);
    api.bugs.length = 0;
    api.spawnBug();
    const robotBug = api.bugs[0];
    const robotUnaffected = robotBug.enemyId === undefined && robotBug.hp === 1;
    api.squashBug(robotBug, false, true);
    const robotDiedInOneHit = robotBug.alive === false;

    window.petNative.setSpecies('mario');
    window.__bitling.advance(0.1);
    api.bugs.length = 0;

    return { alerted, robotUnaffected, robotDiedInOneHit };
  });
  assert.ok(result.alerted, 'Mario should react to a freshly spawned enemy while idle');
  assert.ok(result.robotUnaffected, 'switching species must not leak enemyId/pack changes onto the generic beetle');
  assert.ok(result.robotDiedInOneHit, "the generic beetle's one-hit-kill behavior must be unchanged");
});

test('the control room snapshot reports the enemy pack, current enemy, kill count and boss state', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('walker');
    const before = api.getMarioSnapshot();
    api.squashBug(api.bugs[0], false, true);
    const after = api.getMarioSnapshot();
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('boss');
    const withBoss = api.getMarioSnapshot();
    return { before, after, withBoss };
  });
  assert.equal(result.before.enemyPack, 'Mario World');
  assert.equal(result.before.currentEnemy, 'Stomper');
  assert.equal(result.before.bossState, 'None');
  assert.equal(result.after.currentEnemy, 'None');
  assert.ok(result.after.enemiesDefeated >= 1, 'defeating an enemy must increment the day-stamped counter the panel shows');
  assert.match(result.withBoss.bossState, /^Engaged: /);
});
