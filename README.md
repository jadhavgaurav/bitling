# Bitling

A desktop pet for macOS that lives on your dev activity. Bitling is a small robot with
a screen for a face. It stands on the bottom edge of your screen in a transparent window
above your other apps, watches your cursor, strolls around, and reacts to your commits,
pushes, test runs and deployments. Drag it anywhere. Throw it and it falls back down.

The creature is a web page (`web/bitling.html`, also published as the Bitling Habitat
artifact). The macOS host (`Sources/`) renders it in a borderless WKWebView and adds
everything a page cannot do: window movement, screen physics, a menu bar item, native
prompts, durable state, and the git and CI watchers.

## Build and install

Requires macOS 13 or newer and the Xcode Command Line Tools (`xcode-select --install`).

```bash
./build.sh
```

That derives `Resources/pet.html` from the web page, compiles the host, draws the icon,
ad-hoc signs the bundle, installs `/Applications/Bitling.app` and links the `bitling`
command into `/usr/local/bin` when that folder is writable. Pass a different folder to
install elsewhere, or `INSTALL=0 ./build.sh` to only build into `build/`.

```bash
open /Applications/Bitling.app
```

Bitling has no Dock icon. Look for the smiling face in the menu bar.

## Using it

- **Tap the box three times** to unbox it. You will be asked for a name.
- **Click** the robot to pat it (it tilts its head). **Drag** to carry it: legs dangle.
  Let go mid-air and it drops, tumbling, and lands on its feet with a knee bend. Fling
  it and it glances off the screen edges.
- It **walks** with a real stride and turns to face where it is going. On its own it
  strolls, turns around, stretches, taps a foot when bored, and now and then fires
  its thrusters and **flies** to a spot anywhere on the screen, hovers there for a
  while looking around, then lands. Drop it gently while it is flying and it hovers
  where you left it.
- **Menu bar**: Pat, Feed, Debug bugs, Sleep, plus Tummy, Energy and Joy meters (also
  shown as the three LEDs on its chest once it has grown). Hide/Show, Bring pet to this
  screen, Rename, Sound, Start over, Open at login.
- **Debug bugs** releases four bugs that scurry along the floor. The robot chases and
  stomps them. Click a bug to squash it yourself.
- Snacks are batteries, chips and cookies. Its antenna turns amber when it is hungry.
- Grows through three stages with age and care points: Bootling, Bitling, Overclocked
  Bitling (two antennas, a halo, a shifting shell colour).
- Needs drift while the app is closed (capped at 12 hours). It never dies.

## Git reactions

The app watches every repository under its watched folders (default `~/Desktop/AI`,
plus `~/Developer`, `~/Projects`, `~/Documents/GitHub`, `~/code`, `~/src`, `~/repos`
when they exist; up to three folders deep). Add or remove folders from the menu bar
under Dev activity. Detection tails each repository's reflog, so reactions land within
two seconds without polling `git status`.

| You do | Bitling does |
|---|---|
| commit | catches a falling commit node (hash on it) and eats it |
| commit with "fix" or "bug" in the message | a bug appears and gets stomped |
| commit with "wip" | "wip? okay…" |
| commit over 400 changed lines | "chonky commit!" |
| very short message | asks if that was really the message |
| commit after 23:00 | "go to sleep, human" |
| push | launches a rocket: "shipped main!" |
| merge | confetti, eats a purple merge node |
| checkout | glances around: "now on feature/x" |
| rebase start / finish | dizzy spinning eyes, then relief |
| pull, stash, reset, cherry-pick | a line each |
| 10+ uncommitted files | nags now and then |
| no commit for a day | "git log is lonely" (daytime only) |

## Test and deploy reactions

| Event | Bitling does |
|---|---|
| tests fail | screen flashes red with X eyes and "ERR", antenna red, it shakes, then bugs appear (one per failure, up to five) and it hunts them |
| tests pass | screen shows a green "OK", any bugs die on the spot, "tests green!" |
| deploy starts | amber screen with a progress bar that creeps while it waits |
| deploy finishes | "100%", then a rocket: "deployed to production!" |
| deploy fails | "ERR", smoke, "deploy failed. rollback?" |

Three sources feed these, all optional:

1. **GitHub Actions and GitHub Deployments** through the `gh` CLI, for watched repos
   whose origin is on github.com. `gh auth login` once and it works. Workflows named
   deploy, release, publish, cd or rollout count as deployments; everything else counts
   as tests. Vercel and similar services record GitHub Deployments, so those show up
   too. Polled every minute.
