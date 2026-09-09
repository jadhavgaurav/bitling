#!/usr/bin/env python3
import json
import re
from pathlib import Path

def main():
    sprites_file = Path("Tools/mario_3d_sprites.json")
    with open(sprites_file, "r") as f:
        sprites = json.load(f)

    target_file = Path("web/bitling.html")
    content = target_file.read_text(encoding="utf-8")

    # Construct MARIO_SPRITES dictionary
    sprites_js_lines = [
        "  // ---------------------------------------------------------------- Super Mario (Living 3D Cinema / Disney Style) sprites & renderer",
        "  const MARIO_SPRITES = {"
    ]
    for k, v in sprites.items():
        sprites_js_lines.append(f"    {k}: '{v}',")
    sprites_js_lines.append("  };")
    sprites_js = "\n".join(sprites_js_lines)

    # Complete image instantiations for ALL stages
    images_js = """
  // Small Mario (Stage 0) living poses
  const marioImgSmallIdle = new Image(); marioImgSmallIdle.src = MARIO_SPRITES.small_idle;
  const marioImgSmallWalk = new Image(); marioImgSmallWalk.src = MARIO_SPRITES.small_walk;
  const marioImgSmallRun = marioImgSmallWalk;
  const marioImgSmallRun2 = marioImgSmallWalk;
  const marioImgSmallJump = new Image(); marioImgSmallJump.src = MARIO_SPRITES.small_jump;

  // Super Mario (Stage 1) living poses
  const marioImgSuperIdle = new Image(); marioImgSuperIdle.src = MARIO_SPRITES.super_idle;
  const marioImgSuperThumbs = new Image(); marioImgSuperThumbs.src = MARIO_SPRITES.super_thumbs;
  const marioImgSuperWalk1 = new Image(); marioImgSuperWalk1.src = MARIO_SPRITES.super_walk1;
  const marioImgSuperWalk2 = new Image(); marioImgSuperWalk2.src = MARIO_SPRITES.super_walk2;
  const marioImgSuperRun = new Image(); marioImgSuperRun.src = MARIO_SPRITES.super_run;
  const marioImgSuperRun2 = marioImgSuperRun;
  const marioImgSuperStride = marioImgSuperRun;
  const marioImgSuperJump = new Image(); marioImgSuperJump.src = MARIO_SPRITES.super_jump;

  // Fire Mario (Stage 2) living poses (White suit, clean throwing pose)
  const marioImgFireIdle = new Image(); marioImgFireIdle.src = MARIO_SPRITES.fire_idle;
  const marioImgFireWalk1 = new Image(); marioImgFireWalk1.src = MARIO_SPRITES.fire_walk1;
  const marioImgFireWalk2 = new Image(); marioImgFireWalk2.src = MARIO_SPRITES.fire_walk2;
  const marioImgFireRun = new Image(); marioImgFireRun.src = MARIO_SPRITES.fire_run;
  const marioImgFireRun2 = marioImgFireWalk2;
  const marioImgFireJump = new Image(); marioImgFireJump.src = MARIO_SPRITES.fire_jump;
  const marioImgFireThrow = new Image(); marioImgFireThrow.src = MARIO_SPRITES.fire_throw;

  // Props & Items (scaled proportionally across all pet sizes)
  const marioImgMushroom = new Image(); marioImgMushroom.src = MARIO_SPRITES.mushroom;
  const marioImgStar = new Image(); marioImgStar.src = MARIO_SPRITES.star;
  const marioImgFlower = marioImgStar;
  const marioImgQBlock = new Image(); marioImgQBlock.src = MARIO_SPRITES.qblock;
  const marioImgQBlockHit = new Image(); marioImgQBlockHit.src = MARIO_SPRITES.qblock_hit;
  const marioImgCoin = new Image(); marioImgCoin.src = MARIO_SPRITES.coin;
  const marioImgFireball = new Image(); marioImgFireball.src = MARIO_SPRITES.fireball;
  const marioImgPipe = new Image(); marioImgPipe.src = MARIO_SPRITES.pipe;"""

    pattern_header = r"  // ---------------------------------------------------------------- Super Mario[\s\S]*?function triggerMarioCommitPowerUp\(\) \{"
    match_header = re.search(pattern_header, content)
    assert match_header, "Mario header block not found"

    new_header = sprites_js + images_js + "\n\n  function triggerMarioCommitPowerUp() {"
    content = content[:match_header.start()] + new_header + content[match_header.end():]

    # Universal drawMario function supporting all kinds of Marios and all pet sizes
    new_draw_mario = """  function drawMario() {
    const f = pet.facing;
    const asleep = pet.asleep;
    const isCarried = pet.carried;
    const m = marioState;
    const isSmall = (m.stage === 0);
    const isFire = (m.stage === 2);
    const isStar = (m.stage === 3 || m.invincibleT > 0);
    const r = petR();

    // Target Height: Proportional to master pet radius across ALL pet sizes (0.8 to 1.6)
    // Small Mario is ~1.9x r, Super Mario / Fire / Star is ~2.85x r
    const baseH = r * (isSmall ? 1.9 : 2.85);
    const targetH = baseH * (m.transformT > 0 ? (1 + 0.18 * Math.sin(pet.t * 30)) : 1.0);

    // State detection
    const isJumping = (pet.vy < -20 || pet.jump || pet.mode === 'jump' || (pet.zap > 0 && pet.zapStyle === 'stomp'));
    const isThrowing = (pet.zap > 0 && pet.zapStyle === 'fireball');
    const isWalking = (pet.walking || Math.abs(pet.vx || 0) > 15);
    const isSprinting = (isWalking && Math.abs(pet.vx || 0) > 65);

    // Dynamic living sprite selection for ALL stages
    let sprite = marioImgSuperIdle;
    let walkBob = 0;
    let walkTilt = 0;

    if (isSmall) {
      // ---------------- Small Mario (Stage 0) ----------------
      if (isJumping) {
        sprite = marioImgSmallJump;
        walkTilt = (pet.vy < 0 ? -0.12 : 0.08);
      } else if (isWalking) {
        sprite = marioImgSmallWalk;
        walkBob = Math.abs(Math.sin(pet.t * 10)) * (r * 0.18);
        walkTilt = Math.sin(pet.t * 10) * 0.08;
      } else if (asleep) {
        sprite = marioImgSmallIdle;
        walkBob = Math.sin(pet.t * 1.5) * (r * 0.08);
        walkTilt = 0.08;
      } else {
        sprite = marioImgSmallIdle;
        walkBob = Math.sin(pet.t * 2.8) * (r * 0.06);
      }
    } else if (isFire) {
      // ---------------- Fire Mario (Stage 2) ----------------
      // Crisp white cap & shirt with bright red overalls
      if (isThrowing) {
        // ONLY when actively hurling a fireball at a bug!
        sprite = marioImgFireThrow;
        walkTilt = 0.06;
      } else if (isJumping) {
        sprite = marioImgFireJump;
        walkTilt = (pet.vy < 0 ? -0.10 : 0.06);
      } else if (isSprinting) {
        sprite = marioImgFireRun;
        walkBob = Math.abs(Math.sin(pet.t * 14)) * (r * 0.20);
        walkTilt = 0.12;
      } else if (isWalking) {
        const walkFrame = Math.floor(pet.t * 6) % 2;
        sprite = (walkFrame === 0) ? marioImgFireWalk1 : marioImgFireWalk2;
        walkBob = Math.abs(Math.sin(pet.t * 8)) * (r * 0.16);
        walkTilt = Math.sin(pet.t * 8) * 0.05;
      } else if (asleep) {
        sprite = marioImgFireIdle;
        walkBob = Math.sin(pet.t * 1.4) * (r * 0.08);
        walkTilt = 0.10;
      } else {
        sprite = marioImgFireIdle;
        walkBob = Math.sin(pet.t * 2.5) * (r * 0.06);
      }
    } else {
      // ---------------- Super Mario & Star Mario (Stage 1 & 3) ----------------
      if (isThrowing) {
        sprite = marioImgFireThrow;
        walkTilt = 0.06;
      } else if (isJumping) {
        sprite = marioImgSuperJump;
        walkTilt = (pet.vy < 0 ? -0.10 : 0.06);
      } else if (isSprinting) {
        sprite = marioImgSuperRun;
        walkBob = Math.abs(Math.sin(pet.t * 14)) * (r * 0.20);
        walkTilt = 0.12;
      } else if (isWalking) {
        const walkFrame = Math.floor(pet.t * 6) % 2;
        sprite = (walkFrame === 0) ? marioImgSuperWalk1 : marioImgSuperWalk2;
        walkBob = Math.abs(Math.sin(pet.t * 8)) * (r * 0.16);
        walkTilt = Math.sin(pet.t * 8) * 0.05;
      } else if (asleep) {
        sprite = marioImgSuperIdle;
        walkBob = Math.sin(pet.t * 1.4) * (r * 0.08);
        walkTilt = 0.10;
      } else if (isCarried) {
        sprite = marioImgSuperJump;
        walkBob = Math.sin(pet.t * 8) * (r * 0.10);
        walkTilt = Math.sin(pet.t * 6) * 0.08;
      } else {
        // Living Idle: Alternate between warm wave and proud winking thumbs-up!
        const idleCycle = Math.floor(pet.t / 4.5) % 2;
        sprite = (idleCycle === 0) ? marioImgSuperIdle : marioImgSuperThumbs;
        walkBob = Math.sin(pet.t * 2.5) * (r * 0.06);
      }
    }

    // World Render: Props proportionally scaled with master radius r = petR()
    // 1. 3D Warp Pipe (proportional to pet size)
    if (m.pipeActive && marioImgPipe && marioImgPipe.complete) {
      ctx.save();
      const pw = r * 2.2, ph = r * 3.2;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(marioImgPipe, m.pipeX - pw / 2, groundY - ph, pw, ph);
      ctx.restore();
    }

    // 2. 3D Question Block
    if (m.qblockActive) {
      ctx.save();
      const qw = r * 1.6, qh = r * 1.6;
      const qImg = m.qblockHit ? marioImgQBlockHit : marioImgQBlock;
      if (qImg && qImg.complete) {
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(qImg, m.qblockX - qw / 2, m.qblockY, qw, qh);
      }
      ctx.restore();
    }

    // 3. Popping 3D Coin (spinning on vertical axis)
    if (m.coinAnim && marioImgCoin && marioImgCoin.complete) {
      ctx.save();
      const cw = r * 1.25, ch = r * 1.25;
      ctx.translate(m.coinAnim.x, m.coinAnim.y);
      ctx.scale(Math.cos(m.coinAnim.t * 14), 1);
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(marioImgCoin, -cw / 2, -ch / 2, cw, ch);
      ctx.restore();
    }

    // 4. 3D Movie Super Mushroom
    if (m.mushroomAnim && m.mushroomAnim.active && marioImgMushroom && marioImgMushroom.complete) {
      ctx.save();
      const mw = r * 1.45, mh = r * 1.45;
      ctx.translate(m.mushroomAnim.x, m.mushroomAnim.y);
      ctx.rotate(Math.sin(pet.t * 8) * 0.08);
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(marioImgMushroom, -mw / 2, -mh / 2, mw, mh);
      ctx.restore();
    }

    // 5. 3D Bouncing Fireballs (ONLY drawn as flying projectiles!)
    for (const fb of m.fireballs) {
      if (marioImgFireball && marioImgFireball.complete) {
        ctx.save();
        const fw = r * 1.2, fh = r * 1.2;
        ctx.translate(fb.x, fb.y);
        ctx.rotate(pet.t * 16);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(marioImgFireball, -fw / 2, -fh / 2, fw, fh);
        ctx.restore();
      }
    }

    // Fire Mario ambient ember particles (proportional to size)
    if (isFire && !asleep && Math.random() < 0.28) {
      spawn('spark', pet.x + rand(-r * 0.5, r * 0.5), pet.y - rand(r * 0.3, r * 1.8), 1, {
        spread: 4,
        vx: rand(-15, 15),
        vy: rand(-35, -8),
        size: rand(r * 0.12, r * 0.25),
        hue: pick([25, 42, 12]),
        dur: 0.45
      });
    }

    // Character Rendering
    stageBody({ shadow: !isJumping, bob: isCarried ? 0.01 : 0.02, bobRate: 2.0, sway: isCarried ? 0 : 0.01 }, (radius, t) => {
      ctx.save();

      // Soft 3D ground contact shadow (scaled to targetH)
      if (!isJumping) {
        ctx.save();
        ctx.fillStyle = 'rgba(0, 0, 0, 0.26)';
        ctx.beginPath();
        ctx.ellipse(0, 2, targetH * 0.26, targetH * 0.07, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      // Horizontal facing & movement dynamics
      ctx.scale(f, 1);
      ctx.translate(0, -walkBob);
      ctx.rotate(walkTilt);

      // Star Mario 3D rainbow invincibility aura & orbiting star (scaled to targetH)
      if (isStar) {
        ctx.filter = `hue-rotate(${Math.round((pet.t * 540) % 360)}deg) saturate(1.8) brightness(1.2)`;
        if (marioImgStar && marioImgStar.complete) {
          ctx.save();
          const starAngle = pet.t * 6;
          const starOrbitX = Math.cos(starAngle) * (targetH * 0.55);
          const starOrbitY = -targetH * 0.65 + Math.sin(starAngle) * (targetH * 0.25);
          const starSize = r * 1.5;
          ctx.translate(starOrbitX, starOrbitY);
          ctx.rotate(Math.sin(pet.t * 10) * 0.2);
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';
          ctx.drawImage(marioImgStar, -starSize / 2, -starSize / 2, starSize, starSize);
          ctx.restore();
        }
      }

      // Transform flash
      if (m.transformT > 0 && Math.floor(pet.t * 24) % 2 === 0) {
        ctx.filter = 'brightness(2.2) saturate(0.4)';
      }

      // Draw high-resolution 3D sprite with antialiased high-quality filtering
      if (sprite && sprite.complete && sprite.naturalWidth > 0) {
        const aspect = sprite.naturalWidth / (sprite.naturalHeight || 1);
        const drawW = targetH * aspect;
        const drawX = -drawW * (isThrowing ? 0.40 : 0.50);
        const drawY = -targetH * 0.98;

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(sprite, drawX, drawY, drawW, targetH);
      }

      ctx.restore();
    });
  }"""

    pattern_draw = r"  function drawMario\(\) \{[\s\S]*?\n  \}\n\n  function drawMarioAttack"
    match_draw = re.search(pattern_draw, content)
    assert match_draw, "drawMario block not found"

    content = content[:match_draw.start()] + new_draw_mario + "\n\n  function drawMarioAttack" + content[match_draw.end():]

    target_file.write_text(content, encoding="utf-8")
    print("Successfully patched web/bitling.html with universal Mario support for all forms and sizes!")

if __name__ == "__main__":
    main()
