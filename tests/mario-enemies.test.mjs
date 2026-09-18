import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';
import { chromium } from 'playwright';

const run = promisify(execFile);

async function withPage(t, fn, arg) {
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
    getMarioSnapshot, groundY: () => groundY, scale: () => scale, W: () => W,
    marioEnemyBounds, marioBody, marioAttackBlocked, marioEnemyUnit, updateMarioSimulation, drawMarioAttack,
    MARIO_ENEMY_RENDERERS, MARIO_ENEMY_BEHAVIORS, MARIO_MAX_ACTIVE, MARIO_MAX_ACTIVE_WITH_BOSS, MARIO_MAX_FIREBALLS,
    MAX_PARTICLES, particles, spawn,
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
    await page.waitForTimeout(250); // let the base64 sprite assets decode so render checks see real frames
    const result = await page.evaluate(fn, arg);
    assert.deepEqual(errors, [], `page errors: ${errors.join(', ')}`);
    return result;
  } finally {
    await browser.close();
    await rm(directory, { recursive: true, force: true });
  }
}

// Every animation state each class can be in, as a setup step run against a freshly
// spawned bug. Shared by the "every state renders" and silhouette checks below, and kept
// here (not in the page) so adding a state to the page without a test here is visible.
const ENEMY_STATES = {
  walker: {
    walk: 'b.vx = -30; b.targetVx = -30; b.animT = 0.5;',
    notice: "b.plan = 'notice'; b.noticeT = 0.5;",
    turning: 'b.face = 0.3; b.turnT = 0.1;',
    hurt: 'b.hurtT = 0.1;',
    dead: 'b.alive = false; b.squash = 0.5; b.deathT = 0.25;',
  },
  shell: {
    walk: 'b.vx = -26; b.animT = 0.4;',
    retract: "b.shellState = 'retract'; b.shellT = 0.12;",
    shelled: "b.shellState = 'shelled'; b.shellT = 1;",
    kick: "b.shellState = 'kick'; b.shellT = 0.05; b.vx = -320; b.squashT = 0.1;",
    sliding: "b.shellState = 'sliding'; b.vx = -320; b.targetVx = -320; b.spinAngle = 0.8;",
    bouncing: "b.shellState = 'bouncing'; b.shellT = 0.1; b.vx = 320; b.squashT = 0.1;",
    hit: "b.shellState = 'hit'; b.shellT = 0.1; b.vx = -300;",
    dead: 'b.alive = false; b.squash = 0.45; b.deathSpin = 1;',
  },
  flying: {
    patrol: 'b.altitude = 100; b.flap = 1.0; b.vx = -30;',
    dive: "b.altitude = 60; b.flyState = 'dive'; b.vx = -60; b.altVy = -120;",
    recover: "b.altitude = 90; b.flyState = 'recover'; b.altVy = 80;",
    hurt: 'b.altitude = 100; b.hurtT = 0.1;',
    dead: 'b.altitude = 50; b.alive = false; b.squash = 0.6; b.deathSpin = 1.2;',
  },
  jumping: {
    ground: "b.jumpPhase = 'ground';",
    anticipation: "b.jumpPhase = 'anticipation'; b.jumpT = 0.05;",
    launch: "b.jumpPhase = 'launch'; b.jumpT = 0.05; b.altitude = 4;",
    ascending: "b.jumpPhase = 'ascending'; b.altitude = 50; b.jumpDir = -1;",
    apex: "b.jumpPhase = 'apex'; b.altitude = 70;",
    descending: "b.jumpPhase = 'descending'; b.altitude = 40; b.jumpDir = -1;",
    landing: "b.jumpPhase = 'landing'; b.jumpT = 0.1;",
    recovery: "b.jumpPhase = 'recovery'; b.jumpT = 0.2;",
    dead: 'b.alive = false; b.squash = 0.5; b.altitude = 20; b.deathSpin = 0.7;',
  },
  ambush: {
    hidden: "b.ambushState = 'hidden'; b.ambushRise = 0;",
    emerging: "b.ambushState = 'emerging'; b.ambushRise = 0.5;",
    active: "b.ambushState = 'active'; b.ambushRise = 1;",
    attacking: "b.ambushState = 'attacking'; b.ambushRise = 1; b.vx = -150;",
    retreating: "b.ambushState = 'retreating'; b.ambushRise = 0.4;",
    dead: 'b.alive = false; b.squash = 0.5;',
  },
  elite: {
    stand: '',
    windup: 'b.stepT = 0.1;',
    step: 'b.vx = 80; b.animT = 0.5;',
    dodge: 'b.hopT = 0.15; b.dodgeT = 0.15;',
    hurt: 'b.hp = 1; b.hurtT = 0.3;',
    dead: 'b.alive = false; b.squash = 0.66; b.deathT = 0.44;',
  },
  boss: {
    stance: '',
    windup: "b.bossState = 'windup'; b.bossT = 0.1;",
    charge: "b.bossState = 'charge'; b.vx = -190; b.animT = 0.5;",
    recover: "b.bossState = 'recover'; b.bossT = 0.2;",
    stagger: "b.bossState = 'stagger'; b.hurtT = 0.2;",
    rage: 'b.hp = 2;',
    dead1: 'b.alive = false; b.squash = 2.2 * 0.6; b.deathT = 0.88;',
    dead2: 'b.alive = false; b.squash = 2.2 * 0.35; b.deathT = 1.43;',
    dead3: 'b.alive = false; b.squash = 2.2 * 0.1; b.deathT = 1.98;',
  },
};

