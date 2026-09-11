// Watches Claude Code sessions by tailing the transcripts it writes under
// %USERPROFILE%\.claude\projects\<project>\<session>.jsonl. Every line is a JSON object;
// the ones that matter here are human prompts, assistant tool calls, tool results (with
// errors) and end-of-turn assistant messages. No configuration is needed: every Claude
// Code front end (terminal, desktop app, IDE) writes the same files.
//
// Ported from apps/macos/Sources/ClaudeWatcher.swift.
using System.Text.Json.Nodes;
using Bitling.Models;
using Bitling.Settings;

namespace Bitling.Watchers;

public sealed class ClaudeWatcher
{
    public event Action<GitEvent>? OnEvent;

    private sealed class Session
    {
        public required string File;
        public required string SessionId;
        public long Offset;
        public string Project = "";
        public string Title = "";
        public DateTime LastActivity;
        public DateTime LastToolEvent = DateTime.MinValue;
        public bool Working;
        public bool IdleReported = true;
    }

    private const string TodayKey = "claudeToday";
    private readonly string _root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".claude", "projects");
    private readonly Dictionary<string, Session> _sessions = new();
    private System.Threading.Timer? _scanTimer, _pollTimer;
    private DateTime _started = DateTime.Now;

    public int PromptsToday { get; private set; }
    public int ToolsToday { get; private set; }
    public int SessionsToday { get; private set; }
    private string _todayKeyValue = "";
    public string LastSummary { get; private set; } = "nothing yet";

    public int ActiveSessionCount { get { lock (_sessions) return _sessions.Values.Count(s => (DateTime.Now - s.LastActivity) < TimeSpan.FromMinutes(5)); } }

    private static string DayString() => DateTime.Now.ToString("yyyy-MM-dd");

    public ClaudeWatcher()
    {
        _todayKeyValue = DayString();
        var today = AppSettings.GetObject(TodayKey);
        if (today?["day"]?.GetValue<string>() == _todayKeyValue)
        {
            PromptsToday = today["prompts"]?.GetValue<int>() ?? 0;
            ToolsToday = today["tools"]?.GetValue<int>() ?? 0;
            SessionsToday = today["sessions"]?.GetValue<int>() ?? 0;
        }
    }

    private void Bump(int prompts = 0, int tools = 0, int sessions = 0)
    {
        var day = DayString();
        if (day != _todayKeyValue) { _todayKeyValue = day; PromptsToday = 0; ToolsToday = 0; SessionsToday = 0; }
        PromptsToday += prompts;
        ToolsToday += tools;
        SessionsToday += sessions;
        AppSettings.SetObject(TodayKey, new JsonObject { ["day"] = day, ["prompts"] = PromptsToday, ["tools"] = ToolsToday, ["sessions"] = SessionsToday });
    }

    public void Start()
    {
        _started = DateTime.Now;
        Task.Run(Scan);
        _scanTimer = new System.Threading.Timer(_ => Task.Run(Scan), null, TimeSpan.FromSeconds(10), TimeSpan.FromSeconds(10));
        _pollTimer = new System.Threading.Timer(_ => Task.Run(Poll), null, TimeSpan.FromSeconds(2), TimeSpan.FromSeconds(2));
    }

    private static long FileSize(string path) => File.Exists(path) ? new FileInfo(path).Length : 0;

    private void Scan()
    {
        if (!Directory.Exists(_root)) return;
        var now = DateTime.Now;
        IEnumerable<string> projects;
        try { projects = Directory.EnumerateDirectories(_root); } catch { return; }
        foreach (var project in projects)
        {
            IEnumerable<string> files;
            try { files = Directory.EnumerateFiles(project, "*.jsonl", SearchOption.AllDirectories); }
            catch { continue; }
            foreach (var file in files)
            {
                FileInfo info;
                try { info = new FileInfo(file); } catch { continue; }
                if ((now - info.LastWriteTime) >= TimeSpan.FromMinutes(15)) continue;
                lock (_sessions) { if (_sessions.ContainsKey(file)) continue; }
                var created = info.CreationTime;
                var brandNew = created > _started && (now - created) < TimeSpan.FromSeconds(120);
                var projectName = ProjectName(Path.GetFileName(project));
                var session = new Session
                {
                    File = file, SessionId = Path.GetFileNameWithoutExtension(file),
                    Offset = brandNew ? 0 : FileSize(file), Project = projectName, LastActivity = info.LastWriteTime,
                };
                lock (_sessions) _sessions[file] = session;
                if (brandNew)
                {
                    Bump(sessions: 1);
                    Emit(new GitEvent { Kind = "claude-session-start", Repo = projectName, Name = projectName });
                }
            }
        }
        // Forget sessions that have been quiet for an hour.
        lock (_sessions)
        {
            foreach (var key in _sessions.Where(kv => (now - kv.Value.LastActivity) >= TimeSpan.FromHours(1)).Select(kv => kv.Key).ToList())
                _sessions.Remove(key);
        }
    }

    private static string ProjectName(string folder)
    {
        // "-Users-a12345-Desktop-AI-OyeChats" -> "OyeChats"
        var parts = folder.Split('-', StringSplitOptions.RemoveEmptyEntries);
        return parts.Length > 0 ? parts[^1] : folder;
    }

    private void Poll()
    {
        var now = DateTime.Now;
        List<Session> snapshot;
        lock (_sessions) snapshot = _sessions.Values.ToList();
        foreach (var session in snapshot)
        {
            var size = FileSize(session.File);
            if (size < session.Offset) session.Offset = size;
            if (size > session.Offset)
            {
                var text = ReadTail(session.File, session.Offset);
                session.Offset = size;
                session.LastActivity = now;
                foreach (var line in text.Split('\n', StringSplitOptions.RemoveEmptyEntries))
                    Handle(line, session);
            }
            else if (session.Working && !session.IdleReported && (now - session.LastActivity) > TimeSpan.FromMinutes(5))
            {
                session.Working = false;
                session.IdleReported = true;
                Emit(new GitEvent { Kind = "claude-idle", Repo = session.Project, Name = session.Project });
            }
        }
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

    private static string Preview(string text, int limit = 60)
    {
        var flat = text.Replace("\n", " ").Trim();
        return flat.Length > limit ? flat[..(limit - 1)] + "…" : flat;
    }

    private static DateTime? EntryDate(JsonNode? raw) =>
        raw is null ? null : (DateTime.TryParse(raw.GetValue<string>(), null,
            System.Globalization.DateTimeStyles.RoundtripKind, out var d) ? d : null);

    private void Handle(string line, Session session)
    {
        JsonObject? entry;
        try { entry = JsonNode.Parse(line) as JsonObject; } catch { return; }
        var type = entry?["type"]?.GetValue<string>();
        if (entry is null || type is null) return;
        var cwd = entry["cwd"]?.GetValue<string>();
        if (!string.IsNullOrEmpty(cwd)) session.Project = Path.GetFileName(cwd.TrimEnd('\\', '/'));
        if (entry["isSidechain"]?.GetValue<bool>() == true) return;
        if (EntryDate(entry["timestamp"]) is { } when && when < _started) return;
        var message = entry["message"] as JsonObject;
        var content = message?["content"];

        switch (type)
        {
            case "custom-title":
                session.Title = entry["customTitle"]?.GetValue<string>() ?? session.Title;
                break;
            case "user":
                if (entry["isMeta"]?.GetValue<bool>() == true) return;
                if (content is JsonValue textValue && textValue.TryGetValue<string>(out var text))
                {
                    if ((entry["origin"] as JsonObject)?["kind"]?.GetValue<string>() == "system") return;
                    session.Working = true;
                    session.IdleReported = false;
                    Bump(prompts: 1);
                    Emit(new GitEvent { Kind = "claude-prompt", Repo = session.Project, Message = Preview(text), Name = session.Project });
                }
                else if (content is JsonArray blocks)
                {
                    foreach (var block in blocks.OfType<JsonObject>().Where(b => b["type"]?.GetValue<string>() == "tool_result"))
                    {
                        var failed = block["is_error"]?.GetValue<bool>() == true
                            || (entry["toolUseResult"] as JsonObject)?["success"]?.GetValue<bool>() == false;
                        if (failed) Emit(new GitEvent { Kind = "claude-tool-error", Repo = session.Project, Name = session.Project });
                    }
                }
                break;
            case "assistant":
                if (content is not JsonArray abocks) return;
                var stop = message?["stop_reason"]?.GetValue<string>() ?? "";
                foreach (var block in abocks.OfType<JsonObject>())
                {
                    var kind = block["type"]?.GetValue<string>() ?? "";
                    if (kind == "tool_use")
                    {
                        var tool = block["name"]?.GetValue<string>() ?? "tool";
                        var input = block["input"] as JsonObject ?? new JsonObject();
                        var detail = input["command"]?.GetValue<string>() ?? input["file_path"]?.GetValue<string>()
                            ?? input["pattern"]?.GetValue<string>() ?? input["query"]?.GetValue<string>() ?? "";
                        session.Working = true;
                        session.IdleReported = false;
                        Bump(tools: 1);
                        if ((DateTime.Now - session.LastToolEvent) > TimeSpan.FromSeconds(3))
                        {
                            session.LastToolEvent = DateTime.Now;
                            Emit(new GitEvent { Kind = "claude-tool", Repo = session.Project, Message = Preview(detail, 80), Name = tool });
                        }
                    }
                    else if (kind == "text" && stop == "end_turn")
                    {
                        session.Working = false;
                        session.IdleReported = true;
                        Emit(new GitEvent { Kind = "claude-done", Repo = session.Project, Message = Preview(block["text"]?.GetValue<string>() ?? ""), Name = session.Project });
                    }
                }
                break;
        }
    }

    private void Emit(GitEvent e)
    {
        LastSummary = $"{e.Kind.Replace("claude-", "")} · {e.Name}";
        OnEvent?.Invoke(e);
    }
}
