// Green at 0%, amber at 60%, red from 85%, blended smoothly between. The pet page
// (apps/macos/web/bitling.html, usageRgb) and the macOS menu bar (UsageColor in
// SystemMonitor.swift) use the same stops, so every surface agrees.
using System.Drawing;

namespace Bitling.Usage;

public static class UsageColor
{
    private static readonly (double At, int R, int G, int B)[] Stops =
    {
        (0, 34, 197, 94), (60, 245, 158, 11), (85, 239, 68, 68),
    };

    public static (int R, int G, int B) Rgb(double percent)
    {
        var p = Math.Clamp(double.IsNaN(percent) ? 0 : percent, 0, 100);
        var last = Stops[^1];
        if (p >= last.At) return (last.R, last.G, last.B);
        var index = 0;
        while (p > Stops[index + 1].At) index++;
        var from = Stops[index];
        var to = Stops[index + 1];
        var t = (p - from.At) / (to.At - from.At);
        // Away from zero, like JavaScript's Math.round for these positive values; the default
        // banker's rounding would make the Windows colour differ by one on exact halves.
        int Mix(int a, int b) => (int)Math.Round(a + (b - a) * t, MidpointRounding.AwayFromZero);
        return (Mix(from.R, to.R), Mix(from.G, to.G), Mix(from.B, to.B));
    }

    public static Color For(double percent)
    {
        var (r, g, b) = Rgb(percent);
        return Color.FromArgb(r, g, b);
    }
}
