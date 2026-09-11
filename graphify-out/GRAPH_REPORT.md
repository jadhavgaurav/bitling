# Graph Report - Bitling  (2026-09-11)

## Corpus Check
- 116 files · ~767,572 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 853 nodes · 1598 edges · 128 communities (87 shown, 41 thin omitted)
- Extraction: 89% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 167 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b6c296e4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- OverlayView
- CIWatcher
- ClaudeWatcher
- GitWatcher
- web/bitling.html (Bitling Pet Renderer)
- package.json
- Path
- PetWindow
- Clean Pikachu Charge Sprite (White/Gray Pass 2)
- build.sh
- Pet Species Roster Table
- web/bitling.html (shared creature page)
- drawPet() species draw dispatch
- Bitling README Overview
- Working on Bitling (AGENTS.md)
- Bitling Control Room Page
- kaiju-browser.test.mjs
- mario.test.mjs
- rules/graphify.md
- ronaldo.test.mjs
- workflows/graphify.md
- GitHub Without the gh CLI
- render
- Godzilla Plan Verification Results
- 2026-09-09-shenron.md
- verify_spiderman_visuals.mjs
- check_bubble_gap.mjs
- ironman.test.mjs
- naruto.test.mjs
- goku.test.mjs
- shenron-native.test.mjs
- pikachu.test.mjs
- Goku Avatar
- kaiju.test.mjs
- bitling
- Flight
- Dragon Avatar
- build_mario_3d_bundle.py
- lint.mjs
- test_demo.mjs
- Kaiju Species (codename Rumble)
- Goku on Flying Nimbus Animated Demo
- build_openpets_bundle.mjs
- Mario Avatar
- Pikachu Avatar
- Deploy Reaction Screenshot
- Full-Screen Bug-Hunt Stage Overlay
- Pet Flight Mode Screenshot
- Affectionate/Happy Pet State
- Parachute/Parafoil Throw Animation
- Git Push Rocket Reaction
- macOS Permission Request Prompt
- Sources/Overlay.swift (OverlayView implementation compiled by renderoverlay.swift)
- Build Mario 3D Sprite Bundle
- Iron Man Avatar
- A New Box Arrives
- Claude Code Reaction Icon
- Git Commit Reaction Bubble
- Bug Squashing Reaction
- Pat Received Night Scene
- Sleep State Screenshot ("goodnight, human")
- Tests Failed Screenshot ("3 tests failing in api")
- Tests Passed Screenshot ("all bugs squashed!")
- shenron.test.mjs
- capture_shenron.mjs
- README.md
- ControlPanel
- verify_hd_pikachu.mjs
- test_all_goku_visuals.mjs
- 2026-09-10-calm-movement.md
- calm-movement.test.mjs
- spiderman.test.mjs
- verify_thor_visuals.mjs
- thor.test.mjs
- petting-reactions.test.mjs
- AppDelegate
- String
- GitHubAuth
- .menuNeedsUpdate
- verify_spiderman_sleep_visuals.mjs
- spiderman_sleep.test.mjs
- .buildWebView

## God Nodes (most connected - your core abstractions)
1. `AppDelegate` - 92 edges
2. `GitWatcher` - 48 edges
3. `OverlayView` - 41 edges
4. `CIWatcher` - 32 edges
5. `GitEvent` - 28 edges
6. `Overlay` - 27 edges
7. `ClaudeWatcher` - 25 edges
8. `Beam` - 23 edges
9. `Bitling README Overview` - 23 edges
10. `ControlPanel` - 19 edges

## Surprising Connections (you probably didn't know these)
- `OverlayView` --semantically_similar_to--> `Goku pet config`  [INFERRED] [semantically similar]
  Sources/Overlay.swift → Resources/pets/goku/pet.json
- `OverlayView` --semantically_similar_to--> `Pikachu pet config`  [INFERRED] [semantically similar]
  Sources/Overlay.swift → Resources/pets/pikachu/pet.json