2. **Local pytest runs**: pytest rewrites `.pytest_cache/v/cache/nodeids` on every run
   and lists failing tests in `lastfailed`. Checked every three seconds for the repo root
   and its first-level folders.
3. **The `bitling` command** for anything else. It sends events over the `bitling://`
   URL scheme, so it works from any shell, Makefile, npm script or git hook:

```bash
bitling run npm test                    # reports pass or fail, keeps the exit status
bitling run pytest -q
bitling deploy production ./deploy.sh   # start, then finished or failed
bitling event test-failed count=3 name=api
bitling say "lunch?"
bitling claude < hook.json                # Claude Code hook adapter (installed for you by the menu)
```

If `build.sh` could not link the command, do it once yourself:

```bash
sudo ln -sf /Applications/Bitling.app/Contents/Resources/bitling /usr/local/bin/bitling
```

## Claude Code reactions

Bitling watches your Claude Code sessions too. It tails the session transcripts Claude
Code writes under `~/.claude/projects`, so this works with no configuration for the
terminal, the desktop app and IDE extensions.

| Claude Code | Bitling does |
|---|---|
| you send a prompt | "on it", antenna turns orange, typing dots on its screen, it stops strolling and stares at the code |
| Claude edits, runs commands, reads, searches | occasional chatter: "editing files…", "running tests…", "reading around…" |
| a tool call errors | brief "!" flicker, "hmm, that errored" |
| Claude finishes a turn | "done! check it", sparkles, arms up |
| Claude waits for your permission | waves both arms, "?" on screen, "Claude needs you!" (hooks only) |
| new session, idle 5 minutes, session ends | a line each |

**Hooks** make this instant and add the permission alert. "Connect Claude Code hooks…"
in the Dev activity menu adds Bitling to `~/.claude/settings.json` for SessionStart,
UserPromptSubmit, PreToolUse, Stop, Notification and SessionEnd. Existing hooks are kept,
a backup is written beside the file, and "Disconnect" removes only Bitling's entries.
Each hook runs `bitling claude`, which reads the hook JSON and forwards one event. With
both hooks and transcripts active, duplicates within three seconds are dropped.

The Dev activity submenu shows what is being watched, today's commits and pushes,
lifetime totals, the CI source status, Claude Code activity, and "Pretend…" items for a
demo.

State lives in `~/Library/Preferences/app.bitling.pet.plist`. Delete it, or use Start
over, for a fresh box.

## Layout

```
Sources/main.swift        macOS host: window, drag + physics, menu bar, bridge, URL scheme
Sources/GitWatcher.swift  reflog tailing, repo discovery, github slugs
Sources/CIWatcher.swift   gh runs + deployments, pytest caches
Sources/ClaudeWatcher.swift  Claude Code transcript tailing
Resources/pet.html        generated desktop page (do not edit by hand)
Resources/bitling         command line tool copied into the app bundle
Resources/Info.plist      bundle metadata (LSUIElement, icon, URL scheme)
Tools/make_pet_html.py    derives pet.html from web/bitling.html
Tools/makeicon.swift      draws the app icon set
Tools/patch_*.py          one-off migrations kept for the record
web/bitling.html          the creature: shared with the web artifact
build.sh                  build, sign, install
```

To change the creature, edit `web/bitling.html` and rebuild. To preview the desktop
layout in a normal browser, open the generated page with `?desktop=1`, or set
`window.__forceDesktop = true` before the script runs.

## Bridge

Page to host (`window.webkit.messageHandlers.pet`): `save` (state JSON), `state`
(snapshot for the menu), `walk` (idle stroll request), `askName`, `ready`.

Host to page (`window.petNative`): `action(name)`, `grab()`, `drag(vx, vy)`,
`release()`, `land(impact)`, `walking(dir)`, `cursor(x, y)`, `setName(name)`,
`reset()`, `gitEvent(event)`, `gitStatus(info)`.

Event kinds: commit, amend, merge, push, checkout, rebase, rebase-done, pull, stash,
reset, cherry-pick, test-failed, test-passed, deploy-started, deploy-finished,
deploy-failed, claude-session-start, claude-prompt, claude-tool, claude-tool-error,
claude-done, claude-notify, claude-idle, claude-session-end, say.
