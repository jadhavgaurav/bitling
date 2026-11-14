// The Windows counterpart of the macOS menu bar readout. The tray cannot hold live text, so a
// second tray icon is redrawn once a second as three thin bars (Claude's weekly use, CPU,
// RAM), each filled to its level and coloured on the green to red scale. The tooltip spells
// the numbers out, a left click opens the detail card, and the right-click menu lists them.
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

namespace Bitling.Usage;

sealed class UsageTray : IDisposable
{
    private readonly System.Windows.Forms.NotifyIcon _icon = new();
    private readonly System.Windows.Forms.ContextMenuStrip _menu = new();
    private UsagePopup? _popup;
    private DateTime _popupClosedAt = DateTime.MinValue;
    private Icon? _current;
    private string _drawnKey = "";
    private SystemMonitor.Sample _system;
    private QuotaProvider _claude = new(), _codex = new();

    public event Action? HideRequested;

    public UsageTray()
    {
        _icon.MouseClick += (_, e) =>
        {
            if (e.Button == System.Windows.Forms.MouseButtons.Left) TogglePopup();
        };
        _menu.Opening += (_, _) => BuildMenu();
        _icon.ContextMenuStrip = _menu;
        Render();
    }

    public bool Visible
    {
        get => _icon.Visible;
        set
        {
            _icon.Visible = value;
            if (!value) _popup?.Close();
        }
    }

    public void Update(SystemMonitor.Sample sample)
    {
        _system = sample;
        Render();
    }

    public void Update(QuotaProvider claude, QuotaProvider codex)
    {
        _claude = claude;
        _codex = codex;
        Render();
    }

    private static int? Whole(double? percent) =>
        percent is { } value && !double.IsNaN(value) ? (int)Math.Round(Math.Clamp(value, 0, 100), MidpointRounding.AwayFromZero) : null;

    private void Render()
    {
        var claude = Whole(_claude.Weekly?.UsedPercent);
        var cpu = Whole(_system.Cpu);
        var ram = Whole(_system.Memory);
        // A stale Claude figure is the last one that worked: it is greyed and marked "~".
        var claudeStale = _claude.Weekly is { } week && QuotaMerge.IsStale(week, DateTimeOffset.Now);
        _icon.Text = $"Claude {(claudeStale ? "~" : "")}{Label(claude)}  CPU {Label(cpu)}  RAM {Label(ram)}";
        // Redraw only when a shown number changed: most seconds nothing has.
        var key = $"{claude}|{claudeStale}|{cpu}|{ram}";
        if (key != _drawnKey)
        {
            _drawnKey = key;
            var next = Draw(new[] { (claude, claudeStale), (cpu, false), (ram, false) });
            _icon.Icon = next;
            _current?.Dispose();
            _current = next;
        }
        _popup?.Update(new UsageSnapshot(_system, _claude, _codex));
    }

    private static string Label(int? percent) => percent is { } value ? $"{value}%" : "--";

    /// <summary>One thin vertical bar per figure: a faint track, filled from the bottom in the level's colour.</summary>
    private static Icon Draw(IReadOnlyList<(int? Level, bool Stale)> levels)
    {
        var size = System.Windows.Forms.SystemInformation.SmallIconSize;
        using var bitmap = new Bitmap(size.Width, size.Height, PixelFormat.Format32bppArgb);
        using (var graphics = Graphics.FromImage(bitmap))
        {
            graphics.Clear(Color.Transparent);
            var gap = Math.Max(1, size.Width / 8);
            var barWidth = Math.Max(2, (size.Width - gap * (levels.Count - 1)) / levels.Count);
            var left = (size.Width - (barWidth * levels.Count + gap * (levels.Count - 1))) / 2;
            using var track = new SolidBrush(Color.FromArgb(110, 150, 150, 150));
            for (var i = 0; i < levels.Count; i++)
            {
                var x = left + i * (barWidth + gap);
                graphics.FillRectangle(track, x, 0, barWidth, size.Height);
                if (levels[i].Level is not { } level) continue;
                var filled = level == 0 ? 0 : Math.Max(1, (int)Math.Round(size.Height * level / 100.0));
                using var fill = new SolidBrush(levels[i].Stale ? Color.FromArgb(170, 170, 170) : UsageColor.For(level));
                graphics.FillRectangle(fill, x, size.Height - filled, barWidth, filled);
            }
        }
        var handle = bitmap.GetHicon();
        try { return (Icon)Icon.FromHandle(handle).Clone(); }
        finally { DestroyIcon(handle); }
    }

    private void TogglePopup()
    {
        if (_popup is not null) { _popup.Close(); return; }
        // Clicking the tray icon deactivates an open card first, which closes it; without this
        // the same click would then open it again.
        if ((DateTime.UtcNow - _popupClosedAt).TotalMilliseconds < 300) return;
        var popup = new UsagePopup(System.Windows.Forms.Cursor.Position);
        popup.Closed += (_, _) =>
        {
            _popup = null;
            _popupClosedAt = DateTime.UtcNow;
        };
        _popup = popup;
        popup.Update(new UsageSnapshot(_system, _claude, _codex));
        popup.Show();
    }

    private void BuildMenu()
    {
        _menu.Items.Clear();
        void Line(string text) => _menu.Items.Add(new System.Windows.Forms.ToolStripMenuItem(text) { Enabled = false });
        Line($"Claude: {(_claude.Weekly is { } week ? $"week {Label(Whole(week.UsedPercent))} used" : "no recent usage data")}");
        if (_codex.FiveHour is not null || _codex.Weekly is not null)
        {
            var parts = new[]
            {
                _codex.FiveHour is { } five ? $"5h {Label(Whole(five.UsedPercent))} used" : null,
                _codex.Weekly is { } weekly ? $"week {Label(Whole(weekly.UsedPercent))} used" : null,
            }.Where(p => p is not null);
            Line($"Codex: {string.Join(" · ", parts)}");
        }
        Line($"CPU: {Label(Whole(_system.Cpu))} used");
        Line($"Memory: {Label(Whole(_system.Memory))} used");
        _menu.Items.Add(new System.Windows.Forms.ToolStripSeparator());
        var hide = new System.Windows.Forms.ToolStripMenuItem("Hide this icon");
        hide.Click += (_, _) => HideRequested?.Invoke();
        _menu.Items.Add(hide);
    }

    public void Dispose()
    {
        _icon.Visible = false;
        _popup?.Close();
        _icon.Dispose();
        _menu.Dispose();
        _current?.Dispose();
    }

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool DestroyIcon(IntPtr handle);
}
