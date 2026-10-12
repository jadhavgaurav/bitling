// QuotaWatcher.swift
//
// Reports the usage limits that Claude and Codex have already written down on this Mac.
// Nothing here is estimated or assumed: a window appears only when a tool recorded it, and
// it carries the time it was recorded so the pet can say how old a figure is instead of
// passing a stale one off as live.
//
//   Claude  ~/Library/Application Support/Claude/plan-usage-history.json
//           Claude Desktop samples the used percent of the 5 hour (fh) and weekly (sd)
//           windows. It records no reset time, so none is shown.
//   Codex   ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl
//           Every turn logs payload.rate_limits with the used percent, the window length
//           and the exact reset time, plus the plan. Only the tail of the newest rollout is
//           read, and only the "codex" bucket: the log also holds a separate "premium" one.

import Foundation
import Security

struct QuotaWindow: Codable, Equatable {
    var usedPercent: Double
    /// Epoch ms. Present only when the tool recorded a reset time.
    var resetsAt: Double?
    /// Epoch ms of the reading itself.
    var asOf: Double
}

struct QuotaProvider: Codable, Equatable {
    var plan: String?
    var fiveHour: QuotaWindow?
    var weekly: QuotaWindow?
    /// Why the live reading is unavailable, when it was asked for. nil when it is working or off.
    var liveStatus: String?
}

struct QuotaData: Codable, Equatable {
    var claude = QuotaProvider()
    var codex = QuotaProvider()
}

/// What the page receives: the readings plus which providers the user wants shown.
struct QuotaPayload: Encodable {
    let claude: QuotaProvider
    let codex: QuotaProvider
    let showClaude: Bool
    let showCodex: Bool

    var json: String {
        guard let data = try? JSONEncoder().encode(self) else { return "{}" }
        return String(decoding: data, as: UTF8.self)
    }
}

enum QuotaReader {
    private static let fiveHours: TimeInterval = 5 * 3600
    private static let sevenDays: TimeInterval = 7 * 86400

    static func read(home: URL, now: Date = Date()) -> QuotaData {
        QuotaData(claude: readClaude(home: home, now: now), codex: readCodex(home: home, now: now))
    }

    // MARK: Claude

    static func readClaude(home: URL, now: Date) -> QuotaProvider {
        var provider = QuotaProvider()
        var orgId: String?
        if let obj = jsonObject(at: home.appendingPathComponent(".claude.json")),
           let account = obj["oauthAccount"] as? [String: Any] {
            orgId = account["organizationUuid"] as? String
            provider.plan = claudePlan(tier: account["organizationRateLimitTier"] as? String)
        }

        let history = home.appendingPathComponent("Library/Application Support/Claude/plan-usage-history.json")
        guard let obj = jsonObject(at: history), let samples = obj["samples"] as? [[String: Any]] else { return provider }

        // The newest sample for this account, or the newest of all when none can be matched.
        func stamp(_ s: [String: Any]) -> Double { (s["t"] as? Double) ?? 0 }
        let mine = samples.filter { orgId != nil && ($0["org"] as? String) == orgId }
        guard let latest = (mine.isEmpty ? samples : mine).max(by: { stamp($0) < stamp($1) }),
              let usage = latest["u"] as? [String: Any], stamp(latest) > 0 else { return provider }

        // A reading older than its own window says nothing about the window that is open now.
        let asOf = stamp(latest)
        let age = now.timeIntervalSince1970 - asOf / 1000
        if let fh = usage["fh"] as? Double, age < fiveHours {
            provider.fiveHour = QuotaWindow(usedPercent: clamp(fh), resetsAt: nil, asOf: asOf)
        }
        if let sd = usage["sd"] as? Double, age < sevenDays {
            provider.weekly = QuotaWindow(usedPercent: clamp(sd), resetsAt: nil, asOf: asOf)
        }
        return provider
    }

