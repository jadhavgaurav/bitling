# Bitling for Windows

A native Windows port of the macOS menubar pet (`apps/macos/`), written in C# / WPF /
WebView2. It reuses the same creature page (`apps/macos/web/bitling.html`) that the
macOS app and the website demo derive from — per `AGENTS.md`, that file stays the single
hand-edited source of truth for the pet's look and behavior; nothing here forks it.

## Status: unverified V1 port, not yet built or run on Windows

This was written by reading the Swift source line by line and re-deriving each behavior
in C#, in a Linux container with no Windows machine and no .NET desktop toolchain
available to compile or run it against. **It has never been built, launched, or clicked
on.** Treat it as a detailed first draft, not a working app: budget real time to bring it
up on an actual Windows machine, fix whatever `dotnet build`/`dotnet publish` surface
first, and then work through the manual test plan below.

The single highest-risk area is **vertical physics polarity** in
`Bitling.Windows/Windows/PetWindow.xaml.cs`. macOS screen coordinates are Y-up (origin
bottom-left); WPF/Win32 are Y-down (origin top-left). Every formula that involves falling,
throwing, flying, or landing was re-derived by hand for the flipped axis rather than
copied, and is exactly the kind of thing `AGENTS.md` warns has been wrong on every pet at
least once when *measured* on a real screen — this hasn't been measured on any screen yet.
First thing to check on real hardware: drop the pet mid-air and confirm it falls *down*
toward the taskbar and lands, rather than floating up or launching off-screen.

The second: `Native/MouseHook.cs` uses a low-level `WH_MOUSE_LL` hook to detect
drag-to-move over the pet, because WebView2 hosts a real Chromium child HWND and WPF's own
`Preview*` mouse events don't reliably fire over it (a known WPF+WebView2 limitation, not
specific to this app — see `PetWindow.swift`'s `sendEvent` override, which taps macOS's
event stream for the identical reason). Low-level hooks are timing-sensitive; if the pet
becomes undraggable or the hook silently stops firing, that's the first place to look.

Third: DPI scaling (`Native/WindowInterop.cs`). The app declares Per-Monitor-V2 DPI
awareness in `app.manifest` so WPF's device-independent window coordinates line up with
`System.Windows.Forms.Screen`'s physical-pixel monitor bounds, but this has not been
exercised on a real multi-monitor or mixed-DPI setup.

## What's ported

- **The creature itself** — unchanged. `pet.html` is derived from the same
  `apps/macos/web/bitling.html` by the same `packages/pet-engine/scripts/make_pet_html.py`
  used for macOS; `panel.html` (the control room) is the same file macOS loads.
- **Tray icon + menu** (`AppController.cs`) — pat/feed/play/sleep/rename/sound/reset,
  show/hide, bring-to-this-screen, dev-activity submenu, open-at-login, quit. Windows has
  no menu-bar strip, so the app menu (About/Hide/Quit) macOS builds for its `LSUIElement`
  process has no equivalent here — there's nothing for it to replace.
- **The pet window** (`Windows/PetWindow.xaml.cs`) — transparent, borderless, always-on-top,
  click-through when the cursor isn't over a drawn pixel of the pet (reported by the page
  itself, same as macOS), drag-to-throw physics, walk/fly/hover/land state machine.
- **The control room** (`Windows/ControlPanelWindow.xaml.cs`) — second WebView2 window,
  same bridge shape (`window.panel.update(...)` pushed from the host, `{type:"action",
  value:...}` messages back).
- **Git activity watching** (`Watchers/GitWatcher.cs`) — reflog tailing, identical logic to
  `GitWatcher.swift`, just Windows paths and drives instead of `/Volumes`.
- **CI watching** (`Watchers/CIWatcher.cs`) — `gh` CLI or GitHub device-flow token, plus
  pytest cache watching.
- **Claude Code watching** (`Watchers/ClaudeWatcher.cs`) — tails
  `%USERPROFILE%\.claude\projects\**\*.jsonl`, same as macOS tails `~/.claude/projects`.
- **GitHub device-flow sign-in** (`Auth/GitHubAuth.cs`) — same OAuth flow and client ID;
  the token lives in Windows Credential Manager instead of Keychain.
- **Launch at login** (`Native/LoginItem.cs`) — `HKCU\...\Run` key instead of
  `SMAppService`.
- **The `bitling://` protocol** (`Native/ProtocolRegistration.cs`,
  `Native/SingleInstance.cs`) — registered under `HKEY_CURRENT_USER` (no admin needed,
  same as macOS needing no `sudo`); a second launch forwards its URL to the running
  instance over a named pipe, since Windows has no built-in equivalent of macOS routing
  a second `open bitling://...` into the already-running app.
