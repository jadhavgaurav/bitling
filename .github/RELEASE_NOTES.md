A desktop pet for macOS that lives on your dev activity. A small robot stands on the
bottom edge of your screen, watches your cursor, walks around, flies off to hover
somewhere else, and reacts to what you are actually doing.

**Install (one line, no warnings)**

```
curl -fsSL https://raw.githubusercontent.com/jadhavgaurav/bitling/main/install.sh | bash
```

**Or by hand:** download the `.dmg` below, drag Bitling to Applications, and open it. macOS
will refuse the first launch because this build is signed ad hoc rather than with a paid
Apple Developer ID. Click **Done** (never "Move to Trash"), then either open **System
Settings → Privacy & Security** and click **Open Anyway**, or run
`xattr -dr com.apple.quarantine /Applications/Bitling.app`.

Bitling has no Dock icon. Look for the smiling face in the menu bar.

**What it reacts to**

- **git**, in every repository on the machine: commits drop a node it catches and eats,
  pushes launch a rocket, merges get confetti, rebases make it dizzy, `fix` commits
  spawn a bug it stomps. Reflog based, so there is nothing to configure.
- **tests and deploys**: red screen with X eyes and a swarm of bugs when tests fail, a
  green OK when they pass, a progress bar while a deploy runs, a rocket when it lands.
  Reads GitHub Actions and Deployments through the `gh` CLI, local pytest caches, and
  anything you send with the bundled `bitling` command.
- **Claude Code sessions**: typing dots while it works, chatter about what it is doing,
  a wave when Claude needs your permission, sparkles when it finishes.

**The control room**

Right click the pet and pick **Control room** (or run `bitling panel`). Two tabs: **Activity**
has a live portrait, its gauges, today's commits, pushes and Claude turns, a twelve-hour
timeline and the full stream of everything it noticed. **Setup** has what is being watched and
every switch that used to be buried in the menu.

**Care**

Tap the box three times to unbox it. Click to pat, drag to carry, throw it and it
deploys a parafoil. Feed it batteries, send it bug hunting, and let it sleep. It grows
through three stages, and it never dies.

Requires macOS 13 or later. Apple Silicon and Intel.
