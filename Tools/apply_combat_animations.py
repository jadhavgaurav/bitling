#!/usr/bin/env python3
import base64

artifact_dir = "/Users/a12345/.gemini/antigravity-ide/brain/251518e0-36c4-45f1-b359-1b1615cce758"

# Load base64 for the three action sprites
with open(f"{artifact_dir}/goku_hd_kame_charge_right_opt.png", "rb") as f:
    b64_kame_charge = base64.b64encode(f.read()).decode("ascii")

with open(f"{artifact_dir}/goku_hd_kame_fire_right_opt.png", "rb") as f:
    b64_kame_fire = base64.b64encode(f.read()).decode("ascii")

with open(f"{artifact_dir}/goku_hd_kiball_fire_right_opt.png", "rb") as f:
    b64_kiball = base64.b64encode(f.read()).decode("ascii")

print("Loaded base64 sprites successfully.")

files_to_patch = ["web/bitling.html", "docs/index.html"]

for filepath in files_to_patch:
    print(f"Patching {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update GOKU_SPRITES and image instantiations
    old_sprites_end = "    fly: 'data:image/png;base64,"
    idx = content.find(old_sprites_end)
    assert idx != -1, f"Could not find {old_sprites_end} in {filepath}"
    
    # find the closing of fly and GOKU_SPRITES
    end_sprites_idx = content.find("  };\n\n  const gokuImgIdle = new Image();", idx)
    assert end_sprites_idx != -1, f"Could not find end of GOKU_SPRITES in {filepath}"
    
    old_init = "  const gokuImgIdle = new Image(); gokuImgIdle.src = GOKU_SPRITES.idle;\n  const gokuImgFly = new Image(); gokuImgFly.src = GOKU_SPRITES.fly;"
    new_init = (
        "  const gokuImgIdle = new Image(); gokuImgIdle.src = GOKU_SPRITES.idle;\n"
        "  const gokuImgFly = new Image(); gokuImgFly.src = GOKU_SPRITES.fly;\n"
        "  const gokuImgKameCharge = new Image(); gokuImgKameCharge.src = GOKU_SPRITES.kameCharge;\n"
        "  const gokuImgKameFire = new Image(); gokuImgKameFire.src = GOKU_SPRITES.kameFire;\n"
        "  const gokuImgKiBlast = new Image(); gokuImgKiBlast.src = GOKU_SPRITES.kiBlast;"
    )

    # Insert kameCharge, kameFire, kiBlast into GOKU_SPRITES
    added_sprites = (
        f",\n    kameCharge: 'data:image/png;base64,{b64_kame_charge}',\n"
        f"    kameFire: 'data:image/png;base64,{b64_kame_fire}',\n"
        f"    kiBlast: 'data:image/png;base64,{b64_kiball}'\n  }};"
    )
    content = content[:end_sprites_idx] + added_sprites + content[end_sprites_idx + 5:]
    content = content.replace(old_init, new_init, 1)

    # 2. Update attack origin & draw in species('goku')
    old_attack_origin = "origin: (r) => [{ x: Math.round(pet.x + pet.facing * r * 0.65), y: Math.round(pet.y - r * 1.5) }],"
    new_attack_origin = (
        "origin: (r) => [{\n"
        "        x: Math.round(pet.x + pet.facing * r * (pet.zapStyle === 'kamehameha' || pet.zapBoss ? 0.68 : 1.10)),\n"
        "        y: Math.round(pet.y - r * (pet.zapStyle === 'kamehameha' || pet.zapBoss ? 1.53 : 1.23))\n"
        "      }],"
    )
    content = content.replace(old_attack_origin, new_attack_origin, 1)

    old_attack_draw = "const ox = pet.x + pet.facing * r * 0.65, oy = pet.y - r * 1.5;"
    new_attack_draw = (
        "const isKame = (style === 'kamehameha' || isBoss);\n"
        "        const ox = pet.x + pet.facing * r * (isKame ? 0.68 : 1.10);\n"
        "        const oy = pet.y - r * (isKame ? 1.53 : 1.23);"
    )
    content = content.replace(old_attack_draw, new_attack_draw, 1)

    # 3. Update voice lines
    old_voice = (
        '      play: ["KAMEHAMEHA time!", "Let\'s see what you got!", "Powering up to the max!", "Here I come!"],\n'
        '      working: ["Gathering ki...", "KA... ME... HA... ME...", "Focusing all my power...", "Almost charged!"],\n'
        '      done: ["And that is that!", "We won!", "Awesome teamwork!", "Now where\'s the feast?"],\n'
        '      testFail: ["Whoa, they hit hard!", "Ouch, all of them at once!", "Don\'t give up! Stand back up!"],\n'
        '      testPass: ["KA-ME-HA-ME-HA! Total wipeout!", "All green! Flawless victory!", "Not one left standing!"],'
    )
    new_voice = (
        '      play: ["Let\'s see what you got!", "Bug hunting time!", "Nimbus, full throttle!", "Here I come!"],\n'
        '      working: ["Focusing hard...", "Keep typing, partner!", "I\'m keeping watch!", "Building up strong discipline!", "Almost done!"],\n'
        '      done: ["And that is that!", "We won!", "Awesome teamwork!", "Now where\'s the feast?"],\n'
        '      testFail: ["Whoa, they hit hard!", "Ouch, all of them at once!", "Don\'t give up! Stand back up!"],\n'
        '      testPass: ["All green! Flawless victory!", "Not one bug left standing!", "We did it, partner! All tests passed!"],'
    )
    content = content.replace(old_voice, new_voice, 1)

    # Also clean up sleepy "Resting the ki..." -> "Resting up..."
    content = content.replace('"Resting the ki..."', '"Resting up..."', 1)

    # 4. Combat audio & speech triggers
    old_charge_sound = "if (resolved && resolved.sound === 'kameCharge') audio.kameCharge();"
    new_charge_sound = (
        "if (resolved && resolved.sound === 'kameCharge') {\n"
        "          audio.kameCharge();\n"
        '          if (state.species === \'goku\') say("KA... ME... HA... ME...", Math.round(pet.zapFull * 1000) + 150);\n'
        "        }"
    )
    content = content.replace(old_charge_sound, new_charge_sound, 1)

    old_fire_sound = (
        "if (shotStyle === 'kamehameha') audio.kameFire();\n"
        "          else if (shotStyle === 'kiball') audio.kiBlast();"
    )
    new_fire_sound = (
        "if (shotStyle === 'kamehameha') {\n"
        "            audio.kameFire();\n"
        '            if (state.species === \'goku\') say("HA---!", 1400);\n'
        "          } else if (shotStyle === 'kiball') {\n"
        "            audio.kiBlast();\n"
        "            if (state.species === 'goku' && Math.random() < 0.75) {\n"
        '              say(pick(["Ha!", "Take this!", "Ki blast!", "Gotcha!"]), 1000);\n'
        "            }\n"
        "          }"
    )
    content = content.replace(old_fire_sound, new_fire_sound, 1)

    # 5. drawGoku() sprite selection
    old_sprite_select = "const sprite = isFlying ? gokuImgFly : gokuImgIdle;"
    new_sprite_select = (
        "let sprite = gokuImgIdle;\n"
        "    let targetW = r * 2.5;\n"
        "    let yOffset = 0.86;\n"
        "    if (charging && isKame) {\n"
        "      sprite = gokuImgKameCharge;\n"
        "      targetW = r * 2.65;\n"
        "      yOffset = 0.86;\n"
        "    } else if (firing && isKame) {\n"
        "      sprite = gokuImgKameFire;\n"
        "      targetW = r * 3.25;\n"
        "      yOffset = 0.85;\n"
        "    } else if (firing || charging) {\n"
        "      sprite = gokuImgKiBlast;\n"
        "      targetW = r * 3.05;\n"
        "      yOffset = 0.86;\n"
        "    } else if (isFlying) {\n"
        "      sprite = gokuImgFly;\n"
        "      targetW = r * 2.75;\n"
        "      yOffset = 0.88;\n"
        "    }"
    )
    content = content.replace(old_sprite_select, new_sprite_select, 1)

    old_draw_block = (
        "        // Maintain the EXACT same large heroic size whether sitting idle or flying/dragging\n"
        "        const isFlySprite = (sprite === gokuImgFly);\n"
        "        const targetW = r * (isFlySprite ? 2.75 : 2.5);\n"
        "        const targetH = targetW * (sh / sw);\n\n"
        "        // Cloud base alignment offset: aligns the cloud at the exact same grounded origin\n"
        "        const yOffset = isFlySprite ? 0.88 : 0.86;\n"
        "        ctx.drawImage(sprite, -targetW / 2, -targetH * yOffset, targetW, targetH);"
    )
    new_draw_block = (
        "        const targetH = targetW * (sh / sw);\n"
        "        ctx.drawImage(sprite, -targetW / 2, -targetH * yOffset, targetW, targetH);"
    )
    content = content.replace(old_draw_block, new_draw_block, 1)

    # 6. Align dynamic overlays to outstretched hands
    old_chg_sphere = (
        "const pulse = r * (0.28 + grow * 0.24 + Math.sin(t * 30) * 0.06);\n"
        "        const kg = ctx.createRadialGradient(r * 0.45, -r * 0.08, 2, r * 0.45, -r * 0.08, pulse);"
    )
    new_chg_sphere = (
        "const pulse = r * (0.28 + grow * 0.24 + Math.sin(t * 30) * 0.06);\n"
        "        const kg = ctx.createRadialGradient(r * 0.02, -r * 1.20, 2, r * 0.02, -r * 1.20, pulse);"
    )
    content = content.replace(old_chg_sphere, new_chg_sphere, 1)
    content = content.replace("ctx.arc(r * 0.45, -r * 0.08, pulse, 0, Math.PI * 2);", "ctx.arc(r * 0.02, -r * 1.20, pulse, 0, Math.PI * 2);", 1)

    old_fire_muzzle = (
        "const mrad = r * (0.85 + Math.sin(t * 40) * 0.15);\n"
        "        const mg = ctx.createRadialGradient(r * 0.65, -r * 0.12, 3, r * 0.65, -r * 0.12, mrad);"
    )
    new_fire_muzzle = (
        "const mrad = r * (0.85 + Math.sin(t * 40) * 0.15);\n"
        "        const mg = ctx.createRadialGradient(r * 0.68, -r * 1.53, 3, r * 0.68, -r * 1.53, mrad);"
    )
    content = content.replace(old_fire_muzzle, new_fire_muzzle, 1)
    content = content.replace("ctx.arc(r * 0.65, -r * 0.12, mrad, 0, Math.PI * 2);", "ctx.arc(r * 0.68, -r * 1.53, mrad, 0, Math.PI * 2);", 1)

    old_ki_flash = (
        "const krad = r * (0.48 + Math.sin(t * 35) * 0.08);\n"
        "        const kg = ctx.createRadialGradient(r * 0.75, -r * 0.18, 2, r * 0.75, -r * 0.18, krad);"
    )
    new_ki_flash = (
        "const krad = r * (0.48 + Math.sin(t * 35) * 0.08);\n"
        "        const kg = ctx.createRadialGradient(r * 1.10, -r * 1.23, 2, r * 1.10, -r * 1.23, krad);"
    )
    content = content.replace(old_ki_flash, new_ki_flash, 1)
    content = content.replace("ctx.arc(r * 0.75, -r * 0.18, krad, 0, Math.PI * 2);", "ctx.arc(r * 1.10, -r * 1.23, krad, 0, Math.PI * 2);", 1)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully patched {filepath}!")
