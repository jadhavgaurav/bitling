// Global git hooks (core.hooksPath), so every repository on this PC reports commits,
// merges, checkouts, rebases and pushes the moment they happen.
//
// Ported from the GitHooks enum in apps/macos/Sources/main.swift. Git for Windows ships
// its own sh.exe and runs hook scripts through it via the shebang line, exactly like on
// macOS/Linux, so the hook script bodies are unchanged; they just shell out to
// powershell.exe to run bitling.ps1 instead of the macOS `bitling` bash script.
using System.Diagnostics;
using Bitling.Settings;

namespace Bitling.Native;

static class GitHooks
{
    public static readonly string[] HookNames = { "post-commit", "post-merge", "post-checkout", "post-rewrite", "pre-push" };
    private const string PreviousKey = "gitPreviousHooksPath";

    public sealed class HooksException : Exception
    {
        public HooksException(string message) : base(message) { }
    }

    /// Placeholders: __TOOL__ (powershell invocation of bitling.ps1), __NAME__ (hook name),
    /// __CHAIN__ (an optional call into a pre-existing global hooks path).
    private const string HookTemplate =
        "#!/bin/sh\n" +
        "# Installed by Bitling. Reports this event to the desktop pet, then runs your own hooks.\n" +
        "__TOOL__ __NAME__ \"$@\" >/dev/null 2>&1 || true\n" +
        "__CHAIN__\n" +
        "repo_hook=\"$(git rev-parse --git-common-dir 2>/dev/null)/hooks/__NAME__\"\n" +
        "if [ -x \"$repo_hook\" ]; then exec \"$repo_hook\" \"$@\"; fi\n" +
        "exit 0\n";

    public static string Directory => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Bitling", "githooks");

    private static string ToolCommand(string bitlingPs1Path) =>
        $"powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"{ToUnixPath(bitlingPs1Path)}\" git";

    /// git for Windows' bundled sh treats the path as POSIX-ish; forward slashes are safe
    /// even for a Windows path when quoted like this.
    private static string ToUnixPath(string path) => path.Replace('\\', '/');

    private static string RunGit(string[] arguments)
    {
        var psi = new ProcessStartInfo(GitExecutable())
        {
            RedirectStandardOutput = true, RedirectStandardError = true,
            UseShellExecute = false, CreateNoWindow = true,
        };
        foreach (var arg in arguments) psi.ArgumentList.Add(arg);
        using var process = Process.Start(psi) ?? throw new HooksException("could not launch git");
        var stdout = process.StandardOutput.ReadToEnd().Trim();
        var stderr = process.StandardError.ReadToEnd().Trim();
        process.WaitForExit();
        if (process.ExitCode == 0) return stdout;
        var isUnsetGet = arguments.Length > 0 && arguments[0] == "config" && arguments.Contains("--get") && stdout.Length == 0 && stderr.Length == 0;
        if (isUnsetGet) return stdout;
        throw new HooksException(stderr.Length == 0 ? $"git exited with status {process.ExitCode}" : stderr);
    }

    private static string GitExecutable()
    {
        foreach (var candidate in new[] { @"C:\Program Files\Git\cmd\git.exe", @"C:\Program Files\Git\bin\git.exe" })
            if (File.Exists(candidate)) return candidate;
        return "git";
    }

    public static string CurrentHooksPath()
    {
        try { return RunGit(new[] { "config", "--global", "--get", "core.hooksPath" }); }
        catch { return ""; }
    }

    public static bool Installed() => CurrentHooksPath() == Directory;

    /// `git config --global` briefly fails with a lock-file error if another git process
    /// on the machine is also writing the global config at that instant. That is a normal,
    /// recoverable race, not a real failure, so retry a few times before giving up.
    private static void RetryingGlobalConfig(string[] arguments)
    {
        Exception? last = null;
        for (var attempt = 0; attempt < 5; attempt++)
        {
            try { RunGit(new[] { "config", "--global" }.Concat(arguments).ToArray()); return; }
            catch (Exception ex) { last = ex; if (attempt < 4) Thread.Sleep(200); }
        }
        throw last ?? new HooksException($"git config --global {string.Join(' ', arguments)} failed");
    }

    public static void Install(string bitlingPs1Path)
    {
        var previous = CurrentHooksPath();
        if (previous.Length > 0 && previous != Directory) AppSettings.Set(PreviousKey, previous);
        System.IO.Directory.CreateDirectory(Directory);
        var tool = ToolCommand(bitlingPs1Path);
        var chained = AppSettings.GetString(PreviousKey) ?? "";
        foreach (var name in HookNames)
        {
            var script = HookTemplate.Replace("__TOOL__", tool).Replace("__NAME__", name);
            if (chained.Length == 0)
            {
                script = script.Replace("__CHAIN__", "");
            }
            else
            {
                var chainedUnix = ToUnixPath(chained);
                var chain = $"if [ -x \"{chainedUnix}/{name}\" ]; then\n  \"{chainedUnix}/{name}\" \"$@\" || exit $?\nfi";
                script = script.Replace("__CHAIN__", chain);
            }
            var path = Path.Combine(Directory, name);
            File.WriteAllText(path, script.Replace("\r\n", "\n"));
            // sh.exe needs the executable bit; .NET on Windows has no chmod, but Git for
            // Windows' sh only checks that the file is readable, not the Windows ACL "x" bit,
            // so no extra step is needed here (unlike the macOS FileManager.setAttributes call).
        }
        RetryingGlobalConfig(new[] { "core.hooksPath", Directory });
        if (!Installed()) throw new HooksException("git accepted core.hooksPath but reading it back gave a different value");
    }

    public static void Uninstall()
    {
        var previous = AppSettings.GetString(PreviousKey) ?? "";
        if (previous.Length == 0) RetryingGlobalConfig(new[] { "--unset", "core.hooksPath" });
        else RetryingGlobalConfig(new[] { "core.hooksPath", previous });
        AppSettings.Remove(PreviousKey);
    }
}
