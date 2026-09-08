import AppKit
import WebKit

/// One line in the control room's activity stream.
struct ActivityEntry {
    let time: Date
    let kind: String
    let title: String
    let repo: String

    var asDictionary: [String: Any] {
        ["t": Int(time.timeIntervalSince1970 * 1000), "kind": kind, "title": title, "repo": repo]
    }

    init(time: Date = Date(), kind: String, title: String, repo: String) {
        self.time = time
        self.kind = kind
        self.title = title
        self.repo = repo
    }

    init?(dictionary: [String: Any]) {
        guard let ms = dictionary["t"] as? Double,
              let kind = dictionary["kind"] as? String,
              let title = dictionary["title"] as? String else { return nil }
        time = Date(timeIntervalSince1970: ms / 1000)
        self.kind = kind
        self.title = title
        repo = dictionary["repo"] as? String ?? ""
    }
}

/// Turns a raw watcher event into the sentence the stream shows, or nil for the
/// chatter that would only pad the log (idle pings, individual tool calls).
enum ActivityLine {
    static func describe(_ event: GitEvent) -> ActivityEntry? {
        let branch = event.branch.isEmpty ? "a branch" : event.branch
        let subject = event.message.isEmpty ? "no message" : event.message
        let target = event.target.isEmpty ? "somewhere" : event.target
        let title: String

        switch event.kind {
        case "commit", "cherry-pick":
            let counts = event.files > 0 ? " (\(event.files) file\(event.files == 1 ? "" : "s"))" : ""
            title = subject + counts
        case "amend":
            title = "amended: \(subject)"
        case "push":
            title = "pushed \(branch)"
        case "merge":
            title = "merged \(branch)"
        case "checkout":
            title = "switched to \(branch)"
        case "rebase":
            title = "rebasing \(branch)"
        case "rebase-done":
            title = "rebase finished"
        case "pull":
            title = "pulled \(branch)"
        case "stash":
            title = "stashed the working tree"
        case "reset":
            title = "reset \(branch)"
        case "test-failed":
            let n = max(1, event.count)
            title = "\(n) test\(n == 1 ? "" : "s") failing in \(event.name.isEmpty ? "the suite" : event.name)"
        case "test-passed":
            title = "tests green in \(event.name.isEmpty ? "the suite" : event.name)"
        case "deploy-started":
            title = "deploying to \(target)"
        case "deploy-finished":
            title = "deployed to \(target)"
        case "deploy-failed":
            title = "deploy to \(target) failed"
        case "claude-session-start":
            title = "Claude Code session opened"
        case "claude-prompt":
            title = subject == "no message" ? "you asked Claude something" : "you: \(subject)"
        case "claude-done":
            title = subject == "no message" ? "Claude finished" : "Claude: \(subject)"
        case "claude-tool-error":
            title = "a tool call went red"
        case "claude-notify":
            title = "Claude wants your attention"
        default:
            return nil
        }
        return ActivityEntry(kind: event.kind, title: title, repo: event.repo)
    }
}

/// Keeps the recent activity, capped and persisted so the room is not empty after a restart.
final class ActivityLog {
    private static let key = "activityLog"
    private static let limit = 120
    private(set) var entries: [ActivityEntry]

    init() {
        let raw = UserDefaults.standard.array(forKey: Self.key) as? [[String: Any]] ?? []
        entries = raw.compactMap(ActivityEntry.init(dictionary:)).suffix(Self.limit)
    }

    @discardableResult
    func record(_ event: GitEvent) -> ActivityEntry? {
        guard let entry = ActivityLine.describe(event) else { return nil }
        entries.append(entry)
        if entries.count > Self.limit { entries.removeFirst(entries.count - Self.limit) }
        save()
        return entry
    }

    func clear() {
        entries = []
        save()
    }

    private func save() {
        UserDefaults.standard.set(entries.map(\.asDictionary), forKey: Self.key)
    }

    var asJSON: String {
        let payload = entries.map(\.asDictionary)
        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let json = String(data: data, encoding: .utf8) else { return "[]" }
        return json
    }
}

/// The control room: a small window that shows what the pet is doing, what it is
/// watching, and the switches that used to be buried in the menu.
final class ControlPanel: NSObject, WKScriptMessageHandler, WKNavigationDelegate {
    /// Fired for every button, chip and link in the panel.
    var onAction: ((String) -> Void)?
    /// Asked for a fresh payload whenever the page is ready or the window comes back.
    var stateProvider: (() -> [String: Any])?

    private var window: NSWindow?
    private var webView: WKWebView?
    private var ready = false

    var isOpen: Bool { window?.isVisible == true }

    func show() {
        if let window {
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            refresh()
            return
        }
        build()
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    /// Push the whole payload. Cheap enough at the rate the app updates.
    func refresh() {
        guard ready, isOpen, let payload = stateProvider?() else { return }
        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let json = String(data: data, encoding: .utf8) else { return }
        webView?.evaluateJavaScript("window.panel.update(\(json))") { _, _ in }
    }

    // MARK: Window

    private func build() {
        let config = WKWebViewConfiguration()
        let controller = WKUserContentController()
        controller.add(self, name: "panel")
        config.userContentController = controller

        let frame = NSRect(x: 0, y: 0, width: 420, height: 690)
        let view = WKWebView(frame: frame, configuration: config)
        view.navigationDelegate = self
        view.setValue(false, forKey: "drawsBackground")
        if #available(macOS 12.0, *) { view.underPageBackgroundColor = NSColor(red: 0.078, green: 0.086, blue: 0.165, alpha: 1) }
        view.autoresizingMask = [.width, .height]
        webView = view

        let win = NSWindow(
            contentRect: frame,
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered, defer: false
        )
        win.title = "Bitling"
        win.titlebarAppearsTransparent = true
        win.appearance = NSAppearance(named: .darkAqua)
        win.backgroundColor = NSColor(red: 0.078, green: 0.086, blue: 0.165, alpha: 1)
        win.minSize = NSSize(width: 384, height: 520)
        win.contentView = view
        win.isReleasedWhenClosed = false
        win.setFrameAutosaveName("BitlingControlRoom")
        if win.frame.origin == .zero { win.center() }
        window = win

        guard let url = Bundle.main.url(forResource: "panel", withExtension: "html") else {
            fatalError("panel.html missing from the app bundle")
        }
        view.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
    }

    // MARK: Bridge

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        ready = true
        refresh()
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let body = message.body as? [String: Any], let type = body["type"] as? String else { return }
        switch type {
        case "ready":
            ready = true
            refresh()
        case "action":
            guard let value = body["value"] as? String else { return }
            onAction?(value)
        default:
            break
        }
    }
}