test('Mario is registered with his own enemy pack, distinct from the shared beetle and from Goku\'s pack', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    return {
      enemyPack: api.SPECIES.mario.enemyPack,
      otherPacksUnaffected: ['robot', 'goku', 'thor', 'spiderman', 'dragon'].every((id) => api.SPECIES[id].enemyPack !== 'mario'),
      classIds: Object.keys(api.MARIO_ENEMIES).sort(),
      rendererIds: Object.keys(api.MARIO_ENEMY_RENDERERS).sort(),
      behaviorIds: Object.keys(api.MARIO_ENEMY_BEHAVIORS).sort(),
      dataComplete: Object.values(api.MARIO_ENEMIES).every((d) => d.hitbox && d.accel > 0 && d.deathDur > 0 && d.behavior && d.renderer && d.attackType && d.animationProfile && Number.isFinite(d.spawnWeight)),
    };
  });
  assert.equal(result.enemyPack, 'mario');
  assert.ok(result.otherPacksUnaffected, 'no other species should report the Mario pack');
  assert.deepEqual(result.classIds, ['ambush', 'boss', 'elite', 'flying', 'jumping', 'shell', 'walker']);
  assert.deepEqual(result.rendererIds, result.classIds, 'every class must have a renderer in the registry');
  assert.deepEqual(result.behaviorIds, result.classIds, 'every class must have a behaviour in the registry');
  assert.ok(result.dataComplete, 'every class must carry its own hitbox, accel, death duration, behaviour, renderer, attack type, animation profile and spawn weight');
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
      spawned.push({ kind, hp: b.hp, maxHp: b.maxHp, boss: b.boss, grounded: api.marioEnemyClass(kind).grounded, altitude: b.altitude, distance: Math.abs(b.x - api.pet.x) });
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
    return { failures, spawned, r: api.petR() };
  });
  assert.deepEqual(result.failures, []);
  const byKind = Object.fromEntries(result.spawned.map((s) => [s.kind, s]));
  assert.equal(byKind.walker.hp, 1, 'a common walker should die in one hit even at higher stages');
  assert.equal(byKind.flying.grounded, false, 'the flying class must be marked airborne');
  assert.ok(byKind.flying.altitude > 0, 'a flying enemy must spawn above ground level');
  assert.ok(byKind.elite.hp >= 3, 'an elite must take more than one hit');
  assert.ok(byKind.boss.hp >= 7 && byKind.boss.boss, 'the boss class must be flagged boss and have real health');
  for (const s of result.spawned) assert.ok(s.distance > result.r * 1.5, `${s.kind} must not spawn on top of Mario (${s.distance.toFixed(0)}px away)`);
});

test('every enemy animation state renders through the registry, and silhouettes have the right shape', async (t) => {
  const result = await withPage(t, (ENEMY_STATES) => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 1;
    Object.assign(api.pet, { x: 90, y: api.groundY(), grounded: true });
    const failures = [];
    const boxes = {};
    const { width, height } = api.canvas;
    const dpr = width / 320;
    for (const [kind, states] of Object.entries(ENEMY_STATES)) {
      for (const [name, setup] of Object.entries(states)) {
        api.bugs.length = 0;
        window.__bitling.marioSpawnEnemy(kind);
        const b = api.bugs[0];
        b.x = 220; b.face = -1; b.facing = -1;
        new Function('b', 'api', setup)(b, api);
        api.ctx.clearRect(0, 0, 320, 360);
        try {
          api.drawBugs();
        } catch (e) {
          failures.push(`${kind}/${name} threw: ${e.message}`);
          continue;
        }
        const px = api.ctx.getImageData(0, 0, width, height).data;
        let minX = width, maxX = 0, minY = height, maxY = 0, opaque = 0;
        for (let y = 0; y < height; y++) {
          for (let x = 0; x < width; x++) {
            if (px[(y * width + x) * 4 + 3] > 100) {
              opaque++;
              if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
            }
          }
        }
        if (opaque < 40) failures.push(`${kind}/${name} rendered too few pixels: ${opaque}`);
        boxes[`${kind}/${name}`] = { w: (maxX - minX) / dpr, h: (maxY - minY) / dpr, top: minY / dpr, bottom: maxY / dpr, opaque, u: api.marioEnemyUnit(api.marioEnemyClass(kind)), altitude: b.altitude || 0 };
      }
    }
    return { failures, boxes, groundY: api.groundY(), marioH: api.petR() * 2.85 };
  }, ENEMY_STATES);
  assert.deepEqual(result.failures, []);
  const bx = result.boxes;
  // Silhouette sanity: measured off the painted pixels, not the code.
  const walker = bx['walker/walk'];
  assert.ok(walker.h > walker.u * 1.7 && walker.h < walker.u * 2.6, `walker should stand about two units tall (${walker.h.toFixed(0)}px for u=${walker.u.toFixed(1)})`);
  assert.ok(walker.h > result.marioH * 0.38 && walker.h < result.marioH * 0.65, `a walker should be roughly half of Super Mario, not a speck (${walker.h.toFixed(0)} vs ${result.marioH.toFixed(0)})`);
  assert.ok(bx['boss/stance'].h > walker.h * 2, 'the boss must tower over the common walker');
  assert.ok(bx['boss/stance'].h > result.marioH, 'the boss must be taller than Mario');
  assert.ok(bx['elite/stand'].h > walker.h * 1.3, 'the elite must be visibly heavier than the walker');
  assert.ok(bx['shell/shelled'].h < bx['shell/walk'].h * 0.75, 'a retracted shell must be lower than the walking creature');
  assert.ok(bx['ambush/hidden'].h < bx['ambush/active'].h * 0.5, 'a hidden lurker must show only a sliver of itself');
  assert.ok(bx['flying/patrol'].bottom < result.groundY - bx['flying/patrol'].altitude * 0.5, 'a flier must paint in the air, not on the ground line');
  assert.ok(bx['walker/dead'].h < walker.h * 0.6, 'a dead walker must be flattened');
  assert.ok(bx['jumping/anticipation'].h < bx['jumping/launch'].h, 'the hopper must compress before it launches and stretch as it leaves');
});

