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
//   Claude  `claude -p /usage`, parsed from its text. Claude reads its own sign-in, so Bitling
//           never touches the keychain or a token (reading Claude Code's keychain item meant a
//           password prompt after every token renewal, because Claude Code recreates the item).
//           It costs a few seconds of CPU, so it is asked every 5 minutes.
//   Codex   `codex app-server`, asked for account/rateLimits/read. Codex answers with its own
//           sign-in, so no credential passes through Bitling at all.

struct LiveFailure: Error {
    let message: String
    /// How long to leave it alone before asking again. A declined keychain dialog comes back
    /// every time it is asked, so that one is asked rarely.
    let retryAfter: TimeInterval

    static let notSignedIn = LiveFailure(message: "sign in to Claude Code for live usage", retryAfter: 120)
    // Short, because Claude Code updates itself by replacing its binary, which is missing for a moment.
    static let claudeMissing = LiveFailure(message: "the claude command was not found", retryAfter: 120)
    static let claudeSilent = LiveFailure(message: "claude did not answer", retryAfter: 60)
    static let codexMissing = LiveFailure(message: "the codex command was not found", retryAfter: 3600)
    static let codexSilent = LiveFailure(message: "codex did not answer", retryAfter: 120)
    static let codexNotSignedIn = LiveFailure(message: "sign in to Codex for live usage", retryAfter: 600)
}

/// Outcomes only, so a failing feed can be diagnosed: never a token, a header, or a response body.
/// ~/Library/Logs/Bitling/usage.log, trimmed when it grows.
enum UsageLog {
    private static let lock = NSLock()
    static func write(_ line: String) {
        lock.lock(); defer { lock.unlock() }
        let fm = FileManager.default
        let dir = fm.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Bitling")
        let file = dir.appendingPathComponent("usage.log")
        try? fm.createDirectory(at: dir, withIntermediateDirectories: true)
        if let size = (try? fm.attributesOfItem(atPath: file.path)[.size]) as? Int, size > 64_000 { try? fm.removeItem(at: file) }
        let stamp = ISO8601DateFormatter().string(from: Date())
        guard let data = "\(stamp) \(line)\n".data(using: .utf8) else { return }
        if let handle = try? FileHandle(forWritingTo: file) {
            defer { try? handle.close() }
            _ = try? handle.seekToEnd(); try? handle.write(contentsOf: data)
        } else {
            try? data.write(to: file)
        }
    }
}

struct LiveReading {
    var plan: String?
    var fiveHour: QuotaWindow?
    var weekly: QuotaWindow?
    let fetchedAt: Date
}

enum ClaudeUsageTextParser {
    /// `claude -p /usage` prints, among other lines:
    ///   Current session: 7% used · resets Oct 16 at 1:20pm (Asia/Calcutta)
    ///   Current week (all models): 82% used · resets Oct 18 at 5:30am (Asia/Calcutta)
    /// A window with no reset (nothing used yet) has no "resets" part.
    static func parse(_ text: String, fetchedAt: Date) -> LiveReading? {
        let five = window(prefix: "Current session:", in: text, now: fetchedAt)
        let week = window(prefix: "Current week (all models):", in: text, now: fetchedAt)
        return five == nil && week == nil ? nil : LiveReading(plan: nil, fiveHour: five, weekly: week, fetchedAt: fetchedAt)
    }

