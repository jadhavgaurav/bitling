// Watches git repositories under a set of root folders and reports activity.
//
// No git process is needed to notice events: every repository keeps a reflog in
// .git/logs/HEAD (commits, checkouts, merges, rebases, resets) and one per remote
// branch in .git/logs/refs/remotes/<remote>/<branch> ("update by push"). Tailing
// those files every couple of seconds is cheap and instant. `git` itself is only
// run for optional enrichment (commit size) and for the periodic dirty-file count.

import Foundation

struct GitEvent {
    var kind: String          // commit, amend, merge, push, checkout, rebase, rebase-done, pull, stash, reset, cherry-pick
    var repo: String
    var branch: String
    var message: String
    var hash: String
    var insertions = 0
    var deletions = 0
    var files = 0

    var asDictionary: [String: Any] {
        ["kind": kind, "repo": repo, "branch": branch, "message": message, "hash": hash,
         "insertions": insertions, "deletions": deletions, "files": files]
    }
}

struct GitStatus {
    var repo: String
    var branch: String
    var dirty: Int
    var minutesSinceCommit: Int

    var asDictionary: [String: Any] {
        ["repo": repo, "branch": branch, "dirty": dirty, "minutesSinceCommit": minutesSinceCommit]
    }
}

final class GitWatcher {
    private struct Tracked {
        let workTree: URL
        let gitDir: URL
        var headLogSize: UInt64
        var stashLogSize: UInt64
        var remoteLogSizes: [String: UInt64]
        var lastCommitDate: Date?
        var lastActivity: Date
        var name: String { workTree.lastPathComponent }
    }

    private static let rootsKey = "gitRoots"
    private static let todayKey = "gitToday"
    private static let skippedDirectories: Set<String> = [
        "node_modules", ".venv", "venv", "Library", ".Trash", "build", "dist", "target", "Pods", "DerivedData", ".next", ".cache",
    ]

    private(set) var roots: [URL]
    private var tracked: [String: Tracked] = [:]
    private let queue = DispatchQueue(label: "app.jellykin.git", qos: .utility)
    private var pollTimer: Timer?
    private var scanTimer: Timer?
    private var statusTimer: Timer?
    private var lastActiveRepo: String?

    private(set) var commitsToday = 0
    private(set) var pushesToday = 0
    private var todayKey = ""
    private(set) var lastEventSummary = "nothing yet"

    var onEvent: ((GitEvent) -> Void)?
    var onStatus: ((GitStatus) -> Void)?

    var repositoryCount: Int { tracked.count }

    init() {
        let defaults = UserDefaults.standard
        if let saved = defaults.array(forKey: Self.rootsKey) as? [String], !saved.isEmpty {
            roots = saved.map { URL(fileURLWithPath: $0) }
        } else {
            roots = Self.defaultRoots()
        }
        if let today = defaults.dictionary(forKey: Self.todayKey),
           let day = today["day"] as? String, day == Self.dayString() {
            commitsToday = today["commits"] as? Int ?? 0
            pushesToday = today["pushes"] as? Int ?? 0
        }
        todayKey = Self.dayString()
    }

    private static func defaultRoots() -> [URL] {
        let home = FileManager.default.homeDirectoryForCurrentUser
        let candidates = ["Desktop/AI", "Developer", "Projects", "Documents/GitHub", "code", "src", "repos"]
        let existing = candidates.map { home.appendingPathComponent($0) }.filter { url in
            var isDir: ObjCBool = false
            return FileManager.default.fileExists(atPath: url.path, isDirectory: &isDir) && isDir.boolValue
        }
        return existing.isEmpty ? [home.appendingPathComponent("Desktop")] : existing
    }

