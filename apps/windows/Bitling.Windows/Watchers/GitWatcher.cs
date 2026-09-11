// Watches git repositories under a set of root folders and reports activity.
//
// No git process is needed to notice events: every repository keeps a reflog in
// .git\logs\HEAD (commits, checkouts, merges, rebases, resets) and one per remote
// branch in .git\logs\refs\remotes\<remote>\<branch> ("update by push"). Tailing
// those files every couple of seconds is cheap and instant. `git` itself is only
// run for optional enrichment (commit size) and for the periodic dirty-file count.
//
// Ported from apps/macos/Sources/GitWatcher.swift. Behavior should match line for line;
// only the platform primitives (paths, process launching, persistence) differ.
using System.Diagnostics;
using System.Text.RegularExpressions;
using Bitling.Models;
using Bitling.Settings;

namespace Bitling.Watchers;

public sealed class GitWatcher
{
    private sealed class Tracked
    {
        public required string WorkTree;
        public required string GitDir;
        public long HeadLogSize;
        public long StashLogSize;
        public Dictionary<string, long> RemoteLogSizes = new();
        public DateTime? LastCommitDate;
        public DateTime LastActivity;
        public string? Slug;
        public string Name => Path.GetFileName(WorkTree.TrimEnd(Path.DirectorySeparatorChar));
    }

    private const string RootsKey = "gitExtraRoots";
    private const string CacheKey = "gitRepoCache";
    private const string TodayKey = "gitToday";
    private const int MaxDepth = 7;
    private static readonly HashSet<string> SkippedDirectories = new(StringComparer.OrdinalIgnoreCase)
    {
        "node_modules", ".venv", "venv", "env", "AppData", "build", "dist", "target", "out", "Pods",
        "DerivedData", ".next", ".nuxt", ".turbo", ".cache", ".npm", ".cargo", ".rustup", ".gradle", ".m2",
        ".pub-cache", "Pictures", "Music", "Videos", "Public", "vendor", "site-packages", "__pycache__",
        "$Recycle.Bin", "System Volume Information", "Windows", "Program Files", "Program Files (x86)",
    };

    public List<string> ExtraRoots { get; }
    public DateTime? LastScan { get; private set; }
    private bool _scanning;
    private readonly Dictionary<string, Tracked> _tracked = new();
    private readonly object _lock = new();
    private System.Threading.Timer? _pollTimer, _scanTimer, _statusTimer;
    private string? _lastActiveRepo;

    public int CommitsToday { get; private set; }
    public int PushesToday { get; private set; }
    private string _todayKey = "";
    public string LastEventSummary { get; private set; } = "nothing yet";

    public event Action<GitEvent>? OnEvent;
    public event Action<GitStatus>? OnStatus;

    public int RepositoryCount { get { lock (_lock) return _tracked.Count; } }

    public List<WatchedRepo> Repositories()
    {
        lock (_lock) return _tracked.Values.Select(t => new WatchedRepo(t.WorkTree, t.Slug)).ToList();
    }

    private static string DayString() => DateTime.Now.ToString("yyyy-MM-dd");

    public GitWatcher()
    {
        ExtraRoots = AppSettings.GetStringArray(RootsKey).ToList();
        var today = AppSettings.GetObject(TodayKey);
        if (today?["day"]?.GetValue<string>() == DayString())
        {
            CommitsToday = today["commits"]?.GetValue<int>() ?? 0;
            PushesToday = today["pushes"]?.GetValue<int>() ?? 0;
        }
        _todayKey = DayString();
    }