test('a shell walks, retracts on the first stomp, settles, auto-slides after its delay, and chain-reacts into another enemy', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 1; // not Star Mario - the shell gimmick applies
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('shell');
    const shell = api.bugs[0];
    shell.x = 140;
    Object.assign(api.pet, { x: 60, grounded: true });
    const stateBeforeStomp = shell.shellState;
    api.squashBug(shell, true, false); // first stomp: retract, do not kill
    const afterFirstStomp = { alive: shell.alive, shellState: shell.shellState, vx: shell.vx };
    const seen = new Set([shell.shellState]);
    for (let i = 0; i < 20; i++) { api.updateBugs(1 / 60); seen.add(shell.shellState); }
    const afterRetract = { shellState: shell.shellState, vx: shell.vx };

    // drive time forward past the shell delay so it auto-slides without a second stomp
    for (let i = 0; i < 100; i++) { api.updateBugs(1 / 60); seen.add(shell.shellState); }
    const afterDelay = { shellState: shell.shellState, sliding: Math.abs(shell.vx) > 0, moving: ['kick', 'sliding', 'bouncing'].includes(shell.shellState) };

    // pin it to a known spot moving in a known direction, then place a second, ordinary
    // enemy directly in its path so the chain reaction is deterministic to test
    shell.x = 150; shell.vx = 200; shell.targetVx = 200; shell.shellHitCd = 0; shell.shellState = 'sliding';
    window.__bitling.marioSpawnEnemy('walker');
    const walker = api.bugs[api.bugs.length - 1];
    walker.x = 158;
    walker.hp = 1;
    let chained = false, walkerKnock = 0, shellStateOnHit = '', shellVxOnHit = 0;
    for (let i = 0; i < 60 && !chained; i++) {
      api.updateBugs(1 / 60);
      if (!walker.alive) { chained = true; walkerKnock = walker.knockVx; shellStateOnHit = shell.shellState; shellVxOnHit = shell.vx; }
    }
    for (let i = 0; i < 20; i++) api.updateBugs(1 / 60);
    return { stateBeforeStomp, afterFirstStomp, afterRetract, afterDelay, chained, walkerKnock, shellStateOnHit, shellVxOnHit, shellStillGoing: Math.abs(shell.vx) > 100 && shell.alive, seen: [...seen] };
  });
  assert.equal(result.stateBeforeStomp, 'walk');
  assert.equal(result.afterFirstStomp.alive, true, 'the first stomp must retract the shell, not kill it');
  assert.equal(result.afterFirstStomp.shellState, 'retract', 'the first stomp starts the visible retract beat');
  assert.equal(result.afterFirstStomp.vx, 0, 'a retracting Koopa stops where it is');
  assert.equal(result.afterRetract.shellState, 'shelled', 'the retract beat must settle into the stationary shell');
  assert.equal(result.afterRetract.vx, 0, 'a freshly shelled Koopa should sit still');
  assert.ok(result.afterDelay.moving, `the shell must auto-slide once its delay elapses (state ${result.afterDelay.shellState})`);
  assert.ok(result.afterDelay.sliding, 'a sliding shell must have real horizontal velocity');
  assert.ok(result.seen.includes('kick'), 'the auto-slide must pass through the kick beat before it is a free-sliding shell');
  assert.ok(result.chained, 'a sliding shell must be able to defeat another enemy in its path');
  assert.ok(result.walkerKnock > 0, 'the struck enemy must be knocked in the shell\'s direction of travel');
  assert.equal(result.shellStateOnHit, 'hit', 'the shell must register the impact as its own beat');
  assert.ok(result.shellVxOnHit > 100, 'the shell keeps most of its speed through the impact');
  assert.ok(result.shellStillGoing, 'the shell must carry on sliding after the chain reaction');
});

test('a second stomp while shelled kicks it into sliding immediately, a stomp on a sliding shell stops it, and only a strong hit destroys it', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 1;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('shell');
    const shell = api.bugs[0];
    shell.x = 150;
    api.squashBug(shell, true, false); // -> retract
    for (let i = 0; i < 20; i++) api.updateBugs(1 / 60); // -> shelled
    const beforeKick = shell.shellState;
    api.squashBug(shell, true, false); // -> kicked into sliding
    const afterKick = { shellState: shell.shellState, vx: shell.vx, alive: shell.alive };
    for (let i = 0; i < 10; i++) api.updateBugs(1 / 60);
    const afterKickSettles = shell.shellState;
    api.squashBug(shell, true, false); // Mario landing on a moving shell stops it
    const afterStomp = { alive: shell.alive, shellState: shell.shellState, vx: shell.vx };
    api.squashBug(shell, true, false); // and kicks it again
    api.squashBug(shell, false, false); // a walk-in bump against a sliding shell does nothing to it
    const afterBump = { alive: shell.alive, shellState: shell.shellState };
    api.squashBug(shell, false, true); // a strong (fireball) hit should finish it
    const afterStrongHit = { alive: shell.alive, state: shell.state };
    return { beforeKick, afterKick, afterKickSettles, afterStomp, afterBump, afterStrongHit };
  });
  assert.equal(result.beforeKick, 'shelled');
  assert.equal(result.afterKick.shellState, 'kick');
  assert.notEqual(result.afterKick.vx, 0, 'the kick must launch the shell with immediate horizontal velocity');
  assert.equal(result.afterKick.alive, true);
  assert.equal(result.afterKickSettles, 'sliding');
  assert.equal(result.afterStomp.alive, true);
  assert.equal(result.afterStomp.shellState, 'shelled', 'stomping a sliding shell must stop it, like the real thing');
  assert.equal(result.afterStomp.vx, 0);
  assert.equal(result.afterBump.alive, true, 'walking into a sliding shell must not destroy it');
  assert.equal(result.afterBump.shellState, 'kick');
  assert.equal(result.afterStrongHit.alive, false, 'a strong hit must destroy a sliding shell');
  assert.equal(result.afterStrongHit.state, 'dying');
});

