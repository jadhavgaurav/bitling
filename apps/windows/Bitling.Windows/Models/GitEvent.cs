using System.Text.Json.Nodes;

namespace Bitling.Models;

/// git: commit, amend, merge, push, checkout, rebase, rebase-done, pull, stash, reset, cherry-pick
/// ci: test-failed, test-passed, deploy-started, deploy-finished, deploy-failed; misc: say
/// claude: claude-session-start, claude-prompt, claude-tool, claude-tool-error, claude-done, claude-idle, claude-notify, claude-session-end
public sealed class GitEvent
{
    public string Kind { get; init; } = "";
    public string Repo { get; init; } = "";
    public string Branch { get; init; } = "";
    public string Message { get; init; } = "";
    public string Hash { get; init; } = "";
    public int Insertions { get; init; }
    public int Deletions { get; init; }
    public int Files { get; init; }
    public int Count { get; init; }
    public string Target { get; init; } = "";
    public string Name { get; init; } = "";
    public string[] Tests { get; init; } = Array.Empty<string>();
    public int CommitsToday { get; set; }
    public int PushesToday { get; set; }

    public JsonObject ToJson() => new()
    {
        ["kind"] = Kind,
        ["repo"] = Repo,
        ["branch"] = Branch,
        ["message"] = Message,
        ["hash"] = Hash,
        ["insertions"] = Insertions,
        ["deletions"] = Deletions,
        ["files"] = Files,
        ["count"] = Count,
        ["target"] = Target,
        ["name"] = Name,
        ["tests"] = new JsonArray(Tests.Select(t => (JsonNode)t).ToArray()),
        ["commitsToday"] = CommitsToday,
        ["pushesToday"] = PushesToday,
    };
}

public sealed class GitStatus
{
    public required string Repo { get; init; }
    public required string Branch { get; init; }
    public int Dirty { get; init; }
    public int MinutesSinceCommit { get; init; }
    public int CommitsToday { get; init; }
    public int PushesToday { get; init; }

    public JsonObject ToJson() => new()
    {
        ["repo"] = Repo,
        ["branch"] = Branch,
        ["dirty"] = Dirty,
        ["minutesSinceCommit"] = MinutesSinceCommit,
        ["commitsToday"] = CommitsToday,
        ["pushesToday"] = PushesToday,
    };
}

public sealed record WatchedRepo(string WorkTree, string? Slug)
{
    public string Name => Path.GetFileName(WorkTree.TrimEnd(Path.DirectorySeparatorChar));
}