    private static let pattern = try! NSRegularExpression(pattern: #"(\d+(?:\.\d+)?)% used(?: · resets (.+?) \((.+?)\))?\s*$"#)

    private static func group(_ index: Int, of match: NSTextCheckingResult, in line: String) -> String? {
        Range(match.range(at: index), in: line).map { String(line[$0]) }
    }

    private static func window(prefix: String, in text: String, now: Date) -> QuotaWindow? {
        guard let line = text.split(separator: "\n").first(where: { $0.hasPrefix(prefix) }).map(String.init),
              let match = pattern.firstMatch(in: line, range: NSRange(line.startIndex..., in: line)),
              let used = Double(group(1, of: match, in: line) ?? "") else { return nil }
        let stamp = now.timeIntervalSince1970 * 1000
        let reset = group(2, of: match, in: line).flatMap { resetDate($0, zone: group(3, of: match, in: line), now: now) }
        return QuotaWindow(usedPercent: min(100, max(0, used)), resetsAt: reset.map { $0.timeIntervalSince1970 * 1000 }, asOf: stamp)
    }

    /// "Oct 16 at 1:20pm", "Oct 16 at 1pm" or just "1:20pm", in the zone the CLI names. A date with
    /// no year is the next one that is not in the past.
    private static func resetDate(_ text: String, zone: String?, now: Date) -> Date? {
        var calendar = Calendar(identifier: .gregorian)
        let tz = zone.flatMap(TimeZone.init(identifier:)) ?? .current
        calendar.timeZone = tz
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = tz
        formatter.calendar = calendar
        for (format, withDay) in [("MMM d 'at' h:mma", true), ("MMM d 'at' ha", true), ("h:mma", false), ("ha", false)] {
            formatter.dateFormat = format
            formatter.defaultDate = calendar.startOfDay(for: now)
            guard let date = formatter.date(from: text) else { continue }
            let step: Calendar.Component = withDay ? .year : .day
            return date < now.addingTimeInterval(-3600) ? calendar.date(byAdding: step, value: 1, to: date) : date
        }
        return nil
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
    /// Blocks until `claude -p /usage` answers: call off the main thread. The command answers
    /// from the account without a model turn, costing a few seconds of CPU, and Claude reads its
    /// own sign-in, so Bitling never touches the keychain or any token.
    func fetch(now: Date = Date()) -> Result<LiveReading, LiveFailure> {
        guard let path = Self.candidates.first(where: { FileManager.default.isExecutableFile(atPath: $0) }) else {
            UsageLog.write("claude: the claude command was not found")
            return .failure(.claudeMissing)
        }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: path)
        // BITLING_PROBE tells Bitling's own Claude hooks to ignore this run.
        process.arguments = ["-p", "/usage", "--no-session-persistence"]
        process.currentDirectoryURL = FileManager.default.temporaryDirectory
        var environment = ProcessInfo.processInfo.environment
        environment["BITLING_PROBE"] = "1"
        process.environment = environment
        let output = Pipe()
        process.standardInput = FileHandle.nullDevice
        process.standardOutput = output
        process.standardError = FileHandle.nullDevice
        let collected = LockedData()
        output.fileHandleForReading.readabilityHandler = { handle in
            let chunk = handle.availableData
            if chunk.isEmpty { handle.readabilityHandler = nil } else { collected.append(chunk) }
        }
        let finished = DispatchSemaphore(value: 0)
        process.terminationHandler = { _ in finished.signal() }
        do { try process.run() } catch { UsageLog.write("claude: could not start the claude command"); return .failure(.claudeMissing) }
        defer { output.fileHandleForReading.readabilityHandler = nil }
        if finished.wait(timeout: .now() + 60) == .timedOut {
            process.terminate()
            UsageLog.write("claude: /usage took too long and was stopped")
            return .failure(.claudeSilent)
        }
        // The handler may still be draining the pipe when the child exits.
        Thread.sleep(forTimeInterval: 0.1)
        let text = String(decoding: collected.value, as: UTF8.self)
        guard let reading = ClaudeUsageTextParser.parse(text, fetchedAt: now) else {
            let first = text.split(separator: "\n").first.map { String($0.prefix(80)) } ?? "nothing"
            UsageLog.write("claude: /usage printed no session or week line, it began: \(first)")
            return .failure(.notSignedIn)
        }
        UsageLog.write("claude: live 5h \(reading.fiveHour?.usedPercent ?? -1)% week \(reading.weekly?.usedPercent ?? -1)%")
        return .success(reading)
    }

    private static var candidates: [String] {
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        let onPath = (ProcessInfo.processInfo.environment["PATH"] ?? "").split(separator: ":").map { "\($0)/claude" }
        return ["\(home)/.npm-global/bin/claude", "\(home)/.local/bin/claude", "\(home)/.claude/local/claude",
                "\(home)/.bun/bin/claude", "\(home)/.volta/bin/claude",
                "/opt/homebrew/bin/claude", "/usr/local/bin/claude"] + onPath
    }
}

private final class LockedData {
    private let lock = NSLock()
    private var data = Data()
    func append(_ chunk: Data) { lock.lock(); data.append(chunk); lock.unlock() }
    var value: Data { lock.lock(); defer { lock.unlock() }; return data }
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
    /// How often a fresh reading is asked for, and how long one is still called live.
    let interval: TimeInterval
    var freshness: TimeInterval { interval * 3 }
    let fetch: () -> Result<LiveReading, LiveFailure>
    init(interval: TimeInterval, fetch: @escaping () -> Result<LiveReading, LiveFailure>) { self.interval = interval; self.fetch = fetch }

