// Claude Code hooks in %USERPROFILE%\.claude\settings.json, for instant reactions
// instead of only transcript tailing.
//
// Ported from the ClaudeHooks enum in apps/macos/Sources/main.swift. Claude Code invokes
// hook commands through the OS shell either way, so the only change from macOS is the
// command line itself: a PowerShell invocation of bitling.ps1 instead of the bash script.
using System.Text.Json.Nodes;

namespace Bitling.Native;

static class ClaudeHooks
{
    public static readonly string[] Events = { "SessionStart", "UserPromptSubmit", "PreToolUse", "Stop", "Notification", "SessionEnd" };

    public static string Command(string bitlingPs1Path) =>
        $"powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"{bitlingPs1Path}\" claude";

    public sealed class HooksException : Exception
    {
        public HooksException(string message) : base(message) { }
    }

    private static string SettingsPath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".claude", "settings.json");

    private static JsonObject Load()
    {
        if (!File.Exists(SettingsPath)) return new JsonObject();
        var parsed = JsonNode.Parse(File.ReadAllText(SettingsPath));
        if (parsed is not JsonObject obj) throw new HooksException("settings.json is not a JSON object");
        return obj;
    }

    private static void Save(JsonObject settings)
    {
        var backup = Path.Combine(Path.GetDirectoryName(SettingsPath)!, "settings.json.bitling-backup");
        if (File.Exists(SettingsPath))
        {
            try { File.Copy(SettingsPath, backup, overwrite: true); } catch { /* best-effort backup */ }
        }
        var options = new System.Text.Json.JsonSerializerOptions { WriteIndented = true };
        Directory.CreateDirectory(Path.GetDirectoryName(SettingsPath)!);
        File.WriteAllText(SettingsPath, settings.ToJsonString(options));
    }

    private static bool IsOurs(JsonObject group, string command)
    {
        var hooks = group["hooks"] as JsonArray;
        if (hooks is null || hooks.Count == 0) return false;
        return hooks.OfType<JsonObject>().All(h => (h["command"]?.GetValue<string>() ?? "").EndsWith("bitling.ps1\" claude"));
    }

    public static bool Installed(string bitlingPs1Path)
    {
        var settings = Load();
        var hooks = settings["hooks"] as JsonObject;
        var groups = hooks?["UserPromptSubmit"] as JsonArray;
        return groups?.OfType<JsonObject>().Any(g => IsOurs(g, Command(bitlingPs1Path))) ?? false;
    }

    public static void Install(string bitlingPs1Path)
    {
        var command = Command(bitlingPs1Path);
        var settings = Load();
        var hooks = settings["hooks"] as JsonObject ?? new JsonObject();
        foreach (var eventName in Events)
        {
            var groups = (hooks[eventName] as JsonArray)?.DeepClone() as JsonArray ?? new JsonArray();
            var kept = new JsonArray(groups.OfType<JsonObject>().Where(g => !IsOurs(g, command)).Select(g => (JsonNode)g.DeepClone()!).ToArray());
            kept.Add(new JsonObject
            {
                ["matcher"] = "",
                ["hooks"] = new JsonArray(new JsonObject { ["type"] = "command", ["command"] = command, ["timeout"] = 10 }),
            });
            hooks[eventName] = kept;
        }
        settings["hooks"] = hooks;
        Save(settings);
    }

    public static void Uninstall(string bitlingPs1Path)
    {
        var command = Command(bitlingPs1Path);
        var settings = Load();
        if (settings["hooks"] is not JsonObject hooks) return;
        foreach (var eventName in Events)
        {
            var groups = (hooks[eventName] as JsonArray)?.DeepClone() as JsonArray ?? new JsonArray();
            var kept = new JsonArray(groups.OfType<JsonObject>().Where(g => !IsOurs(g, command)).Select(g => (JsonNode)g.DeepClone()!).ToArray());
            if (kept.Count == 0) hooks.Remove(eventName); else hooks[eventName] = kept;
        }
        settings["hooks"] = hooks;
        Save(settings);
    }
}