    private static func dayString() -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f.string(from: Date())
    }

    // MARK: Lifecycle

    func start() {
        queue.async { self.scan() }
        pollTimer = Timer(timeInterval: 2.0, repeats: true) { [weak self] _ in
            self?.queue.async { self?.poll() }
        }
        scanTimer = Timer(timeInterval: 60.0, repeats: true) { [weak self] _ in
            self?.queue.async { self?.scan() }
        }
        statusTimer = Timer(timeInterval: 20.0, repeats: true) { [weak self] _ in
            self?.queue.async { self?.reportStatus() }
        }
        for timer in [pollTimer!, scanTimer!, statusTimer!] { RunLoop.main.add(timer, forMode: .common) }
    }

    func addRoot(_ url: URL) {
        guard !roots.contains(where: { $0.path == url.path }) else { return }
        roots.append(url)
        saveRoots()
        queue.async { self.scan() }
    }

    func removeRoot(_ url: URL) {
        roots.removeAll { $0.path == url.path }
        saveRoots()
        queue.async {
            self.tracked = self.tracked.filter { entry in
                self.roots.contains { entry.key.hasPrefix($0.path) }
            }
        }
    }

    private func saveRoots() {
        UserDefaults.standard.set(roots.map { $0.path }, forKey: Self.rootsKey)
    }

    private func bumpToday(commits: Int = 0, pushes: Int = 0) {
        let day = Self.dayString()
        if day != todayKey { todayKey = day; commitsToday = 0; pushesToday = 0 }
        commitsToday += commits
        pushesToday += pushes
        UserDefaults.standard.set(["day": day, "commits": commitsToday, "pushes": pushesToday], forKey: Self.todayKey)
    }

    // MARK: Discovery

    private func scan() {
        for root in roots { scanDirectory(root, depth: 0) }
    }

    private func scanDirectory(_ dir: URL, depth: Int) {
        guard depth <= 3 else { return }
        let fm = FileManager.default
        let gitEntry = dir.appendingPathComponent(".git")
        if fm.fileExists(atPath: gitEntry.path) {
            register(workTree: dir)
            return
        }
        guard let children = try? fm.contentsOfDirectory(at: dir, includingPropertiesForKeys: [.isDirectoryKey, .isSymbolicLinkKey], options: [.skipsHiddenFiles]) else { return }
        for child in children {
            let values = try? child.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])
            guard values?.isDirectory == true, values?.isSymbolicLink != true else { continue }
            if Self.skippedDirectories.contains(child.lastPathComponent) { continue }
            scanDirectory(child, depth: depth + 1)
        }
    }

    private func resolveGitDir(workTree: URL) -> URL? {
        let entry = workTree.appendingPathComponent(".git")
        var isDir: ObjCBool = false
        guard FileManager.default.fileExists(atPath: entry.path, isDirectory: &isDir) else { return nil }
        if isDir.boolValue { return entry }
        // Worktrees and submodules keep a pointer file: "gitdir: <path>"
        guard let text = try? String(contentsOf: entry, encoding: .utf8) else { return nil }
        let line = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard line.hasPrefix("gitdir:") else { return nil }
        let raw = line.dropFirst("gitdir:".count).trimmingCharacters(in: .whitespaces)
        let url = raw.hasPrefix("/") ? URL(fileURLWithPath: raw) : workTree.appendingPathComponent(raw)
        return url.standardizedFileURL
    }

    private func register(workTree: URL) {
        let key = workTree.path
        guard tracked[key] == nil, let gitDir = resolveGitDir(workTree: workTree) else { return }
        let headLog = gitDir.appendingPathComponent("logs/HEAD")
        let entry = Tracked(
            workTree: workTree, gitDir: gitDir,
            headLogSize: fileSize(headLog),
            stashLogSize: fileSize(gitDir.appendingPathComponent("logs/refs/stash")),
            remoteLogSizes: remoteLogSizes(gitDir),
            lastCommitDate: lastReflogDate(headLog),
            lastActivity: (try? headLog.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
        )
        tracked[key] = entry
    }

    // MARK: Polling

    private func fileSize(_ url: URL) -> UInt64 {
        (try? FileManager.default.attributesOfItem(atPath: url.path)[.size] as? UInt64) ?? 0
    }

    private func remoteLogSizes(_ gitDir: URL) -> [String: UInt64] {
        var sizes: [String: UInt64] = [:]
        let base = gitDir.appendingPathComponent("logs/refs/remotes")
        guard let enumerator = FileManager.default.enumerator(at: base, includingPropertiesForKeys: [.isRegularFileKey]) else { return sizes }
        for case let file as URL in enumerator {
            guard (try? file.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile) == true else { continue }
            sizes[file.path] = fileSize(file)
        }
        return sizes
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

    private func lastReflogDate(_ url: URL) -> Date? {
        guard let text = try? String(contentsOf: url, encoding: .utf8) else { return nil }
        guard let line = text.split(separator: "\n").last else { return nil }
        return Self.parseReflogLine(String(line))?.date
    }

    private struct ReflogLine {
        let oldHash: String
        let newHash: String
        let date: Date
        let message: String
    }

    private static func parseReflogLine(_ line: String) -> ReflogLine? {
        // "<old> <new> Name <email> <unix-ts> <tz>\t<message>"
        let parts = line.split(separator: "\t", maxSplits: 1, omittingEmptySubsequences: false)
        guard parts.count == 2 else { return nil }
        let head = parts[0].split(separator: " ")
        guard head.count >= 4 else { return nil }
        let tsIndex = head.count - 2
        let ts = TimeInterval(head[tsIndex]) ?? 0
        return ReflogLine(oldHash: String(head[0]), newHash: String(head[1]), date: Date(timeIntervalSince1970: ts), message: String(parts[1]))
    }

    private func currentBranch(_ gitDir: URL) -> String {
        guard let text = try? String(contentsOf: gitDir.appendingPathComponent("HEAD"), encoding: .utf8) else { return "" }
        let line = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if line.hasPrefix("ref: refs/heads/") { return String(line.dropFirst("ref: refs/heads/".count)) }
        return "detached"
    }

    private func poll() {
        for (key, var repo) in tracked {
            // `git stash` rewrites HEAD with a "reset: moving to HEAD" reflog line; report the stash, not a reset.
            let stashLog = repo.gitDir.appendingPathComponent("logs/refs/stash")
            let stashSize = fileSize(stashLog)
            let stashed = stashSize > repo.stashLogSize
            repo.stashLogSize = stashSize
            if stashed {
                repo.lastActivity = Date()
                lastActiveRepo = key
                emit(GitEvent(kind: "stash", repo: repo.name, branch: currentBranch(repo.gitDir), message: "", hash: ""))
            }

            let headLog = repo.gitDir.appendingPathComponent("logs/HEAD")
            let size = fileSize(headLog)
            if size < repo.headLogSize { repo.headLogSize = size }
            if size > repo.headLogSize {
                let text = readTail(headLog, from: repo.headLogSize)
                repo.headLogSize = size
                repo.lastActivity = Date()
                lastActiveRepo = key
                for raw in text.split(separator: "\n") {
                    guard let line = Self.parseReflogLine(String(raw)) else { continue }
                    repo.lastCommitDate = line.date
                    guard let event = classify(line, repo: repo) else { continue }
                    if stashed && event.kind == "reset" { continue }
                    emit(event)
                }
            }

            let remoteSizes = remoteLogSizes(repo.gitDir)
            for (path, newSize) in remoteSizes {
                let url = URL(fileURLWithPath: path)
                let start: UInt64
                if let old = repo.remoteLogSizes[path] {
                    guard newSize > old else { continue }
                    start = old
                } else {
                    // A remote branch log that just appeared (first push of a new branch) counts only if it is fresh.
                    let modified = (try? url.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
                    guard Date().timeIntervalSince(modified) < 10 else { continue }
                    start = 0
                }
                let text = readTail(url, from: start)
                for raw in text.split(separator: "\n") {
                    guard let line = Self.parseReflogLine(String(raw)), line.message.hasPrefix("update by push") else { continue }
                    let branch = URL(fileURLWithPath: path).lastPathComponent
                    repo.lastActivity = Date()
                    lastActiveRepo = key
                    emit(GitEvent(kind: "push", repo: repo.name, branch: branch, message: "", hash: line.newHash))
                }
            }
            repo.remoteLogSizes = remoteSizes
            tracked[key] = repo
        }
    }

    private func classify(_ line: ReflogLine, repo: Tracked) -> GitEvent? {
        let msg = line.message
        let branch = currentBranch(repo.gitDir)
        func after(_ prefix: String) -> String {
            String(msg.dropFirst(prefix.count)).trimmingCharacters(in: .whitespaces)
        }
        var event: GitEvent?
        if msg.hasPrefix("commit (amend):") {
            event = GitEvent(kind: "amend", repo: repo.name, branch: branch, message: after("commit (amend):"), hash: line.newHash)
        } else if msg.hasPrefix("commit (initial):") {
            event = GitEvent(kind: "commit", repo: repo.name, branch: branch, message: after("commit (initial):"), hash: line.newHash)
        } else if msg.hasPrefix("commit (merge):") {
            event = GitEvent(kind: "merge", repo: repo.name, branch: branch, message: after("commit (merge):"), hash: line.newHash)
        } else if msg.hasPrefix("commit:") {
            event = GitEvent(kind: "commit", repo: repo.name, branch: branch, message: after("commit:"), hash: line.newHash)
        } else if msg.hasPrefix("checkout: moving from") {
            let target = msg.components(separatedBy: " to ").last ?? branch
            event = GitEvent(kind: "checkout", repo: repo.name, branch: target, message: "", hash: line.newHash)
        } else if msg.hasPrefix("merge ") {
            event = GitEvent(kind: "merge", repo: repo.name, branch: branch, message: msg, hash: line.newHash)
        } else if msg.hasPrefix("pull") {
            event = GitEvent(kind: "pull", repo: repo.name, branch: branch, message: msg, hash: line.newHash)
        } else if msg.hasPrefix("rebase") && msg.contains("(start)") {
            event = GitEvent(kind: "rebase", repo: repo.name, branch: branch, message: msg, hash: line.newHash)
        } else if msg.hasPrefix("rebase") && msg.contains("(finish)") {
            event = GitEvent(kind: "rebase-done", repo: repo.name, branch: branch, message: msg, hash: line.newHash)
        } else if msg.hasPrefix("reset:") {
            event = GitEvent(kind: "reset", repo: repo.name, branch: branch, message: after("reset:"), hash: line.newHash)
        } else if msg.hasPrefix("cherry-pick:") {
            event = GitEvent(kind: "cherry-pick", repo: repo.name, branch: branch, message: after("cherry-pick:"), hash: line.newHash)
        }
        guard var result = event else { return nil }
        if ["commit", "amend", "merge", "cherry-pick"].contains(result.kind), !result.hash.isEmpty {
            let stat = commitStat(workTree: repo.workTree, hash: result.hash)
            result.files = stat.files
            result.insertions = stat.insertions
            result.deletions = stat.deletions
        }
        return result
    }

    private func emit(_ event: GitEvent) {
        switch event.kind {
        case "commit", "merge", "cherry-pick": bumpToday(commits: 1)
        case "push": bumpToday(pushes: 1)
        default: bumpToday()
        }
        lastEventSummary = "\(event.kind) in \(event.repo)" + (event.branch.isEmpty ? "" : " (\(event.branch))")
        DispatchQueue.main.async { self.onEvent?(event) }
    }

    // MARK: git subprocess helpers

    private func runGit(_ arguments: [String], in workTree: URL) -> String? {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/git")
        process.arguments = ["-C", workTree.path] + arguments
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = FileHandle.nullDevice
        var env = ProcessInfo.processInfo.environment
        env["GIT_OPTIONAL_LOCKS"] = "0"
        process.environment = env
        do { try process.run() } catch { return nil }
        let deadline = DispatchWorkItem { if process.isRunning { process.terminate() } }
        queue.asyncAfter(deadline: .now() + 5, execute: deadline)
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        deadline.cancel()
        guard process.terminationStatus == 0 else { return nil }
        return String(decoding: data, as: UTF8.self)
    }

    private func commitStat(workTree: URL, hash: String) -> (files: Int, insertions: Int, deletions: Int) {
        guard let out = runGit(["show", "--shortstat", "--format=", hash], in: workTree) else { return (0, 0, 0) }
        // " 3 files changed, 120 insertions(+), 4 deletions(-)"
        func number(before word: String) -> Int {
            guard let range = out.range(of: word) else { return 0 }
            let prefix = out[..<range.lowerBound]
            let digits = prefix.reversed().drop(while: { $0 == " " }).prefix(while: { $0.isNumber })
            return Int(String(digits.reversed())) ?? 0
        }
        return (number(before: " file"), number(before: " insertion"), number(before: " deletion"))
    }

    private func reportStatus() {
        let candidate = lastActiveRepo.flatMap { tracked[$0] } ?? tracked.values.max { $0.lastActivity < $1.lastActivity }
        guard let repo = candidate else { return }
        let out = runGit(["status", "--porcelain", "--untracked-files=no"], in: repo.workTree) ?? ""
        let dirty = out.split(separator: "\n").count
        let minutes = repo.lastCommitDate.map { Int(Date().timeIntervalSince($0) / 60) } ?? -1
        let status = GitStatus(repo: repo.name, branch: currentBranch(repo.gitDir), dirty: dirty, minutesSinceCommit: minutes)
        DispatchQueue.main.async { self.onStatus?(status) }
    }
}
