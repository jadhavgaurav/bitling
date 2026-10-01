# Graph Report - Bitling  (2026-09-18)

## Corpus Check
- 169 files · ~890,501 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1257 nodes · 2285 edges · 160 communities (102 shown, 58 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 144 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d2727759`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- OverlayView
- GitHubAuth
- ActivityEntry
- CIWatcher
- docs/index.html (Deployed Copy)
- scripts
- Path
- GitWatcher
- ActivityLog
- Release GitHub Actions Workflow
- Pet Species Roster Table
- Antigravity Brain artifact directory (raw AI sprite source)
- GitWatcher
- Bitling README Overview
- Working on Bitling (AGENTS.md)
- Lint Entry Point
- Pattern: every named pose must render without a thrown error and must paint a minimum count of opaque pixels (species not invisible/degenerate)
- PetWindow
- rules/graphify.md
- MouseHook
- workflows/graphify.md
- GitHub Without the gh CLI
- render
- Godzilla Reference and Motion Implementation Plan
- 2026-09-09-shenron.md
- String
- check_bubble_gap.mjs
- AppController
- devDependencies
- CIWatcher
- shenron-native.test.mjs
- AppSettings
- compilerOptions
- ClaudeWatcher
- .userContentController
- app/page.tsx
- ClaudeWatcher
- .Js
- lint.mjs
- ControlPanelWindow
- Rumble Kaiju Animated Demo
- Goku on Flying Nimbus Animated Demo
- Window
- WindowInterop
- .js
- ClaudeHooks
- GitEvent
- Deploy Reaction Screenshot
- Full-Screen Bug-Hunt Stage Overlay
- Pet Flight Mode Screenshot
- Affectionate/Happy Pet State
- Parachute/Parafoil Throw Animation
- Git Push Rocket Reaction
- macOS Permission Request Prompt
- Working Alongside Other Agents
- .application
- Bitling for Windows
- build.sh script
- bitling
- Flight
- Bitling.Windows.csproj
- pet-engine/package.json
- Window
- mario-enemies.test.mjs
- build_mario_3d_bundle.py
- test_demo.mjs
- verify_spiderman_sleep_visuals.mjs
- verify_spiderman_visuals.mjs
- verify_thor_visuals.mjs
- install.sh
- demo/page.tsx
- layout.tsx
- kaiju-native.test.mjs
- @bitling/pet-engine
- goku-enemies.test.mjs
- A New Box Arrives
- Claude Code Reaction Icon
- Git Commit Reaction Bubble
- Bug Squashing Reaction
- Pat Received Night Scene
- Sleep State Screenshot ("goodnight, human")
- Tests Failed Screenshot ("3 tests failing in api")
- Tests Passed Screenshot ("all bugs squashed!")
- build_openpets_bundle.mjs
- test_all_goku_visuals.mjs
- verify_hd_pikachu.mjs
- assets/README.md
- AGENTS.md
- eslint.config.mjs
- next.config.ts
- next-env.d.ts
- shenron.test.mjs
- ControlPanel
- capture_shenron.mjs
- 2026-09-10-calm-movement.md
- calm-movement.test.mjs
- spiderman.test.mjs
- thor.test.mjs
- legacy/README.md
- petting-reactions.test.mjs
- AppDelegate
- PetWindow
- spiderman_sleep.test.mjs
- app.js
- docs/index.html (GitHub Pages demo)
- /tmp/ironman_data.json (Iron Man asset bundle)
- Check Speech Bubble Gap QA Tool
- Make App Icon
- Bool

## God Nodes (most connected - your core abstractions)
1. `AppDelegate` - 87 edges
2. `PetWindow` - 59 edges
3. `GitWatcher` - 45 edges
4. `GitWatcher` - 44 edges
5. `OverlayView` - 39 edges
6. `AppController` - 35 edges
7. `CIWatcher` - 27 edges
8. `CIWatcher` - 27 edges
9. `Overlay` - 26 edges
10. `ClaudeWatcher` - 23 edges

## Surprising Connections (you probably didn't know these)
- `reach and half Are Measured, Never Guessed` --semantically_similar_to--> `62/38 Stance-Recovery Gait Design`  [INFERRED] [semantically similar]
  AGENTS.md → docs/superpowers/plans/2026-09-08-godzilla-reference.md
- `Measure the Thing the User Can See` --semantically_similar_to--> `Native Orange-Fire Renderer Regression Fixed`  [INFERRED] [semantically similar]
  AGENTS.md → docs/superpowers/plans/2026-09-08-godzilla-reference.md
- `Concurrent Goku Attack Renderer Edit (preserved)` --references--> `Goku (Kid Goku)`  [AMBIGUOUS]
  docs/superpowers/plans/2026-09-08-godzilla-reference.md → README.md
- `line(key) Shuffle Bag Keyed by Species+Phrase` --conceptually_related_to--> `Pikachu (Electric Mouse)`  [INFERRED]
  AGENTS.md → README.md
- `kaijuPose() function` --conceptually_related_to--> `Rumble (Atomic Titan / Kaiju)`  [INFERRED]
  AGENTS.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Small-vs-boss dual attack resolution tested identically across five species** — tests_goku_test, tests_ironman_test, tests_naruto_test, tests_pikachu_test, tests_ronaldo_test [INFERRED 0.85]
- **petNative.setSpecies() reversible host-bridge switching tested identically across species suites** — tests_goku_test, tests_ironman_test, tests_naruto_test, tests_pikachu_test, tests_ronaldo_test, tests_kaiju_browser_test [INFERRED 0.85]
- **Godzilla is verified across three independent layers: pure gait math (unit), full browser rendering/host-bridge (integration), and the native Swift overlay renderer (native)** — tests_kaiju_test, tests_kaiju_browser_test, tests_kaiju_native_test [INFERRED 0.80]
- **Three Regressions Fixed During Godzilla Plan Review** — godzilla_verification_results, godzilla_native_orange_fire_bug, godzilla_hovering_shadow_bug, godzilla_throw_bounds_bug [EXTRACTED 0.85]

## Communities (160 total, 58 thin omitted)

### Community 0 - "OverlayView"
Cohesion: 0.13
Nodes (26): Beam, Beetle, .alive, .size, Overlay, .isBusy, OverlayRocket, OverlayView (+18 more)

### Community 1 - "GitHubAuth"
Cohesion: 0.13
Nodes (17): AuthError, denied, .errorDescription, expired, network, notConfigured, DeviceCode, GitHubAuth (+9 more)

### Community 2 - "ActivityEntry"
Cohesion: 0.18
Nodes (11): AppKit, ActivityEntry, .asDictionary, ActivityLine, ActivityLog, .asJSON, Any, Date (+3 more)

### Community 3 - "CIWatcher"
Cohesion: 0.06
Nodes (27): CREDENTIAL, DeviceCode, GitHubAuth, DllImport, int, IntPtr, JsonObject, long (+19 more)

### Community 5 - "scripts"
Cohesion: 0.09
Nodes (21): globals, devDependencies, eslint, globals, playwright, engines, node, eslint (+13 more)

### Community 6 - "Path"
Cohesion: 0.08
Nodes (17): build(), patch(), Path, run_fix(), main(), main(), get_b64_resized(), main() (+9 more)

### Community 7 - "GitWatcher"
Cohesion: 0.11
Nodes (20): GitEvent, .asDictionary, GitStatus, .asDictionary, GitWatcher, .repositoryCount, .roots, ReflogLine (+12 more)

### Community 8 - "ActivityLog"
Cohesion: 0.06
Nodes (21): ActivityEntry, ActivityLine, ActivityLog, int, JsonArray, JsonObject, List, string (+13 more)

### Community 9 - "Release GitHub Actions Workflow"
Cohesion: 0.50
Nodes (4): Release Notes Template, Universal Binary arch Check (lipo), Release GitHub Actions Workflow, Build From Source Instructions

### Community 10 - "Pet Species Roster Table"
Cohesion: 0.25
Nodes (8): Bitling (The Little Machine), CR7 (Cristiano Ronaldo), Ember (Baby Dragon), Iron Man (Armored Avenger), Mario (Super Mario), Naruto (Ninja of the Leaf), Nimbo (Cloud Fighter), Pet Species Roster Table

### Community 12 - "GitWatcher"
Cohesion: 0.08
Nodes (18): GitWatcher, ReflogLine, Tracked, bool, DateTime, Dictionary, HashSet, int (+10 more)

### Community 13 - "Bitling README Overview"
Cohesion: 0.18
Nodes (11): bitling CLI command, Bug and Boss Hunting System, Three CI/Deploy Data Sources, Optional Claude Code Hooks, Claude Code Session Reactions, What Connects to Where (privacy/network), Control Room UI Description, Screen-Wide Desktop Bug Overlay (+3 more)

### Community 14 - "Working on Bitling (AGENTS.md)"
Cohesion: 0.16
Nodes (14): Assets and Likeness Policy, Before You Say It Works (verification gate), canFire Grounded Gate, Floater Can Hit the Ceiling, Generated Files Must Not Be Hand-Edited, The Launch Race (build.sh timing bug), Movement Rules (limb hinge, trail, canFire), Working on Bitling (AGENTS.md) (+6 more)

### Community 16 - "Pattern: every named pose must render without a thrown error and must paint a minimum count of opaque pixels (species not invisible/degenerate)"
Cohesion: 0.11
Nodes (18): Pattern: species.attack.resolve(isBoss) must return a distinct attack style (and sound) for small bugs vs boss bugs, Pattern: window.petNative.setSpecies() must update state.species and be reversible (switch away then back), Invariant: opaque character pixels must never touch the canvas edge, so the desktop transparent window never clips the sprite, Invariant: native host 'walking' distance drives pet.stride using the same stance/swing ratio (0.72/0.62) as the gait function, Invariant: feet lift only during recovery and never both leave the floor at once, Invariant: a planted (stance) foot cancels forward travel throughout the stance phase, Invariant: the walk loop is continuous (no pop/jump) at lift-off and touchdown phase boundaries, Invariant: triggerMarioCommitPowerUp() activates marioState.qblockActive and scoreMarioWarpPipe() activates marioState.pipeActive (+10 more)

### Community 17 - "PetWindow"
Cohesion: 0.11
Nodes (16): Flight, PetWindow, bool, CoreWebView2WebMessageReceivedEventArgs, DateTime, DispatcherTimer, double, int (+8 more)

### Community 19 - "MouseHook"
Cohesion: 0.09
Nodes (19): Action, Application, App, MouseHook, MSLLHOOKSTRUCT, POINT, DllImport, int (+11 more)

### Community 21 - "GitHub Without the gh CLI"
Cohesion: 0.24
Nodes (7): Adding a Pet (SPECIES registration), apiData(_:) function, defineSpecies() function, GitHub OAuth Device-Flow Fallback, GitHub Without the gh CLI, Ad-Hoc Re-Signing Invalidates Keychain Access, resize() Runs Before Late Species Definitions

### Community 22 - "render"
Cohesion: 0.29
Nodes (9): Cocoa, NSBezierPath, render(), rgb(), rounded(), CGFloat, Data, Int (+1 more)

### Community 23 - "Godzilla Reference and Motion Implementation Plan"
Cohesion: 0.18
Nodes (13): Anything Derived From the Art Must Be Measured Off the Art, kaijuPose() function, Kaiju Breath Mispositioned From Hard-Coded Constant, Measure the Thing the User Can See, line(key) Shuffle Bag Keyed by Species+Phrase, Hovering-Shadow Regression Fixed, Native Orange-Fire Renderer Regression Fixed, Reference Illustration Audit (color/shape mismatches) (+5 more)

### Community 25 - "String"
Cohesion: 0.15
Nodes (14): ClaudeHooks, .command, .settingsURL, GitHooks, .directory, HooksError, .errorDescription, jsString() (+6 more)

### Community 26 - "check_bubble_gap.mjs"
Cohesion: 0.25
Nodes (8): args, debug, HERE, measure(), PAGE, results, SEED, wanted

### Community 27 - "AppController"
Cohesion: 0.11
Nodes (9): AppController, Dictionary, DispatcherTimer, JsonObject, LoginItem, string, ContextMenuStrip, Icon (+1 more)

### Community 28 - "devDependencies"
Cohesion: 0.06
Nodes (30): dependencies, next, react, react-dom, devDependencies, eslint, eslint-config-next, @types/node (+22 more)

### Community 29 - "CIWatcher"
Cohesion: 0.18
Nodes (12): CIWatcher, Any, Bool, Data, Date, GitEvent, Set, String (+4 more)

### Community 31 - "AppSettings"
Cohesion: 0.15
Nodes (7): GitHooks, string, AppSettings, JsonObject, object, string, IEnumerable

### Community 32 - "compilerOptions"
Cohesion: 0.07
Nodes (27): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+19 more)

### Community 33 - "ClaudeWatcher"
Cohesion: 0.18
Nodes (14): ClaudeWatcher, .activeSessionCount, Session, Any, Bool, Date, GitEvent, Int (+6 more)

### Community 34 - ".userContentController"
Cohesion: 0.18
Nodes (4): CGFloat, NSPoint, NSRect, WKScriptMessage

### Community 35 - "app/page.tsx"
Cohesion: 0.13
Nodes (16): BitlingEngine, DEMO_COMMITS, DEMO_TESTS, FAQS, FILTERS, makeRandomCommitEvent(), makeRandomFailEvent(), pickOne() (+8 more)

### Community 36 - "ClaudeWatcher"
Cohesion: 0.17
Nodes (10): ClaudeWatcher, Session, bool, DateTime, Dictionary, JsonNode, long, string (+2 more)

### Community 38 - "lint.mjs"
Cohesion: 0.50
Nodes (3): errors, eslint, results

### Community 39 - "ControlPanelWindow"
Cohesion: 0.14
Nodes (10): Browser, Window, ControlPanelWindow, bool, CoreWebView2WebMessageReceivedEventArgs, Func, JsonObject, Task (+2 more)

### Community 41 - "Goku on Flying Nimbus Animated Demo"
Cohesion: 0.67
Nodes (3): Goku on Flying Nimbus Animated Demo, Goku Demo Background Landscape, Goku/Dragon Ball themed pet skin or Easter egg

### Community 42 - "Window"
Cohesion: 0.15
Nodes (14): Body, CancelButton, Headline, NameBox, OkButton, Window, NameDialog, bool (+6 more)

### Community 43 - "WindowInterop"
Cohesion: 0.24
Nodes (7): WindowInterop, DllImport, int, IntPtr, Point, Rect, Window

### Community 45 - "ClaudeHooks"
Cohesion: 0.28
Nodes (7): AuthException, ClaudeHooks, HooksException, JsonObject, string, HooksException, Exception

### Community 46 - "GitEvent"
Cohesion: 0.27
Nodes (3): GitEvent, GitStatus, JsonObject

### Community 54 - "Working Alongside Other Agents"
Cohesion: 0.40
Nodes (5): Non-Unique String-Replace Corruption Bug, Working Alongside Other Agents, Concurrent Goku Attack Renderer Edit (preserved), Goku (Kid Goku), Walker vs Floater Movement Types

### Community 56 - "Bitling for Windows"
Cohesion: 0.29
Nodes (6): Bitling for Windows, Building, Manual test plan (none of this has been run yet), Status: unverified V1 port, not yet built or run on Windows, What's deferred to V2, What's ported

### Community 57 - "build.sh script"
Cohesion: 0.50
Nodes (3): compile(), build.sh script, release.sh script

### Community 58 - "bitling"
Cohesion: 0.60
Nodes (3): bitling script, send(), usage()

### Community 59 - "Flight"
Cohesion: 0.40
Nodes (5): Flight, flying, hovering, landing, none

### Community 60 - "Bitling.Windows.csproj"
Cohesion: 0.40
Nodes (3): net8.0-windows, Microsoft.Web.WebView2 (1.0.2739.15), Microsoft.NET.Sdk

### Community 61 - "pet-engine/package.json"
Cohesion: 0.40
Nodes (4): description, name, private, version

### Community 62 - "Window"
Cohesion: 0.50
Nodes (3): Browser, Window, WebView2

### Community 63 - "mario-enemies.test.mjs"
Cohesion: 0.67
Nodes (3): ENEMY_STATES, run, withPage()

### Community 64 - "build_mario_3d_bundle.py"
Cohesion: 0.83
Nodes (3): load_and_crop(), main(), to_webp_b64()

### Community 103 - "ControlPanel"
Cohesion: 0.13
Nodes (13): ControlPanel, .isOpen, Bool, NSWindow, Void, WKNavigation, WKScriptMessage, WKUserContentController (+5 more)

### Community 121 - "AppDelegate"
Cohesion: 0.14
Nodes (14): AppDelegate, Date, GitStatus, Int, Timer, WKNavigation, WKUserContentController, WKWebView (+6 more)

### Community 123 - "PetWindow"
Cohesion: 0.25
Nodes (7): PetWindow, .canBecomeKey, .canBecomeMain, TimeInterval, Void, NSEvent, NSWindow

### Community 128 - "app.js"
Cohesion: 0.27
Nodes (11): copyToClipboard(), fallbackCopy(), openPetModal(), PETS_DATA, renderPetGallery(), setupCopyButtons(), setupFilterListeners(), setupSimulatorBridge() (+3 more)

## Ambiguous Edges - Review These
- `Goku (Kid Goku)` → `Concurrent Goku Attack Renderer Edit (preserved)`  [AMBIGUOUS]
  docs/superpowers/plans/2026-09-08-godzilla-reference.md · relation: references

## Knowledge Gaps
- **234 isolated node(s):** `HERE`, `PAGE`, `SEED`, `args`, `wanted` (+229 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **58 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Goku (Kid Goku)` and `Concurrent Goku Attack Renderer Edit (preserved)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `AppDelegate` connect `AppDelegate` to `OverlayView`, `ClaudeWatcher`, `ActivityEntry`, `.userContentController`, `ControlPanel`, `GitWatcher`, `PetWindow`, `.js`, `.application`, `String`, `Flight`, `CIWatcher`, `Bool`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `AppController` connect `AppController` to `CIWatcher`, `ClaudeWatcher`, `.Js`, `ControlPanelWindow`, `ActivityLog`, `GitWatcher`, `ClaudeHooks`, `GitEvent`, `PetWindow`, `MouseHook`, `AppSettings`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `GitWatcher` connect `GitWatcher` to `AppDelegate`, `CIWatcher`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `AppDelegate` (e.g. with `CIWatcher` and `ClaudeWatcher`) actually correct?**
  _`AppDelegate` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `OverlayView` (e.g. with `.clearBeetles()` and `.doomAll()`) actually correct?**
  _`OverlayView` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `HERE`, `PAGE`, `SEED` to the rest of the system?**
  _234 weakly-connected nodes found - possible documentation gaps or missing edges._