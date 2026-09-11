import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';

const run = promisify(execFile);
test('native Shenron stage fills the display, stays fixed and restores floating and walking pets', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'bitling-shenron-native-'));
  try {
    const source = await readFile('apps/macos/Sources/main.swift', 'utf8');
    const start = source.lastIndexOf('\nlet app = NSApplication.shared');
    assert.ok(start > 0);
    const probe = `
extension AppDelegate {
    func verifyShenronStage() {
        let visible = NSScreen.main!.visibleFrame
        let original = NSRect(x: visible.minX + 40, y: visible.minY + 50, width: 300, height: 340)
        petSizeScale = 1
        webView = WKWebView(frame: NSRect(origin: .zero, size: original.size))
        window = PetWindow(contentRect: original, styleMask: [.borderless], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false
        snapshot.species = "dragon"; snapshot.hatched = true; snapshot.locomotion = "float"
        applyDesktopStage(true)
        applyLocomotion(true)
        precondition(window.frame == visible, "Shenron stage does not cover display")
        precondition(window.onStageDrag != nil && window.ignoresMouseEvents, "Stage drag/click-through missing")
        let stage = window.frame
        tick(); tick(); tick()
        precondition(window.frame == stage, "Native flight must not move full-display stage")
        window.ignoresMouseEvents = false
        lastHoverReport = Date.distantPast
        tick()
        precondition(window.ignoresMouseEvents, "Failed stage must let desktop clicks pass")
        snapshot.species = "ironman"
        applyDesktopStage(false); applyLocomotion(true)
        precondition(window.frame == original, "Switching to another floater must restore original window")
        precondition(window.onStageDrag == nil && floating && flight == .flying)
        snapshot.species = "dragon"
        applyDesktopStage(true); applyLocomotion(true)
        petSizeScale = 1.4
        snapshot.species = "mario"; snapshot.locomotion = "ground"
        applyDesktopStage(false); applyLocomotion(false)
        precondition(window.frame.size == petWindowSize, "Latest size must apply when restoring a pet")
        precondition(!desktopStage && !floating && window.onStageDrag == nil)
        print("stage, restore, scale, stationary motion and click-through passed")
    }
}
let app = NSApplication.shared
let delegate = AppDelegate()
delegate.verifyShenronStage()
`;
    const sourcePath = join(directory, 'main.swift'), executable = join(directory, 'probe');
    await writeFile(sourcePath, source.slice(0, start) + probe);
    await run('swiftc', ['-swift-version', '5', '-framework', 'Cocoa', '-framework', 'WebKit',
      '-framework', 'ServiceManagement', '-framework', 'Security', sourcePath,
      ...['GitWatcher', 'CIWatcher', 'ClaudeWatcher', 'Overlay', 'ControlPanel', 'GitHubAuth'].map(n => `apps/macos/Sources/${n}.swift`), '-o', executable]);
    const { stdout } = await run(executable);
    assert.match(stdout, /click-through passed/);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
