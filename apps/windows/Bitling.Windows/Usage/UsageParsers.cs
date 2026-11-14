// Turns what `claude -p /usage` prints and what `codex app-server` answers into readings, and
// decides which reading to show. Ported from ClaudeUsageTextParser, CodexUsageParser and
// QuotaWatcher.merge in apps/macos/Sources/QuotaWatcher.swift. Pure functions: nothing here
// touches a process, a file or the clock, so all of it is tested off Windows too.
using System.Globalization;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace Bitling.Usage;

public static class ClaudeUsageTextParser
{
    // "Current week (all models): 82% used · resets Oct 18 at 5:30am (Asia/Calcutta)". A window
    // with nothing used yet has no "resets" part.
    private static readonly Regex Pattern =
        new(@"(\d+(?:\.\d+)?)% used(?: · resets (.+?) \((.+?)\))?\s*$", RegexOptions.CultureInvariant);

    private static readonly (string Format, bool WithDay)[] ResetFormats =
    {
        ("MMM d 'at' h:mmtt", true), ("MMM d 'at' htt", true), ("h:mmtt", false), ("htt", false),
    };

    /// <summary>Claude has no 5 hour limit any more, so only the weekly line is read.</summary>
    public static LiveReading? Parse(string text, DateTimeOffset fetchedAt)
    {
        var week = Window("Current week (all models):", text, fetchedAt);
        return week is null ? null : new LiveReading(null, null, week, fetchedAt);
    }

    private static QuotaWindow? Window(string prefix, string text, DateTimeOffset now)
    {
        var line = text.Split('\n').Select(l => l.TrimEnd('\r'))
            .FirstOrDefault(l => l.StartsWith(prefix, StringComparison.Ordinal));
        if (line is null) return null;
        var match = Pattern.Match(line);
        if (!match.Success || !double.TryParse(match.Groups[1].Value, NumberStyles.Float, CultureInfo.InvariantCulture, out var used))
            return null;
        var reset = match.Groups[2].Success
            ? ResetDate(match.Groups[2].Value, match.Groups[3].Success ? match.Groups[3].Value : null, now)
            : null;
        return new QuotaWindow(Math.Clamp(used, 0, 100), reset?.ToUnixTimeMilliseconds(), now.ToUnixTimeMilliseconds());
    }

    /// <summary>
    /// "Oct 16 at 1:20pm", "Oct 16 at 1pm" or just "1:20pm", in the zone the CLI names. A date with
    /// no year is the next one that is not in the past.
    /// </summary>
    public static DateTimeOffset? ResetDate(string text, string? zone, DateTimeOffset now)
    {
        var tz = TimeZoneInfo.Local;
        if (zone is not null)
        {
            try { tz = TimeZoneInfo.FindSystemTimeZoneById(zone); }
            catch (Exception e) when (e is TimeZoneNotFoundException or InvalidTimeZoneException) { /* keep the local zone */ }
        }
        var local = TimeZoneInfo.ConvertTime(now, tz);
        foreach (var (format, withDay) in ResetFormats)
        {
            if (!DateTime.TryParseExact(text, format, CultureInfo.InvariantCulture, DateTimeStyles.AllowWhiteSpaces, out var parsed))
                continue;
            try
            {
                var wall = withDay
                    ? new DateTime(local.Year, parsed.Month, parsed.Day, parsed.Hour, parsed.Minute, 0)
                    : local.Date.Add(parsed.TimeOfDay);
                var result = At(wall, tz);
                if (result < now.AddHours(-1)) result = At(withDay ? wall.AddYears(1) : wall.AddDays(1), tz);
                return result;
            }
            catch (ArgumentOutOfRangeException) { return null; } // 29 February in a year that has none
        }
        return null;
    }

    private static DateTimeOffset At(DateTime wall, TimeZoneInfo tz) => new(wall, tz.GetUtcOffset(wall));
}

public static class CodexUsageParser
{
    /// <summary>
    /// The result of account/rateLimits/read: the "codex" bucket, with the 5 hour window as
    /// "primary" and the weekly one as "secondary". A window is told apart by its length.
    /// </summary>
    public static LiveReading? Parse(JsonObject result, DateTimeOffset fetchedAt)
    {
        var limits = (result["rateLimitsByLimitId"] as JsonObject)?["codex"] as JsonObject;
        if (limits is null && result["rateLimits"] is JsonObject fallback
            && fallback["limitId"] is JsonValue id && id.TryGetValue<string>(out var limitId) && limitId == "codex")
            limits = fallback;
        if (limits is null) return null;

        string? plan = null;
        if (limits["planType"] is JsonValue p && p.TryGetValue<string>(out var planType) && !string.IsNullOrEmpty(planType))
            plan = char.ToUpperInvariant(planType[0]) + planType[1..];

        var now = fetchedAt.ToUnixTimeMilliseconds();
        QuotaWindow? fiveHour = null, weekly = null;
        foreach (var key in new[] { "primary", "secondary" })
        {
            if (limits[key] is not JsonObject raw) continue;
            if (Number(raw["usedPercent"]) is not { } used || Number(raw["windowDurationMins"]) is not { } minutes) continue;
            var window = new QuotaWindow(Math.Clamp(used, 0, 100), Number(raw["resetsAt"]) * 1000, now);
            if (minutes <= 600) fiveHour = window; else weekly = window;
        }
        return fiveHour is null && weekly is null ? null : new LiveReading(plan, fiveHour, weekly, fetchedAt);
    }

    private static double? Number(JsonNode? node) =>
        node is JsonValue value && value.TryGetValue<double>(out var number) ? number : null;
}

public static class QuotaMerge
{
    /// <summary>How long the last live reading is still worth showing, marked stale, when refreshing fails.</summary>
    public static readonly TimeSpan StaleLiveKeep = TimeSpan.FromHours(6);

    /// <summary>
    /// Claude is asked every 5 minutes, so a reading older than three asks is no longer live: it is
    /// the last one that worked, and anything that shows it has to say so.
    /// </summary>
    public static readonly TimeSpan StaleAfter = TimeSpan.FromMinutes(15);

    public static bool IsStale(QuotaWindow window, DateTimeOffset now) =>
        now.ToUnixTimeMilliseconds() - window.AsOfMs > StaleAfter.TotalMilliseconds;

    /// <summary>
    /// A fresh live reading is what is shown. One that has gone stale (a refresh failed) is still
    /// better than nothing, so it stays on screen with the reason it is not live, until it is too
    /// old. A window whose reset has passed is dropped: its figure no longer describes anything.
    /// </summary>
    public static QuotaProvider Apply(QuotaProvider provider, LiveReading? live, LiveFailure? failure, TimeSpan freshness, DateTimeOffset now)
    {
        if (live is null) return provider with { LiveStatus = failure?.Message };
        var age = now - live.FetchedAt;
        if (age < freshness)
            return provider with { FiveHour = live.FiveHour, Weekly = live.Weekly, Plan = live.Plan ?? provider.Plan };

        provider = provider with { LiveStatus = failure?.Message };
        if (age >= StaleLiveKeep) return provider;
        var nowMs = now.ToUnixTimeMilliseconds();
        QuotaWindow? Newer(QuotaWindow? kept, QuotaWindow? candidate)
        {
            if (candidate is null || (candidate.ResetsAtMs is { } reset && reset <= nowMs)) return kept;
            return (kept?.AsOfMs ?? 0) < candidate.AsOfMs ? candidate : kept;
        }
        return provider with { FiveHour = Newer(provider.FiveHour, live.FiveHour), Weekly = Newer(provider.Weekly, live.Weekly) };
    }
}