    func reset() { reading = nil; failure = nil; next = .distantPast }
}

/// Re-reads the quota files on a timer, and asks Claude and Codex for live usage where that is
/// switched on. The file reads are tiny (one small JSON file and the tail of one log), so a
/// 30 second cadence costs nothing; Codex live runs about once a minute and Claude every 5.
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
    private let claudeFeed = LiveFeed(interval: 300, fetch: { ClaudeLiveUsage().fetch() })
    private let codexFeed = LiveFeed(interval: 60, fetch: { CodexLiveUsage().fetch() })
    private var timer: Timer?
    private var reading = false

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
                    feed.next = Date().addingTimeInterval(feed.interval)
                case .failure(let failure):
                    feed.failure = failure
                    feed.next = Date().addingTimeInterval(failure.retryAfter)
                }
                self?.refresh()
            }
        }
    }

    /// How long the last live reading is still worth showing, marked as stale, when refreshing fails.
    static let staleLiveKeep: TimeInterval = 6 * 3600

    /// A fresh live reading replaces the file-based windows. A live reading that has gone stale
    /// (a refresh failed) is still better than nothing, and better than a file reading older
    /// than it, so it stays on screen with its age and the reason it is not live. A window
    /// whose reset has passed is dropped: its figure no longer describes anything.
    static func merge(_ provider: inout QuotaProvider, live: LiveReading?, failure: LiveFailure?, freshness: TimeInterval, now: Date) {
        guard let live else { provider.liveStatus = failure?.message; return }
        let age = now.timeIntervalSince(live.fetchedAt)
        if age < freshness {
            provider.fiveHour = live.fiveHour
            provider.weekly = live.weekly
            if let plan = live.plan { provider.plan = plan }
            return
        }
        provider.liveStatus = failure?.message
        guard age < staleLiveKeep else { return }
        let nowMs = now.timeIntervalSince1970 * 1000
        func newer(_ kept: QuotaWindow?, _ candidate: QuotaWindow?) -> QuotaWindow? {
            guard let candidate, candidate.resetsAt.map({ $0 > nowMs }) ?? true else { return kept }
            return (kept?.asOf ?? 0) < candidate.asOf ? candidate : kept
        }
        provider.fiveHour = newer(provider.fiveHour, live.fiveHour)
        provider.weekly = newer(provider.weekly, live.weekly)
    }

    /// A fresh live reading replaces the file-based windows; otherwise the files stand, with
    /// the reason live data is missing attached so the menu can say so.
    private func applyingLive(to files: QuotaData) -> QuotaData {
        var data = files
        func merge(_ provider: inout QuotaProvider, _ feed: LiveFeed) {
            guard feed.enabled else { return }
            Self.merge(&provider, live: feed.reading, failure: feed.failure, freshness: feed.freshness, now: Date())
        }
        merge(&data.claude, claudeFeed)
        merge(&data.codex, codexFeed)
        return data
    }
}