    /// "default_claude_max_20x" -> "Max 20x". Anything unrecognised yields nil, not a guess.
    static func claudePlan(tier: String?) -> String? {
        guard let tier = tier?.lowercased() else { return nil }
        if let range = tier.range(of: #"max_(\d+)x"#, options: .regularExpression) {
            let multiple = tier[range].dropFirst("max_".count).dropLast()
            return "Max \(multiple)x"
        }
        if tier.contains("max") { return "Max" }
        if tier.contains("pro") { return "Pro" }
        if tier.contains("team") { return "Team" }
        return nil
    }

    // MARK: Codex

    static func readCodex(home: URL, now: Date) -> QuotaProvider {
        let sessions = home.appendingPathComponent(".codex/sessions")
        for file in recentRollouts(in: sessions, dayFolders: 3, limit: 8) {
            guard let tail = tail(of: file.url, bytes: 512 * 1024) else { continue }
            for line in tail.split(separator: "\n", omittingEmptySubsequences: true).reversed() {
                guard line.contains("\"rate_limits\""),
                      let data = line.data(using: .utf8),
                      let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
                      let payload = obj["payload"] as? [String: Any],
                      let limits = payload["rate_limits"] as? [String: Any],
                      limits["limit_id"] as? String == "codex" else { continue }
                let recorded = timestamp(obj["timestamp"] as? String) ?? file.modified
                return codexProvider(from: limits, recordedAt: recorded, now: now)
            }
        }
        return QuotaProvider()
    }

    static func codexProvider(from limits: [String: Any], recordedAt: Date, now: Date) -> QuotaProvider {
        var provider = QuotaProvider()
        if let plan = limits["plan_type"] as? String, !plan.isEmpty {
            provider.plan = plan.prefix(1).uppercased() + plan.dropFirst()
        }
        let nowMs = now.timeIntervalSince1970 * 1000
        for key in ["primary", "secondary"] {
            guard let raw = limits[key] as? [String: Any],
                  let used = raw["used_percent"] as? Double,
                  let minutes = raw["window_minutes"] as? Double else { continue }
            var window = QuotaWindow(usedPercent: clamp(used),
                                     resetsAt: (raw["resets_at"] as? Double).map { $0 * 1000 },
                                     asOf: recordedAt.timeIntervalSince1970 * 1000)
            // The window rolled over after the last turn was logged. Anything spent since
            // would have been logged too, so the new window is untouched.
            if let reset = window.resetsAt, reset <= nowMs {
                window = QuotaWindow(usedPercent: 0, resetsAt: nil, asOf: reset)
            }
            if minutes <= 600 { provider.fiveHour = window } else { provider.weekly = window }
        }
        return provider
    }

    /// Rollout files from the newest few day folders, most recently written first.
    private static func recentRollouts(in root: URL, dayFolders: Int, limit: Int) -> [(url: URL, modified: Date)] {
        let fm = FileManager.default
        func children(_ url: URL) -> [URL] {
            ((try? fm.contentsOfDirectory(at: url, includingPropertiesForKeys: nil)) ?? [])
                .filter { Int($0.lastPathComponent) != nil }
                .sorted { $0.lastPathComponent > $1.lastPathComponent }
        }
        var days: [URL] = []
        outer: for year in children(root) {
            for month in children(year) {
                for day in children(month) {
                    days.append(day)
                    if days.count == dayFolders { break outer }
                }
            }
        }
        var files: [(url: URL, modified: Date)] = []
        for day in days {
            let urls = (try? fm.contentsOfDirectory(at: day, includingPropertiesForKeys: [.contentModificationDateKey])) ?? []
            for url in urls where url.lastPathComponent.hasPrefix("rollout-") && url.pathExtension == "jsonl" {
                let modified = (try? url.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
                files.append((url, modified))
            }
        }
        return Array(files.sorted { $0.modified > $1.modified }.prefix(limit))
    }

    // MARK: Helpers

    private static func clamp(_ value: Double) -> Double { min(100, max(0, value)) }

    private static func jsonObject(at url: URL) -> [String: Any]? {
        guard let data = try? Data(contentsOf: url) else { return nil }
        return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
    }

    private static func tail(of url: URL, bytes: Int) -> String? {
        guard let handle = try? FileHandle(forReadingFrom: url) else { return nil }
        defer { try? handle.close() }
        guard let size = try? handle.seekToEnd() else { return nil }
        let start = size > UInt64(bytes) ? size - UInt64(bytes) : 0
        guard (try? handle.seek(toOffset: start)) != nil, let data = try? handle.readToEnd() else { return nil }
        return String(decoding: data, as: UTF8.self)
    }

    private static func timestamp(_ text: String?) -> Date? {
        guard let text else { return nil }
        let precise = ISO8601DateFormatter()
        precise.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return precise.date(from: text) ?? ISO8601DateFormatter().date(from: text)
    }
}

// MARK: Live usage
//
// The files above lag. Claude Desktop only samples now and then, and Codex logs only the turns
// its CLI writes to disk, so anything done from the Codex app is invisible there. Both tools
// can say what they know right now, and that is preferred whenever it is available:
//
//   Claude  the endpoint behind Claude Code's /usage. It takes the sign-in token Claude Code
//           keeps in the login keychain. The token is never logged, stored or written
//           anywhere, is sent only to api.anthropic.com, and is never refreshed here:
//           refreshing would rotate it and could sign Claude Code out, so an expired token
//           just means waiting until Claude Code renews it. macOS asks once, in its own
//           dialog, whether Bitling may read the item.
//   Codex   `codex app-server`, asked for account/rateLimits/read. Codex answers with its own
//           sign-in, so no credential passes through Bitling at all.

struct LiveFailure: Error {
    let message: String
    /// How long to leave it alone before asking again. A declined keychain dialog comes back
    /// every time it is asked, so that one is asked rarely.
    let retryAfter: TimeInterval