test('a sliding shell bounces off the world edges without losing speed and registers the bounce as a beat', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 1;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('shell');
    const shell = api.bugs[0];
    Object.assign(api.pet, { x: 160, grounded: true });
    shell.x = 60; shell.shellState = 'sliding'; shell.vx = -320; shell.targetVx = -320;
    const speedBefore = Math.abs(shell.vx);
    let bounced = false, minX = shell.x;
    const states = new Set();
    for (let i = 0; i < 40; i++) {
      api.updateBugs(1 / 60);
      states.add(shell.shellState);
      minX = Math.min(minX, shell.x);
      if (shell.vx > 0) bounced = true;
    }
    return { bounced, minX, speedAfter: Math.abs(shell.vx), speedBefore, states: [...states], alive: shell.alive, x: shell.x };
  });
  assert.ok(result.bounced, 'the shell must reverse off the left edge');
  assert.ok(result.minX >= 0, 'it must never leave the window');
  assert.ok(result.speedAfter > result.speedBefore * 0.9, `the bounce keeps its speed (${result.speedAfter.toFixed(0)} of ${result.speedBefore})`);
  assert.ok(result.states.includes('bouncing'), 'the edge hit must pass through the bouncing beat');
  assert.ok(result.states.includes('sliding') && result.alive, 'and settle back into free sliding');
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

    // Star contact: brushing past an enemy on the ground is a hit, with its own impact beat.
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('walker');
    const walker = api.bugs[0];
    Object.assign(api.pet, { x: 160, y: api.groundY(), grounded: true, held: false, carried: false });
    api.state.asleep = false;
    walker.x = 162;
    api.updateBugs(1 / 60);
    const contact = { alive: walker.alive, starHitT: api.marioState.starHitT };

    return { eliteHpBefore, eliteAfterOneHit, shellAfterOneHit, bossHpBefore, bossAfterOneHit, contact };
  });
  assert.ok(result.eliteHpBefore > 1, 'this test needs an elite that would normally survive one hit');
  assert.equal(result.eliteAfterOneHit.alive, false, 'Star Mario must down a multi-hit enemy in a single hit');
  assert.ok(Math.abs(result.eliteAfterOneHit.knockVx) > 0, 'the kill must still carry knockback');
  assert.equal(result.shellAfterOneHit.alive, false, 'Star Mario must blow straight through the shell gimmick too');
  assert.ok(result.bossHpBefore > 1, 'this test needs a boss with real health');
  assert.equal(result.bossAfterOneHit.alive, true, 'the boss must still take real, gradual damage even from Star Mario');
  assert.equal(result.bossAfterOneHit.hp, result.bossHpBefore - 1);
  assert.equal(result.contact.alive, false, 'Star Mario touching an enemy must defeat it');
  assert.ok(result.contact.starHitT > 0, 'a star contact must trigger its own impact beat');
});

test('a jumping enemy uses a real gravity arc through every phase, not a teleport, and squashes on landing', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('jumping');
    const b = api.bugs[0];
    Object.assign(api.pet, { x: 40, grounded: true });
    b.x = 200;
    b.jumpCd = 0; // force the next update to launch it
    const altitudes = [];
    const phases = [];
    for (let i = 0; i < 120; i++) {
      api.updateBugs(1 / 60);
      altitudes.push(b.altitude);
      if (phases[phases.length - 1] !== b.jumpPhase) phases.push(b.jumpPhase);
    }
    const rose = altitudes.some((a) => a > 5);
    const cameBackDown = altitudes[altitudes.length - 1] === 0;
    // monotonic teleport would jump straight from 0 to a large value in a single 1/60s
    // step; a real arc changes altitude smoothly, so no single step should be huge.
    let maxStep = 0;
    for (let i = 1; i < altitudes.length; i++) maxStep = Math.max(maxStep, Math.abs(altitudes[i] - altitudes[i - 1]));
    return { rose, cameBackDown, maxStep, phases };
  });
  assert.ok(result.rose, 'the jumping enemy must actually leave the ground');
  assert.ok(result.cameBackDown, 'the jumping enemy must come back down under its own gravity');
  assert.ok(result.maxStep < 30, `altitude should change smoothly frame to frame, not teleport (max step ${result.maxStep})`);
  const order = ['anticipation', 'launch', 'ascending', 'apex', 'descending', 'landing', 'recovery', 'ground'];
  const idx = order.map((p) => result.phases.indexOf(p));
  assert.ok(idx.every((i) => i >= 0), `every phase must occur: ${result.phases.join(' > ')}`);
  assert.ok(idx.every((i, n) => n === 0 || i > idx[n - 1]), `phases must run in order: ${result.phases.join(' > ')}`);
});

