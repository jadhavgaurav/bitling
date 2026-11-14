// Asks Claude and Codex what they know right now. Ported from ClaudeLiveUsage and
// CodexLiveUsage in apps/macos/Sources/QuotaWatcher.swift.
//
//   Claude  `claude -p /usage`, parsed from its text. Claude reads its own sign-in, so Bitling
//           never touches a token. It costs a few seconds of CPU, so it is asked every 5 minutes.
//   Codex   `codex app-server`, asked for account/rateLimits/read over its JSON-RPC lines.
//           Codex answers with its own sign-in, so no credential passes through Bitling.
//
// Both block until the tool answers: call them off the UI thread.
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json.Nodes;

namespace Bitling.Usage;

/// <summary>Outcomes only, so a failing feed can be diagnosed: never a token, a header or a response body.</summary>
static class UsageLog
{
    private static readonly object Gate = new();
    private static readonly string Directory =
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Bitling", "Logs");

    public static void Write(string line)
    {
        try
        {
            lock (Gate)
            {
                System.IO.Directory.CreateDirectory(Directory);
                var file = Path.Combine(Directory, "usage.log");
                if (File.Exists(file) && new FileInfo(file).Length > 64_000) File.Delete(file);
                File.AppendAllText(file, $"{DateTimeOffset.UtcNow:yyyy-MM-ddTHH:mm:ssZ} {line}{Environment.NewLine}");
            }
        }
        catch { /* logging is a diagnostic aid, never a reason to fail a reading */ }
    }
}

static class CommandFinder
{
    private static readonly string[] Extensions = { ".exe", ".cmd", ".bat" };

    /// <summary>The first <paramref name="name"/>.exe/.cmd/.bat in the extra folders, then on PATH.</summary>
    public static string? Find(string name, IEnumerable<string> extraDirectories)
    {
        var onPath = (Environment.GetEnvironmentVariable("PATH") ?? "").Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries);
        foreach (var raw in extraDirectories.Concat(onPath))
        {
            var directory = raw.Trim().Trim('"');
            if (directory.Length == 0) continue;
            foreach (var extension in Extensions)
            {
                try
                {
                    var candidate = Path.Combine(directory, name + extension);
                    if (File.Exists(candidate)) return candidate;
                }
                catch (ArgumentException) { /* a malformed PATH entry */ }
            }
        }
        return null;
    }

    /// <summary>npm and the native installers put .cmd shims on PATH, and those only run through cmd.exe.</summary>
    public static ProcessStartInfo StartInfo(string path, params string[] arguments)
    {
        var isShim = path.EndsWith(".cmd", StringComparison.OrdinalIgnoreCase) || path.EndsWith(".bat", StringComparison.OrdinalIgnoreCase);
        var info = new ProcessStartInfo
        {
            FileName = isShim ? "cmd.exe" : path,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            WorkingDirectory = Path.GetTempPath(),
        };
        if (isShim) { info.ArgumentList.Add("/c"); info.ArgumentList.Add(path); }
        foreach (var argument in arguments) info.ArgumentList.Add(argument);
        return info;
    }
}

static class ClaudeLiveUsage
{
    private static IEnumerable<string> ExtraDirectories()
    {
        var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        yield return Path.Combine(home, ".local", "bin");
        yield return Path.Combine(home, ".claude", "local");
        yield return Path.Combine(appData, "npm");
    }

    public static LiveResult Fetch()
    {
        var first = Attempt();
        if (first.Reading is not null) return first;
        // Claude Code replaces its own binary when it updates, and a run that starts in that gap
        // fails or prints nothing. One more try a few seconds later usually lands after it.
        Thread.Sleep(TimeSpan.FromSeconds(4));
        return Attempt();
    }