    static let notSignedIn = LiveFailure(message: "sign in to Claude Code for live usage", retryAfter: 600)
    static let keychainDenied = LiveFailure(message: "keychain access was declined", retryAfter: 3600)
    static let tokenExpired = LiveFailure(message: "waiting for Claude Code to renew its sign-in", retryAfter: 120)
    static let signInRejected = LiveFailure(message: "Claude Code's sign-in was rejected", retryAfter: 120)
    static let rateLimited = LiveFailure(message: "usage service is busy", retryAfter: 300)
    static let offline = LiveFailure(message: "usage service unreachable", retryAfter: 120)
    static let unexpectedResponse = LiveFailure(message: "unexpected usage response", retryAfter: 120)
    static func httpStatus(_ code: Int) -> LiveFailure { LiveFailure(message: "usage service answered \(code)", retryAfter: 120) }
    static let codexMissing = LiveFailure(message: "the codex command was not found", retryAfter: 3600)
    static let codexSilent = LiveFailure(message: "codex did not answer", retryAfter: 120)
    static let codexNotSignedIn = LiveFailure(message: "sign in to Codex for live usage", retryAfter: 600)
}

struct LiveReading {
    var plan: String?
    var fiveHour: QuotaWindow?
    var weekly: QuotaWindow?
    let fetchedAt: Date
}

struct ClaudeCredential: CustomStringConvertible {
    let accessToken: String
    let expiresAt: Date?

    /// Never prints the token, even by accident in a string interpolation.
    var description: String { "ClaudeCredential(<redacted>)" }

    func isExpired(at now: Date) -> Bool { expiresAt.map { $0 <= now } ?? false }

    /// The keychain item is JSON: {"claudeAiOauth": {"accessToken": "...", "expiresAt": <ms>}}.
    static func parse(_ data: Data) -> ClaudeCredential? {
        guard let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
              let oauth = obj["claudeAiOauth"] as? [String: Any],
              let token = oauth["accessToken"] as? String, !token.isEmpty else { return nil }
        let expires = (oauth["expiresAt"] as? Double).map { Date(timeIntervalSince1970: $0 / 1000) }
        return ClaudeCredential(accessToken: token, expiresAt: expires)
    }
}

enum ClaudeUsageParser {
    /// {"five_hour": {"utilization": 37.0, "resets_at": "2026-10-12T09:30:00.123456+00:00"},
    ///  "seven_day": {...}}. A window with no usage comes back null, which means untouched.
    static func parse(_ data: Data, fetchedAt: Date) -> LiveReading? {
        guard let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
              obj.keys.contains("five_hour") || obj.keys.contains("seven_day") else { return nil }
        let now = fetchedAt.timeIntervalSince1970 * 1000
        func window(_ key: String) -> QuotaWindow {
            guard let raw = obj[key] as? [String: Any], let used = raw["utilization"] as? Double else {
                return QuotaWindow(usedPercent: 0, resetsAt: nil, asOf: now)
            }
            return QuotaWindow(usedPercent: min(100, max(0, used)),
                               resetsAt: date(raw["resets_at"] as? String).map { $0.timeIntervalSince1970 * 1000 },
                               asOf: now)
        }
        return LiveReading(plan: nil, fiveHour: window("five_hour"), weekly: window("seven_day"), fetchedAt: fetchedAt)
    }

