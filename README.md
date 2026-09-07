# Jellykin

A desktop pet for macOS. A wobbly jelly creature lives in a small transparent window
that floats above your other apps and sits on the bottom edge of the screen. Drag it
anywhere. Throw it and it falls back down. It watches your cursor across the whole
screen, strolls around on its own, and is fed, played with and put to sleep from the
menu bar.

The creature is a web page (`web/jellykin.html`, the same one published as the
Jellykin Habitat artifact). The macOS host (`Sources/main.swift`) renders it in a
borderless WKWebView and adds everything a page cannot do: window movement, screen
physics, a menu bar item, native prompts, and durable state.

## Build and install

Requires macOS 13 or newer and the Xcode Command Line Tools (`xcode-select --install`).

```bash
./build.sh
```

That derives `Resources/pet.html` from the web page, compiles the host, draws the
icon, ad-hoc signs the bundle and installs `/Applications/Jellykin.app`. Pass a
different folder to install elsewhere, or `INSTALL=0 ./build.sh` to only build into
`build/`.

Open it from Launchpad or:

```bash
open /Applications/Jellykin.app
```

Jellykin has no Dock icon. Look for the smiling face in the menu bar.

## Using it

- **Tap the egg three times** to hatch. You will be asked for a name.
- **Click** the pet to pat it. **Drag** to carry it. Let go mid-air and it drops.
  Fling it and it bounces off the screen edges.
- **Menu bar**: Pat, Feed, Debug bugs, Sleep, plus Tummy, Energy and Joy meters. Also
  Hide/Show, Bring pet to this screen, Rename, Sound, Start over, and Open at login.
- **Debug bugs** releases four bugs that scurry along the floor. The pet chases and
  stomps them. Click a bug to squash it yourself.
- It walks around the bottom of the screen on its own, talks in a speech bubble, and
  grows through three stages with age and care.
- Needs drift while the app is closed (capped at 12 hours). It never dies.

## Git reactions

The app watches for git activity in every repository under its watched folders
(default: `~/Desktop/AI`, plus `~/Developer`, `~/Projects`, `~/Documents/GitHub`,
`~/code`, `~/src`, `~/repos` when they exist; up to three folders deep). Add or
remove folders from the menu bar under Git. Detection tails each repository's
reflog, so there is no polling of `git status` for events and reactions land within
two seconds.

| You do | The pet does |
|---|---|
| commit | catches a falling commit node (hash on it) and eats it. Tummy and Joy go up. |
| commit with "fix" or "bug" in the message | a bug appears and gets stomped |
| commit with "wip" | "wip? okay…" |
| commit over 400 changed lines | "chonky commit!" |
| very short message | asks if that was really the message |
| commit after 23:00 | "go to sleep, human" |
| push | launches a rocket: "shipped main!" |
| merge | confetti, eats a purple merge node |
| checkout | glances around: "now on feature/x" |
| rebase start / finish | dizzy eyes, then relief |
| pull, stash, reset, cherry-pick | a line each |
| 10+ uncommitted files | nags now and then |
| no commit for a day | "git log is lonely" (daytime only) |

It wakes up for commits, pushes and merges. The Git submenu shows today's commit
and push counts and lifetime totals, and has "Pretend I committed" / "Pretend I
pushed" for a demo without touching a repo.

State lives in `~/Library/Preferences/app.jellykin.pet.plist`. Delete it, or use
Start over, to get a fresh egg. The window's last position is stored there too.

## Layout

```
Sources/main.swift        macOS host: window, drag + physics, menu bar, bridge
Resources/pet.html        generated desktop page (do not edit by hand)
Resources/Info.plist      bundle metadata (LSUIElement, icon, ids)
Tools/make_pet_html.py    derives pet.html from web/jellykin.html
Tools/makeicon.swift      draws the app icon set
web/jellykin.html         the creature: shared with the web artifact
build.sh                  build, sign, install
```

To change the creature, edit `web/jellykin.html` and rebuild. To preview the desktop
layout in a normal browser, open the generated page with `?desktop=1`.

## Bridge

Page to host (`window.webkit.messageHandlers.pet`): `save` (state JSON), `state`
(snapshot for the menu), `walk` (idle stroll request), `askName`, `ready`.

Host to page (`window.petNative`): `action(name)`, `grab()`, `drag(vx, vy)`,
`release()`, `land(impact)`, `walking(dir)`, `cursor(x, y)`, `setName(name)`,
`reset()`.