test('a flying enemy holds a smooth altitude, dives toward a nearby Mario and recovers, and stays on screen', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('flying');
    const b = api.bugs[0];
    Object.assign(api.pet, { x: 160, y: api.groundY(), grounded: true, zapCharge: 0 });
    b.x = 170; b.altitude = 110; b.baseAltitude = 110;
    const before = [];
    b.diveCd = 10; // patrol only
    for (let i = 0; i < 60; i++) { api.updateBugs(1 / 60); before.push(b.altitude); }
    let maxStep = 0;
    for (let i = 1; i < before.length; i++) maxStep = Math.max(maxStep, Math.abs(before[i] - before[i - 1]));
    const patrolMin = Math.min(...before), patrolMax = Math.max(...before);
    b.diveCd = 0; // now a dive is allowed
    const states = new Set();
    let lowest = b.altitude;
    for (let i = 0; i < 150; i++) { api.updateBugs(1 / 60); states.add(b.flyState); lowest = Math.min(lowest, b.altitude); }
    const recovered = b.altitude;
    return { maxStep, patrolMin, patrolMax, states: [...states], lowest, recovered, groundY: api.groundY(), alive: b.alive };
  });
  assert.ok(result.maxStep < 4, `altitude must ease, not jump (max step ${result.maxStep.toFixed(1)}px per frame)`);
  assert.ok(result.patrolMax - result.patrolMin < 30, 'a patrolling flier stays near its cruising height');
  assert.ok(result.states.includes('dive') && result.states.includes('recover'), `the flier must dive and recover: ${result.states.join(', ')}`);
  assert.ok(result.lowest < result.patrolMin - 15, 'the dive must bring it visibly lower than its patrol');
  assert.ok(result.recovered > result.lowest + 10, 'it must climb back after the dive');
  assert.ok(result.lowest >= 18, 'it never drops onto the ground line');
});

test('the ambush enemy runs hidden -> emerging -> active -> attacking -> retreating -> hidden with a rising body, not a scaled one', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('ambush');
    const b = api.bugs[0];
    Object.assign(api.pet, { x: 60, grounded: true });
    b.x = 220; b.ambushT = 0.05;
    const order = [];
    const rises = {};
    for (let i = 0; i < 260; i++) {
      api.updateBugs(1 / 60);
      if (order[order.length - 1] !== b.ambushState) order.push(b.ambushState);
      // only the first cycle's numbers: a second emerge would restart from low again
      if (order.length <= 6) (rises[b.ambushState] = rises[b.ambushState] || []).push(b.ambushRise);
    }
    const hiddenH = api.marioEnemyBounds(Object.assign(b, { ambushRise: 0 })).h;
    const activeH = api.marioEnemyBounds(Object.assign(b, { ambushRise: 1 })).h;
    return { order, emergeMonotonic: rises.emerging.every((v, i, a) => i === 0 || v >= a[i - 1]), emergeSpan: [Math.min(...rises.emerging), Math.max(...rises.emerging)],
      activeFacing: b.facing, hiddenH, activeH, attackMoved: rises.attacking && rises.attacking.length > 0 };
  });
  const seq = ['hidden', 'emerging', 'active', 'attacking', 'retreating', 'hidden'];
  assert.deepEqual(result.order.slice(0, seq.length), seq, `state order: ${result.order.join(' > ')}`);
  assert.ok(result.emergeMonotonic, 'the body must rise steadily while emerging');
  assert.ok(result.emergeSpan[0] < 0.3 && result.emergeSpan[1] > 0.8, 'emerging must run from low to fully up');
  assert.ok(result.hiddenH < result.activeH * 0.4, 'the collision box must shrink to a sliver while hidden');
});

test('an elite takes several staggering hits with a visible health readout, and dies in stages', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 2;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('elite');
    const b = api.bugs[0];
    Object.assign(api.pet, { x: 60, grounded: true });
    b.x = 220;
    const hits = [];
    while (b.alive && hits.length < 10) {
      api.squashBug(b, false, true);
      hits.push({ alive: b.alive, hp: b.hp, hurtT: b.hurtT, knockVx: b.knockVx, squashT: b.squashT });
      for (let i = 0; i < 30; i++) api.updateBugs(1 / 60);
    }
    const stages = new Set([b.deathStage]);
    const total = api.marioEnemyClass('elite').deathDur;
    for (let i = 0; i < Math.ceil(total * 60) + 5; i++) { api.updateBugs(1 / 60); stages.add(b.deathStage); }
    return { maxHp: b.maxHp, hits, stages: [...stages], removed: !api.bugs.includes(b) };
  });
  assert.equal(result.hits.length, result.maxHp, 'it must take exactly maxHp hits');
  for (const h of result.hits.slice(0, -1)) {
    assert.equal(h.alive, true);
    assert.ok(h.hurtT > 0 && Math.abs(h.knockVx) > 0 && h.squashT > 0, 'every non-lethal hit staggers, knocks back and squashes it');
  }
  assert.equal(result.hits[result.hits.length - 1].alive, false);
  assert.ok(result.stages.includes(1) && result.stages.includes(2), `the collapse must run through its stages (${result.stages.join(',')})`);
  assert.ok(result.removed, 'the corpse must be cleaned up after its death animation');
});