- `Draw Realistic Toriyama Goku Prototype` --conceptually_related_to--> `web/bitling.html (Bitling Pet Renderer)`  [INFERRED]
  Tools/draw_real_goku.mjs → web/bitling.html
- `ronaldo_sprites.json – Ronaldo pet sprite atlas (base64 PNGs)` --conceptually_related_to--> `web/bitling.html (Bitling Pet Renderer)`  [INFERRED]
  Tools/ronaldo_sprites.json → web/bitling.html
- `Lint Entry Point` --references--> `web/bitling.html (shared creature page)`  [EXTRACTED]
  Tools/lint.mjs → web/bitling.html

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Watcher-to-pet event pipeline via GitEvent** — sources_gitwatcher_gitwatcher, sources_ciwatcher_ciwatcher, sources_claudewatcher_claudewatcher, sources_main_appdelegate, sources_gitwatcher_gitevent [INFERRED 0.85]
- **GitHub device-flow / gh CLI authentication** — sources_githubauth_githubauth, sources_ciwatcher_ciwatcher, sources_main_appdelegate [INFERRED 0.80]
- **Build, package, and install chain** — build, release, install, package [EXTRACTED 0.85]
- **Goku Flight Physics + HD Sprite + Combat Upgrade Pipeline** — tools_apply_goku_drag_fix_script, tools_apply_hd_goku_script, tools_apply_combat_animations_script, web_bitling_html_target [INFERRED 0.75]
- **Pikachu Charge Sprite Iterative Cleanup Pipeline** — tools_clean_charge_base_script, tools_clean_charge_base2_script, tools_clean_charge_final_script, tools_clean_charge_white_script, tools_clean_gap_script, tools_clean_stray_script, tools_clean_pikachu_sprites_script [INFERRED 0.85]
- **Pikachu Species Integration Pipeline** — tools_clean_pikachu_sprites_script, tools_build_pikachu_bundle_script, tools_apply_pure_anime_voices_script, tools_capture_pikachu_visuals_script [INFERRED 0.75]
- **NES/SNES retro Mario asset pipeline** — tools_extract_authentic_mario_assets_py, tools_mario_sprites_json, tools_patch_mario_precision_py [EXTRACTED 0.90]
- **3D Cinema-style Mario asset pipeline** — tools_mario_3d_sprites_json, tools_patch_mario_3d_py, tools_patch_mario_universal_py [INFERRED 0.85]
- **Sequential web/bitling.html feature migrations** — tools_patch_git_edition_py, tools_patch_bitling_py, tools_patch_claude_py, tools_patch_clipping_py [INFERRED 0.80]
- **Flight/descent feature build-out: robot flight, emergency chute, parafoil redesign** — tools_patch_motion_script, tools_patch_parachute_script, tools_patch_parafoil_script [INFERRED 0.85]
- **Goku art iteration: vector prototype to pixel-sprite render test to final right-facing integration** — tools_test_goku_vector_script, tools_test_sprite_renderer_script, tools_update_right_facing_goku_script [INFERRED 0.75]
- **Goku combat behavior verified against pet.html via Playwright across multiple ad hoc scripts** — tools_test_bug_combat_script, tools_test_goku_combat_script, tools_verify_live_hunt_script [INFERRED 0.70]
- **Small-vs-boss dual attack resolution tested identically across five species** — tests_goku_test, tests_ironman_test, tests_naruto_test, tests_pikachu_test, tests_ronaldo_test [INFERRED 0.85]
- **petNative.setSpecies() reversible host-bridge switching tested identically across species suites** — tests_goku_test, tests_ironman_test, tests_naruto_test, tests_pikachu_test, tests_ronaldo_test, tests_kaiju_browser_test [INFERRED 0.85]
- **Godzilla is verified across three independent layers: pure gait math (unit), full browser rendering/host-bridge (integration), and the native Swift overlay renderer (native)** — tests_kaiju_test, tests_kaiju_browser_test, tests_kaiju_native_test [INFERRED 0.80]
- **Pre-Completion Verification Gate (lint, test, bubble-gap, build)** — agents_before_you_say_it_works, tools_check_bubble_gap_mjs, build, agents_launch_race [EXTRACTED 0.90]
- **Three Regressions Fixed During Godzilla Plan Review** — godzilla_verification_results, godzilla_native_orange_fire_bug, godzilla_hovering_shadow_bug, godzilla_throw_bounds_bug [EXTRACTED 0.85]
- **Tag-Triggered Release Pipeline** — readme_build_from_source, release, github_workflows_release_workflow, github_release_notes_template [EXTRACTED 0.85]
- **Small-bug vs boss-bug dual attack resolve()** — web_bitling_species_goku, web_bitling_species_pikachu, web_bitling_species_ironman, web_bitling_species_ronaldo, web_bitling_species_naruto, web_bitling_species_mario, web_bitling_attack_system [INFERRED 0.85]
- **Ground-kind species (stand on dock)** — web_bitling_species_robot, web_bitling_species_pikachu, web_bitling_species_kaiju, web_bitling_species_ronaldo, web_bitling_species_naruto, web_bitling_species_mario [INFERRED 0.70]
- **Float-kind species (hover in place)** — web_bitling_species_dragon, web_bitling_species_rider, web_bitling_species_goku, web_bitling_species_ironman [INFERRED 0.70]
- **Pop-culture licensed character species** — web_bitling_species_goku, web_bitling_species_pikachu, web_bitling_species_ironman, web_bitling_species_ronaldo, web_bitling_species_naruto, web_bitling_species_mario [INFERRED 0.60]