    private static func date(_ text: String?) -> Date? {
        guard let text else { return nil }
        let precise = ISO8601DateFormatter()
        precise.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return precise.date(from: text) ?? ISO8601DateFormatter().date(from: text)
    }
}

enum CodexUsageParser {
    /// The result of account/rateLimits/read: the "codex" bucket, with the 5 hour window as
    /// `primary` and the weekly one as `secondary`. A window is told apart by its length.
    static func parse(_ result: [String: Any], fetchedAt: Date) -> LiveReading? {
        let byId = result["rateLimitsByLimitId"] as? [String: Any]
        let fallback = result["rateLimits"] as? [String: Any]
        guard let limits = (byId?["codex"] as? [String: Any])
                ?? (fallback?["limitId"] as? String == "codex" ? fallback : nil) else { return nil }
        var reading = LiveReading(plan: nil, fiveHour: nil, weekly: nil, fetchedAt: fetchedAt)
        if let plan = limits["planType"] as? String, !plan.isEmpty {
            reading.plan = plan.prefix(1).uppercased() + plan.dropFirst()
        }
        let now = fetchedAt.timeIntervalSince1970 * 1000
        for key in ["primary", "secondary"] {
            guard let raw = limits[key] as? [String: Any],
                  let used = raw["usedPercent"] as? Double,
                  let minutes = raw["windowDurationMins"] as? Double else { continue }
            let window = QuotaWindow(usedPercent: min(100, max(0, used)),
                                     resetsAt: (raw["resetsAt"] as? Double).map { $0 * 1000 }, asOf: now)
            if minutes <= 600 { reading.fiveHour = window } else { reading.weekly = window }
        }
        return reading.fiveHour == nil && reading.weekly == nil ? nil : reading
    }
}

final class ClaudeLiveUsage {
    private static let endpoint = URL(string: "https://api.anthropic.com/api/oauth/usage")!

    /// Blocks until the keychain dialog (if any) and the request finish: call off the main thread.
    func fetch(now: Date = Date()) -> Result<LiveReading, LiveFailure> {
        let stored: Data
        switch Self.readKeychain() {
        case .success(let data): stored = data
        case .failure(let failure): return .failure(failure)
        }
        guard let credential = ClaudeCredential.parse(stored) else { return .failure(.notSignedIn) }
        if credential.isExpired(at: now) { return .failure(.tokenExpired) }

        var request = URLRequest(url: Self.endpoint, timeoutInterval: 12)
        request.setValue("Bearer \(credential.accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("oauth-2025-04-20", forHTTPHeaderField: "anthropic-beta")
        request.setValue("bitling", forHTTPHeaderField: "User-Agent")

        let done = DispatchSemaphore(value: 0)
        var body: Data?, status: Int?
        URLSession.shared.dataTask(with: request) { data, response, _ in
            body = data; status = (response as? HTTPURLResponse)?.statusCode
            done.signal()
        }.resume()
        _ = done.wait(timeout: .now() + 15)

        guard let status else { return .failure(.offline) }
        switch status {
        case 200:
            guard let body, let reading = ClaudeUsageParser.parse(body, fetchedAt: now) else { return .failure(.unexpectedResponse) }
            return .success(reading)
        case 401, 403: return .failure(.signInRejected)
        case 429: return .failure(.rateLimited)
        default: return .failure(.httpStatus(status))
        }
    }

    private static func readKeychain() -> Result<Data, LiveFailure> {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: "Claude Code-credentials",
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var item: CFTypeRef?
        switch SecItemCopyMatching(query as CFDictionary, &item) {
        case errSecSuccess: return (item as? Data).map { .success($0) } ?? .failure(.notSignedIn)
        case errSecItemNotFound: return .failure(.notSignedIn)
        // Declined, cancelled, or the keychain is locked and may not ask: all mean "not now".
        default: return .failure(.keychainDenied)
        }
    }
}

/// Collects a child process's output a line at a time so a reader can wait with a timeout.
private final class LineCollector {
    private let lock = NSLock()
    private let signal = DispatchSemaphore(value: 0)
    private var pending = Data()
    private var lines: [Data] = []

