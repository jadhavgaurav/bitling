using System.Text.Json.Nodes;
using Bitling.Settings;

namespace Bitling.Models;

public sealed class ActivityEntry
{
    public DateTimeOffset Time { get; init; } = DateTimeOffset.UtcNow;
    public required string Kind { get; init; }
    public required string Title { get; init; }
    public string Repo { get; init; } = "";

    public JsonObject ToJson() => new()
    {
        ["t"] = Time.ToUnixTimeMilliseconds(),
        ["kind"] = Kind,
        ["title"] = Title,
        ["repo"] = Repo,
    };

    public static ActivityEntry? FromJson(JsonObject o)
    {
        var ms = o["t"]?.GetValue<double>();
        var kind = o["kind"]?.GetValue<string>();
        var title = o["title"]?.GetValue<string>();
        if (ms is null || kind is null || title is null) return null;
        return new ActivityEntry
        {
            Time = DateTimeOffset.FromUnixTimeMilliseconds((long)ms.Value),
            Kind = kind,
            Title = title,
            Repo = o["repo"]?.GetValue<string>() ?? "",
        };
    }
}

/// Turns a raw watcher event into the sentence the activity stream shows, or null for
/// chatter that would only pad the log (idle pings, individual tool calls).
static class ActivityLine
{
    public static ActivityEntry? Describe(GitEvent e)
    {
        var branch = string.IsNullOrEmpty(e.Branch) ? "a branch" : e.Branch;
        var subject = string.IsNullOrEmpty(e.Message) ? "no message" : e.Message;
        var target = string.IsNullOrEmpty(e.Target) ? "somewhere" : e.Target;
        string title;
        switch (e.Kind)
        {
            case "commit":
            case "cherry-pick":
                var counts = e.Files > 0 ? $" ({e.Files} file{(e.Files == 1 ? "" : "s")})" : "";
                title = subject + counts;
                break;
            case "amend": title = $"amended: {subject}"; break;
            case "push": title = $"pushed {branch}"; break;
            case "merge": title = $"merged {branch}"; break;
            case "checkout": title = $"switched to {branch}"; break;
            case "rebase": title = $"rebasing {branch}"; break;
            case "rebase-done": title = "rebase finished"; break;
            case "pull": title = $"pulled {branch}"; break;
            case "stash": title = "stashed the working tree"; break;
            case "reset": title = $"reset {branch}"; break;
            case "test-failed":
                var n = Math.Max(1, e.Count);
                title = $"{n} test{(n == 1 ? "" : "s")} failing in {(string.IsNullOrEmpty(e.Name) ? "the suite" : e.Name)}";
                break;
            case "test-passed": title = $"tests green in {(string.IsNullOrEmpty(e.Name) ? "the suite" : e.Name)}"; break;
            case "deploy-started": title = $"deploying to {target}"; break;
            case "deploy-finished": title = $"deployed to {target}"; break;
            case "deploy-failed": title = $"deploy to {target} failed"; break;
            case "claude-session-start": title = "Claude Code session opened"; break;
            case "claude-prompt": title = subject == "no message" ? "you asked Claude something" : $"you: {subject}"; break;
            case "claude-done": title = subject == "no message" ? "Claude finished" : $"Claude: {subject}"; break;
            case "claude-tool-error": title = "a tool call went red"; break;
            case "claude-notify": title = "Claude wants your attention"; break;
            default: return null;
        }
        return new ActivityEntry { Kind = e.Kind, Title = title, Repo = e.Repo };
    }
}

/// Keeps the recent activity, capped and persisted so the room is not empty after a restart.
sealed class ActivityLog
{
    private const string Key = "activityLog";
    private const int Limit = 120;
    private readonly List<ActivityEntry> _entries = new();

    public IReadOnlyList<ActivityEntry> Entries => _entries;

    public ActivityLog()
    {
        foreach (var raw in AppSettings.GetStringArray(Key))
        {
            if (JsonNode.Parse(raw) is JsonObject o && ActivityEntry.FromJson(o) is { } entry) _entries.Add(entry);
        }
    }

    public ActivityEntry? Record(GitEvent e)
    {
        var entry = ActivityLine.Describe(e);
        if (entry is null) return null;
        _entries.Add(entry);
        if (_entries.Count > Limit) _entries.RemoveRange(0, _entries.Count - Limit);
        Save();
        return entry;
    }

    public void Clear()
    {
        _entries.Clear();
        Save();
    }

    private void Save() => AppSettings.SetStringArray(Key, _entries.Select(e => e.ToJson().ToJsonString()));

    public JsonArray ToJsonArray() => new(_entries.Select(e => (JsonNode)e.ToJson()).ToArray());
}
