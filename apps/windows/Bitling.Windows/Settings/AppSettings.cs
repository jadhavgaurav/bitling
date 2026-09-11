// Windows has no UserDefaults, so every setting the macOS app keeps in UserDefaults
// lives here instead, in one JSON file under %AppData%\Bitling. Reads and writes are
// synchronous and infrequent (menu actions, watcher polls), so a full-file round trip
// per write is simple and cheap enough not to need anything smarter.
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Bitling.Settings;

static class AppSettings
{
    private static readonly string Directory =
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Bitling");
    private static readonly string FilePath = Path.Combine(Directory, "settings.json");
    private static readonly object Lock = new();
    private static JsonObject? _cache;

    private static JsonObject Load()
    {
        if (_cache != null) return _cache;
        try
        {
            if (File.Exists(FilePath))
            {
                _cache = JsonNode.Parse(File.ReadAllText(FilePath)) as JsonObject ?? new JsonObject();
                return _cache;
            }
        }
        catch { /* corrupt or unreadable: start fresh rather than crash the app */ }
        _cache = new JsonObject();
        return _cache;
    }

    private static void Save()
    {
        System.IO.Directory.CreateDirectory(Directory);
        File.WriteAllText(FilePath, _cache!.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
    }

    public static string? GetString(string key)
    {
        lock (Lock) return Load()[key]?.GetValue<string>();
    }

    public static void Set(string key, string? value)
    {
        lock (Lock) { Load()[key] = value; Save(); }
    }

    public static double GetDouble(string key, double fallback)
    {
        lock (Lock) { var node = Load()[key]; return node != null ? node.GetValue<double>() : fallback; }
    }

    public static void Set(string key, double value)
    {
        lock (Lock) { Load()[key] = value; Save(); }
    }

    public static bool GetBool(string key, bool fallback)
    {
        lock (Lock) { var node = Load()[key]; return node != null ? node.GetValue<bool>() : fallback; }
    }

    public static void Set(string key, bool value)
    {
        lock (Lock) { Load()[key] = value; Save(); }
    }

    public static int GetInt(string key, int fallback)
    {
        lock (Lock) { var node = Load()[key]; return node != null ? node.GetValue<int>() : fallback; }
    }

    public static void Set(string key, int value)
    {
        lock (Lock) { Load()[key] = value; Save(); }
    }

    public static string[] GetStringArray(string key)
    {
        lock (Lock)
        {
            var node = Load()[key] as JsonArray;
            return node?.Select(n => n?.GetValue<string>() ?? "").ToArray() ?? Array.Empty<string>();
        }
    }

    public static void SetStringArray(string key, IEnumerable<string> values)
    {
        lock (Lock) { Load()[key] = new JsonArray(values.Select(v => (JsonNode)v).ToArray()); Save(); }
    }

    /// Arbitrary JSON object under a key, for grab-bags like "today's counters".
    public static JsonObject? GetObject(string key)
    {
        lock (Lock) return Load()[key] as JsonObject;
    }

    public static void SetObject(string key, JsonObject value)
    {
        lock (Lock) { Load()[key] = value.DeepClone(); Save(); }
    }

    public static void Remove(string key)
    {
        lock (Lock) { Load().Remove(key); Save(); }
    }
}