test('the boss keeps a real health bar, winds up before charging, staggers when hit, rages at low health and dies in a multi-stage collapse', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 1;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('boss');
    const b = api.bugs[0];
    Object.assign(api.pet, { x: 60, y: api.groundY(), grounded: true });
    b.x = 220; b.bossT = 0.05;
    const seen = [];
    let chargeSpeed = 0;
    for (let i = 0; i < 120; i++) {
      api.updateBugs(1 / 60);
      if (seen[seen.length - 1] !== b.bossState) seen.push(b.bossState);
      if (b.bossState === 'charge') chargeSpeed = Math.max(chargeSpeed, Math.abs(b.vx));
    }
    const maxHp = b.maxHp;
    api.squashBug(b, false, true);
    const afterHit = { hp: b.hp, state: b.bossState, hurtT: b.hurtT, rage: b.rage };
    while (b.hp > 2) api.squashBug(Object.assign(b, { hurtT: 0 }), false, true);
    api.updateBugs(1 / 60);
    const lowHealth = { hp: b.hp, rage: b.rage, enraged: b.hp / b.maxHp <= api.marioEnemyClass('boss').lowHealth };
    while (b.alive) api.squashBug(Object.assign(b, { hurtT: 0 }), false, true);
    const deathDur = api.marioEnemyClass('boss').deathDur;
    const stages = new Set([b.deathStage]);
    let shake = 0;
    for (let i = 0; i < Math.ceil(deathDur * 60) + 5; i++) { api.updateBugs(1 / 60); stages.add(b.deathStage); shake = Math.max(shake, api.pet.shake); }
    return { seen, chargeSpeed, maxHp, afterHit, lowHealth, dying: b.state, deathDur, stages: [...stages], shake, removed: !api.bugs.includes(b) };
  });
  const w = result.seen.indexOf('windup'), c = result.seen.indexOf('charge');
  assert.ok(w >= 0 && c > w, `the boss must wind up before it charges: ${result.seen.join(' > ')}`);
  assert.ok(result.chargeSpeed > 150, 'the charge must be a real burst of speed');
  assert.equal(result.afterHit.hp, result.maxHp - 1);
  assert.equal(result.afterHit.state, 'stagger', 'a hit must stagger the boss');
  assert.ok(result.afterHit.hurtT > 0 && result.afterHit.rage > 0);
  assert.ok(result.lowHealth.enraged, 'the boss must reach its low-health behaviour before it dies');
  assert.equal(result.dying, 'dying');
  assert.ok(result.deathDur >= 2, 'the boss defeat is a long, staged sequence');
  assert.ok([1, 2, 3].every((s) => result.stages.includes(s)), `the collapse must run every stage (${result.stages.join(',')})`);
  assert.ok(result.shake >= 0.5, 'the fall must shake the world');
  assert.ok(result.removed, 'the boss corpse must be cleaned up afterwards');
});

test('stomping is geometry: Mario descending onto an enemy squashes it and bounces him, walking into it only shoves both', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 1;
    api.state.asleep = false;
    const reset = () => {
      api.bugs.length = 0;
      window.__bitling.marioSpawnEnemy('walker');
      const b = api.bugs[0];
      Object.assign(api.pet, { x: 160, y: api.groundY(), grounded: true, held: false, carried: false });
      Object.assign(api.marioState, { jumpH: 0, jumpVy: 0, bumpT: 0, bumpCd: 0, alertT: 0 });
      b.x = 160; b.vx = 0; b.targetVx = 0;
      return b;
    };
    // 1. Feet coming down onto its top.
    let b = reset();
    const eb = api.marioEnemyBounds(b);
    api.marioState.jumpH = (api.groundY() - eb.top) + 2;
    api.marioState.jumpVy = 220; // falling
    api.updateBugs(1 / 60);
    const stomp = { alive: b.alive, bounceVy: api.marioState.jumpVy, stompT: api.marioState.stompT, squashT: b.squashT };
    // 2. Same overlap, but rising: not a stomp.
    b = reset();
    api.marioState.jumpH = (api.groundY() - eb.top) + 2;
    api.marioState.jumpVy = -220;
    api.updateBugs(1 / 60);
    const rising = { alive: b.alive };
    // 3. On the ground, walking straight into it.
    b = reset();
    b.x = 166;
    api.updateBugs(1 / 60);
    const side = { alive: b.alive, bumpT: api.marioState.bumpT, bumpVx: api.marioState.bumpVx, enemyKnock: b.knockVx, enemyBump: b.bumpT };
    // 4. Per-enemy boxes differ: a hidden lurker's box is a sliver, a boss's is huge.
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('boss');
    const bossBox = api.marioEnemyBounds(api.bugs[0]);
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('ambush');
    const lurkBox = api.marioEnemyBounds(api.bugs[0]);
    return { stomp, rising, side, walkerBox: eb, bossBox, lurkBox };
  });
  assert.equal(result.stomp.alive, false, 'descending onto the enemy must squash it');
  assert.ok(result.stomp.bounceVy < 0, 'and bounce Mario back up');
  assert.ok(result.stomp.stompT > 0, 'with his own stomp beat');
  assert.equal(result.rising.alive, true, 'passing upward through the enemy is not a stomp');
  assert.equal(result.side.alive, true, 'walking into an enemy must not count as a stomp');
  assert.ok(result.side.bumpT > 0 && Math.abs(result.side.bumpVx) > 0, 'it shoves Mario back');
  assert.ok(Math.abs(result.side.enemyKnock) > 0 && result.side.enemyBump > 0, 'and shoves the enemy too');
  assert.ok(result.bossBox.h > result.walkerBox.h * 2 && result.bossBox.halfW > result.walkerBox.halfW * 1.5, 'collision boxes follow each class, not one shared radius');
  assert.ok(result.lurkBox.h < result.walkerBox.h * 0.5, 'a hidden lurker presents almost nothing to hit');
});

