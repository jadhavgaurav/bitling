// Watches test runs and deployments and reports them as events.
//
// Three sources, all optional:
//  1. GitHub Actions runs and GitHub Deployments for watched repositories that have a
//     github.com origin, through the `gh` CLI when it is installed and logged in, or
//     through a GitHubAuth device-flow token when it is not.
//  2. Local pytest runs: pytest rewrites .pytest_cache\v\cache\nodeids on every run and
//     keeps failing test ids in .pytest_cache\v\cache\lastfailed.
//  3. The bitling:// URL scheme, handled by the host, for any other tool or script.
//
// Ported from apps/macos/Sources/CIWatcher.swift.
using System.Diagnostics;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using Bitling.Auth;
using Bitling.Models;

namespace Bitling.Watchers;

public sealed class CIWatcher
{
    public Func<List<WatchedRepo>> Repositories { get; set; } = () => new();
    public event Action<GitEvent>? OnEvent;

    private string? _ghPath;
    public string GhStatus { get; private set; } = "checking gh…";
    public string LastSummary { get; private set; } = "nothing yet";

    private readonly Dictionary<string, string> _runState = new();
    private readonly Dictionary<string, string> _deployState = new();
    private readonly HashSet<string> _primedSlugs = new();
    private readonly Dictionary<string, DateTime> _pytestSeen = new();
    private List<string> _pytestTargets = new();

    private System.Threading.Timer? _pytestTimer, _ghTimer, _rescanTimer;

