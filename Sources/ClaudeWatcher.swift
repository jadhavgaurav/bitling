// Watches Claude Code sessions by tailing the transcripts it writes under
// ~/.claude/projects/<project>/<session>.jsonl. Every line is a JSON object; the ones
// that matter here are human prompts, assistant tool calls, tool results (with errors)
// and end-of-turn assistant messages. No configuration is needed: every Claude Code
// front end (terminal, desktop app, IDE) writes the same files.
//
// Hooks (see `bitling claude`) deliver the same kinds faster and add permission
// notifications; the host de-duplicates when both are active.

import Foundation

final class ClaudeWatcher {
    var onEvent: ((GitEvent) -> Void)?

    private struct Session {
        let file: URL
        let sessionId: String
        var offset: UInt64
        var project: String
        var title: String
        var lastActivity: Date
        var lastToolEvent: Date
        var working: Bool
        var idleReported: Bool
    }

    private static let todayKey = "claudeToday"
    private let root = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".claude/projects")
    private let queue = DispatchQueue(label: "app.bitling.claude", qos: .utility)
    private var sessions: [String: Session] = [:]
    private var scanTimer: Timer?
    private var pollTimer: Timer?
    private var started = Date()

    private(set) var promptsToday = 0
    private(set) var toolsToday = 0
    private(set) var sessionsToday = 0
    private var todayKeyValue = ""
    private(set) var lastSummary = "nothing yet"

    var activeSessionCount: Int { queue.sync { sessions.values.filter { Date().timeIntervalSince($0.lastActivity) < 300 }.count } }

    init() {
        let defaults = UserDefaults.standard
        todayKeyValue = Self.dayString()
        if let today = defaults.dictionary(forKey: Self.todayKey), let day = today["day"] as? String, day == todayKeyValue {
            promptsToday = today["prompts"] as? Int ?? 0
            toolsToday = today["tools"] as? Int ?? 0
            sessionsToday = today["sessions"] as? Int ?? 0
        }
    }

    private static func dayString() -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f.string(from: Date())
    }

    private func bump(prompts: Int = 0, tools: Int = 0, sessions: Int = 0) {
        let day = Self.dayString()
        if day != todayKeyValue { todayKeyValue = day; promptsToday = 0; toolsToday = 0; sessionsToday = 0 }
        promptsToday += prompts
        toolsToday += tools
        sessionsToday += sessions
        UserDefaults.standard.set(["day": day, "prompts": promptsToday, "tools": toolsToday, "sessions": sessionsToday], forKey: Self.todayKey)
    }

    func start() {
        started = Date()
        queue.async { self.scan() }
        scanTimer = Timer(timeInterval: 10.0, repeats: true) { [weak self] _ in self?.queue.async { self?.scan() } }
        pollTimer = Timer(timeInterval: 2.0, repeats: true) { [weak self] _ in self?.queue.async { self?.poll() } }
        for timer in [scanTimer!, pollTimer!] { RunLoop.main.add(timer, forMode: .common) }
    }

    // MARK: Discovery

    private func fileSize(_ url: URL) -> UInt64 {
        (try? FileManager.default.attributesOfItem(atPath: url.path)[.size] as? UInt64) ?? 0
    }

    private func scan() {
        let fm = FileManager.default
        guard let projects = try? fm.contentsOfDirectory(at: root, includingPropertiesForKeys: [.isDirectoryKey], options: [.skipsHiddenFiles]) else { return }
        let now = Date()
        for project in projects {
            guard (try? project.resourceValues(forKeys: [.isDirectoryKey]).isDirectory) == true else { continue }
            guard let files = try? fm.contentsOfDirectory(at: project, includingPropertiesForKeys: [.contentModificationDateKey, .creationDateKey], options: [.skipsHiddenFiles]) else { continue }
            for file in files where file.pathExtension == "jsonl" {
                let values = try? file.resourceValues(forKeys: [.contentModificationDateKey, .creationDateKey])
                let modified = values?.contentModificationDate ?? .distantPast
                guard now.timeIntervalSince(modified) < 15 * 60 else { continue }
                let key = file.path
                if sessions[key] != nil { continue }
                let created = values?.creationDate ?? modified
                let brandNew = created > started && now.timeIntervalSince(created) < 120
                let projectName = Self.projectName(fromFolder: project.lastPathComponent)
                sessions[key] = Session(
                    file: file, sessionId: file.deletingPathExtension().lastPathComponent,
                    offset: brandNew ? 0 : fileSize(file), project: projectName, title: "",
                    lastActivity: modified, lastToolEvent: .distantPast, working: false, idleReported: true
                )
                if brandNew {
                    bump(sessions: 1)
                    emit(GitEvent(kind: "claude-session-start", repo: projectName, branch: "", message: "", hash: "", name: projectName))
                }
            }
        }
        // Forget sessions that have been quiet for an hour.
        sessions = sessions.filter { now.timeIntervalSince($0.value.lastActivity) < 3600 }
    }

    private static func projectName(fromFolder folder: String) -> String {
        // "-Users-a12345-Desktop-AI-OyeChats" -> "OyeChats"
        let parts = folder.split(separator: "-").filter { !$0.isEmpty }
        return parts.last.map(String.init) ?? folder
    }

    // MARK: Tailing

    private func poll() {
        let now = Date()
        for (key, var session) in sessions {
            let size = fileSize(session.file)
            if size < session.offset { session.offset = 0 }
            if size > session.offset {
                let text = readTail(session.file, from: session.offset)
                session.offset = size
                session.lastActivity = now
                for line in text.split(separator: "\n") {
                    handle(line: String(line), session: &session)
                }
            } else if session.working, !session.idleReported, now.timeIntervalSince(session.lastActivity) > 5 * 60 {
                session.working = false
                session.idleReported = true
                emit(GitEvent(kind: "claude-idle", repo: session.project, branch: "", message: "", hash: "", name: session.project))
            }
            sessions[key] = session
        }
    }

    private func readTail(_ url: URL, from offset: UInt64) -> String {
        guard let handle = try? FileHandle(forReadingFrom: url) else { return "" }
        defer { try? handle.close() }
        do {
            try handle.seek(toOffset: offset)
            let data = try handle.readToEnd() ?? Data()
            return String(decoding: data, as: UTF8.self)
        } catch { return "" }
    }

    private static func preview(_ text: String, limit: Int = 60) -> String {
        let flat = text.replacingOccurrences(of: "\n", with: " ").trimmingCharacters(in: .whitespacesAndNewlines)
        return flat.count > limit ? String(flat.prefix(limit - 1)) + "…" : flat
    }

    private func handle(line: String, session: inout Session) {
        guard let data = line.data(using: .utf8),
              let entry = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = entry["type"] as? String else { return }
        if let cwd = entry["cwd"] as? String, !cwd.isEmpty { session.project = URL(fileURLWithPath: cwd).lastPathComponent }
        if entry["isSidechain"] as? Bool == true { return }
        let message = entry["message"] as? [String: Any]
        let content = message?["content"]

        switch type {
        case "custom-title":
            session.title = entry["customTitle"] as? String ?? session.title
        case "user":
            if entry["isMeta"] as? Bool == true { return }
            if let text = content as? String {
                guard (entry["origin"] as? [String: Any])?["kind"] as? String != "system" else { return }
                session.working = true
                session.idleReported = false
                bump(prompts: 1)
                emit(GitEvent(kind: "claude-prompt", repo: session.project, branch: "", message: Self.preview(text), hash: "", name: session.project))
            } else if let blocks = content as? [[String: Any]] {
                for block in blocks where block["type"] as? String == "tool_result" {
                    let failed = block["is_error"] as? Bool == true
                        || ((entry["toolUseResult"] as? [String: Any])?["success"] as? Bool == false)
                    if failed {
                        emit(GitEvent(kind: "claude-tool-error", repo: session.project, branch: "", message: "", hash: "", name: session.project))
                    }
                }
            }
        case "assistant":
            guard let blocks = content as? [[String: Any]] else { return }
            let stop = message?["stop_reason"] as? String ?? ""
            for block in blocks {
                let kind = block["type"] as? String ?? ""
                if kind == "tool_use" {
                    let tool = block["name"] as? String ?? "tool"
                    let input = block["input"] as? [String: Any] ?? [:]
                    let detail = (input["command"] as? String) ?? (input["file_path"] as? String) ?? (input["pattern"] as? String) ?? (input["query"] as? String) ?? ""
                    session.working = true
                    session.idleReported = false
                    bump(tools: 1)
                    if Date().timeIntervalSince(session.lastToolEvent) > 3 {
                        session.lastToolEvent = Date()
                        emit(GitEvent(kind: "claude-tool", repo: session.project, branch: "", message: Self.preview(detail, limit: 80), hash: "", name: tool))
                    }
                } else if kind == "text", stop == "end_turn" {
                    session.working = false
                    session.idleReported = true
                    emit(GitEvent(kind: "claude-done", repo: session.project, branch: "", message: Self.preview(block["text"] as? String ?? ""), hash: "", name: session.project))
                }
            }
        default:
            break
        }
    }

    private func emit(_ event: GitEvent) {
        lastSummary = "\(event.kind.replacingOccurrences(of: "claude-", with: "")) · \(event.name)"
        DispatchQueue.main.async { self.onEvent?(event) }
    }
}