## Communities (128 total, 41 thin omitted)

### Community 0 - "OverlayView"
Cohesion: 0.12
Nodes (28): CGContext, CGPoint, NSColor, NSView, WKScriptMessage, WKUserContentController, Beam, Beetle (+20 more)

### Community 1 - "CIWatcher"
Cohesion: 0.08
Nodes (25): AppKit, Foundation, CIWatcher, Any, Bool, Data, Date, Set (+17 more)

### Community 2 - "ClaudeWatcher"
Cohesion: 0.18
Nodes (13): ISO8601DateFormatter, ClaudeWatcher, .activeSessionCount, Session, Any, Bool, Date, Int (+5 more)

### Community 3 - "GitWatcher"
Cohesion: 0.13
Nodes (16): GitStatus, .asDictionary, GitWatcher, .repositoryCount, .roots, ReflogLine, Date, Int (+8 more)

### Community 4 - "web/bitling.html (Bitling Pet Renderer)"
Cohesion: 0.09
Nodes (32): docs/index.html (Deployed Copy), Resources/pet.html (OpenPets Dev Renderer), Apply Goku Combat Animations, Apply Goku Drag/Flight Physics Fix, Apply HD Goku Sprites, Apply HD Iron Man Sprites & Combat Overhaul, Apply Pure Anime Pikachu Voice Clips, Build OpenPets Kid Goku Spritesheet Bundle (+24 more)

### Community 5 - "package.json"
Cohesion: 0.12
Nodes (16): eslint, globals, devDependencies, eslint, globals, playwright, engines, node (+8 more)

### Community 6 - "Path"
Cohesion: 0.08
Nodes (17): Path, run_fix(), main(), main(), get_b64_resized(), main(), chroma_key(), main() (+9 more)

### Community 7 - "PetWindow"
Cohesion: 0.13
Nodes (12): NSEvent, NSWindow, PetWindow, .canBecomeKey, .canBecomeMain, CGFloat, NSPoint, NSRect (+4 more)

### Community 8 - "Clean Pikachu Charge Sprite (White/Gray Pass 2)"
Cohesion: 0.29
Nodes (7): Clean Pikachu Charge Sprite (White/Gray Pass 2), Clean Pikachu Charge Sprite (Platform Pass), Clean Pikachu Charge Sprite (Final Coordinate Pass), Clean Pikachu Charge Sprite (Pure White Removal), Clean Gap Between Pikachu Feet, Clean All Pikachu Sprite Set, Clean Stray Pikachu Sprite Pixels