    func append(_ chunk: Data) {
        lock.lock()
        pending.append(chunk)
        while let newline = pending.firstIndex(of: 0x0A) {
            lines.append(pending[pending.startIndex..<newline])
            pending.removeSubrange(pending.startIndex...newline)
            signal.signal()
        }
        lock.unlock()
    }

    /// The next JSON object that carries `id`, or nil if none arrives in time.
    func next(withId id: Int, until deadline: Date) -> [String: Any]? {
        while true {
            lock.lock()
            let objects = lines.compactMap { (try? JSONSerialization.jsonObject(with: $0)) as? [String: Any] }
            lock.unlock()
            if let match = objects.first(where: { ($0["id"] as? Int) == id }) { return match }
            let remaining = deadline.timeIntervalSinceNow
            if remaining <= 0 || signal.wait(timeout: .now() + remaining) == .timedOut { return nil }
        }
    }
}

final class CodexLiveUsage {
    private static var candidates: [String] {
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        return ["\(home)/.local/bin/codex", "\(home)/.codex/packages/standalone/current/bin/codex",
                "/opt/homebrew/bin/codex", "/usr/local/bin/codex",
                "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"]
    }

    /// Blocks while the child process answers: call off the main thread.
    func fetch(now: Date = Date()) -> Result<LiveReading, LiveFailure> {
        guard let path = Self.candidates.first(where: { FileManager.default.isExecutableFile(atPath: $0) }) else {
            return .failure(.codexMissing)
        }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: path)
        process.arguments = ["app-server"]
        let input = Pipe(), output = Pipe()
        process.standardInput = input
        process.standardOutput = output
        process.standardError = FileHandle.nullDevice
        let collector = LineCollector()
        output.fileHandleForReading.readabilityHandler = { handle in
            let chunk = handle.availableData
            if chunk.isEmpty { handle.readabilityHandler = nil } else { collector.append(chunk) }
        }
        // Writing to a child that has already exited would otherwise raise SIGPIPE and end the app.
        signal(SIGPIPE, SIG_IGN)
        do { try process.run() } catch { return .failure(.codexMissing) }
        defer {
            output.fileHandleForReading.readabilityHandler = nil
            try? input.fileHandleForWriting.close()
            if process.isRunning { process.terminate() }
        }

        func send(_ object: [String: Any]) {
            guard var data = try? JSONSerialization.data(withJSONObject: object) else { return }
            data.append(0x0A)
            try? input.fileHandleForWriting.write(contentsOf: data)
        }
        let deadline = Date().addingTimeInterval(20)
        send(["method": "initialize", "id": 0, "params": ["clientInfo": ["name": "bitling", "title": "Bitling", "version": "1"]]])
        guard collector.next(withId: 0, until: deadline) != nil else { return .failure(.codexSilent) }
        send(["method": "initialized"])
        send(["method": "account/rateLimits/read", "id": 1])
        guard let answer = collector.next(withId: 1, until: deadline) else { return .failure(.codexSilent) }
        guard let result = answer["result"] as? [String: Any] else { return .failure(.codexNotSignedIn) }
        guard let reading = CodexUsageParser.parse(result, fetchedAt: now) else { return .failure(.codexSilent) }
        return .success(reading)
    }
}

/// One provider's live feed: when it last answered, why it did not, and when to ask next.
private final class LiveFeed {
    var enabled = true
    var reading: LiveReading?
    var failure: LiveFailure?
    var next = Date.distantPast
    var fetching = false
    let fetch: () -> Result<LiveReading, LiveFailure>
    init(fetch: @escaping () -> Result<LiveReading, LiveFailure>) { self.fetch = fetch }

