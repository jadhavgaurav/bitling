// Keeps Claude's and Codex's live usage current: Codex about once a minute, Claude every 5.
// Ported from QuotaWatcher in apps/macos/Sources/QuotaWatcher.swift. The macOS version also
// reads Claude Desktop's and Codex's log files as a fallback; this one is live only, so a
// missing or signed-out tool shows as "not live" rather than as an old number.
namespace Bitling.Usage;

public sealed class QuotaWatcher : IDisposable
{
    private sealed class Feed
    {
        public required TimeSpan Interval { get; init; }
        public required Func<LiveResult> Fetch { get; init; }
        public TimeSpan Freshness => Interval * 3;
        public LiveReading? Reading;
        public LiveFailure? Failure;
        public DateTimeOffset Next = DateTimeOffset.MinValue;
        public bool Fetching;
    }

    /// <summary>Raised on a background thread, and only when a reading actually changed.</summary>
    public event Action? Updated;

    public QuotaProvider Claude { get; private set; } = new();
    public QuotaProvider Codex { get; private set; } = new();

    private readonly object _gate = new();
    private readonly Feed _claude = new() { Interval = TimeSpan.FromMinutes(5), Fetch = ClaudeLiveUsage.Fetch };
    private readonly Feed _codex = new() { Interval = TimeSpan.FromMinutes(1), Fetch = CodexLiveUsage.Fetch };
    private System.Threading.Timer? _timer;

    public void Start()
    {
        if (_timer is not null) return;
        _timer = new System.Threading.Timer(_ => Refresh(), null, TimeSpan.Zero, TimeSpan.FromSeconds(30));
    }

    public void Stop()
    {
        _timer?.Dispose();
        _timer = null;
    }

    public void Dispose() => Stop();

    private void Refresh()
    {
        FetchIfDue(_claude);
        FetchIfDue(_codex);
        Recompute();
    }

    private void FetchIfDue(Feed feed)
    {
        lock (_gate)
        {
            if (feed.Fetching || DateTimeOffset.Now < feed.Next) return;
            feed.Fetching = true;
        }
        _ = Task.Run(() =>
        {
            LiveResult result;
            try { result = feed.Fetch(); }
            catch (Exception) { result = LiveResult.Fail(new LiveFailure("the reading failed", TimeSpan.FromMinutes(2))); }
            lock (_gate)
            {
                feed.Fetching = false;
                if (result.Reading is not null)
                {
                    feed.Reading = result.Reading;
                    feed.Failure = null;
                    feed.Next = DateTimeOffset.Now + feed.Interval;
                }
                else
                {
                    feed.Failure = result.Failure;
                    feed.Next = DateTimeOffset.Now + (result.Failure?.RetryAfter ?? TimeSpan.FromMinutes(2));
                }
            }
            Recompute();
        });
    }

    private void Recompute()
    {
        bool changed;
        lock (_gate)
        {
            var now = DateTimeOffset.Now;
            var claude = QuotaMerge.Apply(new QuotaProvider(), _claude.Reading, _claude.Failure, _claude.Freshness, now);
            var codex = QuotaMerge.Apply(new QuotaProvider(), _codex.Reading, _codex.Failure, _codex.Freshness, now);
            changed = claude != Claude || codex != Codex;
            Claude = claude;
            Codex = codex;
        }
        if (changed) Updated?.Invoke();
    }
}