### Community 9 - "build.sh"
Cohesion: 0.18
Nodes (11): compile(), build.sh script, Release Notes Template, Universal Binary arch Check (lipo), Release GitHub Actions Workflow, install.sh script, Goku pet config, Pikachu pet config (+3 more)

### Community 10 - "Pet Species Roster Table"
Cohesion: 0.11
Nodes (21): Anything Derived From the Art Must Be Measured Off the Art, kaijuPose() function, Kaiju Breath Mispositioned From Hard-Coded Constant, Non-Unique String-Replace Corruption Bug, line(key) Shuffle Bag Keyed by Species+Phrase, Working Alongside Other Agents, Concurrent Goku Attack Renderer Edit (preserved), Reference Illustration Audit (color/shape mismatches) (+13 more)

### Community 11 - "web/bitling.html (shared creature page)"
Cohesion: 0.13
Nodes (24): Adding a Pet (SPECIES registration), defineSpecies() function, resize() Runs Before Late Species Definitions, Antigravity Brain artifact directory (raw AI sprite source), docs/index.html (GitHub Pages demo), /tmp/ironman_data.json (Iron Man asset bundle), Extract Authentic Mario Assets, Extract Pikachu Sprites (+16 more)

### Community 12 - "drawPet() species draw dispatch"
Cohesion: 0.26
Nodes (21): Attack/combat resolution (species().attack), Bug spawn/release system (spawnBug/releaseBugs), window.__bitling verification harness, drawPet() species draw dispatch, frame()/update()/draw() main loop, handleGitEvent() dev-signal reactions, HOST native/webkit message bridge, resize() canvas/layout subsystem (+13 more)

### Community 13 - "Bitling README Overview"
Cohesion: 0.15
Nodes (11): apiData(_:) function, bitling CLI command, Bug and Boss Hunting System, Three CI/Deploy Data Sources, Optional Claude Code Hooks, Claude Code Session Reactions, What Connects to Where (privacy/network), Screen-Wide Desktop Bug Overlay (+3 more)

### Community 14 - "Working on Bitling (AGENTS.md)"
Cohesion: 0.14
Nodes (15): Assets and Likeness Policy, Before You Say It Works (verification gate), canFire Grounded Gate, Floater Can Hit the Ceiling, Generated Files Must Not Be Hand-Edited, The Launch Race (build.sh timing bug), Movement Rules (limb hinge, trail, canFire), Working on Bitling (AGENTS.md) (+7 more)

### Community 15 - "Bitling Control Room Page"
Cohesion: 0.20
Nodes (10): Control Room UI Description, Lint Entry Point, all:unset Resets box-sizing Gotcha, Bitling Control Room Page, drawPortrait() function, drawTimeline() function, frame(now) animation loop, web/panel.html (control panel) (+2 more)

### Community 16 - "kaiju-browser.test.mjs"
Cohesion: 0.17
Nodes (11): Pattern: window.petNative.setSpecies() must update state.species and be reversible (switch away then back), Invariant: opaque character pixels must never touch the canvas edge, so the desktop transparent window never clips the sprite, Invariant: native host 'walking' distance drives pet.stride using the same stance/swing ratio (0.72/0.62) as the gait function, Invariant: the native Swift beam renderer must render the species' attack style with a substantial cyan pixel core, matching the web-declared style id, OverlayView (native Swift beam/attack renderer), run, run, atomic attack style (Kaiju, cyan breath beam) (+3 more)

### Community 17 - "mario.test.mjs"
Cohesion: 0.15
Nodes (12): Invariant: triggerMarioCommitPowerUp() activates marioState.qblockActive and scoreMarioWarpPipe() activates marioState.pipeActive, Invariant: attack style depends on marioState.stage (stomp at stage 0, fireball at Fire Mario / boss), not just the boss flag alone, run, drawMario() render function, drawMarioAttack() attack render function, fireball attack style (Fire Mario / boss), Mario species definition (SPECIES.mario, kind:'ground'), marioState (evolution stage tracker) (+4 more)

