// Bitling: a desktop pet for macOS.
//
// The creature itself is a web page (Resources/pet.html) rendered in a transparent,
// borderless, always-on-top window. This host owns everything the page cannot:
// moving the window when you drag the pet, throw physics against the real screen
// edges, idle strolls along the bottom of the screen, a menu bar item for care
// actions, native name prompts, and durable state in UserDefaults.

import Cocoa
import ServiceManagement
import WebKit

let stateDefaultsKey = "petState"
let windowXDefaultsKey = "petWindowX"
let dockIconDefaultsKey = "showInDock"
// Tall enough for the full robot plus a deployed parachute, wide enough for its arms.
let petBaseSize = NSSize(width: 300, height: 340)
let petSizeDefaultsKey = "petSize"
/// How large the creature is, as a multiple of the stock window. Everything that measures
/// the pet reads this, so growing it moves the floor, the clamps and the flight targets too.
var petSizeScale = CGFloat(UserDefaults.standard.object(forKey: petSizeDefaultsKey) as? Double ?? 1)
var petWindowSize: NSSize {
    NSSize(width: (petBaseSize.width * petSizeScale).rounded(),
           height: (petBaseSize.height * petSizeScale).rounded())
}

func jsString(_ value: String) -> String {
    // JSON-encode a single string so it can be embedded as a JS literal.
    guard let data = try? JSONEncoder().encode([value]),
          let array = String(data: data, encoding: .utf8) else { return "\"\"" }
    return String(array.dropFirst().dropLast())
}

// MARK: - Window that turns mouse drags into window movement

final class PetWindow: NSWindow {
    /// Keeps the whole pet on screen while it is dragged, so no part is clipped at an edge.
    static func clamped(_ origin: NSPoint, in visible: NSRect, size: NSSize) -> NSPoint {
        NSPoint(
            x: min(max(origin.x, visible.minX), max(visible.minX, visible.maxX - size.width)),
            y: min(max(origin.y, visible.minY), max(visible.minY, visible.maxY - size.height))
        )
    }

    var onDragStart: (() -> Void)?
    var onDrag: ((CGFloat, CGFloat) -> Void)?
    var onDragEnd: ((CGFloat, CGFloat) -> Void)?
    var onRightClick: (() -> Void)?

    private var pressed = false
    private var dragging = false
    private var downPoint = NSPoint.zero
    private var lastPoint = NSPoint.zero
    private var lastTime: TimeInterval = 0
    private var velocity = CGPoint.zero

    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }

    override func sendEvent(_ event: NSEvent) {
        switch event.type {
        case .leftMouseDown:
            pressed = true
            dragging = false
            downPoint = NSEvent.mouseLocation
            lastPoint = downPoint
            lastTime = event.timestamp
            velocity = .zero
            super.sendEvent(event)
        case .leftMouseDragged:
            guard pressed else { super.sendEvent(event); return }
            let point = NSEvent.mouseLocation
            if !dragging {
                if hypot(point.x - downPoint.x, point.y - downPoint.y) < 6 { return }
                dragging = true
                onDragStart?()
            }
            let dt = max(0.004, event.timestamp - lastTime)
            velocity = CGPoint(x: (point.x - lastPoint.x) / dt, y: (point.y - lastPoint.y) / dt)
            var origin = frame.origin
            origin.x += point.x - lastPoint.x
            origin.y += point.y - lastPoint.y
            let visible = (screen ?? NSScreen.screens.first { $0.frame.contains(point) } ?? NSScreen.main)?.visibleFrame
            if let visible { origin = Self.clamped(origin, in: visible, size: frame.size) }
            setFrameOrigin(origin)
            lastPoint = point
            lastTime = event.timestamp
            onDrag?(velocity.x, velocity.y)
        case .leftMouseUp:
            let wasDragging = dragging
            let stale = event.timestamp - lastTime > 0.1
            pressed = false
            dragging = false
            super.sendEvent(event)
            if wasDragging { onDragEnd?(stale ? 0 : velocity.x, stale ? 0 : velocity.y) }
        case .rightMouseDown:
            // Never forward these to the web view: a right click there began a press that got
            // no matching release, and the pet stayed stuck to the cursor.
            onRightClick?()
        case .rightMouseUp, .rightMouseDragged, .otherMouseDown, .otherMouseUp, .otherMouseDragged:
            break
        default:
            super.sendEvent(event)
        }
    }
}

// MARK: - Snapshot of the creature's state, as reported by the page

struct PetSnapshot {
    var name = "Bitling"
    var stage = "Egg"
    var age = ""
    var full = 0
    var energy = 0
    var joy = 0
    var asleep = false
    var hatched = false
    var sound = true
    var commits = 0
    var pushes = 0
    var bugs = 0
    var bugsToday = 0
    var working = false
    var screen = ""
    var species = "robot"
    var locomotion = "ground"
    var attack = "beam"

    init() {}

    init?(message: [String: Any]) {
        guard let name = message["name"] as? String, let stage = message["stage"] as? String else { return nil }
        self.name = name
        self.stage = stage
        age = message["age"] as? String ?? ""
        full = message["full"] as? Int ?? 0
        energy = message["energy"] as? Int ?? 0
        joy = message["joy"] as? Int ?? 0
        asleep = message["asleep"] as? Bool ?? false
        hatched = message["hatched"] as? Bool ?? false
        sound = message["sound"] as? Bool ?? true
        commits = message["commits"] as? Int ?? 0
        pushes = message["pushes"] as? Int ?? 0
        bugs = message["bugs"] as? Int ?? 0
        bugsToday = message["bugsToday"] as? Int ?? 0
        working = message["working"] as? Bool ?? false
        screen = message["screen"] as? String ?? ""
        species = message["species"] as? String ?? "robot"
        locomotion = message["locomotion"] as? String ?? "ground"
        attack = message["attack"] as? String ?? "beam"
    }
}

// MARK: - App

final class AppDelegate: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, NSMenuDelegate {
    private var window: PetWindow!
    private var webView: WKWebView!
    private var statusItem: NSStatusItem!
    private let menu = NSMenu()
    private var pageReady = false
    private var snapshot = PetSnapshot()
    private let git = GitWatcher()
    private let ci = CIWatcher()
    private let claude = ClaudeWatcher()
    private let overlay = Overlay()
    private let panel = ControlPanel()
    private var dockIconEnabled = UserDefaults.standard.object(forKey: dockIconDefaultsKey) as? Bool ?? true
    private let activity = ActivityLog()
    private var swarmEnabled = UserDefaults.standard.object(forKey: "swarmOnDesktop") as? Bool ?? true
    private var lastSwarmCount = -1
    private var recentEvents: [String: Date] = [:]

    // Motion
    private var timer: Timer?
    private var tickCount = 0
    private var dragging = false
    private var airborne = false
    private var velocityX: CGFloat = 0
    private var velocityY: CGFloat = 0
    private var walkRemaining: CGFloat = 0
    private var walkDirection: CGFloat = 0
    private enum Flight { case none, flying, hovering, landing }
    private var flight: Flight = .none
    private var flyTarget = NSPoint.zero
    private var hoverBase = NSPoint.zero
    private var hoverT: CGFloat = 0
    private var wasFlying = false
    private var chuteOpen = false
    private var chuteSway: CGFloat = 0
    private var lastMouse = NSPoint(x: -1, y: -1)
    /// A floating species has no use for gravity: it hangs where you leave it.
    private var floating = false
    /// The roster the page publishes on boot, shown by the control room's picker.
    private var speciesCatalogue: [[String: Any]] = []
    /// The page probes its own canvas and says whether the cursor is over the drawn creature.
    /// Everywhere else the window has to let the click through to whatever is behind it.
    private var lastHoverReport = Date.distantPast
    private var dragEventCount = 0