    func reset() { reading = nil; failure = nil; next = .distantPast }
}

/// Re-reads the quota files on a timer, and asks Claude and Codex for live usage where that is
/// switched on. The file reads are tiny (one small JSON file and the tail of one log), so a
/// 30 second cadence costs nothing; the live requests run about once a minute.
final class QuotaWatcher {
    /// Fires on the main thread, and only when the readings actually changed.
    var onUpdate: ((QuotaData) -> Void)?
    /// Main thread only.
    private(set) var latestData: QuotaData?

    /// Main thread only. Turning one off drops its live reading at once.
    var claudeLiveEnabled: Bool {
        get { claudeFeed.enabled }
        set { setEnabled(newValue, on: claudeFeed) }
    }
    var codexLiveEnabled: Bool {
        get { codexFeed.enabled }
        set { setEnabled(newValue, on: codexFeed) }
    }

    private let queue = DispatchQueue(label: "app.bitling.quota", qos: .utility)
    private let liveQueue = DispatchQueue(label: "app.bitling.quota.live", qos: .utility, attributes: .concurrent)
    private let claudeFeed = LiveFeed(fetch: { ClaudeLiveUsage().fetch() })
    private let codexFeed = LiveFeed(fetch: { CodexLiveUsage().fetch() })
    private var timer: Timer?
    private var reading = false

    /// A live reading older than this is no longer called live.
    private static let liveFreshness: TimeInterval = 180

    func start() {
        refresh()
        let timer = Timer(timeInterval: 30, repeats: true) { [weak self] _ in self?.refresh() }
        RunLoop.main.add(timer, forMode: .common)
        self.timer = timer
    }

    func stop() {
        timer?.invalidate()
        timer = nil
    }

    private func setEnabled(_ value: Bool, on feed: LiveFeed) {
        guard value != feed.enabled else { return }
        feed.enabled = value
        feed.reset()
        refresh()
    }

    private func refresh() {
        for feed in [claudeFeed, codexFeed] { fetchIfDue(feed) }
        guard !reading else { return }
        reading = true
        queue.async { [weak self] in
            let files = QuotaReader.read(home: FileManager.default.homeDirectoryForCurrentUser)
            DispatchQueue.main.async {
                guard let self else { return }
                self.reading = false
                let data = self.applyingLive(to: files)
                guard data != self.latestData else { return }
                self.latestData = data
                self.onUpdate?(data)
            }
        }
    }

    private func fetchIfDue(_ feed: LiveFeed) {
        guard feed.enabled, !feed.fetching, Date() >= feed.next else { return }
        feed.fetching = true
        liveQueue.async { [weak self] in
            let result = feed.fetch()
            DispatchQueue.main.async {
                feed.fetching = false
                switch result {
                case .success(let reading):
                    feed.reading = reading; feed.failure = nil
                    feed.next = Date().addingTimeInterval(60)
                case .failure(let failure):
                    feed.failure = failure
                    feed.next = Date().addingTimeInterval(failure.retryAfter)
                }
                self?.refresh()
            }
        }
    }

    /// A fresh live reading replaces the file-based windows; otherwise the files stand, with
    /// the reason live data is missing attached so the menu can say so.
    private func applyingLive(to files: QuotaData) -> QuotaData {
        var data = files
        func merge(_ provider: inout QuotaProvider, _ feed: LiveFeed) {
            guard feed.enabled else { return }
            if let live = feed.reading, Date().timeIntervalSince(live.fetchedAt) < Self.liveFreshness {
                provider.fiveHour = live.fiveHour
                provider.weekly = live.weekly
                if let plan = live.plan { provider.plan = plan }
            } else {
                provider.liveStatus = feed.failure?.message
            }
        }
        merge(&data.claude, claudeFeed)
        merge(&data.codex, codexFeed)
        return data
    }
}