test('the fireball is a real projectile: thrown from the hand, falling under gravity, bouncing on the floor, and doing its damage on contact', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    const m = api.marioState;
    m.stage = 2;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('walker');
    const target = api.bugs[0];
    Object.assign(api.pet, { x: 80, y: api.groundY(), grounded: true, facing: 1 });
    target.x = 290; target.vx = 0; target.targetVx = 0;
    m.fireballs.length = 0;
    api.drawMarioAttack(api.petR(), 1, false, 'fireball', target);
    const fb = m.fireballs[0];
    const h = api.petR() * 2.85;
    const launch = { count: m.fireballs.length, x: fb.x, y: fb.y, handDx: fb.x - api.pet.x, handDy: api.groundY() - fb.y, h, throwT: m.throwT };
    const vy0 = fb.vy;
    const track = [];
    for (let i = 0; i < 8; i++) { api.updateMarioSimulation(1 / 60); if (m.fireballs.includes(fb)) track.push({ x: fb.x, y: fb.y, vy: fb.vy, spin: fb.spin }); }
    target.x = 240;
    // Floor bounce: drop one just above the floor.
    m.fireballs.length = 0;
    const bouncer = { x: 100, y: api.groundY() - 12, vx: 150, vy: 320, bounces: 0, t: 0, spin: 0, bounceT: 0, trailT: 0 };
    m.fireballs.push(bouncer);
    api.updateMarioSimulation(1 / 60);
    const bounce = { vy: bouncer.vy, bounces: bouncer.bounces, bounceT: bouncer.bounceT, y: bouncer.y, floor: api.groundY() - 10 };
    // Collision: place one on the target's own box.
    m.fireballs.length = 0; m.flashes.length = 0;
    const eb = api.marioEnemyBounds(target);
    m.fireballs.push({ x: eb.cx - 4, y: eb.cy, vx: 300, vy: 0, bounces: 0, t: 0, spin: 0, bounceT: 0, trailT: 0 });
    api.updateMarioSimulation(1 / 60);
    const impact = { alive: target.alive, knock: target.knockVx, squashT: target.squashT, fireballs: m.fireballs.length, flashes: m.flashes.length };
    // Cleanup: one that leaves the world, one that bounces out, and a cap on the count.
    m.fireballs.length = 0;
    m.fireballs.push({ x: -30, y: 100, vx: -100, vy: 0, bounces: 0, t: 0 }, { x: 100, y: 100, vx: 10, vy: 0, bounces: 5, t: 0 });
    api.updateMarioSimulation(1 / 60);
    const cleaned = m.fireballs.length;
    for (let i = 0; i < 9; i++) api.drawMarioAttack(api.petR(), 1, false, 'fireball', null);
    const capped = m.fireballs.length;
    return { launch, vy0, track, bounce, impact, cleaned, capped, max: api.MARIO_MAX_FIREBALLS };
  });
  assert.equal(result.launch.count, 1);
  assert.ok(result.launch.handDx > result.launch.h * 0.4 && result.launch.handDx < result.launch.h * 0.65, `the fireball must leave from his outstretched hand, not his feet or centre (${result.launch.handDx.toFixed(0)}px forward for a ${result.launch.h.toFixed(0)}px Mario)`);
  assert.ok(result.launch.handDy > result.launch.h * 0.3 && result.launch.handDy < result.launch.h * 0.55, 'at hand height');
  assert.ok(result.launch.throwT > 0, 'the throw must recoil');
  assert.ok(result.track.every((p, i) => i === 0 || p.vy > result.track[i - 1].vy), 'gravity must pull the fireball down frame after frame');
  assert.ok(result.track.every((p, i) => i === 0 || p.x > result.track[i - 1].x), 'it moves forward continuously, never teleports');
  assert.ok(Math.abs(result.track[result.track.length - 1].spin) > 0, 'it rolls as it flies');
  assert.ok(result.bounce.vy < 0 && result.bounce.bounces === 1 && result.bounce.bounceT > 0 && result.bounce.y <= result.bounce.floor, 'the floor bounce reverses it, counts, and deforms it');
  assert.equal(result.impact.alive, false, 'the projectile itself must do the damage');
  assert.ok(Math.abs(result.impact.knock) > 0 && result.impact.squashT > 0, 'with knockback and a visible reaction on the target');
  assert.equal(result.impact.fireballs, 0, 'and it is consumed on impact');
  assert.equal(result.impact.flashes, 1, 'leaving an impact flash');
  assert.equal(result.cleaned, 0, 'out-of-world and spent fireballs are removed');
  assert.ok(result.capped <= result.max, `never more than ${result.max} fireballs in flight`);
});

test('Mario notices a spawn before he attacks: turns to face it, alert beat, then the hunt is allowed; the stomp attack is a real hop', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    const m = api.marioState;
    m.stage = 0; // Small Mario: the stomp attack
    Object.assign(api.pet, { x: 60, y: api.groundY(), grounded: true, held: false, carried: false, facing: -1, zapCharge: 0, zap: 0, reactionT: 0, reaction: '', zapCool: 0 });
    Object.assign(m, { jumpH: 0, jumpVy: 0, alertT: 0, bumpT: 0 });
    api.state.asleep = false;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('walker');
    const b = api.bugs[0];
    b.x = 240; b.vx = 0; b.targetVx = 0;
    const onSpawn = { alertT: m.alertT, facing: api.pet.facing, reaction: api.pet.reaction, blocked: api.marioAttackBlocked(), charging: api.pet.zapCharge > 0 };
    let chargeStartedAt = -1, hopStartedAt = -1, maxJumpH = 0, phases = new Set();
    for (let i = 0; i < 240; i++) {
      window.__bitling.advance(1 / 60);
      if (chargeStartedAt < 0 && api.pet.zapCharge > 0) chargeStartedAt = i / 60;
      if (hopStartedAt < 0 && m.jumpH > 0) hopStartedAt = i / 60;
      maxJumpH = Math.max(maxJumpH, m.jumpH);
      phases.add(m.jumpPhase);
      if (!b.alive) break;
    }
    return { onSpawn, chargeStartedAt, hopStartedAt, maxJumpH, phases: [...phases], stomped: !b.alive, landed: m.jumpH === 0 && m.landT >= 0 };
  });
  assert.ok(result.onSpawn.alertT > 0 && result.onSpawn.reaction === 'alert', 'a spawn must start the alert beat');
  assert.equal(result.onSpawn.facing, 1, 'he must turn to face the newcomer');
  assert.ok(result.onSpawn.blocked && !result.onSpawn.charging, 'no attack may start during the notice beat');
  assert.ok(result.chargeStartedAt > 0.5, `the charge waits for the alert stance (started at ${result.chargeStartedAt}s)`);
  assert.ok(result.hopStartedAt > result.chargeStartedAt, 'the stomp hop follows the charge');
  assert.ok(result.maxJumpH > 20, 'the stomp is a real hop off the ground');
  assert.ok(['launch', 'rise', 'apex', 'fall'].every((p) => result.phases.includes(p)), `the hop runs its phases: ${result.phases.join(',')}`);
  assert.ok(result.stomped, 'and it lands on the target');
});