    private static LiveResult Attempt()
    {
        var path = CommandFinder.Find("claude", ExtraDirectories());
        if (path is null)
        {
            UsageLog.Write("claude: the claude command was not found");
            return LiveResult.Fail(LiveFailure.ClaudeMissing);
        }
        // BITLING_PROBE tells Bitling's own Claude hooks to ignore this run.
        var info = CommandFinder.StartInfo(path, "-p", "/usage", "--no-session-persistence");
        info.Environment["BITLING_PROBE"] = "1";
        Process process;
        try { process = Process.Start(info) ?? throw new InvalidOperationException(); }
        catch (Exception)
        {
            UsageLog.Write("claude: could not start the claude command");
            return LiveResult.Fail(LiveFailure.ClaudeMissing);
        }
        using (process)
        {
            process.StandardInput.Close();
            var output = process.StandardOutput.ReadToEndAsync();
            _ = process.StandardError.ReadToEndAsync(); // drained so a chatty child cannot block on a full pipe
            if (!process.WaitForExit(60_000))
            {
                try { process.Kill(entireProcessTree: true); } catch { /* it exited meanwhile */ }
                UsageLog.Write("claude: /usage took too long and was stopped");
                return LiveResult.Fail(LiveFailure.ClaudeSilent);
            }
            if (!output.Wait(5_000))
            {
                UsageLog.Write("claude: /usage finished but its output did not arrive");
                return LiveResult.Fail(LiveFailure.ClaudeSilent);
            }
            var text = output.Result;
            var reading = ClaudeUsageTextParser.Parse(text, DateTimeOffset.Now);
            if (reading is null)
            {
                var first = text.Split('\n').FirstOrDefault()?.Trim();
                UsageLog.Write($"claude: /usage printed no week line, it began: {(string.IsNullOrEmpty(first) ? "nothing" : first[..Math.Min(80, first.Length)])}");
                return LiveResult.Fail(LiveFailure.NotSignedIn);
            }
            UsageLog.Write($"claude: live week {reading.Weekly?.UsedPercent}%");
            return LiveResult.Ok(reading);
        }
    }
}

static class CodexLiveUsage
{
    /// <summary>Collects a child's output a line at a time so a reader can wait for one answer with a timeout.</summary>
    private sealed class LineCollector
    {
        private readonly object _gate = new();
        private readonly List<JsonObject> _objects = new();

        public void Add(string line)
        {
            JsonObject? parsed;
            try { parsed = JsonNode.Parse(line) as JsonObject; } catch (System.Text.Json.JsonException) { return; }
            if (parsed is null) return;
            lock (_gate) { _objects.Add(parsed); Monitor.PulseAll(_gate); }
        }

        /// <summary>The next JSON object that carries <paramref name="id"/>, or null if none arrives in time.</summary>
        public JsonObject? Next(int id, DateTime deadlineUtc)
        {
            lock (_gate)
            {
                while (true)
                {
                    var match = _objects.FirstOrDefault(o => o["id"] is JsonValue v && v.TryGetValue<int>(out var value) && value == id);
                    if (match is not null) return match;
                    var remaining = deadlineUtc - DateTime.UtcNow;
                    if (remaining <= TimeSpan.Zero) return null;
                    Monitor.Wait(_gate, remaining);
                }
            }
        }
    }

    private static IEnumerable<string> ExtraDirectories()
    {
        var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        yield return Path.Combine(home, ".local", "bin");
        yield return Path.Combine(home, ".codex", "packages", "standalone", "current", "bin");
        yield return Path.Combine(appData, "npm");
    }

    public static LiveResult Fetch()
    {
        var path = CommandFinder.Find("codex", ExtraDirectories());
        if (path is null) return LiveResult.Fail(LiveFailure.CodexMissing);
        Process process;
        try { process = Process.Start(CommandFinder.StartInfo(path, "app-server")) ?? throw new InvalidOperationException(); }
        catch (Exception) { return LiveResult.Fail(LiveFailure.CodexMissing); }

        using (process)
        {
            var collector = new LineCollector();
            _ = Task.Run(async () =>
            {
                try
                {
                    string? line;
                    while ((line = await process.StandardOutput.ReadLineAsync()) is not null) collector.Add(line);
                }
                catch { /* the process ended */ }
            });
            _ = process.StandardError.ReadToEndAsync();

            try
            {
                bool Send(JsonObject message)
                {
                    try { process.StandardInput.WriteLine(message.ToJsonString()); return true; }
                    catch (IOException) { return false; } // the child already exited
                }

                var deadline = DateTime.UtcNow.AddSeconds(20);
                Send(new JsonObject
                {
                    ["method"] = "initialize", ["id"] = 0,
                    ["params"] = new JsonObject { ["clientInfo"] = new JsonObject { ["name"] = "bitling", ["title"] = "Bitling", ["version"] = "1" } },
                });
                if (collector.Next(0, deadline) is null) return LiveResult.Fail(LiveFailure.CodexSilent);
                Send(new JsonObject { ["method"] = "initialized" });
                Send(new JsonObject { ["method"] = "account/rateLimits/read", ["id"] = 1 });
                if (collector.Next(1, deadline) is not { } answer) return LiveResult.Fail(LiveFailure.CodexSilent);
                if (answer["result"] is not JsonObject result) return LiveResult.Fail(LiveFailure.CodexNotSignedIn);
                var reading = CodexUsageParser.Parse(result, DateTimeOffset.Now);
                return reading is null ? LiveResult.Fail(LiveFailure.CodexSilent) : LiveResult.Ok(reading);
            }
            finally
            {
                try { process.StandardInput.Close(); } catch { /* already closed */ }
                try { if (!process.HasExited) process.Kill(entireProcessTree: true); } catch { /* gone */ }
            }
        }
    }
}