### Community 19 - "ronaldo.test.mjs"
Cohesion: 0.17
Nodes (11): Invariant: the free ronaldoBall obeys gravity/velocity physics, kills bugs on strike with a pop-up rebound, and scoreRonaldoGoal() drives a shot that bulges the net, run, drawRonaldo() render function, drawRonaldoAttack() projectile attack render function, knuckleball attack style (Ronaldo small-bug), Ronaldo species definition (SPECIES.ronaldo, kind:'ground'), ronaldoBall (free soccer-ball physics object), ronaldoGoal (goal-celebration state object) (+3 more)

### Community 21 - "GitHub Without the gh CLI"
Cohesion: 0.50
Nodes (3): GitHub OAuth Device-Flow Fallback, GitHub Without the gh CLI, Ad-Hoc Re-Signing Invalidates Keychain Access

### Community 22 - "render"
Cohesion: 0.29
Nodes (9): Cocoa, NSBezierPath, render(), rgb(), rounded(), CGFloat, Data, Int (+1 more)

### Community 23 - "Godzilla Plan Verification Results"
Cohesion: 0.40
Nodes (5): Measure the Thing the User Can See, Hovering-Shadow Regression Fixed, Native Orange-Fire Renderer Regression Fixed, Inflated Throw Bounds Fixed, Godzilla Plan Verification Results

### Community 26 - "check_bubble_gap.mjs"
Cohesion: 0.25
Nodes (8): args, debug, HERE, measure(), PAGE, results, SEED, wanted