test('the world stays bounded: active enemy cap, boss exclusivity, corpse cleanup, particle and fireball ceilings', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 3;
    window.__bitling.advance(0.05);
    api.bugs.length = 0;
    for (let i = 0; i < 12; i++) window.__bitling.marioSpawnEnemy('walker');
    const cappedCount = api.bugs.filter((b) => b.alive).length;
    window.__bitling.marioSpawnEnemy('boss');
    const bossAllowed = api.bugs.some((b) => b.boss && b.alive);
    window.__bitling.marioSpawnEnemy('boss');
    const bossCount = api.bugs.filter((b) => b.boss && b.alive).length;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('boss');
    for (let i = 0; i < 8; i++) window.__bitling.marioSpawnEnemy('jumping');
    const withBoss = api.bugs.filter((b) => b.alive && !b.boss).length;
    // Kill everything (the boss takes several hits) and let the death animations play out.
    for (const b of api.bugs) while (b.alive) api.squashBug(Object.assign(b, { hurtT: 0 }), false, true);
    for (let i = 0; i < 60 * 3; i++) api.updateBugs(1 / 60);
    const leftovers = api.bugs.length;
    // Particle flood.
    for (let i = 0; i < 40; i++) api.spawn('spark', 100, 100, 50, {});
    const particles = api.particles.length;
    return { cappedCount, bossAllowed, bossCount, withBoss, leftovers, particles, caps: { active: api.MARIO_MAX_ACTIVE, withBoss: api.MARIO_MAX_ACTIVE_WITH_BOSS, particles: api.MAX_PARTICLES } };
  });
  assert.equal(result.cappedCount, result.caps.active, 'spawns beyond the active cap are dropped');
  assert.ok(result.bossAllowed, 'the boss always gets in');
  assert.equal(result.bossCount, 1, 'never two bosses');
  assert.equal(result.withBoss, result.caps.withBoss, 'with a boss out the cap for the rest is lower');
  assert.equal(result.leftovers, 0, 'every corpse is removed after its death animation');
  assert.ok(result.particles <= result.caps.particles, `particles are capped (${result.particles} <= ${result.caps.particles})`);
});

test('a flying enemy cannot be stomped by ordinary ground contact, but is squashed when Mario comes down on top of it', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    api.marioState.stage = 1;
    api.bugs.length = 0;
    window.__bitling.marioSpawnEnemy('flying');
    const b = api.bugs[0];
    b.x = 160; b.altitude = 90; b.baseAltitude = 90;
    Object.assign(api.pet, { x: 160, y: api.groundY(), grounded: true, held: false, carried: false, vy: 0 });
    Object.assign(api.marioState, { jumpH: 0, jumpVy: 0, bumpCd: 0 });
    api.state.asleep = false;
    api.updateBugs(1 / 60);
    const survivedGroundContact = b.alive;

    const eb = api.marioEnemyBounds(b);
    Object.assign(api.pet, { x: 160, y: eb.top - 2, grounded: false, vy: 180 }); // thrown/dropped, coming down
    api.updateBugs(1 / 60);
    return { survivedGroundContact, aliveAfterAirborneContact: b.alive };
  });
  assert.ok(result.survivedGroundContact, 'walking under a flier on the ground must not stomp it');
  assert.equal(result.aliveAfterAirborneContact, false, 'coming down right on top of a flier must stomp it');
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
    Object.assign(api.marioState, { jumpH: 0, jumpVy: 0 });
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

test('every Mario enemy exhibits rich 3D shading, highlights, and distinctive color depth matching the 3D aesthetic', async (t) => {
  const result = await withPage(t, () => {
    const api = window.__marioEnemyTest;
    window.__bitling.marioForceStage(3);
    window.__bitling.advance(0.1);
    const colorStats = {};
    const { width, height } = api.canvas;
    for (const kind of ['walker', 'shell', 'flying', 'jumping', 'ambush', 'elite', 'boss']) {
      api.bugs.length = 0;
      window.__bitling.marioSpawnEnemy(kind);
      const b = api.bugs[0];
      b.x = 160;
      api.ctx.clearRect(0, 0, width, height);
      api.drawBugs();
      const px = api.ctx.getImageData(0, 0, width, height).data;
      const uniqueHues = new Set();
      let opaqueCount = 0;
      for (let i = 0; i < px.length; i += 4) {
        if (px[i + 3] > 100) {
          opaqueCount++;
          // Quantize 12-bit color: 4 bits each for r, g, b
          const q = ((px[i] >> 4) << 8) | ((px[i + 1] >> 4) << 4) | (px[i + 2] >> 4);
          uniqueHues.add(q);
        }
      }
      colorStats[kind] = { opaqueCount, colorCount: uniqueHues.size };
    }
    return colorStats;
  });
  for (const [kind, stats] of Object.entries(result)) {
    assert.ok(stats.opaqueCount > 100, `${kind} must paint a substantial silhouette (${stats.opaqueCount}px)`);
    assert.ok(stats.colorCount >= 10, `${kind} must have multi-stop 3D shading and highlights, not flat debug color (${stats.colorCount} quantized colors)`);
  }
});

