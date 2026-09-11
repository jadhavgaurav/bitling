// Watches test runs and deployments and reports them as events.
//
// Three sources, all optional:
//  1. GitHub Actions runs and GitHub Deployments for watched repositories that have a
//     github.com origin, through the `gh` CLI when it is installed and logged in, or
//     through a GitHubAuth device-flow token when it is not. Workflows whose name
//     mentions deploy/release/publish/cd count as deployments, everything else counts
//     as tests. Vercel and similar services record GitHub Deployments, so their
//     deploys show up too.
//  2. Local pytest runs: pytest rewrites .pytest_cache/v/cache/nodeids on every run
//     and keeps failing test ids in .pytest_cache/v/cache/lastfailed.
//  3. The bitling:// URL scheme (see Resources/bitling), handled by the host, for any
//     other tool or script.

import Foundation

final class CIWatcher {
    var repositories: () -> [WatchedRepo] = { [] }
    var onEvent: ((GitEvent) -> Void)?

    private let queue = DispatchQueue(label: "app.bitling.ci", qos: .utility)
    private var ghPath: String?
    private(set) var ghStatus = "checking gh…"
    private(set) var lastSummary = "nothing yet"

    private var runState: [String: String] = [:]
    private var deployState: [String: String] = [:]
    private var primedSlugs: Set<String> = []
    private var pytestSeen: [String: Date] = [:]
    private var pytestTargets: [URL] = []

    private var pytestTimer: Timer?
    private var ghTimer: Timer?
    private var rescanTimer: Timer?

    private static let deployPattern = try! NSRegularExpression(pattern: "deploy|release|publish|\\bcd\\b|rollout", options: [.caseInsensitive])
    private static let skipped: Set<String> = ["node_modules", ".venv", "venv", "build", "dist", "Pods", ".next", ".cache", "__pycache__"]

    func start() {
        queue.async {
            self.detectGh()
            self.rescanPytest()
        }
        pytestTimer = Timer(timeInterval: 3.0, repeats: true) { [weak self] _ in self?.queue.async { self?.pollPytest() } }
        rescanTimer = Timer(timeInterval: 60.0, repeats: true) { [weak self] _ in self?.queue.async { self?.rescanPytest() } }
        ghTimer = Timer(timeInterval: 60.0, repeats: true) { [weak self] _ in self?.queue.async { self?.pollGitHub() } }
        for timer in [pytestTimer!, rescanTimer!, ghTimer!] { RunLoop.main.add(timer, forMode: .common) }
        queue.asyncAfter(deadline: .now() + 8) { self.pollGitHub() }
    }

    // MARK: gh, or a GitHubAuth token when gh is not available

    /// Re-checks both transports. Call after the user connects or disconnects GitHub
    /// in the control room so the panel and the next poll pick it up immediately.
    func refreshGitHubConnection() {
        queue.async {
            self.detectGh()
            self.pollGitHub()
        }
    }

    private func detectGh() {
        let candidates = ["/opt/homebrew/bin/gh", "/usr/local/bin/gh", "/usr/bin/gh"]
        if let path = candidates.first(where: { FileManager.default.isExecutableFile(atPath: $0) }) {
            ghPath = path
            if runGh(["auth", "status"]) != nil {
                ghStatus = "GitHub Actions and deployments via gh"
                return
            }
            ghPath = nil
        }
        if let token = GitHubAuth.storedToken() {
            if let login = GitHubAuth.fetchLogin(token: token) {
                ghStatus = "GitHub Actions and deployments via \(login)'s GitHub account"
            } else {
                GitHubAuth.signOut()
                ghStatus = "GitHub sign-in expired, reconnect in Setup"
            }
            return
        }
        ghStatus = "not connected, connect GitHub in Setup"
    }

