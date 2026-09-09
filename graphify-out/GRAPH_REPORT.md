# Graph Report - .  (2026-09-09)

## Corpus Check
- 140 files · ~488,531 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 795 nodes · 1552 edges · 100 communities (78 shown, 22 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 163 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Overlay bug-hunt renderer (Swift)
- CIWatcher: GitHub Actions/deploys
- ClaudeWatcher: Claude session tracking
- GitWatcher: reflog tailing
- Pikachu sprite art pipeline
- Build/install/lint tooling
- Goku art patch scripts
- App menu bar (AppDelegate)
- Pet window physics (AppDelegate)
- Control panel payload wiring
- AGENTS.md: art & concurrency lessons
- Demo/icon/GIF build scripts
- bitling.html core engine subsystems
- ControlPanel WKWebView bridge
- AGENTS.md: adding a pet
- README: features overview
- Kaiju cross-layer test suite
- Mario test suite
- Pet.html Playwright verification scripts
- Ronaldo test suite
- AGENTS.md: GitHub without gh CLI
- App icon generator (makeicon.swift)
- web/panel.html control room page
- GitHooks: global git hooks install
- AGENTS.md: verification philosophy
- check_bubble_gap.mjs QA tool
- Iron Man test suite
- Naruto test suite
- Goku test suite
- AppDelegate window/dock behavior
- Pikachu test suite
- Goku/Naruto avatars & spritesheets
- Kaiju gait/foot-pose invariants
- bitling CLI script
- Flight state enum
- Dragon/Robot avatars
- Mario 3D sprite bundle build
- lint.mjs entry point
- test_demo.mjs smoke test
- Kaiju/Rumble avatar & demo GIF
- Goku demo GIF & background art
- OpenPets Goku spritesheet bundle
- Mario/Ronaldo avatars
- Pikachu/Nimbo avatars
- Deploy reaction screenshot
- Bug-hunt desktop overlay screenshot
- Flight mode screenshot
- Affection reaction screenshot
- Parachute throw screenshot
- Git push reaction screenshot
- macOS permission prompt screenshot
- renderoverlay.swift verification harness
- Mario sprite bundle scripts (16-bit vs 3D)
- Iron Man avatar
- Unboxing screenshot
- Claude reaction icon
- Git commit reaction screenshot
- Debug/bug-squash screenshot
- Pat-received demo GIF
- Sleep state screenshot
- Tests-failed screenshot
- Tests-passed screenshot

## God Nodes (most connected - your core abstractions)
1. `AppDelegate` - 89 edges
2. `GitWatcher` - 47 edges
3. `OverlayView` - 41 edges
4. `CIWatcher` - 32 edges
5. `GitEvent` - 28 edges
6. `Overlay (controller)` - 27 edges
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
- **Pre-Completion Verification Gate (lint, test, bubble-gap, build)** — agents_before_you_say_it_works, tools_check_bubble_gap_mjs, build_sh, agents_launch_race [EXTRACTED 0.90]
- **Three Regressions Fixed During Godzilla Plan Review** — godzilla_verification_results, godzilla_native_orange_fire_bug, godzilla_hovering_shadow_bug, godzilla_throw_bounds_bug [EXTRACTED 0.85]
- **Tag-Triggered Release Pipeline** — readme_build_from_source, release_sh, github_workflows_release_workflow, github_release_notes_template [EXTRACTED 0.85]
- **Small-bug vs boss-bug dual attack resolve()** — web_bitling_species_goku, web_bitling_species_pikachu, web_bitling_species_ironman, web_bitling_species_ronaldo, web_bitling_species_naruto, web_bitling_species_mario, web_bitling_attack_system [INFERRED 0.85]
- **Ground-kind species (stand on dock)** — web_bitling_species_robot, web_bitling_species_pikachu, web_bitling_species_kaiju, web_bitling_species_ronaldo, web_bitling_species_naruto, web_bitling_species_mario [INFERRED 0.70]
- **Float-kind species (hover in place)** — web_bitling_species_dragon, web_bitling_species_rider, web_bitling_species_goku, web_bitling_species_ironman [INFERRED 0.70]
- **Pop-culture licensed character species** — web_bitling_species_goku, web_bitling_species_pikachu, web_bitling_species_ironman, web_bitling_species_ronaldo, web_bitling_species_naruto, web_bitling_species_mario [INFERRED 0.60]

## Communities (100 total, 22 thin omitted)

### Community 0 - "Overlay bug-hunt renderer (Swift)"
Cohesion: 0.12
Nodes (28): CGContext, CGPoint, NSColor, NSView, WKScriptMessage, WKUserContentController, Beam, Beetle (+20 more)

### Community 1 - "CIWatcher: GitHub Actions/deploys"
Cohesion: 0.08
Nodes (28): Foundation, LocalizedError, Security, CIWatcher, Any, Bool, Data, Date (+20 more)

### Community 2 - "ClaudeWatcher: Claude session tracking"
Cohesion: 0.08
Nodes (26): AppKit, ISO8601DateFormatter, ClaudeWatcher, .activeSessionCount, Session, Any, Bool, Date (+18 more)

### Community 3 - "GitWatcher: reflog tailing"
Cohesion: 0.13
Nodes (17): GitStatus, .asDictionary, GitWatcher, .repositoryCount, .roots, ReflogLine, Date, Int (+9 more)

### Community 4 - "Pikachu sprite art pipeline"
Cohesion: 0.11
Nodes (28): docs/index.html (Deployed Copy), Pikachu Pristine Sprite Set (idle/run/dangle), Apply Goku Combat Animations, Apply Goku Drag/Flight Physics Fix, Apply HD Goku Sprites, Apply HD Iron Man Sprites & Combat Overhaul, Apply Pure Anime Pikachu Voice Clips, Build Pikachu Species Bundle (+20 more)

### Community 5 - "Build/install/lint tooling"
Cohesion: 0.08
Nodes (23): compile(), build.sh script, eslint, globals, install.sh script, devDependencies, eslint, globals (+15 more)

### Community 6 - "Goku art patch scripts"
Cohesion: 0.08
Nodes (17): Path, run_fix(), main(), main(), get_b64_resized(), main(), chroma_key(), main() (+9 more)

### Community 7 - "App menu bar (AppDelegate)"
Cohesion: 0.15
Nodes (12): NSApplicationDelegate, NSMenu, NSMenuDelegate, NSMenuItem, NSStatusItem, AppDelegate, CGFloat, Date (+4 more)

### Community 8 - "Pet window physics (AppDelegate)"
Cohesion: 0.12
Nodes (11): Notification, NSEvent, NSSize, NSWindow, PetWindow, .canBecomeKey, .canBecomeMain, NSPoint (+3 more)

### Community 9 - "Control panel payload wiring"
Cohesion: 0.18
Nodes (9): ServiceManagement, ClaudeHooks, .command, .settingsURL, jsString(), PetSnapshot, Any, Int (+1 more)

### Community 10 - "AGENTS.md: art & concurrency lessons"
Cohesion: 0.11
Nodes (21): Anything Derived From the Art Must Be Measured Off the Art, kaijuPose() function, Kaiju Breath Mispositioned From Hard-Coded Constant, Non-Unique String-Replace Corruption Bug, line(key) Shuffle Bag Keyed by Species+Phrase, Working Alongside Other Agents, Concurrent Goku Attack Renderer Edit (preserved), Reference Illustration Audit (color/shape mismatches) (+13 more)

### Community 11 - "Demo/icon/GIF build scripts"
Cohesion: 0.15
Nodes (21): Antigravity Brain artifact directory (raw AI sprite source), docs/index.html (GitHub Pages demo), /tmp/ironman_data.json (Iron Man asset bundle), Extract Authentic Mario Assets, Extract Pikachu Sprites, Make GitHub Pages Demo, Make README GIF, Make App Icon (+13 more)

### Community 12 - "bitling.html core engine subsystems"
Cohesion: 0.26
Nodes (21): Attack/combat resolution (species().attack), Bug spawn/release system (spawnBug/releaseBugs), window.__bitling verification harness, drawPet() species draw dispatch, frame()/update()/draw() main loop, handleGitEvent() dev-signal reactions, HOST native/webkit message bridge, resize() canvas/layout subsystem (+13 more)

### Community 13 - "ControlPanel WKWebView bridge"
Cohesion: 0.14
Nodes (12): NSObject, ControlPanel, .isOpen, Bool, NSWindow, Void, WKNavigation, WKScriptMessage (+4 more)

### Community 14 - "AGENTS.md: adding a pet"
Cohesion: 0.14
Nodes (14): Adding a Pet (SPECIES registration), Assets and Likeness Policy, canFire Grounded Gate, defineSpecies() function, Floater Can Hit the Ceiling, Generated Files Must Not Be Hand-Edited, Movement Rules (limb hinge, trail, canFire), Working on Bitling (AGENTS.md) (+6 more)

### Community 15 - "README: features overview"
Cohesion: 0.15
Nodes (11): apiData(_:) function, bitling CLI command, Bug and Boss Hunting System, Three CI/Deploy Data Sources, Optional Claude Code Hooks, Claude Code Session Reactions, What Connects to Where (privacy/network), Screen-Wide Desktop Bug Overlay (+3 more)

### Community 16 - "Kaiju cross-layer test suite"
Cohesion: 0.17
Nodes (13): Pattern: window.petNative.setSpecies() must update state.species and be reversible (switch away then back), Invariant: opaque character pixels must never touch the canvas edge, so the desktop transparent window never clips the sprite, Invariant: native host 'walking' distance drives pet.stride using the same stance/swing ratio (0.72/0.62) as the gait function, Invariant: the native Swift beam renderer must render the species' attack style with a substantial cyan pixel core, matching the web-declared style id, OverlayView (native Swift beam/attack renderer), kaiju-browser.test.mjs (Godzilla desktop-window render suite), run, kaiju-native.test.mjs (native Swift atomic-breath color test) (+5 more)

### Community 17 - "Mario test suite"
Cohesion: 0.15
Nodes (13): Invariant: triggerMarioCommitPowerUp() activates marioState.qblockActive and scoreMarioWarpPipe() activates marioState.pipeActive, Invariant: attack style depends on marioState.stage (stomp at stage 0, fireball at Fire Mario / boss), not just the boss flag alone, mario.test.mjs (Super Mario test suite), run, drawMario() render function, drawMarioAttack() attack render function, fireball attack style (Fire Mario / boss), Mario species definition (SPECIES.mario, kind:'ground') (+5 more)

### Community 18 - "Pet.html Playwright verification scripts"
Cohesion: 0.23
Nodes (12): Resources/pet.html (OpenPets Dev Renderer), Build OpenPets Kid Goku Spritesheet Bundle, Capture Pikachu Visual States, Capture Goku Preview Screenshots, Check Speech Bubble Gap QA Tool, test_bug_combat.mjs – manual verification of Goku ki-blast/kamehameha combat, test_drag.mjs – Iron Man drag-direction visual verification, test_drag_visuals.mjs – Goku mouse-drag flight banking verification (+4 more)

### Community 19 - "Ronaldo test suite"
Cohesion: 0.17
Nodes (12): Invariant: the free ronaldoBall obeys gravity/velocity physics, kills bugs on strike with a pop-up rebound, and scoreRonaldoGoal() drives a shot that bulges the net, ronaldo.test.mjs (Cristiano Ronaldo test suite), run, drawRonaldo() render function, drawRonaldoAttack() projectile attack render function, knuckleball attack style (Ronaldo small-bug), Ronaldo species definition (SPECIES.ronaldo, kind:'ground'), ronaldoBall (free soccer-ball physics object) (+4 more)

### Community 21 - "AGENTS.md: GitHub without gh CLI"
Cohesion: 0.20
Nodes (8): GitHub OAuth Device-Flow Fallback, GitHub Without the gh CLI, Ad-Hoc Re-Signing Invalidates Keychain Access, The Launch Race (build.sh timing bug), Release Notes Template, Universal Binary arch Check (lipo), Release GitHub Actions Workflow, Build From Source Instructions

### Community 22 - "App icon generator (makeicon.swift)"
Cohesion: 0.29
Nodes (9): Cocoa, NSBezierPath, render(), rgb(), rounded(), CGFloat, Data, Int (+1 more)

### Community 23 - "web/panel.html control room page"
Cohesion: 0.20
Nodes (10): Control Room UI Description, Lint Entry Point, all:unset Resets box-sizing Gotcha, Bitling Control Room Page, drawPortrait() function, drawTimeline() function, frame(now) animation loop, web/panel.html (control panel) (+2 more)

### Community 24 - "GitHooks: global git hooks install"
Cohesion: 0.38
Nodes (4): GitHooks, .directory, HooksError, .errorDescription

### Community 25 - "AGENTS.md: verification philosophy"
Cohesion: 0.22
Nodes (8): Before You Say It Works (verification gate), Measure the Thing the User Can See, petNative bridge API, Verifying Without Screen Capture, Hovering-Shadow Regression Fixed, Native Orange-Fire Renderer Regression Fixed, Inflated Throw Bounds Fixed, Godzilla Plan Verification Results

### Community 26 - "check_bubble_gap.mjs QA tool"
Cohesion: 0.25
Nodes (8): args, debug, HERE, measure(), PAGE, results, SEED, wanted

### Community 27 - "Iron Man test suite"
Cohesion: 0.25
Nodes (8): ironman.test.mjs (Iron Man test suite), run, drawIronMan() render function, Iron Man species definition (SPECIES.ironman, kind:'float', accent #ff2222), jarvisAsYouWish() voice/audio synth, jarvisOnline() voice/audio synth, repulsor attack style (Iron Man small-bug), unibeam attack style (Iron Man boss)

### Community 28 - "Naruto test suite"
Cohesion: 0.25
Nodes (8): naruto.test.mjs (Naruto Uzumaki test suite), run, make_pet_html.py (build script generating pet.html from bitling.html), drawNaruto() render function, drawNarutoAttack() projectile attack render function, Naruto species definition (SPECIES.naruto, kind:'ground'), rasenshuriken attack style (Naruto boss), shuriken attack style (Naruto small-bug)

### Community 29 - "Goku test suite"
Cohesion: 0.29
Nodes (7): Pattern: species.attack.resolve(isBoss) must return a distinct attack style (and sound) for small bugs vs boss bugs, goku.test.mjs (Kid Goku test suite), run, drawGoku() render function, Goku species definition (SPECIES.goku, kind:'float'), kamehameha attack style (Goku boss), kiball attack style (Goku small-bug)

### Community 30 - "AppDelegate window/dock behavior"
Cohesion: 0.29
Nodes (3): NSApplication, Bool, URL

### Community 31 - "Pikachu test suite"
Cohesion: 0.29
Nodes (7): Pattern: every named pose must render without a thrown error and must paint a minimum count of opaque pixels (species not invisible/degenerate), pikachu.test.mjs (Pikachu test suite), run, drawPikachu() render function, electroball attack style (Pikachu small-bug), Pikachu species definition (SPECIES.pikachu, kind:'ground'), thunderbolt attack style (Pikachu boss)

### Community 32 - "Goku/Naruto avatars & spritesheets"
Cohesion: 0.33
Nodes (6): Goku Avatar, Naruto Avatar, Goku Sprite Sheet (Flying Nimbus, 64-frame grid), Pikachu Sprite Sheet, Goku (species), Naruto (species)

### Community 33 - "Kaiju gait/foot-pose invariants"
Cohesion: 0.33
Nodes (5): Invariant: feet lift only during recovery and never both leave the floor at once, Invariant: a planted (stance) foot cancels forward travel throughout the stance phase, Invariant: the walk loop is continuous (no pop/jump) at lift-off and touchdown phase boundaries, kaiju.test.mjs (Godzilla gait/foot-pose unit test), kaijuFootPose(phase) stance/swing gait function

### Community 34 - "bitling CLI script"
Cohesion: 0.60
Nodes (3): bitling script, send(), usage()

### Community 35 - "Flight state enum"
Cohesion: 0.40
Nodes (5): Flight, flying, hovering, landing, none

### Community 36 - "Dragon/Robot avatars"
Cohesion: 0.50
Nodes (4): Dragon Avatar, Robot Avatar, Dragon (species), Robot (species)

### Community 37 - "Mario 3D sprite bundle build"
Cohesion: 0.83
Nodes (3): load_and_crop(), main(), to_webp_b64()

### Community 38 - "lint.mjs entry point"
Cohesion: 0.50
Nodes (3): errors, eslint, results

### Community 40 - "Kaiju/Rumble avatar & demo GIF"
Cohesion: 0.67
Nodes (3): Kaiju Avatar, Rumble Kaiju Animated Demo, Kaiju Species (codename Rumble)

### Community 41 - "Goku demo GIF & background art"
Cohesion: 0.67
Nodes (3): Goku on Flying Nimbus Animated Demo, Goku Demo Background Landscape, Goku/Dragon Ball themed pet skin or Easter egg

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
- **188 isolated node(s):** `.activeSessionCount`, `AppKit`, `.asDictionary`, `.asJSON`, `.isOpen` (+183 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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
- **Why does `AppDelegate` connect `App menu bar (AppDelegate)` to `Overlay bug-hunt renderer (Swift)`, `CIWatcher: GitHub Actions/deploys`, `ClaudeWatcher: Claude session tracking`, `GitWatcher: reflog tailing`, `Flight state enum`, `Build/install/lint tooling`, `Pet window physics (AppDelegate)`, `Control panel payload wiring`, `ControlPanel WKWebView bridge`, `Panel action handlers (pat/feed/rename)`, `AppDelegate window/dock behavior`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `GitWatcher` connect `GitWatcher: reflog tailing` to `CIWatcher: GitHub Actions/deploys`, `ClaudeWatcher: Claude session tracking`, `Build/install/lint tooling`, `App menu bar (AppDelegate)`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._