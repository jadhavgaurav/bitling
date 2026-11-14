using System.Text.Json.Nodes;
using Bitling.Usage;

// Expected values mirror tests/quota.test.mjs (the macOS parser tests) so both ports agree.
var failures = 0;
void Check(bool ok, string what)
{
    Console.WriteLine($"{(ok ? "ok  " : "FAIL")} {what}");
    if (!ok) failures++;
}

DateTimeOffset At(long ms) => DateTimeOffset.FromUnixTimeMilliseconds(ms);
var fetched = At(1_791_790_000_000);

// Claude /usage text.
var text = "Current session: 31% used · resets 4am (Asia/Calcutta)\r\n" +
           "Current week (all models): 82% used · resets Oct 18 at 5:30am (Asia/Calcutta)\r\n" +
           "Current week (Sonnet only): 4% used\r\n";
var reading = ClaudeUsageTextParser.Parse(text, fetched);
Check(reading is not null && reading.FiveHour is null, "Claude reads no 5 hour window");
Check(reading?.Weekly?.UsedPercent == 82, "weekly is the all-models line, 82%");
Check(reading?.Weekly?.ResetsAtMs == new DateTimeOffset(2026, 10, 18, 0, 0, 0, TimeSpan.Zero).ToUnixTimeMilliseconds(),
    "5:30am Asia/Calcutta is 00:00 UTC on 18 Oct 2026");
Check(reading?.Weekly?.AsOfMs == 1_791_790_000_000, "the reading is stamped with the fetch time");
Check(ClaudeUsageTextParser.Parse("Current week (all models): 0% used\n", fetched)?.Weekly?.ResetsAtMs is null, "an untouched week has no reset");
var clamped = ClaudeUsageTextParser.Parse("Current week (all models): 140% used · resets Jan 3 at 9am (UTC)", fetched);
Check(clamped?.Weekly?.UsedPercent == 100, "140% is clamped to 100");
Check(clamped?.Weekly?.ResetsAtMs == new DateTimeOffset(2027, 1, 3, 9, 0, 0, TimeSpan.Zero).ToUnixTimeMilliseconds(),
    "a date with no year that has passed this year rolls to next year");
Check(ClaudeUsageTextParser.Parse("Please sign in\n", fetched) is null, "no week line is no reading");
Check(ClaudeUsageTextParser.Parse("", fetched) is null, "empty output is no reading");

// Codex rate limits.
var codex = JsonNode.Parse("""
{ "rateLimitsByLimitId": { "codex": { "limitId": "codex", "planType": "plus",
  "primary":   { "usedPercent": 6,  "windowDurationMins": 300,   "resetsAt": 1791800000 },
  "secondary": { "usedPercent": 31.5, "windowDurationMins": 10080, "resetsAt": 1792300000 } } } }
""")!.AsObject();
var cx = CodexUsageParser.Parse(codex, fetched);
Check(cx?.Plan == "Plus", "plan is capitalised");
Check(cx?.FiveHour?.UsedPercent == 6 && cx.FiveHour.ResetsAtMs == 1_791_800_000_000, "the 300 minute window is the 5 hour one");
Check(cx?.Weekly?.UsedPercent == 31.5, "the long window is the weekly one");
Check(CodexUsageParser.Parse(JsonNode.Parse("""{ "rateLimitsByLimitId": { "other": {} } }""")!.AsObject(), fetched) is null, "no codex bucket is no reading");

// Colours: the same stops as the pet page and the macOS menu bar.
Check(UsageColor.Rgb(0) == (34, 197, 94), "0% is green");
Check(UsageColor.Rgb(60) == (245, 158, 11), "60% is amber");
Check(UsageColor.Rgb(85) == (239, 68, 68), "85% is red");
Check(UsageColor.Rgb(12) == (76, 189, 77), "12% blends a fifth of the way to amber");
Check(UsageColor.Rgb(140) == (239, 68, 68) && UsageColor.Rgb(-5) == (34, 197, 94), "out of range stays at the ends");
Check(UsageColor.Rgb(double.NaN) == (34, 197, 94), "NaN does not throw");

// Merge: fresh wins, stale is kept with the reason, old or reset is dropped.
var now = fetched.AddMinutes(1);
var live = new LiveReading("Max 20x", null, new QuotaWindow(11, null, fetched.ToUnixTimeMilliseconds()), fetched);
var fresh = QuotaMerge.Apply(new QuotaProvider(), live, null, TimeSpan.FromMinutes(15), now);
Check(fresh.Weekly?.UsedPercent == 11 && fresh.Plan == "Max 20x" && fresh.LiveStatus is null, "a fresh reading is shown");
var stale = QuotaMerge.Apply(new QuotaProvider(), live, LiveFailure.ClaudeSilent, TimeSpan.FromMinutes(15), fetched.AddHours(2));
Check(stale.Weekly?.UsedPercent == 11 && stale.LiveStatus == "claude did not answer", "a stale reading stays, with the reason");
var tooOld = QuotaMerge.Apply(new QuotaProvider(), live, LiveFailure.ClaudeSilent, TimeSpan.FromMinutes(15), fetched.AddHours(7));
Check(tooOld.Weekly is null && tooOld.LiveStatus == "claude did not answer", "after 6 hours it is dropped");
var past = new LiveReading(null, null, new QuotaWindow(50, fetched.AddHours(1).ToUnixTimeMilliseconds(), fetched.ToUnixTimeMilliseconds()), fetched);
Check(QuotaMerge.Apply(new QuotaProvider(), past, null, TimeSpan.FromMinutes(15), fetched.AddHours(2)).Weekly is null,
    "a stale window past its reset is dropped");
Check(QuotaMerge.Apply(new QuotaProvider(), null, LiveFailure.CodexMissing, TimeSpan.FromMinutes(3), now).LiveStatus == "the codex command was not found",
    "no reading yet carries the reason");

// Staleness: a reading older than three 5-minute asks is the last one that worked, not live.
bool Stale(int minutesOld) =>
    QuotaMerge.IsStale(new QuotaWindow(14, null, now.AddMinutes(-minutesOld).ToUnixTimeMilliseconds()), now);
Check(!Stale(0) && !Stale(14), "a reading under 15 minutes old is live");
Check(Stale(16) && Stale(600), "a reading over 15 minutes old is stale");
Check(!QuotaMerge.IsStale(new QuotaWindow(14, null, now.AddMinutes(5).ToUnixTimeMilliseconds()), now), "a reading stamped in the future is not stale");

Console.WriteLine(failures == 0 ? "all checks passed" : $"{failures} check(s) failed");
return failures == 0 ? 0 : 1;