- **Global git hooks / Claude Code hooks** (`Native/GitHooks.cs`, `Native/ClaudeHooks.cs`)
  — same `core.hooksPath` / `~/.claude/settings.json` mechanism; the installed hook
  scripts are unchanged `#!/bin/sh` (Git for Windows ships its own `sh.exe` and runs
  hooks through it exactly like macOS/Linux) that shell out to `powershell.exe
  bitling.ps1` instead of the macOS bash script.
- **The `bitling` CLI** (`cli/bitling.ps1`) — same command surface as
  `apps/macos/Resources/bitling`, rewritten in PowerShell.

## What's deferred to V2

Cut for scope, not by accident — each of these is a substantial, independently risky
feature that deserved its own verified pass rather than a rushed, unrunnable guess:

- **The cross-screen bug-swarm / laser-beam / rocket-launch overlay**
  (`Overlay.swift`, 1400+ lines) — a full-screen, click-through window per monitor that
  draws beetles, lasers and scorch marks outside the pet's own small window. The bridge
  messages that would drive it (`bugs`, `tests`, `boss`, `zap`, `rocketScreen`,
  `clearBugs`, `doomAll`) are accepted in `PetWindow.HandleBridgeMessage` but currently
  no-op. The pet still reacts to git/CI/Claude events on itself; it just doesn't spawn
  bugs crawling across your desktop yet.
- **"Desktop stage" species** (the dragon/Shenron and Spider-Man full-screen modes,
  `applyDesktopStage` in `main.swift`) — these resize the pet window to the whole screen
  and, for Spider-Man, enumerate other windows as web-slinging "rooftops"
  (`CGWindowListCopyWindowInfo`, which would need `EnumWindows`/DWM APIs on Windows).
  Both species fall back to ordinary walker/floater window physics for now.
- **Idle-time / user-active detection** for Spider-Man (`CGEventSource` →
  `GetLastInputInfo`) — tied to the deferred rooftop feature above.
- **A proper app icon.** `apps/macos/tools/makeicon.swift` draws the `.icns` with Cocoa
  and can't run on Windows; `build.ps1` has a TODO to generate `Resources\Bitling.ico`
  some other way. Until then the tray icon falls back to the system default
  (`AppController.LoadTrayIcon`).
- **Multi-folder "watch a folder" picker** — `NSOpenPanel` supports multi-select;
  `System.Windows.Forms.FolderBrowserDialog` doesn't, so `WatchFolder()` adds one folder
  per pick. Pick again to add more.
- **Code signing / installer.** `build.ps1` publishes a self-contained exe and copies it
  to a folder; there's no Authenticode signing, MSI, or Start Menu shortcut creation yet
  (macOS's ad-hoc `codesign` has no free equivalent — an unsigned exe will get a
  SmartScreen warning on first run elsewhere).

## Building

```powershell
cd apps\windows
.\build.ps1                # publish + install to %LOCALAPPDATA%\Programs\Bitling
.\build.ps1 -NoInstall      # just build, result in apps\windows\publish\
```

Requires the .NET 8 SDK with the WPF/WinForms desktop workload, Python 3 (for
`make_pet_html.py`, same requirement as the macOS build), and Git for Windows (both as a
runtime dependency of `Watchers/GitWatcher.cs` and because its bundled `sh.exe` is what
runs the installed git hooks).

## Manual test plan (none of this has been run yet)

1. `dotnet build` cleanly — fix compile errors first; this is untested code.
2. Launch: does a tray icon appear, and does the pet's egg/creature show at the bottom of
   the primary monitor?
3. Drag the pet: does it follow the cursor, and does letting go while moving fast throw it
   with correct-direction physics (falls down, not up)?
4. Right-click the pet: does the tray context menu appear at the cursor?
5. Pat/feed/play/sleep from the tray menu: does the page react?
6. Open the control room: does WebView2 load `panel.html`, and do its buttons round-trip
   back to tray-menu actions (e.g. toggling sound)?
7. `git commit` in a watched repo: does the pet react within a couple of seconds?
8. Move the window between two monitors with different DPI scaling, if available: does it
   land in the right place instead of jumping or resizing unexpectedly?
9. Connect GitHub via the device flow: does the code prompt, browser launch, and
   post-connect state all work?
10. Restart the app: does saved state (name, stage, needs) survive, confirming
    `AppSettings`'s JSON-file persistence round-trips correctly?