    private static List<string> DeviceRoots()
    {
        var roots = new List<string> { Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) };
        try
        {
            foreach (var drive in DriveInfo.GetDrives())
            {
                if (!drive.IsReady) continue;
                if (drive.DriveType is not (DriveType.Fixed or DriveType.Removable or DriveType.Network)) continue;
                if (drive.RootDirectory.FullName.Equals(Path.GetPathRoot(Environment.SystemDirectory), StringComparison.OrdinalIgnoreCase)) continue;
                roots.Add(drive.RootDirectory.FullName);
            }
        }
        catch { /* removable media can disappear mid-enumeration */ }
        return roots;
    }

    private List<string> Roots => DeviceRoots().Concat(ExtraRoots).ToList();

    public void Start()
    {
        Task.Run(() => { PrimeFromCache(); Scan(); });
        _pollTimer = new System.Threading.Timer(_ => Task.Run(Poll), null, TimeSpan.FromSeconds(2), TimeSpan.FromSeconds(2));
        _scanTimer = new System.Threading.Timer(_ => Task.Run(Scan), null, TimeSpan.FromMinutes(10), TimeSpan.FromMinutes(10));
        _statusTimer = new System.Threading.Timer(_ => Task.Run(ReportStatus), null, TimeSpan.FromSeconds(20), TimeSpan.FromSeconds(20));
    }

    public void AddRoot(string path)
    {
        if (Roots.Any(r => string.Equals(r, path, StringComparison.OrdinalIgnoreCase))) return;
        ExtraRoots.Add(path);
        SaveRoots();
        Task.Run(Scan);
    }

    public void RemoveRoot(string path)
    {
        ExtraRoots.RemoveAll(r => string.Equals(r, path, StringComparison.OrdinalIgnoreCase));
        SaveRoots();
        Task.Run(() =>
        {
            lock (_lock)
            {
                var roots = Roots;
                foreach (var key in _tracked.Keys.Where(k => !roots.Any(r => k.StartsWith(r, StringComparison.OrdinalIgnoreCase))).ToList())
                    _tracked.Remove(key);
                SaveCache();
            }
        });
    }

    public void Rescan() => Task.Run(Scan);

    private void SaveRoots() => AppSettings.SetStringArray(RootsKey, ExtraRoots);

    private void PrimeFromCache()
    {
        foreach (var path in AppSettings.GetStringArray(CacheKey))
        {
            if (Directory.Exists(path)) Register(path);
        }
    }

    private void SaveCache()
    {
        lock (_lock) AppSettings.SetStringArray(CacheKey, _tracked.Keys.OrderBy(k => k));
    }

    private void BumpToday(int commits = 0, int pushes = 0)
    {
        var day = DayString();
        if (day != _todayKey) { _todayKey = day; CommitsToday = 0; PushesToday = 0; }
        CommitsToday += commits;
        PushesToday += pushes;
        AppSettings.SetObject(TodayKey, new System.Text.Json.Nodes.JsonObject
        {
            ["day"] = day, ["commits"] = CommitsToday, ["pushes"] = PushesToday,
        });
    }

    // MARK: Discovery

    private void Scan()
    {
        if (_scanning) return;
        _scanning = true;
        try
        {
            HashSet<string> before;
            lock (_lock) before = new HashSet<string>(_tracked.Keys);
            foreach (var root in Roots) ScanDirectory(root, 0);
            lock (_lock)
            {
                foreach (var key in _tracked.Where(kv => !Directory.Exists(kv.Value.GitDir)).Select(kv => kv.Key).ToList())
                    _tracked.Remove(key);
                if (!before.SetEquals(_tracked.Keys)) SaveCache();
            }
            LastScan = DateTime.Now;
        }
        finally { _scanning = false; }
    }

    private void ScanDirectory(string dir, int depth)
    {
        if (depth > MaxDepth) return;
        var gitEntry = Path.Combine(dir, ".git");
        if (File.Exists(gitEntry) || Directory.Exists(gitEntry)) { Register(dir); return; }
        IEnumerable<string> children;
        try { children = Directory.EnumerateDirectories(dir); }
        catch { return; }
        foreach (var child in children)
        {
            var name = Path.GetFileName(child);
            if (SkippedDirectories.Contains(name) || name.StartsWith('.')) continue;
            DirectoryInfo info;
            try { info = new DirectoryInfo(child); } catch { continue; }
            if (info.Attributes.HasFlag(FileAttributes.ReparsePoint)) continue;
            ScanDirectory(child, depth + 1);
        }
    }

    private static string? ResolveGitDir(string workTree)
    {
        var entry = Path.Combine(workTree, ".git");
        if (Directory.Exists(entry)) return entry;
        if (!File.Exists(entry)) return null;
        // Worktrees and submodules keep a pointer file: "gitdir: <path>"
        var line = File.ReadAllText(entry).Trim();
        if (!line.StartsWith("gitdir:")) return null;
        var raw = line["gitdir:".Length..].Trim();
        var path = Path.IsPathRooted(raw) ? raw : Path.Combine(workTree, raw);
        return Path.GetFullPath(path);
    }

    private static string? GithubSlug(string gitDir)
    {
        var configPath = Path.Combine(gitDir, "config");
        if (!File.Exists(configPath))
        {
            var commonDirFile = Path.Combine(gitDir, "commondir");
            if (!File.Exists(commonDirFile)) return null;
            var common = File.ReadAllText(commonDirFile).Trim();
            var basePath = Path.IsPathRooted(common) ? common : Path.Combine(gitDir, common);
            configPath = Path.Combine(Path.GetFullPath(basePath), "config");
        }
        if (!File.Exists(configPath)) return null;
        var inOrigin = false;
        foreach (var rawLine in File.ReadAllLines(configPath))
        {
            var line = rawLine.Trim();
            if (line.StartsWith('[')) { inOrigin = line == "[remote \"origin\"]"; continue; }
            if (!inOrigin || !line.StartsWith("url")) continue;
            var eq = line.IndexOf('=');
            if (eq < 0) continue;
            var url = line[(eq + 1)..].Trim();
            var idx = url.IndexOf("github.com", StringComparison.Ordinal);
            if (idx < 0) return null;
            var rest = url[(idx + "github.com".Length)..];
            if (rest.StartsWith(':') || rest.StartsWith('/')) rest = rest[1..];
            if (rest.EndsWith(".git")) rest = rest[..^4];
            var parts = rest.Split('/');
            return parts.Length == 2 ? $"{parts[0]}/{parts[1]}" : null;
        }
        return null;
    }

    private void Register(string workTree)
    {
        lock (_lock)
        {
            if (_tracked.ContainsKey(workTree)) return;
            var gitDir = ResolveGitDir(workTree);
            if (gitDir is null) return;
            var headLog = Path.Combine(gitDir, "logs", "HEAD");
            _tracked[workTree] = new Tracked
            {
                WorkTree = workTree,
                GitDir = gitDir,
                HeadLogSize = FileSize(headLog),
                StashLogSize = FileSize(Path.Combine(gitDir, "logs", "refs", "stash")),
                RemoteLogSizes = RemoteLogSizes(gitDir),
                LastCommitDate = LastReflogDate(headLog),
                LastActivity = File.Exists(headLog) ? File.GetLastWriteTime(headLog) : DateTime.MinValue,
                Slug = GithubSlug(gitDir),
            };
        }
    }

    // MARK: Polling

    private static long FileSize(string path) => File.Exists(path) ? new FileInfo(path).Length : 0;

    private static Dictionary<string, long> RemoteLogSizes(string gitDir)
    {
        var sizes = new Dictionary<string, long>();
        var basePath = Path.Combine(gitDir, "logs", "refs", "remotes");
        if (!Directory.Exists(basePath)) return sizes;
        foreach (var file in Directory.EnumerateFiles(basePath, "*", SearchOption.AllDirectories))
            sizes[file] = FileSize(file);
        return sizes;
    }

    private static string ReadTail(string path, long offset)
    {
        try
        {
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            stream.Seek(offset, SeekOrigin.Begin);
            using var reader = new StreamReader(stream);
            return reader.ReadToEnd();
        }
        catch { return ""; }
    }

    private sealed record ReflogLine(string OldHash, string NewHash, DateTime Date, string Message);

    private static DateTime? LastReflogDate(string path)
    {
        if (!File.Exists(path)) return null;
        var lines = File.ReadAllLines(path);
        return lines.Length == 0 ? null : ParseReflogLine(lines[^1])?.Date;
    }

    private static ReflogLine? ParseReflogLine(string line)
    {
        // "<old> <new> Name <email> <unix-ts> <tz>\t<message>"
        var parts = line.Split('\t', 2);
        if (parts.Length != 2) return null;
        var head = parts[0].Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (head.Length < 4) return null;
        var tsIndex = head.Length - 2;
        var ts = long.TryParse(head[tsIndex], out var v) ? v : 0;
        return new ReflogLine(head[0], head[1], DateTimeOffset.FromUnixTimeSeconds(ts).LocalDateTime, parts[1]);
    }

    private static string CurrentBranch(string gitDir)
    {
        var headPath = Path.Combine(gitDir, "HEAD");
        if (!File.Exists(headPath)) return "";
        var line = File.ReadAllText(headPath).Trim();
        return line.StartsWith("ref: refs/heads/") ? line["ref: refs/heads/".Length..] : "detached";
    }

    private int _pollCount;
    /// Reflogs are history files. Anything written before the watcher started has already
    /// happened and must never be reported again, whatever order the files are noticed in.
    private readonly DateTime _watchingSince = DateTime.Now;

    private void Poll()
    {
        _pollCount++;
        List<Tracked> snapshot;
        lock (_lock) snapshot = _tracked.Values.ToList();
        foreach (var repo in snapshot)
        {
            // `git stash` rewrites HEAD with a "reset: moving to HEAD" reflog line; report the stash, not a reset.
            var stashLog = Path.Combine(repo.GitDir, "logs", "refs", "stash");
            var stashSize = FileSize(stashLog);
            var stashed = stashSize > repo.StashLogSize;
            repo.StashLogSize = stashSize;
            if (stashed)
            {
                repo.LastActivity = DateTime.Now;
                _lastActiveRepo = repo.WorkTree;
                Emit(new GitEvent { Kind = "stash", Repo = repo.Name, Branch = CurrentBranch(repo.GitDir) });
            }

            var headLog = Path.Combine(repo.GitDir, "logs", "HEAD");
            var size = FileSize(headLog);
            if (size < repo.HeadLogSize) repo.HeadLogSize = size;
            if (size > repo.HeadLogSize)
            {
                var text = ReadTail(headLog, repo.HeadLogSize);
                repo.HeadLogSize = size;
                repo.LastActivity = DateTime.Now;
                _lastActiveRepo = repo.WorkTree;
                foreach (var raw in text.Split('\n', StringSplitOptions.RemoveEmptyEntries))
                {
                    var line = ParseReflogLine(raw);
                    if (line is null) continue;
                    repo.LastCommitDate = line.Date;
                    if (line.Date <= _watchingSince) continue;
                    var ev = Classify(line, repo);
                    if (ev is null) continue;
                    if (stashed && ev.Kind == "reset") continue;
                    Emit(ev);
                }
            }

            // Remote reflogs: every poll for repos active in the last 15 minutes, every 30 seconds otherwise.
            var recentlyActive = (DateTime.Now - repo.LastActivity) < TimeSpan.FromMinutes(15);
            if (!recentlyActive && _pollCount % 15 != 0) continue;
            var remoteSizes = RemoteLogSizes(repo.GitDir);
            foreach (var (path, newSize) in remoteSizes)
            {
                long start;
                if (repo.RemoteLogSizes.TryGetValue(path, out var old))
                {
                    if (newSize <= old) continue;
                    start = old;
                }
                else
                {
                    // First sighting: read the whole file, but the timestamp filter below
                    // keeps everything that predates this session out of the counters.
                    start = 0;
                }
                var text = ReadTail(path, start);
                foreach (var raw in text.Split('\n', StringSplitOptions.RemoveEmptyEntries))
                {
                    var line = ParseReflogLine(raw);
                    if (line is null || !line.Message.StartsWith("update by push")) continue;
                    if (line.Date <= _watchingSince) continue;
                    var branch = Path.GetFileName(path);
                    repo.LastActivity = DateTime.Now;
                    _lastActiveRepo = repo.WorkTree;
                    Emit(new GitEvent { Kind = "push", Repo = repo.Name, Branch = branch, Hash = line.NewHash });
                }
            }
            repo.RemoteLogSizes = remoteSizes;
        }
    }

    private static GitEvent? Classify(ReflogLine line, Tracked repo)
    {
        var msg = line.Message;
        var branch = CurrentBranch(repo.GitDir);
        string After(string prefix) => msg[prefix.Length..].Trim();
        GitEvent? ev = null;
        if (msg.StartsWith("commit (amend):")) ev = new GitEvent { Kind = "amend", Repo = repo.Name, Branch = branch, Message = After("commit (amend):"), Hash = line.NewHash };
        else if (msg.StartsWith("commit (initial):")) ev = new GitEvent { Kind = "commit", Repo = repo.Name, Branch = branch, Message = After("commit (initial):"), Hash = line.NewHash };
        else if (msg.StartsWith("commit (merge):")) ev = new GitEvent { Kind = "merge", Repo = repo.Name, Branch = branch, Message = After("commit (merge):"), Hash = line.NewHash };
        else if (msg.StartsWith("commit:")) ev = new GitEvent { Kind = "commit", Repo = repo.Name, Branch = branch, Message = After("commit:"), Hash = line.NewHash };
        else if (msg.StartsWith("checkout: moving from"))
        {
            var idx = msg.LastIndexOf(" to ", StringComparison.Ordinal);
            var target = idx >= 0 ? msg[(idx + 4)..] : branch;
            ev = new GitEvent { Kind = "checkout", Repo = repo.Name, Branch = target, Hash = line.NewHash };
        }
        else if (msg.StartsWith("merge ")) ev = new GitEvent { Kind = "merge", Repo = repo.Name, Branch = branch, Message = msg, Hash = line.NewHash };
        else if (msg.StartsWith("pull")) ev = new GitEvent { Kind = "pull", Repo = repo.Name, Branch = branch, Message = msg, Hash = line.NewHash };
        else if (msg.StartsWith("rebase") && msg.Contains("(start)")) ev = new GitEvent { Kind = "rebase", Repo = repo.Name, Branch = branch, Message = msg, Hash = line.NewHash };
        else if (msg.StartsWith("rebase") && msg.Contains("(finish)")) ev = new GitEvent { Kind = "rebase-done", Repo = repo.Name, Branch = branch, Message = msg, Hash = line.NewHash };
        else if (msg.StartsWith("reset:")) ev = new GitEvent { Kind = "reset", Repo = repo.Name, Branch = branch, Message = After("reset:"), Hash = line.NewHash };
        else if (msg.StartsWith("cherry-pick:")) ev = new GitEvent { Kind = "cherry-pick", Repo = repo.Name, Branch = branch, Message = After("cherry-pick:"), Hash = line.NewHash };
        if (ev is null) return null;
        if (new[] { "commit", "amend", "merge", "cherry-pick" }.Contains(ev.Kind) && !string.IsNullOrEmpty(ev.Hash))
        {
            var (files, ins, del) = CommitStat(repo.WorkTree, ev.Hash);
            ev = new GitEvent
            {
                Kind = ev.Kind, Repo = ev.Repo, Branch = ev.Branch, Message = ev.Message, Hash = ev.Hash,
                Files = files, Insertions = ins, Deletions = del,
            };
        }
        return ev;
    }

    public void RecordPretend(int commits = 0, int pushes = 0) => BumpToday(commits, pushes);

    private void Emit(GitEvent e)
    {
        switch (e.Kind)
        {
            case "commit" or "merge" or "cherry-pick": BumpToday(commits: 1); break;
            case "push": BumpToday(pushes: 1); break;
            default: BumpToday(); break;
        }
        e.CommitsToday = CommitsToday;
        e.PushesToday = PushesToday;
        LastEventSummary = $"{e.Kind} in {e.Repo}" + (string.IsNullOrEmpty(e.Branch) ? "" : $" ({e.Branch})");
        OnEvent?.Invoke(e);
    }

    // MARK: git subprocess helpers

    private static string GitExecutable()
    {
        foreach (var candidate in new[] { @"C:\Program Files\Git\cmd\git.exe", @"C:\Program Files\Git\bin\git.exe" })
            if (File.Exists(candidate)) return candidate;
        return "git"; // rely on PATH
    }

    private static string? RunGit(string[] arguments, string workTree)
    {
        try
        {
            var psi = new ProcessStartInfo(GitExecutable())
            {
                WorkingDirectory = workTree,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            foreach (var arg in arguments) psi.ArgumentList.Add(arg);
            psi.Environment["GIT_OPTIONAL_LOCKS"] = "0";
            using var process = Process.Start(psi);
            if (process is null) return null;
            if (!process.WaitForExit(5000)) { process.Kill(); return null; }
            return process.ExitCode == 0 ? process.StandardOutput.ReadToEnd() : null;
        }
        catch { return null; }
    }

    private static readonly Regex FileCountRe = new(@"(\d+) file", RegexOptions.Compiled);
    private static readonly Regex InsertionRe = new(@"(\d+) insertion", RegexOptions.Compiled);
    private static readonly Regex DeletionRe = new(@"(\d+) deletion", RegexOptions.Compiled);

    private static (int files, int insertions, int deletions) CommitStat(string workTree, string hash)
    {
        var output = RunGit(new[] { "show", "--shortstat", "--format=", hash }, workTree);
        if (output is null) return (0, 0, 0);
        int Number(Regex re) => re.Match(output).Success ? int.Parse(re.Match(output).Groups[1].Value) : 0;
        return (Number(FileCountRe), Number(InsertionRe), Number(DeletionRe));
    }

    private void ReportStatus()
    {
        Tracked? candidate;
        lock (_lock)
        {
            candidate = (_lastActiveRepo != null && _tracked.TryGetValue(_lastActiveRepo, out var r)) ? r
                : _tracked.Values.OrderByDescending(t => t.LastActivity).FirstOrDefault();
        }
        if (candidate is null) return;
        var output = RunGit(new[] { "status", "--porcelain", "--untracked-files=no" }, candidate.WorkTree) ?? "";
        var dirty = output.Split('\n', StringSplitOptions.RemoveEmptyEntries).Length;
        var minutes = candidate.LastCommitDate is { } last ? (int)(DateTime.Now - last).TotalMinutes : -1;
        OnStatus?.Invoke(new GitStatus
        {
            Repo = candidate.Name, Branch = CurrentBranch(candidate.GitDir), Dirty = dirty,
            MinutesSinceCommit = minutes, CommitsToday = CommitsToday, PushesToday = PushesToday,
        });
    }
}
