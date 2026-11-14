// What Claude and Codex have said about their usage limits. Ported from the structs at the
// top of apps/macos/Sources/QuotaWatcher.swift. A window the tool never reported is null,
// never a made-up zero.
namespace Bitling.Usage;

/// <param name="UsedPercent">0 to 100.</param>
/// <param name="ResetsAtMs">Epoch ms. Present only when the tool said when the window resets.</param>
/// <param name="AsOfMs">Epoch ms of the reading itself.</param>
public sealed record QuotaWindow(double UsedPercent, double? ResetsAtMs, double AsOfMs);

public sealed record QuotaProvider
{
    public string? Plan { get; init; }
    public QuotaWindow? FiveHour { get; init; }
    public QuotaWindow? Weekly { get; init; }

    /// <summary>Why the live reading is unavailable, when it was asked for. Null when it works.</summary>
    public string? LiveStatus { get; init; }
}

public sealed record LiveReading(string? Plan, QuotaWindow? FiveHour, QuotaWindow? Weekly, DateTimeOffset FetchedAt);

/// <param name="RetryAfter">How long to leave the tool alone before asking again.</param>
public sealed record LiveFailure(string Message, TimeSpan RetryAfter)
{
    public static readonly LiveFailure NotSignedIn = new("sign in to Claude Code for live usage", TimeSpan.FromSeconds(120));
    // Short, because Claude Code updates itself by replacing its binary, which is missing for a moment.
    public static readonly LiveFailure ClaudeMissing = new("the claude command was not found", TimeSpan.FromSeconds(120));
    public static readonly LiveFailure ClaudeSilent = new("claude did not answer", TimeSpan.FromSeconds(60));
    public static readonly LiveFailure CodexMissing = new("the codex command was not found", TimeSpan.FromHours(1));
    public static readonly LiveFailure CodexSilent = new("codex did not answer", TimeSpan.FromSeconds(120));
    public static readonly LiveFailure CodexNotSignedIn = new("sign in to Codex for live usage", TimeSpan.FromSeconds(600));
}

/// <summary>One attempt at a live reading: exactly one of the two is set.</summary>
public readonly record struct LiveResult(LiveReading? Reading, LiveFailure? Failure)
{
    public static LiveResult Ok(LiveReading reading) => new(reading, null);
    public static LiveResult Fail(LiveFailure failure) => new(null, failure);
}