    private static readonly Regex DeployPattern = new(@"deploy|release|publish|\bcd\b|rollout", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly HashSet<string> Skipped = new(StringComparer.OrdinalIgnoreCase)
        { "node_modules", ".venv", "venv", "build", "dist", "Pods", ".next", ".cache", "__pycache__" };

    public void Start()
    {
        Task.Run(() => { DetectGh(); RescanPytest(); });
        _pytestTimer = new System.Threading.Timer(_ => Task.Run(PollPytest), null, TimeSpan.FromSeconds(3), TimeSpan.FromSeconds(3));
        _rescanTimer = new System.Threading.Timer(_ => Task.Run(RescanPytest), null, TimeSpan.FromSeconds(60), TimeSpan.FromSeconds(60));
        _ghTimer = new System.Threading.Timer(_ => Task.Run(PollGitHub), null, TimeSpan.FromSeconds(60), TimeSpan.FromSeconds(60));
        Task.Delay(TimeSpan.FromSeconds(8)).ContinueWith(_ => PollGitHub());
    }

    /// Re-checks both transports. Call after the user connects or disconnects GitHub
    /// in the control room so the panel and the next poll pick it up immediately.
    public void RefreshGitHubConnection() => Task.Run(() => { DetectGh(); PollGitHub(); });

    private static readonly string[] GhCandidates =
    {
        @"C:\Program Files\GitHub CLI\gh.exe",
        @"C:\Program Files (x86)\GitHub CLI\gh.exe",
    };

    private void DetectGh()
    {
        var found = GhCandidates.FirstOrDefault(File.Exists);
        if (found != null)
        {
            _ghPath = found;
            if (RunGh(new[] { "auth", "status" }) != null) { GhStatus = "GitHub Actions and deployments via gh"; return; }
            _ghPath = null;
        }
        else
        {
            // gh may still be reachable on PATH even without a known install path.
            _ghPath = "gh";
            if (RunGh(new[] { "auth", "status" }) != null) { GhStatus = "GitHub Actions and deployments via gh"; return; }
            _ghPath = null;
        }
        var token = GitHubAuth.StoredToken();
        if (token != null)
        {
            var login = GitHubAuth.FetchLogin(token);
            if (login != null) { GhStatus = $"GitHub Actions and deployments via {login}'s GitHub account"; return; }
            GitHubAuth.SignOut();
            GhStatus = "GitHub sign-in expired, reconnect in Setup";
            return;
        }
        GhStatus = "not connected, connect GitHub in Setup";
    }

    private byte[]? RunGh(string[] arguments)
    {
        var gh = _ghPath ?? GhCandidates.FirstOrDefault(File.Exists);
        if (gh is null) return null;
        try
        {
            var psi = new ProcessStartInfo(gh)
            {
                RedirectStandardOutput = true, RedirectStandardError = false,
                UseShellExecute = false, CreateNoWindow = true,
            };
            foreach (var arg in arguments) psi.ArgumentList.Add(arg);
            psi.Environment["GH_NO_UPDATE_NOTIFIER"] = "1";
            psi.Environment["GH_PROMPT_DISABLED"] = "1";
            psi.Environment["NO_COLOR"] = "1";
            using var process = Process.Start(psi);
            if (process is null) return null;
            using var ms = new MemoryStream();
            process.StandardOutput.BaseStream.CopyTo(ms);
            if (!process.WaitForExit(25000)) { process.Kill(); return null; }
            return process.ExitCode == 0 ? ms.ToArray() : null;
        }
        catch { return null; }
    }

    /// Fetches a GitHub REST API path through whichever transport is active: `gh api`
    /// when gh is installed and logged in, otherwise a direct call with the stored token.
    private byte[]? ApiData(string path)
    {
        if (_ghPath != null) return RunGh(new[] { "api", path });
        var token = GitHubAuth.StoredToken();
        if (token is null) return null;
        try { return GitHubAuth.Get(new Uri($"https://api.github.com/{path}"), token); } catch { return null; }
    }

    private static List<JsonObject> JsonArray(byte[]? data)
    {
        if (data is null) return new();
        try { return (JsonNode.Parse(data) as JsonArray)?.OfType<JsonObject>().ToList() ?? new(); }
        catch { return new(); }
    }

    private static JsonObject JsonObj(byte[]? data)
    {
        if (data is null) return new();
        try { return JsonNode.Parse(data) as JsonObject ?? new(); }
        catch { return new(); }
    }

    private static bool IsDeployName(string name) => DeployPattern.IsMatch(name);

    private static DateTime? ParseDate(JsonNode? value) =>
        value is null ? null : (DateTime.TryParse(value.GetValue<string>(), null,
            System.Globalization.DateTimeStyles.RoundtripKind, out var d) ? d : null);

    private void PollGitHub()
    {
        if (_ghPath is null && GitHubAuth.StoredToken() is null) return;
        foreach (var repo in Repositories().Where(r => r.Slug != null))
        {
            PollRuns(repo.Slug!, repo.Name);
            PollDeployments(repo.Slug!, repo.Name);
            _primedSlugs.Add(repo.Slug!);
        }
    }

    private void PollRuns(string slug, string repoName)
    {
        var runs = (JsonObj(ApiData($"repos/{slug}/actions/runs?per_page=10"))["workflow_runs"] as JsonArray)?.OfType<JsonObject>().ToList() ?? new();
        var primed = _primedSlugs.Contains(slug);
        foreach (var run in runs)
        {
            var id = run["id"]?.GetValue<long>();
            if (id is null) continue;
            var key = $"{slug}#{id}";
            var status = run["status"]?.GetValue<string>() ?? "";
            var conclusion = run["conclusion"]?.GetValue<string>() ?? "";
            var current = $"{status}/{conclusion}";
            _runState.TryGetValue(key, out var previous);
            _runState[key] = current;
            if (!primed || previous == current) continue;
            if (ParseDate(run["created_at"]) is { } created && (DateTime.UtcNow - created) > TimeSpan.FromHours(3)) continue;
            var name = run["name"]?.GetValue<string>() ?? "workflow";
            var branch = run["head_branch"]?.GetValue<string>() ?? "";
            var deploy = IsDeployName(name);
            var target = $"{repoName} {branch}".Trim();
            if (status == "in_progress" && previous is null && deploy)
            {
                Emit(new GitEvent { Kind = "deploy-started", Repo = repoName, Branch = branch, Message = name, Target = target, Name = name });
                continue;
            }
            if (status != "completed") continue;
            switch (conclusion)
            {
                case "success":
                    Emit(new GitEvent { Kind = deploy ? "deploy-finished" : "test-passed", Repo = repoName, Branch = branch, Message = name, Target = target, Name = $"{name} on {branch}" });
                    break;
                case "failure" or "timed_out":
                    Emit(new GitEvent { Kind = deploy ? "deploy-failed" : "test-failed", Repo = repoName, Branch = branch, Message = name, Target = target, Name = $"{name} on {branch}" });
                    break;
            }
        }
    }

    private void PollDeployments(string slug, string repoName)
    {
        var deployments = JsonArray(ApiData($"repos/{slug}/deployments?per_page=5"));
        var primed = _primedSlugs.Contains(slug);
        var terminal = new HashSet<string> { "success", "failure", "error", "inactive" };
        foreach (var deployment in deployments)
        {
            var id = deployment["id"]?.GetValue<long>();
            if (id is null) continue;
            var key = $"{slug}#{id}";
            if (_deployState.TryGetValue(key, out var prevState) && terminal.Contains(prevState)) continue;
            if (ParseDate(deployment["created_at"]) is { } created && (DateTime.UtcNow - created) > TimeSpan.FromHours(6))
            {
                _deployState[key] = "inactive";
                continue;
            }
            var environment = (deployment["environment"]?.GetValue<string>() ?? "").ToLowerInvariant();
            var target = string.IsNullOrEmpty(environment) ? repoName : $"{repoName} {environment}";
            var statuses = JsonArray(ApiData($"repos/{slug}/deployments/{id}/statuses?per_page=1"));
            var state = statuses.FirstOrDefault()?["state"]?.GetValue<string>() ?? "pending";
            _deployState.TryGetValue(key, out var previous);
            _deployState[key] = state;
            if (!primed) continue;
            if (previous is null)
                Emit(new GitEvent { Kind = "deploy-started", Repo = repoName, Branch = deployment["ref"]?.GetValue<string>() ?? "", Target = target, Name = environment });
            if (previous == state) continue;
            switch (state)
            {
                case "success": Emit(new GitEvent { Kind = "deploy-finished", Repo = repoName, Target = target, Name = environment }); break;
                case "failure" or "error": Emit(new GitEvent { Kind = "deploy-failed", Repo = repoName, Target = target, Name = environment }); break;
            }
        }
    }

    // MARK: pytest

    private void RescanPytest()
    {
        var targets = new List<string>();
        foreach (var repo in Repositories())
        {
            var candidates = new List<string> { repo.WorkTree };
            try
            {
                foreach (var child in Directory.EnumerateDirectories(repo.WorkTree))
                {
                    var name = Path.GetFileName(child);
                    if (!Skipped.Contains(name)) candidates.Add(child);
                }
            }
            catch { /* unreadable directory */ }
            foreach (var dir in candidates)
                if (File.Exists(Path.Combine(dir, ".pytest_cache", "v", "cache", "nodeids"))) targets.Add(dir);
        }
        _pytestTargets = targets;
        foreach (var dir in targets)
        {
            var path = Path.Combine(dir, ".pytest_cache", "v", "cache", "nodeids");
            if (!_pytestSeen.ContainsKey(path)) _pytestSeen[path] = ModificationDate(path);
        }
    }

    private static DateTime ModificationDate(string path) => File.Exists(path) ? File.GetLastWriteTime(path) : DateTime.MinValue;

    private void PollPytest()
    {
        foreach (var dir in _pytestTargets)
        {
            var nodeidsPath = Path.Combine(dir, ".pytest_cache", "v", "cache", "nodeids");
            var modified = ModificationDate(nodeidsPath);
            if (!_pytestSeen.TryGetValue(nodeidsPath, out var seen)) { _pytestSeen[nodeidsPath] = modified; continue; }
            if (modified <= seen) continue;
            _pytestSeen[nodeidsPath] = modified;
            Task.Delay(1500).ContinueWith(_ => ReportPytest(dir));
        }
    }

    private void ReportPytest(string dir)
    {
        var lastFailed = Path.Combine(dir, ".pytest_cache", "v", "cache", "lastfailed");
        var failing = 0;
        var names = new List<string>();
        if (File.Exists(lastFailed))
        {
            try
            {
                var obj = JsonNode.Parse(File.ReadAllText(lastFailed)) as JsonObject;
                if (obj != null)
                {
                    failing = obj.Count;
                    // "tests/test_billing.py::test_webhook_signature" reads better as the test name alone.
                    names = obj.Select(kv => kv.Key).OrderBy(k => k).Take(6)
                        .Select(key =>
                        {
                            var parts = key.Split("::");
                            if (parts.Length > 1 && parts[^1].Length > 0) return parts[^1];
                            var segs = key.Split('/');
                            return segs[^1];
                        }).ToList();
                }
            }
            catch { /* malformed cache file */ }
        }
        var repos = Repositories();
        var owner = repos.FirstOrDefault(r => dir.StartsWith(r.WorkTree, StringComparison.OrdinalIgnoreCase));
        var name = Path.GetFileName(dir);
        if (owner != null && !owner.WorkTree.Equals(dir, StringComparison.OrdinalIgnoreCase)) name = $"{owner.Name}/{Path.GetFileName(dir)}";
        Emit(new GitEvent
        {
            Kind = failing > 0 ? "test-failed" : "test-passed", Repo = owner?.Name ?? name, Message = "pytest",
            Count = failing, Name = name, Tests = names.ToArray(),
        });
    }

    private void Emit(GitEvent e)
    {
        LastSummary = $"{e.Kind} · {(string.IsNullOrEmpty(e.Name) ? e.Repo : e.Name)}";
        OnEvent?.Invoke(e);
    }
}
