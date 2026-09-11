#!/usr/bin/env python3
"""Precision patch for Mario in web/bitling.html."""
import os
import json

ROOT = "/Users/a12345/Desktop/AI/Bitling"
HTML_PATH = os.path.join(ROOT, "web/bitling.html")
JSON_PATH = os.path.join(ROOT, "Tools/mario_sprites.json")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    sprites = json.load(f)

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix erroneous scoreMarioWarpPipe in attack at ~line 2592
old_attack_block = """          if (state.species === 'mario') {
          scoreMarioWarpPipe(branch ? lineFor('shipped', { b: branch }) : line('shippedPlain'));
        } else if (state.species === 'ronaldo') {"""

new_attack_block = """          if (state.species === 'mario') {
            pet.zapLocal = (shotStyle === 'stomp');
            drawMarioAttack(petR(), 1, pet.zapBoss, shotStyle);
            if (aim.host) {
              native({ type: 'zap', id: aim.id, eyes, style: shotStyle });
            } else {
              squashBug(live, false, true);
            }
          } else if (state.species === 'ronaldo') {"""

assert old_attack_block in content, "Could not find old_attack_block in content!"
content = content.replace(old_attack_block, new_attack_block)
print("1. Fixed attack block.")

# 2. Insert Mario sprites and functions before CR7 sprites
mario_sprites_block = f"""  // ---------------------------------------------------------------- Super Mario (NES/SNES) sprites & renderer
  const MARIO_SPRITES = {{
    small_idle: '{sprites["small_idle"]}',
    small_run: '{sprites["small_run"]}',
    small_run2: '{sprites["small_run2"]}',
    small_jump: '{sprites["small_jump"]}',
    super_idle: '{sprites["super_idle"]}',
    super_run: '{sprites["super_run"]}',
    super_run2: '{sprites["super_run2"]}',
    super_jump: '{sprites["super_jump"]}',
    fire_idle: '{sprites["fire_idle"]}',
    fire_run: '{sprites["fire_run"]}',
    fire_run2: '{sprites["fire_run2"]}',
    fire_jump: '{sprites["fire_jump"]}',
    fire_throw: '{sprites["fire_throw"]}',
    mushroom: '{sprites["mushroom"]}',
    flower: '{sprites["flower"]}',
    star: '{sprites["star"]}',
    qblock: '{sprites["qblock"]}',
    qblock_hit: '{sprites["qblock_hit"]}',
    coin: '{sprites["coin"]}',
    fireball: '{sprites["fireball"]}',
    pipe: '{sprites["pipe"]}',
  }};

  const marioImgSmallIdle = new Image(); marioImgSmallIdle.src = MARIO_SPRITES.small_idle;
  const marioImgSmallRun = new Image(); marioImgSmallRun.src = MARIO_SPRITES.small_run;
  const marioImgSmallRun2 = new Image(); marioImgSmallRun2.src = MARIO_SPRITES.small_run2;
  const marioImgSmallJump = new Image(); marioImgSmallJump.src = MARIO_SPRITES.small_jump;
  const marioImgSuperIdle = new Image(); marioImgSuperIdle.src = MARIO_SPRITES.super_idle;
  const marioImgSuperRun = new Image(); marioImgSuperRun.src = MARIO_SPRITES.super_run;
  const marioImgSuperRun2 = new Image(); marioImgSuperRun2.src = MARIO_SPRITES.super_run2;
  const marioImgSuperJump = new Image(); marioImgSuperJump.src = MARIO_SPRITES.super_jump;
  const marioImgFireIdle = new Image(); marioImgFireIdle.src = MARIO_SPRITES.fire_idle;
  const marioImgFireRun = new Image(); marioImgFireRun.src = MARIO_SPRITES.fire_run;
  const marioImgFireRun2 = new Image(); marioImgFireRun2.src = MARIO_SPRITES.fire_run2;
  const marioImgFireJump = new Image(); marioImgFireJump.src = MARIO_SPRITES.fire_jump;
  const marioImgFireThrow = new Image(); marioImgFireThrow.src = MARIO_SPRITES.fire_throw;
  const marioImgMushroom = new Image(); marioImgMushroom.src = MARIO_SPRITES.mushroom;
  const marioImgFlower = new Image(); marioImgFlower.src = MARIO_SPRITES.flower;
  const marioImgStar = new Image(); marioImgStar.src = MARIO_SPRITES.star;
  const marioImgQBlock = new Image(); marioImgQBlock.src = MARIO_SPRITES.qblock;
  const marioImgQBlockHit = new Image(); marioImgQBlockHit.src = MARIO_SPRITES.qblock_hit;
  const marioImgCoin = new Image(); marioImgCoin.src = MARIO_SPRITES.coin;
  const marioImgFireball = new Image(); marioImgFireball.src = MARIO_SPRITES.fireball;
  const marioImgPipe = new Image(); marioImgPipe.src = MARIO_SPRITES.pipe;

  function triggerMarioCommitPowerUp() {{
    const m = marioState;
    m.qblockActive = true;
    m.qblockHit = false;
    m.qblockX = pet.x;
    m.qblockY = groundY - petR() * 2.8;
    m.qblockVy = 0;

    // Mario leaps up to hit the ? block
    pet.jump = true;
    pet.vy = -380;
    audio.marioJump();

    setTimeout(() => {{
      m.qblockHit = true;
      m.qblockVy = -90;
      audio.splat();

      if (m.stage === 0) {{
        // Spawn Super Mushroom!
        m.mushroomAnim = {{
          x: m.qblockX,
          y: m.qblockY - 24,
          vx: pet.facing * 90,
          vy: -60,
          active: true
        }};
        audio.marioPowerUp();
      }} else {{
        // Spawn Spinning Coin!
        m.coinAnim = {{
          x: m.qblockX,
          y: m.qblockY - 24,
          vy: -280,
          t: 0
        }};
        m.coins++;
        audio.marioCoin();

        // Check evolution to Fire Mario or Star Mario
        if (state.commits >= 4 && m.stage < 2) {{
          m.stage = 2; // Fire Mario
          audio.marioPowerUp();
          m.transformT = 1.2;
        }} else if (state.commits >= 8 && m.stage < 3) {{
          m.stage = 3; // Star Mario
          m.invincibleT = 15;
          audio.marioClear();
        }}
      }}
    }}, 260);
  }}

  function scoreMarioWarpPipe(label) {{
    const m = marioState;
    m.pipeActive = true;
    m.pipeT = 0;
    m.pipeX = pet.facing === 1 ? Math.min(W - 80, pet.x + 140) : Math.max(80, pet.x - 140);
    m.pipeY = groundY - 56;

    // Mario leaps toward the pipe
    pet.facing = (m.pipeX > pet.x ? 1 : -1);
    pet.jump = true;
    pet.vx = (m.pipeX - pet.x) * 1.5;
    pet.vy = -420;
    audio.marioJump();

    setTimeout(() => {{
      audio.marioPipe();
      audio.marioClear();
      for (let i = 0; i < 24; i++) {{
        spawn('spark', m.pipeX + 16, m.pipeY, 1, {{
          spread: 16,
          vx: rand(-120, 120),
          vy: rand(-180, -40),
          size: rand(5, 11),
          hue: pick([120, 48, 55, 200]),
          dur: rand(0.8, 1.8)
        }});
      }}
    }}, 450);

    say(label || pick([
      "COURSE CLEAR! World 1-1 deployed to main! WAHOO!",
      "Stage clear! 100 bonus points for clean production release!",
      "YAHOO! Pipe warp straight to production!",
      "Super Mario release! Flagpole reached!"
    ]), 4000);
  }}

  function updateMarioSimulation(dt) {{
    if (state.species !== 'mario') return;
    const m = marioState;

    // Invincibility countdown
    if (m.invincibleT > 0) {{
      m.invincibleT = Math.max(0, m.invincibleT - dt);
      if (Math.random() < 0.4) {{
        spawn('spark', pet.x + rand(-18, 18), pet.y - rand(10, petR() * 2), 1, {{
          spread: 6,
          vx: rand(-40, 40),
          vy: rand(-50, 10),
          size: rand(4, 9),
          hue: (pet.t * 360) % 360,
          dur: 0.4
        }});
      }}
    }}

    if (m.transformT > 0) m.transformT = Math.max(0, m.transformT - dt);

    // QBlock bouncing
    if (m.qblockActive && m.qblockHit) {{
      m.qblockY += m.qblockVy * dt;
      m.qblockVy += 400 * dt;
      if (m.qblockY >= groundY - petR() * 2.8) {{
        m.qblockY = groundY - petR() * 2.8;
        m.qblockVy = 0;
      }}
    }}

    // Coin animation popping out of block
    if (m.coinAnim) {{
      const c = m.coinAnim;
      c.t += dt;
      c.y += c.vy * dt;
      c.vy += 650 * dt;
      if (c.t > 0.85) m.coinAnim = null;
    }}

    // Mushroom sliding along floor
    if (m.mushroomAnim && m.mushroomAnim.active) {{
      const sh = m.mushroomAnim;
      sh.x += sh.vx * dt;
      sh.vy += 700 * dt;
      sh.y += sh.vy * dt;
      const floor = groundY - 18;
      if (sh.y >= floor) {{
        sh.y = floor;
        sh.vy = 0;
      }}
      // Collision with Mario -> Grow into Super Mario!
      if (Math.hypot(pet.x - sh.x, (pet.y - petR()) - sh.y) < petR() * 1.4) {{
        sh.active = false;
        m.mushroomAnim = null;
        m.stage = 1; // Super Mario!
        m.transformT = 1.0;
        audio.marioPowerUp();
        say("Power-up! SUPER MARIO! YAHOO!", 2200);
      }}
    }}

    // Fireballs physics & collision
    for (let i = m.fireballs.length - 1; i >= 0; i--) {{
      const fb = m.fireballs[i];
      fb.x += fb.vx * dt;
      fb.vy += 850 * dt;
      fb.y += fb.vy * dt;
      const floor = groundY - 10;
      if (fb.y >= floor) {{
        fb.y = floor;
        fb.vy = -260; // bounce
        fb.bounces = (fb.bounces || 0) + 1;
      }}

      // Smoke trail
      if (Math.random() < 0.6) {{
        spawn('spark', fb.x, fb.y, 1, {{
          spread: 3,
          vx: -fb.vx * 0.1,
          vy: -30,
          size: 5,
          hue: pick([28, 45, 12]),
          dur: 0.25
        }});
      }}

      // Check bug collision
      let hit = false;
      for (const bug of bugs) {{
        if (!bug.alive) continue;
        const bugY = groundY - 9 * scale;
        if (Math.hypot(fb.x - bug.x, fb.y - bugY) < 22) {{
          hit = true;
          squashBug(bug, false, true);
          break;
        }}
      }}

      if (hit || fb.bounces > 4 || fb.x < 0 || fb.x > W) {{
        m.fireballs.splice(i, 1);
        audio.splat();
        for (let s = 0; s < 8; s++) {{
          spawn('spark', fb.x, fb.y, 1, {{
            spread: 8,
            vx: rand(-90, 90),
            vy: rand(-120, -20),
            size: rand(5, 9),
            hue: 35,
            dur: 0.4
          }});
        }}
      }}
    }}

    // Pipe timer
    if (m.pipeActive) {{
      m.pipeT += dt;
      if (m.pipeT > 4.2) m.pipeActive = false;
    }}
  }}

  function drawMario() {{
    const f = pet.facing;
    const asleep = pet.asleep;
    const isCarried = pet.carried;
    const m = marioState;
    const isSmall = (m.stage === 0);
    const isFire = (m.stage === 2);
    const isStar = (m.stage === 3 || m.invincibleT > 0);

    // Target Height: Small Mario is 0.72x, Super Mario is full height
    const baseH = petR() * (isSmall ? 1.95 : 2.75);
    const targetH = baseH * (m.transformT > 0 ? (1 + 0.15 * Math.sin(pet.t * 30)) : 1.0);

    // Select sprite
    let sprite = isSmall ? marioImgSmallIdle : (isFire ? marioImgFireIdle : marioImgSuperIdle);
    const isJumping = (pet.vy < -20 || pet.jump || pet.mode === 'jump' || (pet.zap > 0 && pet.zapStyle === 'stomp'));
    const isThrowing = (pet.zap > 0 && pet.zapStyle === 'fireball');

    if (isJumping) {{
      sprite = isSmall ? marioImgSmallJump : (isFire ? marioImgFireJump : marioImgSuperJump);
    }} else if (isThrowing && isFire) {{
      sprite = marioImgFireThrow;
    }} else if (pet.walking || Math.abs(pet.vx || 0) > 15) {{
      const walkFrame = Math.floor(pet.t * 8) % 2;
      if (isSmall) {{
        sprite = walkFrame === 0 ? marioImgSmallRun : marioImgSmallRun2;
      }} else if (isFire) {{
        sprite = walkFrame === 0 ? marioImgFireRun : marioImgFireRun2;
      }} else {{
        sprite = walkFrame === 0 ? marioImgSuperRun : marioImgSuperRun2;
      }}
    }}

    // World Render: Props
    // 1. Warp Pipe
    if (m.pipeActive) {{
      ctx.save();
      const pw = 64, ph = 64;
      ctx.drawImage(marioImgPipe, m.pipeX - pw / 2, m.pipeY, pw, ph);
      ctx.restore();
    }}

    // 2. Question Block
    if (m.qblockActive) {{
      ctx.save();
      const qw = 36, qh = 36;
      const qImg = m.qblockHit ? marioImgQBlockHit : marioImgQBlock;
      ctx.drawImage(qImg, m.qblockX - qw / 2, m.qblockY, qw, qh);
      ctx.restore();
    }}

    // 3. Popping Coin
    if (m.coinAnim) {{
      ctx.save();
      const cw = 28, ch = 28;
      ctx.drawImage(marioImgCoin, m.coinAnim.x - cw / 2, m.coinAnim.y - ch / 2, cw, ch);
      ctx.restore();
    }}

    // 4. Mushroom
    if (m.mushroomAnim && m.mushroomAnim.active) {{
      ctx.save();
      const mw = 32, mh = 32;
      ctx.drawImage(marioImgMushroom, m.mushroomAnim.x - mw / 2, m.mushroomAnim.y - mh / 2, mw, mh);
      ctx.restore();
    }}

    // 5. Fireballs
    for (const fb of m.fireballs) {{
      ctx.save();
      const fw = 20, fh = 20;
      ctx.translate(fb.x, fb.y);
      ctx.rotate(pet.t * 16);
      ctx.drawImage(marioImgFireball, -fw / 2, -fh / 2, fw, fh);
      ctx.restore();
    }}

    // Character Rendering
    stageBody({{ shadow: !isJumping, bob: isCarried ? 0.01 : 0.02, bobRate: 2.0, sway: isCarried ? 0 : 0.01 }}, (r, t) => {{
      ctx.save();

      // Horizontal facing
      ctx.scale(f, 1);

      // Star Mario rainbow invincibility filter
      if (isStar) {{
        ctx.filter = `hue-rotate(${{Math.round((pet.t * 540) % 360)}}deg) saturate(1.8) brightness(1.15)`;
      }}

      // Transform flash
      if (m.transformT > 0 && Math.floor(pet.t * 24) % 2 === 0) {{
        ctx.filter = 'brightness(2.2) saturate(0.5)';
      }}

      // Draw sprite
      const aspect = sprite.width / (sprite.height || 1);
      const drawW = targetH * aspect;
      const drawX = -drawW * 0.48;
      const drawY = -targetH * 0.98;

      ctx.imageSmoothingEnabled = false; // Crisp pixel art!
      ctx.drawImage(sprite, drawX, drawY, drawW, targetH);
      ctx.restore();
    }});
  }}

  function drawMarioAttack(r, k, isBoss, style) {{
    // Stomp or Fireball
    if (style === 'fireball' || marioState.stage >= 2 || isBoss) {{
      // Fireball blast
      const ox = pet.x + pet.facing * r * 0.5, oy = groundY - 14;
      const targetX = Number.isFinite(pet.zapX) ? pet.zapX : (ox + pet.facing * 140);
      const targetY = Number.isFinite(pet.zapY) ? pet.zapY : (groundY - 10);
      const bdx = targetX - ox, bdy = targetY - oy;
      const dist = Math.max(1, Math.hypot(bdx, bdy));
      const spd = 520;
      marioState.fireballs.push({{
        x: ox,
        y: oy,
        vx: (bdx / dist) * spd,
        vy: (bdy / dist) * spd - 60,
        bounces: 0
      }});
      audio.marioFireball();
    }} else {{
      // Stomp leap
      pet.jump = true;
      pet.vy = -340;
      audio.marioJump();
      setTimeout(() => {{
        audio.marioStomp();
      }}, 240);
    }}
  }}
"""

cr7_header = "  // ---------------------------------------------------------------- Cristiano Ronaldo (CR7) sprites & renderer"
assert cr7_header in content, "Could not find cr7_header in content!"

content = content.replace(cr7_header, f"{mario_sprites_block}\n{cr7_header}")
print("2. Inserted Mario sprites and renderer.")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Precision patch complete.")
