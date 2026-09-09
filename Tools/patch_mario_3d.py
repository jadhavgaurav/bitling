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

    # Construct MARIO_SPRITES JS block
    sprites_js_lines = ["  // ---------------------------------------------------------------- Super Mario (3D Cinema / Disney Style) sprites & renderer",
                        "  const MARIO_SPRITES = {"]
    for k, v in sprites.items():
        sprites_js_lines.append(f"    {k}: '{v}',")
    sprites_js_lines.append("  };")
    sprites_js = "\n".join(sprites_js_lines)

    # Images block
    images_js = """
  const marioImgSmallIdle = new Image(); marioImgSmallIdle.src = MARIO_SPRITES.small_idle;
  const marioImgSmallRun = marioImgSmallIdle;
  const marioImgSmallRun2 = marioImgSmallIdle;
  const marioImgSmallJump = marioImgSmallIdle;
  const marioImgSuperIdle = new Image(); marioImgSuperIdle.src = MARIO_SPRITES.super_idle;
  const marioImgSuperStride = new Image(); marioImgSuperStride.src = MARIO_SPRITES.super_stride;
  const marioImgSuperRun = marioImgSuperStride;
  const marioImgSuperRun2 = marioImgSuperStride;
  const marioImgSuperJump = new Image(); marioImgSuperJump.src = MARIO_SPRITES.super_jump;
  const marioImgFireThrow = new Image(); marioImgFireThrow.src = MARIO_SPRITES.fire_throw;
  const marioImgFireIdle = marioImgFireThrow;
  const marioImgFireRun = marioImgFireThrow;
  const marioImgFireRun2 = marioImgFireThrow;
  const marioImgFireJump = marioImgFireThrow;
  const marioImgMushroom = new Image(); marioImgMushroom.src = MARIO_SPRITES.mushroom;
  const marioImgStar = new Image(); marioImgStar.src = MARIO_SPRITES.star;
  const marioImgFlower = marioImgStar;
  const marioImgQBlock = new Image(); marioImgQBlock.src = MARIO_SPRITES.qblock;
  const marioImgQBlockHit = new Image(); marioImgQBlockHit.src = MARIO_SPRITES.qblock_hit;
  const marioImgCoin = new Image(); marioImgCoin.src = MARIO_SPRITES.coin;
  const marioImgFireball = new Image(); marioImgFireball.src = MARIO_SPRITES.fireball;
  const marioImgPipe = new Image(); marioImgPipe.src = MARIO_SPRITES.pipe;"""

    # Replacement regex for MARIO_SPRITES and image definitions
    # Match from "// ---------------------------------------------------------------- Super Mario" up to "function triggerMarioCommitPowerUp"
    pattern_header = r"  // ---------------------------------------------------------------- Super Mario[\s\S]*?function triggerMarioCommitPowerUp\(\) \{"
    match_header = re.search(pattern_header, content)
    assert match_header, "Mario header block not found"

    new_header = sprites_js + images_js + "\n\n  function triggerMarioCommitPowerUp() {"
    content = content[:match_header.start()] + new_header + content[match_header.end():]

    # Replacement for drawMario
    new_draw_mario = """  function drawMario() {
    const f = pet.facing;
    const isCarried = pet.carried;
    const m = marioState;
    const isSmall = (m.stage === 0);
    const isFire = (m.stage === 2);
    const isStar = (m.stage === 3 || m.invincibleT > 0);

    // Target Height: 3D character scale
    // Small Mario is ~1.9x petR, Super Mario is ~2.85x petR
    const baseH = petR() * (isSmall ? 1.9 : 2.85);
    const targetH = baseH * (m.transformT > 0 ? (1 + 0.18 * Math.sin(pet.t * 30)) : 1.0);

    // Dynamic 3D Sprite selection
    let sprite = isSmall ? marioImgSmallIdle : (isFire ? marioImgFireThrow : marioImgSuperIdle);
    const isJumping = (pet.vy < -20 || pet.jump || pet.mode === 'jump' || (pet.zap > 0 && pet.zapStyle === 'stomp'));
    const isThrowing = (pet.zap > 0 && pet.zapStyle === 'fireball');
    const isWalking = (pet.walking || Math.abs(pet.vx || 0) > 15);

    let walkBob = 0;
    let walkTilt = 0;

    if (isJumping) {
      sprite = isSmall ? marioImgSmallIdle : (isFire ? marioImgFireThrow : marioImgSuperJump);
    } else if (isThrowing || isFire) {
      sprite = marioImgFireThrow;
    } else if (isWalking) {
      sprite = isSmall ? marioImgSmallIdle : marioImgSuperStride;
      walkBob = Math.abs(Math.sin(pet.t * 10)) * 4;
      walkTilt = Math.sin(pet.t * 10) * 0.06;
    } else {
      sprite = isSmall ? marioImgSmallIdle : marioImgSuperIdle;
      // Gentle breathing idle sway
      walkBob = Math.sin(pet.t * 3) * 1.5;
    }

    // World Render: Props
    // 1. 3D Warp Pipe
    if (m.pipeActive && marioImgPipe && marioImgPipe.complete) {
      ctx.save();
      const pw = 52, ph = 76;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(marioImgPipe, m.pipeX - pw / 2, groundY - ph, pw, ph);
      ctx.restore();
    }

    // 2. 3D Question Block
    if (m.qblockActive) {
      ctx.save();
      const qw = 40, qh = 40;
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
      const cw = 30, ch = 30;
      ctx.translate(m.coinAnim.x, m.coinAnim.y);
      ctx.scale(Math.cos(m.coinAnim.t * 14), 1); // 3D Coin rotation
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(marioImgCoin, -cw / 2, -ch / 2, cw, ch);
      ctx.restore();
    }

    // 4. 3D Movie Super Mushroom
    if (m.mushroomAnim && m.mushroomAnim.active && marioImgMushroom && marioImgMushroom.complete) {
      ctx.save();
      const mw = 36, mh = 36;
      ctx.translate(m.mushroomAnim.x, m.mushroomAnim.y);
      ctx.rotate(Math.sin(pet.t * 8) * 0.08); // gentle rolling wobble
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(marioImgMushroom, -mw / 2, -mh / 2, mw, mh);
      ctx.restore();
    }

    // 5. 3D Bouncing Fireballs
    for (const fb of m.fireballs) {
      if (marioImgFireball && marioImgFireball.complete) {
        ctx.save();
        const fw = 28, fh = 28;
        ctx.translate(fb.x, fb.y);
        ctx.rotate(pet.t * 16);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(marioImgFireball, -fw / 2, -fh / 2, fw, fh);
        ctx.restore();
      }
    }

    // Character Rendering
    stageBody({ shadow: !isJumping, bob: isCarried ? 0.01 : 0.02, bobRate: 2.0, sway: isCarried ? 0 : 0.01 }, (r, t) => {
      ctx.save();

      // Soft 3D ground contact shadow
      if (!isJumping) {
        ctx.save();
        ctx.fillStyle = 'rgba(0, 0, 0, 0.28)';
        ctx.beginPath();
        ctx.ellipse(0, 2, targetH * 0.26, targetH * 0.07, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      // Horizontal facing
      ctx.scale(f, 1);
      ctx.translate(0, -walkBob);
      ctx.rotate(walkTilt);

      // Star Mario 3D rainbow invincibility aura & orbiting star
      if (isStar) {
        ctx.filter = `hue-rotate(${Math.round((pet.t * 540) % 360)}deg) saturate(1.8) brightness(1.2)`;
        if (marioImgStar && marioImgStar.complete) {
          ctx.save();
          const starAngle = pet.t * 6;
          const starOrbitX = Math.cos(starAngle) * (targetH * 0.55);
          const starOrbitY = -targetH * 0.65 + Math.sin(starAngle) * (targetH * 0.25);
          ctx.translate(starOrbitX, starOrbitY);
          ctx.rotate(Math.sin(pet.t * 10) * 0.2);
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';
          ctx.drawImage(marioImgStar, -18, -18, 36, 36);
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
        const drawX = -drawW * (isThrowing || isFire ? 0.40 : 0.50);
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
    print("Successfully patched web/bitling.html with 3D Cinema Mario assets!")

if __name__ == "__main__":
    main()
