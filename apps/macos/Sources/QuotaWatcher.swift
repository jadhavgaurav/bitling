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

/// Re-reads the quota files on a timer. The reads are tiny (one small JSON file and the
/// tail of one log), so a 30 second cadence costs nothing and is plenty for figures that
/// move one percent at a time.
final class QuotaWatcher {
    /// Fires on the main thread, and only when the readings actually changed.
    var onUpdate: ((QuotaData) -> Void)?
    /// Main thread only.
    private(set) var latestData: QuotaData?

    private let queue = DispatchQueue(label: "app.bitling.quota", qos: .utility)
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

    private func refresh() {
        guard !reading else { return }
        reading = true
        queue.async { [weak self] in
            let data = QuotaReader.read(home: FileManager.default.homeDirectoryForCurrentUser)
            DispatchQueue.main.async {
                guard let self else { return }
                self.reading = false
                guard data != self.latestData else { return }
                self.latestData = data
                self.onUpdate?(data)
            }
        }
    }
}