### Community 27 - "ironman.test.mjs"
Cohesion: 0.25
Nodes (7): run, drawIronMan() render function, Iron Man species definition (SPECIES.ironman, kind:'float', accent #ff2222), jarvisAsYouWish() voice/audio synth, jarvisOnline() voice/audio synth, repulsor attack style (Iron Man small-bug), unibeam attack style (Iron Man boss)

### Community 28 - "naruto.test.mjs"
Cohesion: 0.25
Nodes (7): run, make_pet_html.py (build script generating pet.html from bitling.html), drawNaruto() render function, drawNarutoAttack() projectile attack render function, Naruto species definition (SPECIES.naruto, kind:'ground'), rasenshuriken attack style (Naruto boss), shuriken attack style (Naruto small-bug)

### Community 29 - "goku.test.mjs"
Cohesion: 0.29
Nodes (6): Pattern: species.attack.resolve(isBoss) must return a distinct attack style (and sound) for small bugs vs boss bugs, run, drawGoku() render function, Goku species definition (SPECIES.goku, kind:'float'), kamehameha attack style (Goku boss), kiball attack style (Goku small-bug)

### Community 31 - "pikachu.test.mjs"
Cohesion: 0.29
Nodes (6): Pattern: every named pose must render without a thrown error and must paint a minimum count of opaque pixels (species not invisible/degenerate), run, drawPikachu() render function, electroball attack style (Pikachu small-bug), Pikachu species definition (SPECIES.pikachu, kind:'ground'), thunderbolt attack style (Pikachu boss)

### Community 32 - "Goku Avatar"
Cohesion: 0.33
Nodes (6): Goku Avatar, Naruto Avatar, Goku Sprite Sheet (Flying Nimbus, 64-frame grid), Pikachu Sprite Sheet, Goku (species), Naruto (species)

### Community 33 - "kaiju.test.mjs"
Cohesion: 0.33
Nodes (4): Invariant: feet lift only during recovery and never both leave the floor at once, Invariant: a planted (stance) foot cancels forward travel throughout the stance phase, Invariant: the walk loop is continuous (no pop/jump) at lift-off and touchdown phase boundaries, kaijuFootPose(phase) stance/swing gait function

### Community 34 - "bitling"
Cohesion: 0.60
Nodes (3): bitling script, send(), usage()

### Community 35 - "Flight"
Cohesion: 0.40
Nodes (5): Flight, flying, hovering, landing, none

### Community 36 - "Dragon Avatar"
Cohesion: 0.50
Nodes (4): Dragon Avatar, Robot Avatar, Dragon (species), Robot (species)

### Community 37 - "build_mario_3d_bundle.py"
Cohesion: 0.83
Nodes (3): load_and_crop(), main(), to_webp_b64()

### Community 38 - "lint.mjs"
Cohesion: 0.50
Nodes (3): errors, eslint, results

### Community 40 - "Kaiju Species (codename Rumble)"
Cohesion: 0.67
Nodes (3): Kaiju Avatar, Rumble Kaiju Animated Demo, Kaiju Species (codename Rumble)

### Community 41 - "Goku on Flying Nimbus Animated Demo"
Cohesion: 0.67
Nodes (3): Goku on Flying Nimbus Animated Demo, Goku Demo Background Landscape, Goku/Dragon Ball themed pet skin or Easter egg

### Community 103 - "ControlPanel"
Cohesion: 0.12
Nodes (14): NSApplication, NSObject, NSSize, ControlPanel, .isOpen, Bool, NSWindow, Void (+6 more)

### Community 121 - "AppDelegate"
Cohesion: 0.14
Nodes (7): Notification, NSApplicationDelegate, NSMenuDelegate, NSStatusItem, AppDelegate, Date, Timer

### Community 122 - "String"
Cohesion: 0.14
Nodes (14): Double, ServiceManagement, ClaudeHooks, .command, .settingsURL, GitHooks, .directory, HooksError (+6 more)

### Community 123 - "GitHubAuth"
Cohesion: 0.14
Nodes (17): LocalizedError, Security, AuthError, denied, .errorDescription, expired, network, notConfigured (+9 more)

### Community 124 - ".menuNeedsUpdate"
Cohesion: 0.32
Nodes (3): NSMenu, NSMenuItem, Int

## Ambiguous Edges - Review These
- `Apply Goku Combat Animations` → `Apply HD Goku Sprites`  [AMBIGUOUS]
  Tools/apply_combat_animations.py · relation: conceptually_related_to
- `Apply Goku Drag/Flight Physics Fix` → `Draw Realistic Toriyama Goku Prototype`  [AMBIGUOUS]
  Tools/draw_real_goku.mjs · relation: semantically_similar_to
- `Make App Icon` → `Patch: Jelly/Egg to Bitling Robot/Box`  [AMBIGUOUS]
  Tools/makeicon.swift · relation: semantically_similar_to
- `Goku (Kid Goku)` → `Concurrent Goku Attack Renderer Edit (preserved)`  [AMBIGUOUS]
  docs/superpowers/plans/2026-09-08-godzilla-reference.md · relation: references
- `frame()/update()/draw() main loop` → `HOST native/webkit message bridge`  [AMBIGUOUS]
  web/bitling.html · relation: conceptually_related_to

## Knowledge Gaps
- **212 isolated node(s):** `.activeSessionCount`, `AppKit`, `.asDictionary`, `.asJSON`, `.isOpen` (+207 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **41 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Apply Goku Combat Animations` and `Apply HD Goku Sprites`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Apply Goku Drag/Flight Physics Fix` and `Draw Realistic Toriyama Goku Prototype`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `Make App Icon` and `Patch: Jelly/Egg to Bitling Robot/Box`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `Goku (Kid Goku)` and `Concurrent Goku Attack Renderer Edit (preserved)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `frame()/update()/draw() main loop` and `HOST native/webkit message bridge`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `AppDelegate` connect `AppDelegate` to `OverlayView`, `CIWatcher`, `ClaudeWatcher`, `GitWatcher`, `Flight`, `ControlPanel`, `PetWindow`, `build.sh`, `String`, `GitHubAuth`, `.menuNeedsUpdate`, `.buildWebView`?**
  _High betweenness centrality (0.159) - this node is a cross-community bridge._
- **Why does `Bitling README Overview` connect `Bitling README Overview` to `build.sh`, `Pet Species Roster Table`, `web/bitling.html (shared creature page)`, `Working on Bitling (AGENTS.md)`, `Bitling Control Room Page`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._