    // Menu items whose titles or states change
    private let controlItem = NSMenuItem(title: "Control room…", action: #selector(openPanel), keyEquivalent: "k")
    private let headerItem = NSMenuItem(title: "Bitling", action: nil, keyEquivalent: "")
    private let stageItem = NSMenuItem(title: "Egg", action: nil, keyEquivalent: "")
    private let tummyItem = NSMenuItem(title: "Tummy", action: nil, keyEquivalent: "")
    private let energyItem = NSMenuItem(title: "Energy", action: nil, keyEquivalent: "")
    private let joyItem = NSMenuItem(title: "Joy", action: nil, keyEquivalent: "")
    private let patItem = NSMenuItem(title: "Pat", action: #selector(patAction), keyEquivalent: "")
    private let feedItem = NSMenuItem(title: "Feed", action: #selector(feedAction), keyEquivalent: "f")
    private let playItem = NSMenuItem(title: "Debug bugs", action: #selector(playAction), keyEquivalent: "d")
    private let sleepItem = NSMenuItem(title: "Sleep", action: #selector(sleepAction), keyEquivalent: "s")
    private let showItem = NSMenuItem(title: "Hide pet", action: #selector(toggleShown), keyEquivalent: "h")
    private let bringItem = NSMenuItem(title: "Bring pet to this screen", action: #selector(bringHere), keyEquivalent: "")
    private let renameItem = NSMenuItem(title: "Rename…", action: #selector(renameAction), keyEquivalent: "")
    private let soundItem = NSMenuItem(title: "Sound", action: #selector(soundAction), keyEquivalent: "")
    private let resetItem = NSMenuItem(title: "Start over…", action: #selector(resetAction), keyEquivalent: "")
    private let loginItem = NSMenuItem(title: "Open at login", action: #selector(toggleLogin), keyEquivalent: "")
    private let gitMenu = NSMenu(title: "Git")
    private let gitItem = NSMenuItem(title: "Dev activity", action: nil, keyEquivalent: "")
    private let gitWatchingItem = NSMenuItem(title: "Watching…", action: nil, keyEquivalent: "")
    private let gitTodayItem = NSMenuItem(title: "Today: 0 commits · 0 pushes", action: nil, keyEquivalent: "")
    private let gitLastItem = NSMenuItem(title: "Last: nothing yet", action: nil, keyEquivalent: "")
    private let gitTotalsItem = NSMenuItem(title: "Lifetime: 0 commits caught · 0 pushes · 0 bugs", action: nil, keyEquivalent: "")
    private let stopWatchingMenu = NSMenu(title: "Stop watching")
    private let ciStatusItem = NSMenuItem(title: "CI: checking…", action: nil, keyEquivalent: "")
    private let ciLastItem = NSMenuItem(title: "Last CI: nothing yet", action: nil, keyEquivalent: "")
    private let claudeStatusItem = NSMenuItem(title: "Claude Code: watching transcripts", action: nil, keyEquivalent: "")
    private let claudeTodayItem = NSMenuItem(title: "Today: 0 prompts · 0 tool calls", action: nil, keyEquivalent: "")
    private let claudeLastItem = NSMenuItem(title: "Last: nothing yet", action: nil, keyEquivalent: "")
    private let hooksItem = NSMenuItem(title: "Connect Claude Code hooks…", action: #selector(toggleClaudeHooks), keyEquivalent: "")
    private let swarmItem = NSMenuItem(title: "Let bugs loose on the screen", action: #selector(toggleSwarm), keyEquivalent: "")
    private let gitHooksItem = NSMenuItem(title: "Connect global git hooks…", action: #selector(toggleGitHooks), keyEquivalent: "")

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(dockIconEnabled ? .regular : .accessory)
        buildMainMenu()
        buildWebView()
        buildWindow()
        buildStatusItem()
        loadPage()
        git.onEvent = { [weak self] event in self?.deliverGitEvent(event) }
        git.onStatus = { [weak self] status in self?.deliverGitStatus(status) }
        git.start()
        ci.repositories = { [weak self] in self?.git.repositories() ?? [] }
        ci.onEvent = { [weak self] event in self?.deliverGitEvent(event) }
        ci.start()
        claude.onEvent = { [weak self] event in self?.deliverGitEvent(event) }
        claude.start()
        overlay.onKill = { [weak self] beetle in
            guard let self else { return }
            self.js("petNative.killed(\(beetle.boss ? "true" : "false"))")
        }
        panel.stateProvider = { [weak self] in self?.panelPayload() ?? [:] }
        panel.onAction = { [weak self] action in self?.handlePanelAction(action) }
        timer = Timer(timeInterval: 1.0 / 60.0, repeats: true) { [weak self] _ in self?.tick() }
        RunLoop.main.add(timer!, forMode: .common)
        NotificationCenter.default.addObserver(
            self, selector: #selector(screensChanged), name: NSApplication.didChangeScreenParametersNotification, object: nil
        )
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows: Bool) -> Bool {
        panel.show()
        return true
    }

    func applicationWillTerminate(_ notification: Notification) {
        saveWindowX()
    }

    // bitling://<kind>?key=value… from the `bitling` command line tool or any script.
    func application(_ application: NSApplication, open urls: [URL]) {
        for url in urls {
            guard url.scheme?.lowercased() == "bitling", let kind = url.host?.lowercased() else { continue }
            if kind == "panel" { panel.show(); continue }
            var query: [String: String] = [:]
            URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems?.forEach { query[$0.name] = $0.value ?? "" }
            if kind == "pet" {
                if let id = query["id"], !id.isEmpty { js("petNative.setSpecies(\(jsString(id)))") }
                continue
            }
            if kind == "size" {
                if let v = Double(query["v"] ?? "") { applyPetSize(CGFloat(v)) }
                continue
            }
            let event = GitEvent(
                kind: kind, repo: query["repo"] ?? "", branch: query["branch"] ?? "",
                message: query["message"] ?? query["text"] ?? "", hash: query["hash"] ?? "",
                count: Int(query["count"] ?? "") ?? 0, target: query["target"] ?? "", name: query["name"] ?? "",
                tests: (query["tests"] ?? "").split(separator: ",").map(String.init)
            )
            deliverGitEvent(event)
        }
    }

    // MARK: Setup

    private func buildWebView() {
        let config = WKWebViewConfiguration()
        config.mediaTypesRequiringUserActionForPlayback = []
        let controller = WKUserContentController()
        controller.add(self, name: "pet")
        if let saved = UserDefaults.standard.string(forKey: stateDefaultsKey) {
            let script = WKUserScript(
                source: "window.__petSavedState = \(jsString(saved));",
                injectionTime: .atDocumentStart, forMainFrameOnly: true
            )
            controller.addUserScript(script)
        }
        config.userContentController = controller
        webView = WKWebView(frame: NSRect(origin: .zero, size: petWindowSize), configuration: config)
        webView.navigationDelegate = self
        webView.setValue(false, forKey: "drawsBackground")
        if #available(macOS 12.0, *) { webView.underPageBackgroundColor = .clear }
        webView.autoresizingMask = [.width, .height]
    }

    private func buildWindow() {
        window = PetWindow(
            contentRect: NSRect(origin: .zero, size: petWindowSize),
            styleMask: [.borderless], backing: .buffered, defer: false
        )
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.level = .floating
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]
        window.isReleasedWhenClosed = false
        window.isMovableByWindowBackground = false
        window.contentView = webView
        window.onDragStart = { [weak self] in self?.dragStarted() }
        window.onDrag = { [weak self] vx, vy in self?.dragMoved(vx, vy) }
        window.onDragEnd = { [weak self] vx, vy in self?.dragEnded(vx, vy) }
        window.onRightClick = { [weak self] in self?.showPetMenu() }

        let screen = NSScreen.main ?? NSScreen.screens[0]
        let visible = screen.visibleFrame
        let savedX = UserDefaults.standard.object(forKey: windowXDefaultsKey) as? Double
        let x = savedX.map { CGFloat($0) } ?? (visible.maxX - petWindowSize.width - 48)
        window.setFrameOrigin(NSPoint(x: clampX(x, in: visible), y: visible.minY))
        window.orderFrontRegardless()
    }

    /// The menu bar strip a Dock app is expected to have. Harmless while running as an accessory.
    private func buildMainMenu() {
        let main = NSMenu()

        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "About Bitling", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(.separator())
        let room = NSMenuItem(title: "Control Room", action: #selector(openPanel), keyEquivalent: ",")
        room.target = self
        appMenu.addItem(room)
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Hide Bitling", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        let others = NSMenuItem(title: "Hide Others", action: #selector(NSApplication.hideOtherApplications(_:)), keyEquivalent: "h")
        others.keyEquivalentModifierMask = [.command, .option]
        appMenu.addItem(others)
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Quit Bitling", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        main.addItem(appItem)

        let editItem = NSMenuItem()
        let editMenu = NSMenu(title: "Edit")
        editMenu.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
        let redo = NSMenuItem(title: "Redo", action: Selector(("redo:")), keyEquivalent: "z")
        redo.keyEquivalentModifierMask = [.command, .shift]
        editMenu.addItem(redo)
        editMenu.addItem(.separator())
        editMenu.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = editMenu
        main.addItem(editItem)

        let windowItem = NSMenuItem()
        let windowMenu = NSMenu(title: "Window")
        windowMenu.addItem(withTitle: "Minimize", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        windowMenu.addItem(withTitle: "Close", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        windowItem.submenu = windowMenu
        main.addItem(windowItem)

        NSApp.mainMenu = main
        NSApp.windowsMenu = windowMenu
    }

    private func setDockIcon(_ enabled: Bool) {
        dockIconEnabled = enabled
        UserDefaults.standard.set(enabled, forKey: dockIconDefaultsKey)
        NSApp.setActivationPolicy(enabled ? .regular : .accessory)
        if enabled { NSApp.activate(ignoringOtherApps: true) }
    }

    private func buildStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = statusItem.button {
            let image = NSImage(systemSymbolName: "face.smiling", accessibilityDescription: "Bitling")
            image?.isTemplate = true
            button.image = image
            button.toolTip = "Bitling"
        }
        menu.delegate = self
        menu.autoenablesItems = false
        for item in [headerItem, stageItem, tummyItem, energyItem, joyItem] { item.isEnabled = false }
        headerItem.attributedTitle = NSAttributedString(string: "Bitling", attributes: [.font: NSFont.boldSystemFont(ofSize: 13)])
        menu.addItem(headerItem)
        menu.addItem(stageItem)
        menu.addItem(tummyItem)
        menu.addItem(energyItem)
        menu.addItem(joyItem)
        menu.addItem(.separator())
        controlItem.target = self
        menu.addItem(controlItem)
        menu.addItem(.separator())
        for item in [patItem, feedItem, playItem, sleepItem] { item.target = self; menu.addItem(item) }
        menu.addItem(.separator())
        for item in [showItem, bringItem, renameItem, soundItem, resetItem] { item.target = self; menu.addItem(item) }
        menu.addItem(.separator())
        gitMenu.autoenablesItems = false
        for item in [gitWatchingItem, gitTodayItem, gitLastItem, gitTotalsItem] { item.isEnabled = false; gitMenu.addItem(item) }
        gitMenu.addItem(.separator())
        for item in [ciStatusItem, ciLastItem] { item.isEnabled = false; gitMenu.addItem(item) }
        gitMenu.addItem(.separator())
        for item in [claudeStatusItem, claudeTodayItem, claudeLastItem] { item.isEnabled = false; gitMenu.addItem(item) }
        hooksItem.target = self
        gitMenu.addItem(hooksItem)
        swarmItem.target = self
        gitMenu.addItem(swarmItem)
        gitMenu.addItem(.separator())
        gitHooksItem.target = self
        gitMenu.addItem(gitHooksItem)
        let rescan = NSMenuItem(title: "Rescan for repositories now", action: #selector(rescanRepos), keyEquivalent: "")
        rescan.target = self
        gitMenu.addItem(rescan)
        let watchFolder = NSMenuItem(title: "Also watch a folder outside home…", action: #selector(watchFolder), keyEquivalent: "")
        watchFolder.target = self
        gitMenu.addItem(watchFolder)
        let stopItem = NSMenuItem(title: "Stop watching extra folder", action: nil, keyEquivalent: "")
        stopItem.submenu = stopWatchingMenu
        gitMenu.addItem(stopItem)
        gitMenu.addItem(.separator())
        let pretend = NSMenuItem(title: "Pretend I committed", action: #selector(pretendCommit), keyEquivalent: "")
        pretend.target = self
        gitMenu.addItem(pretend)
        let pretendPush = NSMenuItem(title: "Pretend I pushed", action: #selector(pretendPush), keyEquivalent: "")
        pretendPush.target = self
        gitMenu.addItem(pretendPush)
        let pretendFail = NSMenuItem(title: "Pretend tests failed", action: #selector(pretendTestsFailed), keyEquivalent: "")
        pretendFail.target = self
        gitMenu.addItem(pretendFail)
        let pretendDeploy = NSMenuItem(title: "Pretend a deploy ran", action: #selector(pretendDeploy), keyEquivalent: "")
        pretendDeploy.target = self
        gitMenu.addItem(pretendDeploy)
        gitItem.submenu = gitMenu
        menu.addItem(gitItem)
        menu.addItem(.separator())
        loginItem.target = self
        menu.addItem(loginItem)
        let quit = NSMenuItem(title: "Quit Bitling", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        menu.addItem(quit)
        statusItem.menu = menu
    }

    private func loadPage() {
        guard let url = Bundle.main.url(forResource: "pet", withExtension: "html") else {
            fatalError("pet.html missing from the app bundle")
        }
        webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
    }

    // MARK: Bridge

    private func js(_ code: String) {
        guard pageReady else { return }
        webView.evaluateJavaScript(code) { _, _ in }
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        pageReady = true
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let body = message.body as? [String: Any], let type = body["type"] as? String else { return }
        switch type {
        case "save":
            if let json = body["json"] as? String { UserDefaults.standard.set(json, forKey: stateDefaultsKey) }
        case "state":
            if let snap = PetSnapshot(message: body) {
                snapshot = snap
                applyLocomotion(snap.locomotion == "float")
            }
        case "walk":
            let direction = (body["dir"] as? Double ?? 1) < 0 ? CGFloat(-1) : CGFloat(1)
            startWalk(direction: direction)
        case "fly":
            guard !dragging, !airborne, flight == .none else { return }
            let fx = CGFloat(body["x"] as? Double ?? 0.5), fy = CGFloat(body["y"] as? Double ?? 0.5)
            let visible = screenForWindow().visibleFrame
            flyTarget = NSPoint(
                x: visible.minX + min(max(fx, 0), 1) * max(0, visible.width - petWindowSize.width),
                y: visible.minY + (1 - min(max(fy, 0), 1)) * max(0, visible.height - petWindowSize.height)
            )
            walkRemaining = 0
            if walkDirection != 0 { walkDirection = 0; js("petNative.walking(0)") }
            flight = .flying
            js("petNative.flight('takeoff')")
        case "land":
            guard flight != .none else { return }
            flight = .landing
            js("petNative.flight('landing')")
        case "bugs":
            guard swarmEnabled else { return }
            overlay.release(count: body["n"] as? Int ?? 1,
                            labels: body["labels"] as? [String] ?? [],
                            persistent: body["persistent"] as? Bool ?? false,
                            on: screenForWindow(), floorScreenY: petFloorY(), fromScreenX: window.frame.midX)
        case "tests":
            guard swarmEnabled else { return }
            overlay.reconcile(failing: body["failing"] as? [String] ?? [],
                              on: screenForWindow(), floorScreenY: petFloorY(), fromScreenX: window.frame.midX)
            overlay.syncBoss(failures: body["count"] as? Int ?? 0)
        case "doomAll":
            overlay.doomAll()
        case "boss":
            guard swarmEnabled else { return }
            overlay.releaseBoss(hp: body["hp"] as? Int ?? 3,
                                label: body["label"] as? String ?? "",
                                on: screenForWindow(), floorScreenY: petFloorY(), fromScreenX: window.frame.midX)
        case "clearBugs":
            overlay.clearBeetles()
        case "zap":
            let id = body["id"] as? Int ?? -1
            let eyes = (body["eyes"] as? [[String: Any]] ?? []).map { eye in
                CGPoint(x: window.frame.minX + CGFloat(eye["x"] as? Double ?? 0),
                        y: window.frame.maxY - CGFloat(eye["y"] as? Double ?? 0))
            }
            let attackStyle = (body["style"] as? String) ?? snapshot.attack
            overlay.fire(at: id, fromEyes: eyes, style: attackStyle)
        case "rocketScreen":
            guard swarmEnabled else { return }
            overlay.launchRocket(label: body["label"] as? String ?? "",
                                 on: screenForWindow(),
                                 fromScreen: CGPoint(x: window.frame.midX,
                                                     y: window.frame.maxY - CGFloat(body["y"] as? Double ?? 90)))
        case "askName":
            let first = body["first"] as? Bool ?? false
            let suggestion = body["suggestion"] as? String ?? "Pip"
            DispatchQueue.main.async { self.askName(first: first, suggestion: suggestion) }
        case "hover":
            lastHoverReport = Date()
            setClickThrough(!(body["on"] as? Bool ?? true))
        case "species":
            if let list = body["list"] as? [[String: Any]] {
                speciesCatalogue = list
                panel.refresh()
            }
        case "ready":
            pageReady = true
            js("petNative.swarmMode(\(swarmEnabled ? "true" : "false"))")
        default:
            break
        }
    }

    // MARK: Menu

    private func meter(_ label: String, _ value: Int) -> String {
        let filled = max(0, min(10, Int((Double(value) / 10.0).rounded())))
        let bar = String(repeating: "●", count: filled) + String(repeating: "○", count: 10 - filled)
        return "\(label)  \(bar)  \(value)%"
    }

    func menuNeedsUpdate(_ menu: NSMenu) {
        headerItem.attributedTitle = NSAttributedString(
            string: snapshot.hatched ? snapshot.name : "A mysterious box",
            attributes: [.font: NSFont.boldSystemFont(ofSize: 13)]
        )
        stageItem.title = snapshot.hatched ? "\(snapshot.stage) · \(snapshot.age)" : "Tap it three times to unbox"
        tummyItem.isHidden = !snapshot.hatched
        energyItem.isHidden = !snapshot.hatched
        joyItem.isHidden = !snapshot.hatched
        tummyItem.title = meter("Tummy ", snapshot.full)
        energyItem.title = meter("Energy", snapshot.energy)
        joyItem.title = meter("Joy   ", snapshot.joy)
        patItem.title = snapshot.hatched ? (snapshot.asleep ? "Wake with a pat" : "Pat") : "Tap the box"
        feedItem.isEnabled = snapshot.hatched && !snapshot.asleep
        playItem.isEnabled = snapshot.hatched && !snapshot.asleep
        sleepItem.isEnabled = snapshot.hatched
        sleepItem.title = snapshot.asleep ? "Wake" : "Sleep"
        showItem.title = window.isVisible ? "Hide pet" : "Show pet"
        let extras = git.extraRoots.count
        let scope = extras == 0 ? "this Mac" : "this Mac + \(extras) extra folder\(extras == 1 ? "" : "s")"
        gitWatchingItem.title = "Watching \(git.repositoryCount) repositories across \(scope)"
        gitHooksItem.title = GitHooks.installed() ? "Disconnect global git hooks" : "Connect global git hooks…"
        gitTodayItem.title = "Today: \(git.commitsToday) commit\(git.commitsToday == 1 ? "" : "s") · \(git.pushesToday) push\(git.pushesToday == 1 ? "" : "es")"
        gitLastItem.title = "Last: \(git.lastEventSummary)"
        gitTotalsItem.title = "Lifetime: \(snapshot.commits) commits caught · \(snapshot.pushes) pushes · \(snapshot.bugs) bugs squashed"
        ciStatusItem.title = "CI: \(ci.ghStatus) · pytest caches"
        ciLastItem.title = "Last CI: \(ci.lastSummary)"
        let hooked = ClaudeHooks.installed()
        let active = claude.activeSessionCount
        claudeStatusItem.title = "Claude Code: \(active) active session\(active == 1 ? "" : "s") · \(hooked ? "hooks connected" : "transcripts only")"
        claudeTodayItem.title = "Today: \(claude.promptsToday) prompt\(claude.promptsToday == 1 ? "" : "s") · \(claude.toolsToday) tool calls · \(claude.sessionsToday) new session\(claude.sessionsToday == 1 ? "" : "s")"
        claudeLastItem.title = "Last: \(claude.lastSummary)"
        hooksItem.title = hooked ? "Disconnect Claude Code hooks" : "Connect Claude Code hooks…"
        swarmItem.state = swarmEnabled ? .on : .off
        stopWatchingMenu.removeAllItems()
        stopWatchingMenu.autoenablesItems = false
        if git.extraRoots.isEmpty {
            let none = NSMenuItem(title: "No extra folders", action: nil, keyEquivalent: "")
            none.isEnabled = false
            stopWatchingMenu.addItem(none)
        }
        for root in git.extraRoots {
            let item = NSMenuItem(title: root.path.replacingOccurrences(of: NSHomeDirectory(), with: "~"), action: #selector(stopWatching(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = root
            stopWatchingMenu.addItem(item)
        }
        renameItem.isEnabled = snapshot.hatched
        soundItem.state = snapshot.sound ? .on : .off
        if #available(macOS 13.0, *) {
            loginItem.isHidden = false
            loginItem.state = SMAppService.mainApp.status == .enabled ? .on : .off
        } else {
            loginItem.isHidden = true
        }
    }

    // MARK: Control room

    @objc private func openPanel() { panel.show() }

    private func openAtLoginEnabled() -> Bool {
        guard #available(macOS 13.0, *) else { return false }
        return SMAppService.mainApp.status == .enabled
    }

    private func panelPayload() -> [String: Any] {
        let ghConnected = ci.ghStatus.hasPrefix("GitHub Actions")
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "?"
        return [
            "pet": [
                "name": snapshot.name, "stage": snapshot.stage, "age": snapshot.age,
                "full": snapshot.full, "energy": snapshot.energy, "joy": snapshot.joy,
                "asleep": snapshot.asleep, "hatched": snapshot.hatched,
                "working": snapshot.working, "screen": snapshot.screen,
                "sound": snapshot.sound, "species": snapshot.species,
            ],
            "today": [
                "commits": git.commitsToday, "pushes": git.pushesToday,
                "prompts": claude.promptsToday, "tools": claude.toolsToday,
                "zapped": snapshot.bugsToday,
            ],
            "lifetime": ["commits": snapshot.commits, "pushes": snapshot.pushes, "bugs": snapshot.bugs],
            "watch": [
                "repos": git.repositoryCount,
                "roots": git.extraRoots.count,
                "claudeActive": claude.activeSessionCount,
                "login": openAtLoginEnabled(),
                "ci": ghConnected ? "GitHub Actions" : "CI needs gh",
                "ciOn": ghConnected,
                "ciDetail": "\(ci.ghStatus). Last: \(ci.lastSummary)",
                "claudeHooks": ClaudeHooks.installed(),
                "gitHooks": GitHooks.installed(),
                "swarm": swarmEnabled,
                "petVisible": window.isVisible,
                "size": Double(petSizeScale),
                "dock": dockIconEnabled,
                "version": version,
            ],
            "species": speciesCatalogue,
            "events": activity.entries.map(\.asDictionary),
        ]
    }

    private func handlePanelAction(_ action: String) {
        switch action {
        case "pat": patAction()
        case "feed": feedAction()
        case "play": playAction()
        case "sleep": sleepAction()
        case "rescan": rescanRepos()
        case "gitHooks": toggleGitHooks()
        case "claudeHooks": toggleClaudeHooks()
        case "swarm": toggleSwarm()
        case "hide": toggleShown()
        case _ where action.hasPrefix("size:"):
            applyPetSize(CGFloat(Double(action.dropFirst(5)) ?? 1))
        case "rename": renameAction()
        case "sound": soundAction()
        case "login": toggleLogin()
        case "reset": resetAction()
        case "watchFolder": watchFolder()
        case "bringHere": bringHere()
        case "dock": setDockIcon(!dockIconEnabled)
        case "repo": NSWorkspace.shared.open(URL(string: "https://github.com/jadhavgaurav/bitling")!)
        case "quit": NSApp.terminate(nil)
        default:
            // "pet:<id>" from the picker.
            guard action.hasPrefix("pet:") else { return }
            js("petNative.setSpecies(\(jsString(String(action.dropFirst(4)))))")
        }
        panel.refresh()
    }

    @objc private func patAction() { js("petNative.action('pat')") }
    @objc private func feedAction() { js("petNative.action('feed')") }
    @objc private func playAction() { js("petNative.action('play')") }
    @objc private func sleepAction() { js("petNative.action('sleep')") }
    @objc private func soundAction() { js("petNative.action('sound')") }

    /// Right clicking the pet opens the same menu as the menu bar item.
    private func showPetMenu() {
        NSApp.activate(ignoringOtherApps: true)
        let attached = statusItem.menu
        statusItem.menu = nil
        menu.popUp(positioning: nil, at: NSEvent.mouseLocation, in: nil)
        statusItem.menu = attached
    }

    @objc private func toggleShown() {
        if window.isVisible { window.orderOut(nil) } else { window.orderFrontRegardless() }
    }

    @objc private func bringHere() {
        let screen = screenUnderMouse()
        let visible = screen.visibleFrame
        airborne = false
        flight = .none
        js("petNative.flight('landed')")
        walkRemaining = 0
        velocityX = 0
        velocityY = 0
        window.setFrameOrigin(NSPoint(x: visible.midX - petWindowSize.width / 2, y: visible.minY))
        window.orderFrontRegardless()
        saveWindowX()
    }

    @objc private func renameAction() {
        askName(first: false, suggestion: snapshot.name)
    }

    @objc private func resetAction() {
        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.messageText = "Start over?"
        alert.informativeText = snapshot.hatched
            ? "\(snapshot.name) and its history will be gone for good. A new egg will take its place."
            : "The box will be replaced with a fresh one."
        alert.alertStyle = .warning
        alert.addButton(withTitle: "Keep my pet")
        alert.addButton(withTitle: "Start over")
        if alert.runModal() == .alertSecondButtonReturn {
            UserDefaults.standard.removeObject(forKey: stateDefaultsKey)
            activity.clear()
            js("petNative.reset()")
            panel.refresh()
        }
    }

    @objc private func toggleLogin() {
        guard #available(macOS 13.0, *) else { return }
        let service = SMAppService.mainApp
        do {
            if service.status == .enabled { try service.unregister() } else { try service.register() }
        } catch {
            NSApp.activate(ignoringOtherApps: true)
            let alert = NSAlert()
            alert.messageText = "Could not change the login setting"
            alert.informativeText = "\(error.localizedDescription)\n\nMove Bitling.app to the Applications folder and try again."
            alert.runModal()
        }
    }

    // MARK: Git

    private func deliverGitEvent(_ event: GitEvent) {
        // Hooks and transcript tailing can report the same moment; keep the first within 3 seconds.
        if event.kind.hasPrefix("claude-") {
            let key = "\(event.kind)|\(event.name)"
            let now = Date()
            recentEvents = recentEvents.filter { now.timeIntervalSince($0.value) < 30 }
            if let last = recentEvents[key], now.timeIntervalSince(last) < 3 { return }
            recentEvents[key] = now
        }
        activity.record(event)
        panel.refresh()
        guard let data = try? JSONSerialization.data(withJSONObject: event.asDictionary),
              let json = String(data: data, encoding: .utf8) else { return }
        js("petNative.gitEvent(\(json))")
    }

    private func deliverGitStatus(_ status: GitStatus) {
        guard let data = try? JSONSerialization.data(withJSONObject: status.asDictionary),
              let json = String(data: data, encoding: .utf8) else { return }
        js("petNative.gitStatus(\(json))")
    }

    @objc private func watchFolder() {
        NSApp.activate(ignoringOtherApps: true)
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = true
        panel.prompt = "Watch"
        panel.message = "Bitling will look for git repositories up to three folders deep."
        guard panel.runModal() == .OK else { return }
        for url in panel.urls { git.addRoot(url) }
    }

    @objc private func stopWatching(_ sender: NSMenuItem) {
        guard let url = sender.representedObject as? URL else { return }
        git.removeRoot(url)
    }

    @objc private func rescanRepos() {
        git.rescan()
        js("petNative.gitEvent({kind:'say', message: 'looking for repos…'})")
    }

    @objc private func toggleGitHooks() {
        NSApp.activate(ignoringOtherApps: true)
        let installed = GitHooks.installed()
        let alert = NSAlert()
        alert.messageText = installed ? "Disconnect global git hooks?" : "Connect global git hooks?"
        alert.informativeText = installed
            ? "Restores your previous global core.hooksPath setting. Bitling keeps noticing git activity by watching repositories directly."
            : "Sets git's global core.hooksPath to Bitling's hook folder so every repository on this Mac reports commits, merges, checkouts, rebases and pushes the moment they happen, even ones outside your home folder. Each hook calls your repository's own hook afterwards, and any global hooks path you already use is chained too."
        alert.addButton(withTitle: installed ? "Disconnect" : "Connect")
        alert.addButton(withTitle: "Cancel")
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        do {
            if installed { try GitHooks.uninstall() } else { try GitHooks.install() }
            js("petNative.gitEvent({kind:'say', message: \(jsString(installed ? "hooks off" : "hooks on, every repo"))})")
        } catch {
            let failure = NSAlert()
            failure.messageText = "Could not update the git hooks setting"
            failure.informativeText = error.localizedDescription
            failure.runModal()
        }
    }

    @objc private func pretendCommit() {
        let samples = ["fix: stop the widget from eating cookies", "wip", "feat: add jelly physics", "typo in README", "Revert \"remove tests\"", "refactor everything"]
        deliverGitEvent(GitEvent(kind: "commit", repo: "demo", branch: "main", message: samples.randomElement() ?? "commit", hash: String(UUID().uuidString.prefix(7)).lowercased(), insertions: Int.random(in: 1...600), deletions: Int.random(in: 0...80), files: Int.random(in: 1...12)))
    }

    @objc private func pretendPush() {
        deliverGitEvent(GitEvent(kind: "push", repo: "demo", branch: "main", message: "", hash: ""))
    }

    @objc private func toggleClaudeHooks() {
        NSApp.activate(ignoringOtherApps: true)
        let installed = ClaudeHooks.installed()
        let alert = NSAlert()
        alert.messageText = installed ? "Disconnect Claude Code hooks?" : "Connect Claude Code hooks?"
        alert.informativeText = installed
            ? "Removes the Bitling entries from the hooks section of ~/.claude/settings.json. Other hooks stay untouched. Bitling keeps watching transcripts."
            : "Adds Bitling to the hooks section of ~/.claude/settings.json for SessionStart, UserPromptSubmit, PreToolUse, Stop, Notification and SessionEnd. Each hook runs \(ClaudeHooks.command) which forwards one event to the pet. Existing hooks are kept, and a backup is written next to the file. This makes reactions instant and lets the pet tell you when Claude is waiting for permission."
        alert.addButton(withTitle: installed ? "Disconnect" : "Connect")
        alert.addButton(withTitle: "Cancel")
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        do {
            if installed { try ClaudeHooks.uninstall() } else { try ClaudeHooks.install() }
            js("petNative.gitEvent({kind:'say', message: \(jsString(installed ? "hooks off. still watching." : "hooks on. I hear everything now."))})")
        } catch {
            let failure = NSAlert()
            failure.messageText = "Could not update ~/.claude/settings.json"
            failure.informativeText = error.localizedDescription
            failure.runModal()
        }
    }

    /// The line the pet stands on, in screen coordinates. The page keeps its ground
    /// 34px above the bottom of the window.
    /// Swallow clicks only where the creature actually is. Never while it is being dragged:
    /// a fast drag can outrun the cursor probe, and losing the pet mid-throw is worse than
    /// blocking a click. Flight is fine, since the host moves the window, not the mouse.
    private func setClickThrough(_ through: Bool) {
        let value = through && !dragging
        if window.ignoresMouseEvents != value { window.ignoresMouseEvents = value }
    }

    /// Where the creature's feet are in screen coordinates. A floater hangs in the
    /// middle of its window rather than standing on the bottom edge of it.
    /// Resize the creature in place: keep it centred on where it was and, if it was
    /// standing on the floor, keep it standing on the floor.
    private func applyPetSize(_ scale: CGFloat) {
        let wanted = max(0.7, min(2.0, scale))
        guard abs(wanted - petSizeScale) > 0.01 else { return }
        petSizeScale = wanted
        UserDefaults.standard.set(Double(wanted), forKey: petSizeDefaultsKey)
        let visible = screenForWindow().visibleFrame
        var frame = window.frame
        let centreX = frame.midX
        let onFloor = abs(frame.minY - visible.minY) < 2
        frame.size = petWindowSize
        frame.origin.x = clampX(centreX - petWindowSize.width / 2, in: visible)
        frame.origin.y = onFloor ? visible.minY : min(frame.origin.y, visible.maxY - frame.height)
        window.setFrame(frame, display: true)
        hoverBase = frame.origin
        saveWindowX()
    }

    private func petFloorY() -> CGFloat {
        floating ? window.frame.minY + petWindowSize.height * 0.46 : window.frame.minY + 34
    }

    /// Switching between a walker and a floater has to move the creature: one belongs on
    /// the floor, the other in the air.
    private func applyLocomotion(_ isFloat: Bool) {
        guard isFloat != floating else { return }
        floating = isFloat
        guard !dragging else { return }
        if isFloat {
            airborne = false
            chuteOpen = false
            velocityX = 0
            velocityY = 0
            walkRemaining = 0
            if walkDirection != 0 { walkDirection = 0; js("petNative.walking(0)") }
            let visible = screenForWindow().visibleFrame
            flyTarget = NSPoint(
                x: clampX(window.frame.origin.x, in: visible),
                y: visible.minY + visible.height * 0.42
            )
            flight = .flying
            js("petNative.flight('takeoff')")
        } else if flight != .none {
            flight = .landing
            js("petNative.flight('landing')")
        }
    }

    @objc private func toggleSwarm() {
        swarmEnabled.toggle()
        UserDefaults.standard.set(swarmEnabled, forKey: "swarmOnDesktop")
        if !swarmEnabled { overlay.clearBeetles() }
        js("petNative.swarmMode(\(swarmEnabled ? "true" : "false"))")
    }

    @objc private func pretendTestsFailed() {
        deliverGitEvent(GitEvent(kind: "test-failed", repo: "demo", branch: "main", message: "pytest", hash: "", count: Int.random(in: 1...4), name: "demo/api"))
        DispatchQueue.main.asyncAfter(deadline: .now() + 14) { [weak self] in
            self?.deliverGitEvent(GitEvent(kind: "test-passed", repo: "demo", branch: "main", message: "pytest", hash: "", name: "demo/api"))
        }
    }

    @objc private func pretendDeploy() {
        deliverGitEvent(GitEvent(kind: "deploy-started", repo: "demo", branch: "main", message: "", hash: "", target: "production"))
        DispatchQueue.main.asyncAfter(deadline: .now() + 6) { [weak self] in
            self?.deliverGitEvent(GitEvent(kind: "deploy-finished", repo: "demo", branch: "main", message: "", hash: "", target: "production"))
        }
    }

    private func askName(first: Bool, suggestion: String) {
        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.messageText = first ? "It booted up!" : "Rename your Bitling"
        alert.informativeText = first
            ? "Give your Bitling a name. You can change it later from the menu bar."
            : "Pick a new name."
        let field = NSTextField(frame: NSRect(x: 0, y: 0, width: 220, height: 24))
        field.stringValue = suggestion
        field.placeholderString = "Give it a name"
        alert.accessoryView = field
        alert.window.initialFirstResponder = field
        alert.addButton(withTitle: first ? "Name it" : "Rename")
        alert.addButton(withTitle: "Cancel")
        let response = alert.runModal()
        let typed = field.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        let name = response == .alertFirstButtonReturn && !typed.isEmpty ? typed : (first ? suggestion : "")
        if !name.isEmpty { js("petNative.setName(\(jsString(name)))") }
    }

    // MARK: Motion

    private func screenForWindow() -> NSScreen {
        window.screen ?? NSScreen.main ?? NSScreen.screens[0]
    }

    private func screenUnderMouse() -> NSScreen {
        let mouse = NSEvent.mouseLocation
        return NSScreen.screens.first { $0.frame.contains(mouse) } ?? NSScreen.main ?? NSScreen.screens[0]
    }

    private func clampX(_ x: CGFloat, in visible: NSRect) -> CGFloat {
        min(max(x, visible.minX), max(visible.minX, visible.maxX - petWindowSize.width))
    }


    private func saveWindowX() {
        UserDefaults.standard.set(Double(window.frame.minX), forKey: windowXDefaultsKey)
    }

    private func dragStarted() {
        dragging = true
        chuteOpen = false
        wasFlying = flight != .none
        flight = .none
        airborne = false
        walkRemaining = 0
        if walkDirection != 0 { walkDirection = 0; js("petNative.walking(0)") }
        dragEventCount = 0
        js("petNative.grab()")
    }

    private func dragMoved(_ vx: CGFloat, _ vy: CGFloat) {
        dragEventCount += 1
        if dragEventCount % 3 == 0 { js("petNative.drag(\(Int(vx)), \(Int(vy)))") }
    }

    private func dragEnded(_ vx: CGFloat, _ vy: CGFloat) {
        defer { lastHoverReport = Date() }
        dragging = false
        js("petNative.release()")
        if floating {
            // Dropped a floater: it simply stays in the air where you left it.
            flight = .hovering
            hoverBase = window.frame.origin
            hoverT = 0
            airborne = false
            velocityX = 0
            velocityY = 0
            js("petNative.flight('hover')")
            return
        }
        let onFloor = abs(window.frame.minY - screenForWindow().visibleFrame.minY) < 2
        if wasFlying && hypot(vx, vy) < 260 && !onFloor {
            // Let go gently mid-air while it was flying: it hovers where it was left.
            flight = .hovering
            hoverBase = window.frame.origin
            hoverT = 0
            js("petNative.flight('hover')")
            return
        }
        velocityX = max(-2200, min(2200, vx))
        velocityY = max(-2200, min(2200, vy))
        airborne = true
        js("petNative.flight('thrown')")
    }

    private func startWalk(direction: CGFloat) {
        guard !floating else { return }
        guard !dragging, !airborne, flight == .none, walkRemaining <= 0, window.isVisible else { return }
        let visible = screenForWindow().visibleFrame
        let distance = CGFloat.random(in: 80...200)
        var dir = direction
        let target = window.frame.minX + dir * distance
        if target < visible.minX || target + petWindowSize.width > visible.maxX { dir = -dir }
        walkDirection = dir
        walkRemaining = distance
        js("petNative.walking(\(Int(dir)))")
    }

    @objc private func screensChanged() {
        // The floor may have moved (dock, resolution, display added or removed): let gravity sort it out.
        let visible = screenForWindow().visibleFrame
        var origin = window.frame.origin
        origin.x = clampX(origin.x, in: visible)
        if origin.y < visible.minY { origin.y = visible.minY }
        window.setFrameOrigin(origin)
        if flight != .none { hoverBase = origin; flyTarget = origin; return }
        airborne = true
    }

    private func tick() {
        tickCount += 1
        if tickCount % 30 == 0 { panel.refresh() }
        guard !dragging else { return }
        let dt: CGFloat = 1.0 / 60.0
        let visible = screenForWindow().visibleFrame
        var frame = window.frame
        let floor = visible.minY

        switch flight {
        case .flying:
            chuteOpen = false
            let dx = flyTarget.x - frame.origin.x, dy = flyTarget.y - frame.origin.y
            let dist = hypot(dx, dy)
            if dist < 3 {
                flight = .hovering
                hoverBase = frame.origin
                hoverT = 0
                js("petNative.flight('hover')")
            } else {
                let speed = min(380, 70 + dist * 2.2)
                frame.origin.x += dx / dist * speed * dt
                frame.origin.y += dy / dist * speed * dt
                window.setFrameOrigin(frame.origin)
                // Tell the page which way it is travelling so it can pitch into the flight
                // and aim its thrust backwards. Screen coordinates: y grows downward.
                if tickCount % 6 == 0 {
                    js("petNative.flightVec(\(String(format: "%.2f", dx / dist)), \(String(format: "%.2f", -dy / dist)))")
                }
            }
        case .hovering:
            if tickCount % 12 == 0 { js("petNative.flightVec(0, 0)") }
            hoverT += dt
            frame.origin = NSPoint(x: hoverBase.x + sin(hoverT * 0.9) * 8, y: hoverBase.y + sin(hoverT * 2.1) * 5)
            window.setFrameOrigin(frame.origin)
        case .landing:
            frame.origin.y -= 230 * dt
            frame.origin.x = clampX(frame.origin.x, in: visible)
            if frame.origin.y <= floor {
                frame.origin.y = floor
                flight = .none
                airborne = false
                velocityX = 0
                velocityY = 0
                js("petNative.flight('landed')")
                saveWindowX()
            }
            window.setFrameOrigin(frame.origin)
        case .none:
            if airborne {
                let height = frame.minY - floor
                if chuteOpen {
                    // Under canopy: slow terminal descent with a gentle side-to-side drift.
                    velocityY += max(0, (-140 - velocityY)) * min(1, dt * 3)
                    velocityY = max(velocityY, -170)
                    chuteSway += dt * 1.7
                    velocityX += (sin(chuteSway) * 70 - velocityX) * min(1, dt * 2)
                } else {
                    velocityY -= 2600 * dt
                    // Falling fast with room to spare: pop the chute.
                    if velocityY < -620 && height > max(220, visible.height * 0.22) {
                        chuteOpen = true
                        js("petNative.flight('chute')")
                    }
                }
                frame.origin.x += velocityX * dt
                frame.origin.y += velocityY * dt
                if frame.minX < visible.minX { frame.origin.x = visible.minX; velocityX = abs(velocityX) * (chuteOpen ? 0.4 : 0.5) }
                if frame.maxX > visible.maxX { frame.origin.x = visible.maxX - frame.width; velocityX = -abs(velocityX) * (chuteOpen ? 0.4 : 0.5) }
                if frame.maxY > visible.maxY { frame.origin.y = visible.maxY - frame.height; velocityY = -abs(velocityY) * 0.3 }
                if frame.minY <= floor {
                    // Robots land on their feet: no bounce, a knee bend instead.
                    frame.origin.y = floor
                    let impact = chuteOpen ? 0.12 : min(0.45, abs(velocityY) / 2600)
                    velocityY = 0
                    velocityX = 0
                    airborne = false
                    if chuteOpen { chuteOpen = false; js("petNative.flight('chute-cut')") }
                    js("petNative.land(\(String(format: "%.2f", impact)))")
                    saveWindowX()
                }
                window.setFrameOrigin(frame.origin)
            } else if walkRemaining > 0 {
                let speed: CGFloat = snapshot.species == "kaiju" ? 32 : 70
                let step = min(walkRemaining, speed * dt)
                frame.origin.x += step * walkDirection
                walkRemaining -= step
                if frame.minX < visible.minX || frame.maxX > visible.maxX {
                    frame.origin.x = clampX(frame.origin.x, in: visible)
                    walkRemaining = 0
                }
                window.setFrameOrigin(frame.origin)
                if walkRemaining <= 0 {
                    walkDirection = 0
                    js("petNative.walking(0)")
                    saveWindowX()
                }
            } else if abs(frame.minY - floor) > 1 {
                airborne = true
                js("petNative.flight('thrown')")
            }
        }

        if tickCount % 6 == 0 && swarmEnabled && window.isVisible {
            let list = overlay.swarm(relativeTo: window.frame)
            if !list.isEmpty || lastSwarmCount != 0 {
                lastSwarmCount = list.count
                if let data = try? JSONSerialization.data(withJSONObject: list),
                   let json = String(data: data, encoding: .utf8) {
                    js("petNative.swarm(\(json))")
                }
            }
        }

        if window.ignoresMouseEvents, Date().timeIntervalSince(lastHoverReport) > 3 {
            window.ignoresMouseEvents = false
        }

        // Every other tick: the page cannot decide whether the cursor is over the creature
        // until it knows where the cursor is, and that answer gates every click.
        if tickCount % 2 == 0 && window.isVisible {
            let mouse = NSEvent.mouseLocation
            if mouse != lastMouse {
                lastMouse = mouse
                let localX = mouse.x - frame.minX
                let localY = frame.maxY - mouse.y
                js("petNative.cursor(\(Int(localX)), \(Int(localY)))")
            }
        }
    }
}

// MARK: - Global git hooks (core.hooksPath)

enum GitHooks {
    static let hookNames = ["post-commit", "post-merge", "post-checkout", "post-rewrite", "pre-push"]
    private static let previousKey = "gitPreviousHooksPath"

    struct HooksError: LocalizedError {
        let message: String
        var errorDescription: String? { message }
    }

    /// Placeholders: __TOOL__ (path to the bitling command), __NAME__ (hook name),
    /// __CHAIN__ (an optional call into a pre-existing global hooks path).
    private static let hookTemplate = """
    #!/bin/sh
    # Installed by Bitling. Reports this event to the desktop pet, then runs your own hooks.
    "__TOOL__" git __NAME__ "$@" >/dev/null 2>&1 || true
    __CHAIN__
    repo_hook="$(git rev-parse --git-common-dir 2>/dev/null)/hooks/__NAME__"
    if [ -x "$repo_hook" ]; then exec "$repo_hook" "$@"; fi
    exit 0
    """

    static var directory: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/Bitling/githooks")
    }

    @discardableResult
    private static func git(_ arguments: [String]) throws -> String {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/git")
        process.arguments = arguments
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = FileHandle.nullDevice
        try process.run()
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        return String(decoding: data, as: UTF8.self).trimmingCharacters(in: .whitespacesAndNewlines)
    }

    static func currentHooksPath() -> String {
        (try? git(["config", "--global", "--get", "core.hooksPath"])) ?? ""
    }

    static func installed() -> Bool {
        currentHooksPath() == directory.path
    }

    static func install() throws {
        let previous = currentHooksPath()
        if !previous.isEmpty, previous != directory.path {
            UserDefaults.standard.set(previous, forKey: previousKey)
        }
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let tool = "\(Bundle.main.bundlePath)/Contents/Resources/bitling"
        let chained = UserDefaults.standard.string(forKey: previousKey) ?? ""
        for name in hookNames {
            // Built from a template so the shell quoting stays readable.
            var script = Self.hookTemplate
                .replacingOccurrences(of: "__TOOL__", with: tool)
                .replacingOccurrences(of: "__NAME__", with: name)
            if chained.isEmpty {
                script = script.replacingOccurrences(of: "__CHAIN__", with: "")
            } else {
                let chain = """
                if [ -x "\(chained)/\(name)" ]; then
                  "\(chained)/\(name)" "$@" || exit $?
                fi
                """
                script = script.replacingOccurrences(of: "__CHAIN__", with: chain)
            }
            let url = directory.appendingPathComponent(name)
            try script.write(to: url, atomically: true, encoding: .utf8)
            try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: url.path)
        }
        try git(["config", "--global", "core.hooksPath", directory.path])
        guard installed() else { throw HooksError(message: "git did not accept the new core.hooksPath value") }
    }

    static func uninstall() throws {
        let previous = UserDefaults.standard.string(forKey: previousKey) ?? ""
        if previous.isEmpty {
            try git(["config", "--global", "--unset", "core.hooksPath"])
        } else {
            try git(["config", "--global", "core.hooksPath", previous])
        }
        UserDefaults.standard.removeObject(forKey: previousKey)
    }
}

// MARK: - Claude Code hooks in ~/.claude/settings.json

enum ClaudeHooks {
    static let events = ["SessionStart", "UserPromptSubmit", "PreToolUse", "Stop", "Notification", "SessionEnd"]
    static var command: String { "\(Bundle.main.bundlePath)/Contents/Resources/bitling claude" }
    private static var settingsURL: URL {
        FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".claude/settings.json")
    }

    struct HooksError: LocalizedError {
        let message: String
        var errorDescription: String? { message }
    }

    private static func load() throws -> [String: Any] {
        guard FileManager.default.fileExists(atPath: settingsURL.path) else { return [:] }
        let data = try Data(contentsOf: settingsURL)
        guard let object = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw HooksError(message: "settings.json is not a JSON object")
        }
        return object
    }

    private static func save(_ settings: [String: Any]) throws {
        let backup = settingsURL.deletingLastPathComponent().appendingPathComponent("settings.json.bitling-backup")
        if FileManager.default.fileExists(atPath: settingsURL.path) {
            try? FileManager.default.removeItem(at: backup)
            try FileManager.default.copyItem(at: settingsURL, to: backup)
        }
        let data = try JSONSerialization.data(withJSONObject: settings, options: [.prettyPrinted, .sortedKeys])
        try data.write(to: settingsURL, options: .atomic)
    }

    private static func isOurs(_ group: [String: Any]) -> Bool {
        let hooks = group["hooks"] as? [[String: Any]] ?? []
        return !hooks.isEmpty && hooks.allSatisfy { ($0["command"] as? String ?? "").hasSuffix("/bitling claude") }
    }

    static func installed() -> Bool {
        guard let settings = try? load(), let hooks = settings["hooks"] as? [String: Any] else { return false }
        let groups = hooks["UserPromptSubmit"] as? [[String: Any]] ?? []
        return groups.contains(where: isOurs)
    }

    static func install() throws {
        var settings = try load()
        var hooks = settings["hooks"] as? [String: Any] ?? [:]
        for event in events {
            var groups = hooks[event] as? [[String: Any]] ?? []
            groups.removeAll(where: isOurs)
            groups.append(["matcher": "", "hooks": [["type": "command", "command": command, "timeout": 10]]])
            hooks[event] = groups
        }
        settings["hooks"] = hooks
        try save(settings)
    }

    static func uninstall() throws {
        var settings = try load()
        guard var hooks = settings["hooks"] as? [String: Any] else { return }
        for event in events {
            var groups = hooks[event] as? [[String: Any]] ?? []
            groups.removeAll(where: isOurs)
            if groups.isEmpty { hooks.removeValue(forKey: event) } else { hooks[event] = groups }
        }
        settings["hooks"] = hooks
        try save(settings)
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
