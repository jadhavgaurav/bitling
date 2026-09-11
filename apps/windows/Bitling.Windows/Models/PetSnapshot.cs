using System.Text.Json.Nodes;

namespace Bitling.Models;

/// Mirrors the "state" message the page pushes on every change (pushState() in bitling.html,
/// via make_pet_html.py's host bridge patch). One-way: host reads, never writes, these fields.
public sealed class PetSnapshot
{
    public string Name { get; set; } = "Bitling";
    public string Stage { get; set; } = "Egg";
    public string Age { get; set; } = "";
    public int Full { get; set; }
    public int Energy { get; set; }
    public int Joy { get; set; }
    public bool Asleep { get; set; }
    public bool Hatched { get; set; }
    public bool Sound { get; set; } = true;
    public int Commits { get; set; }
    public int Pushes { get; set; }
    public int Bugs { get; set; }
    public int BugsToday { get; set; }
    public bool Working { get; set; }
    public string Screen { get; set; } = "";
    public string Species { get; set; } = "robot";
    public string Locomotion { get; set; } = "ground";
    public string Attack { get; set; } = "beam";
    public JsonObject ShenronSettings { get; set; } = new();
    public JsonObject Goku { get; set; } = new();
    public JsonObject Thor { get; set; } = new();

    public static PetSnapshot? FromMessage(JsonObject message)
    {
        var name = message["name"]?.GetValue<string>();
        var stage = message["stage"]?.GetValue<string>();
        if (name is null || stage is null) return null;
        return new PetSnapshot
        {
            Name = name,
            Stage = stage,
            Age = message["age"]?.GetValue<string>() ?? "",
            Full = message["full"]?.GetValue<int>() ?? 0,
            Energy = message["energy"]?.GetValue<int>() ?? 0,
            Joy = message["joy"]?.GetValue<int>() ?? 0,
            Asleep = message["asleep"]?.GetValue<bool>() ?? false,
            Hatched = message["hatched"]?.GetValue<bool>() ?? false,
            Sound = message["sound"]?.GetValue<bool>() ?? true,
            Commits = message["commits"]?.GetValue<int>() ?? 0,
            Pushes = message["pushes"]?.GetValue<int>() ?? 0,
            Bugs = message["bugs"]?.GetValue<int>() ?? 0,
            BugsToday = message["bugsToday"]?.GetValue<int>() ?? 0,
            Working = message["working"]?.GetValue<bool>() ?? false,
            Screen = message["screen"]?.GetValue<string>() ?? "",
            Species = message["species"]?.GetValue<string>() ?? "robot",
            Locomotion = message["locomotion"]?.GetValue<string>() ?? "ground",
            Attack = message["attack"]?.GetValue<string>() ?? "beam",
            ShenronSettings = message["shenronSettings"] as JsonObject ?? new JsonObject(),
            Goku = message["goku"] as JsonObject ?? new JsonObject(),
            Thor = message["thor"] as JsonObject ?? new JsonObject(),
        };
    }
}