    private func runGh(_ arguments: [String]) -> Data? {
        guard let gh = ghPath ?? ["/opt/homebrew/bin/gh", "/usr/local/bin/gh"].first(where: { FileManager.default.isExecutableFile(atPath: $0) }) else { return nil }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: gh)
        process.arguments = arguments
        var env = ProcessInfo.processInfo.environment
        env["GH_NO_UPDATE_NOTIFIER"] = "1"
        env["GH_PROMPT_DISABLED"] = "1"
        env["NO_COLOR"] = "1"
        process.environment = env
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = FileHandle.nullDevice
        do { try process.run() } catch { return nil }
        let deadline = DispatchWorkItem { if process.isRunning { process.terminate() } }
        queue.asyncAfter(deadline: .now() + 25, execute: deadline)
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        deadline.cancel()
        return process.terminationStatus == 0 ? data : nil
    }

    /// Fetches a GitHub REST API path through whichever transport is active: `gh api`
    /// when gh is installed and logged in, otherwise a direct call with the stored token.
    private func apiData(_ path: String) -> Data? {
        if ghPath != nil { return runGh(["api", path]) }
        guard let token = GitHubAuth.storedToken() else { return nil }
        return try? GitHubAuth.get(url: URL(string: "https://api.github.com/\(path)")!, token: token)
    }

    private func jsonArray(_ data: Data?) -> [[String: Any]] {
        guard let data, let parsed = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]] else { return [] }
        return parsed
    }

    private func jsonObject(_ data: Data?) -> [String: Any] {
        guard let data, let parsed = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return [:] }
        return parsed
    }

    private static func isDeployName(_ name: String) -> Bool {
        deployPattern.firstMatch(in: name, range: NSRange(name.startIndex..., in: name)) != nil
    }

    private static func parseDate(_ value: Any?) -> Date? {
        guard let text = value as? String else { return nil }
        let iso = ISO8601DateFormatter()
        return iso.date(from: text)
    }

    private func pollGitHub() {
        guard ghPath != nil || GitHubAuth.storedToken() != nil else { return }
        let repos = repositories().filter { $0.slug != nil }
        for repo in repos {
            guard let slug = repo.slug else { continue }
            pollRuns(slug: slug, repoName: repo.workTree.lastPathComponent)
            pollDeployments(slug: slug, repoName: repo.workTree.lastPathComponent)
            primedSlugs.insert(slug)
        }
    }

    private func pollRuns(slug: String, repoName: String) {
        let runs = jsonObject(apiData("repos/\(slug)/actions/runs?per_page=10"))["workflow_runs"] as? [[String: Any]] ?? []
        let primed = primedSlugs.contains(slug)
        for run in runs {
            guard let id = run["id"] as? Int else { continue }
            let key = "\(slug)#\(id)"
            let status = run["status"] as? String ?? ""
            let conclusion = run["conclusion"] as? String ?? ""
            let current = "\(status)/\(conclusion)"
            let previous = runState[key]
            runState[key] = current
            guard primed, previous != current else { continue }
            if let created = Self.parseDate(run["created_at"]), Date().timeIntervalSince(created) > 3 * 3600 { continue }
            let name = run["name"] as? String ?? "workflow"
            let branch = run["head_branch"] as? String ?? ""
            let deploy = Self.isDeployName(name)
            let target = "\(repoName) \(branch)".trimmingCharacters(in: .whitespaces)
            if status == "in_progress", previous == nil, deploy {
                emit(GitEvent(kind: "deploy-started", repo: repoName, branch: branch, message: name, hash: "", target: target, name: name))
                continue
            }
            guard status == "completed" else { continue }
            switch conclusion {
            case "success":
                emit(GitEvent(kind: deploy ? "deploy-finished" : "test-passed", repo: repoName, branch: branch, message: name, hash: "", target: target, name: "\(name) on \(branch)"))
            case "failure", "timed_out":
                emit(GitEvent(kind: deploy ? "deploy-failed" : "test-failed", repo: repoName, branch: branch, message: name, hash: "", target: target, name: "\(name) on \(branch)"))
            default:
                break
            }
        }
    }

    private func pollDeployments(slug: String, repoName: String) {
        let deployments = jsonArray(apiData("repos/\(slug)/deployments?per_page=5"))
        let primed = primedSlugs.contains(slug)
        let terminal: Set<String> = ["success", "failure", "error", "inactive"]
        for deployment in deployments {
            guard let id = deployment["id"] as? Int else { continue }
            let key = "\(slug)#\(id)"
            if let previous = deployState[key], terminal.contains(previous) { continue }
            if let created = Self.parseDate(deployment["created_at"]), Date().timeIntervalSince(created) > 6 * 3600 {
                deployState[key] = "inactive"
                continue
            }
            let environment = (deployment["environment"] as? String ?? "").lowercased()
            let target = environment.isEmpty ? repoName : "\(repoName) \(environment)"
            let statuses = jsonArray(apiData("repos/\(slug)/deployments/\(id)/statuses?per_page=1"))
            let state = statuses.first?["state"] as? String ?? "pending"
            let previous = deployState[key]
            deployState[key] = state
            guard primed else { continue }
            if previous == nil {
                emit(GitEvent(kind: "deploy-started", repo: repoName, branch: deployment["ref"] as? String ?? "", message: "", hash: "", target: target, name: environment))
            }
            guard previous != state else { continue }
            switch state {
            case "success":
                emit(GitEvent(kind: "deploy-finished", repo: repoName, branch: "", message: "", hash: "", target: target, name: environment))
            case "failure", "error":
                emit(GitEvent(kind: "deploy-failed", repo: repoName, branch: "", message: "", hash: "", target: target, name: environment))
            default:
                break
            }
        }
    }

    // MARK: pytest

    private func rescanPytest() {
        var targets: [URL] = []
        let fm = FileManager.default
        for repo in repositories() {
            var candidates = [repo.workTree]
            if let children = try? fm.contentsOfDirectory(at: repo.workTree, includingPropertiesForKeys: [.isDirectoryKey], options: [.skipsHiddenFiles]) {
                for child in children where (try? child.resourceValues(forKeys: [.isDirectoryKey]).isDirectory) == true && !Self.skipped.contains(child.lastPathComponent) {
                    candidates.append(child)
                }
            }
            for dir in candidates {
                let nodeids = dir.appendingPathComponent(".pytest_cache/v/cache/nodeids")
                if fm.fileExists(atPath: nodeids.path) { targets.append(dir) }
            }
        }
        pytestTargets = targets
        for dir in targets {
            let path = dir.appendingPathComponent(".pytest_cache/v/cache/nodeids").path
            if pytestSeen[path] == nil { pytestSeen[path] = modificationDate(path) }
        }
    }

    private func modificationDate(_ path: String) -> Date {
        (try? FileManager.default.attributesOfItem(atPath: path)[.modificationDate] as? Date) ?? .distantPast
    }

    private func pollPytest() {
        for dir in pytestTargets {
            let nodeidsPath = dir.appendingPathComponent(".pytest_cache/v/cache/nodeids").path
            let modified = modificationDate(nodeidsPath)
            guard let seen = pytestSeen[nodeidsPath] else { pytestSeen[nodeidsPath] = modified; continue }
            guard modified > seen else { continue }
            pytestSeen[nodeidsPath] = modified
            queue.asyncAfter(deadline: .now() + 1.5) { self.reportPytest(dir: dir) }
        }
    }

    private func reportPytest(dir: URL) {
        let lastFailed = dir.appendingPathComponent(".pytest_cache/v/cache/lastfailed")
        var failing = 0
        var names: [String] = []
        if let data = try? Data(contentsOf: lastFailed), let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            failing = dict.count
            // "tests/test_billing.py::test_webhook_signature" reads better as the test name alone.
            names = dict.keys.sorted().prefix(6).map { key in
                if let last = key.components(separatedBy: "::").last, !last.isEmpty { return last }
                return key.components(separatedBy: "/").last ?? key
            }
        }
        let repos = repositories()
        let owner = repos.first { dir.path.hasPrefix($0.workTree.path) }
        var name = dir.lastPathComponent
        if let owner, owner.workTree.path != dir.path { name = "\(owner.workTree.lastPathComponent)/\(dir.lastPathComponent)" }
        let event = GitEvent(kind: failing > 0 ? "test-failed" : "test-passed", repo: owner?.workTree.lastPathComponent ?? name, branch: "", message: "pytest", hash: "", count: failing, target: "", name: name, tests: names)
        emit(event)
    }

    private func emit(_ event: GitEvent) {
        lastSummary = "\(event.kind) · \(event.name.isEmpty ? event.repo : event.name)"
        DispatchQueue.main.async { self.onEvent?(event) }
    }
}
