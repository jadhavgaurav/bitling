// The small card that opens from the usage tray icon: Claude, Codex and the machine's CPU and
// memory, each a bar that runs from green to the colour of its current level. It is the Windows
// counterpart of the pet HUD's usage section and the macOS menu bar menu, and follows the
// pet HUD's look (dark card, thin gradient bars). Built in code, not XAML, so there is no
// markup to get wrong without a Windows machine to try it on.
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Brush = System.Windows.Media.Brush;
using Brushes = System.Windows.Media.Brushes;
using Color = System.Windows.Media.Color;
using FontFamily = System.Windows.Media.FontFamily;
using HorizontalAlignment = System.Windows.HorizontalAlignment;
using Orientation = System.Windows.Controls.Orientation;

namespace Bitling.Usage;

public sealed record UsageSnapshot(SystemMonitor.Sample System, QuotaProvider Claude, QuotaProvider Codex);

sealed class UsagePopup : Window
{
    private const double TrackWidth = 132;
    private static readonly FontFamily Font = new("Segoe UI");
    private static readonly Brush Dim = new SolidColorBrush(Color.FromArgb(150, 255, 255, 255));
    private static readonly Brush Bright = new SolidColorBrush(Color.FromArgb(240, 255, 255, 255));
    private static readonly Brush Track = new SolidColorBrush(Color.FromArgb(36, 255, 255, 255));
    private static readonly Brush Amber = new SolidColorBrush(Color.FromRgb(0xf5, 0x9e, 0x0b));

    private sealed class Row
    {
        public required Border Fill { get; init; }
        public required TextBlock Value { get; init; }
        public TextBlock? Sub { get; init; }
    }

    private readonly System.Drawing.Point _anchor;
    private readonly StackPanel _body = new();
    private readonly Row _claudeWeek, _codexFiveHour, _codexWeek, _cpu, _memory;
    private readonly StackPanel _claudeSection = new(), _codexSection = new();
    private readonly Border _codexDivider = Divider();
    private readonly TextBlock _claudePlan, _codexPlan, _claudeNote, _codexNote;

    public UsagePopup(System.Drawing.Point anchorPixels)
    {
        _anchor = anchorPixels;
        WindowStyle = WindowStyle.None;
        AllowsTransparency = true;
        Background = Brushes.Transparent;
        ShowInTaskbar = false;
        Topmost = true;
        ResizeMode = ResizeMode.NoResize;
        SizeToContent = SizeToContent.Height;
        Width = 244;
        Opacity = 0; // shown only once it has been placed, so it never flashes in the wrong spot

        (_claudePlan, _claudeNote) = Header(_claudeSection, "Claude");
        _claudeWeek = AddRow(_claudeSection, "Wk");
        _claudeSection.Children.Add(_claudeNote);
        (_codexPlan, _codexNote) = Header(_codexSection, "Codex");
        _codexFiveHour = AddRow(_codexSection, "5h");
        _codexWeek = AddRow(_codexSection, "Wk");
        _codexSection.Children.Add(_codexNote);
        var system = new StackPanel();
        Header(system, "System");
        _cpu = AddRow(system, "CPU", withSub: false);
        _memory = AddRow(system, "RAM", withSub: false);

        _body.Children.Add(_claudeSection);
        _body.Children.Add(_codexDivider);
        _body.Children.Add(_codexSection);
        _body.Children.Add(Divider());
        _body.Children.Add(system);
        Content = new Border
        {
            Background = new SolidColorBrush(Color.FromArgb(240, 18, 20, 32)),
            BorderBrush = new SolidColorBrush(Color.FromArgb(41, 255, 255, 255)),
            BorderThickness = new Thickness(1),
            CornerRadius = new CornerRadius(12),
            Padding = new Thickness(14, 12, 14, 12),
            Child = _body,
        };

        Loaded += (_, _) => Place();
        Deactivated += (_, _) => Close();
    }

    protected override void OnContentRendered(EventArgs e)
    {
        base.OnContentRendered(e);
        Activate(); // so a click anywhere else deactivates it and closes it
    }

    private void Place()
    {
        var dpi = VisualTreeHelper.GetDpi(this);
        var area = System.Windows.Forms.Screen.FromPoint(_anchor).WorkingArea;
        var width = ActualWidth * dpi.DpiScaleX;
        var height = ActualHeight * dpi.DpiScaleY;
        var x = Math.Clamp(_anchor.X - width / 2, area.Left + 8, Math.Max(area.Left + 8, area.Right - width - 8));
        // Above the click when the taskbar is at the bottom, below it when the taskbar is at the top.
        var y = _anchor.Y - height - 12;
        if (y < area.Top + 8) y = Math.Min(_anchor.Y + 12, area.Bottom - height - 8);
        Left = x / dpi.DpiScaleX;
        Top = y / dpi.DpiScaleY;
        Opacity = 1;
    }

    public void Update(UsageSnapshot snapshot)
    {
        var now = DateTimeOffset.Now.ToUnixTimeMilliseconds();
        var claude = snapshot.Claude;
        var codex = snapshot.Codex;
        _claudePlan.Text = claude.Plan ?? "";
        var claudeStale = claude.Weekly is { } week && QuotaMerge.IsStale(week, DateTimeOffset.Now);
        Paint(_claudeWeek, claude.Weekly?.UsedPercent, claude.Weekly is null ? "no recent data" : Resets(claude.Weekly, now), claudeStale);
        Note(_claudeNote, claude.LiveStatus);

        // Codex is optional: a PC without it shows no empty section.
        var hasCodex = codex.FiveHour is not null || codex.Weekly is not null;
        _codexSection.Visibility = hasCodex ? Visibility.Visible : Visibility.Collapsed;
        _codexDivider.Visibility = hasCodex ? Visibility.Visible : Visibility.Collapsed;
        _codexPlan.Text = codex.Plan ?? "";
        Paint(_codexFiveHour, codex.FiveHour?.UsedPercent, codex.FiveHour is null ? "no recent data" : Resets(codex.FiveHour, now));
        Paint(_codexWeek, codex.Weekly?.UsedPercent, codex.Weekly is null ? "no recent data" : Resets(codex.Weekly, now));
        Note(_codexNote, codex.LiveStatus);

        Paint(_cpu, snapshot.System.Cpu, null);
        Paint(_memory, snapshot.System.Memory, null);
    }

    private static string Resets(QuotaWindow window, long nowMs)
    {
        var used = $"{window.UsedPercent:0}% used";
        if (QuotaMerge.IsStale(window, DateTimeOffset.FromUnixTimeMilliseconds(nowMs)))
            return $"{used}, last read {Span(TimeSpan.FromMilliseconds(nowMs - window.AsOfMs))} ago, not current";
        return window.ResetsAtMs is { } reset && reset > nowMs ? $"{used}, resets in {Span(TimeSpan.FromMilliseconds(reset - nowMs))}" : used;
    }

    private static string Span(TimeSpan span)
    {
        var minutes = Math.Max(1, (int)Math.Round(span.TotalMinutes));
        if (minutes < 60) return $"{minutes}m";
        var hours = minutes / 60;
        return hours < 48 ? $"{hours}h {minutes % 60}m" : $"{hours / 24}d {hours % 24}h";
    }

    private static void Note(TextBlock note, string? status)
    {
        note.Visibility = status is null ? Visibility.Collapsed : Visibility.Visible;
        note.Text = status is null ? "" : $"Not live: {status}";
    }

    private static void Paint(Row row, double? percent, string? sub, bool stale = false)
    {
        if (row.Sub is not null) row.Sub.Text = sub ?? "";
        if (percent is not { } value || double.IsNaN(value))
        {
            row.Fill.Width = 0;
            row.Fill.Background = Brushes.Transparent;
            row.Value.Text = "--";
            row.Value.Foreground = Dim;
            return;
        }
        var used = Math.Clamp(value, 0, 100);
        var shown = (int)Math.Round(used, MidpointRounding.AwayFromZero);
        // A stale figure is the last one that worked: grey and marked "~", not coloured as current.
        var end = stale ? Color.FromRgb(170, 170, 170) : Media(UsageColor.For(shown));
        row.Fill.Width = TrackWidth * used / 100;
        row.Fill.Background = stale ? new SolidColorBrush(end) : new LinearGradientBrush(Media(UsageColor.For(0)), end, 0);
        row.Value.Text = $"{(stale ? "~" : "")}{shown}%";
        row.Value.Foreground = new SolidColorBrush(end);
    }

    private static Color Media(System.Drawing.Color color) => Color.FromRgb(color.R, color.G, color.B);

    private static TextBlock Text(string text, double size, Brush foreground, FontWeight? weight = null) => new()
    {
        Text = text, FontFamily = Font, FontSize = size, Foreground = foreground,
        FontWeight = weight ?? FontWeights.Normal, VerticalAlignment = VerticalAlignment.Center,
    };

    private static (TextBlock Plan, TextBlock Note) Header(StackPanel parent, string title)
    {
        var grid = new Grid();
        grid.ColumnDefinitions.Add(new ColumnDefinition());
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        var name = Text(title, 13, Bright, FontWeights.SemiBold);
        var plan = Text("", 10, Dim);
        Grid.SetColumn(plan, 1);
        grid.Children.Add(name);
        grid.Children.Add(plan);
        parent.Children.Add(grid);
        var note = Text("", 10, Amber);
        note.Margin = new Thickness(30, 3, 0, 0);
        note.TextWrapping = TextWrapping.Wrap;
        note.Visibility = Visibility.Collapsed;
        return (plan, note);
    }

    private static Row AddRow(StackPanel parent, string label, bool withSub = true)
    {
        var grid = new Grid { Margin = new Thickness(0, 6, 0, 0) };
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(30) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(TrackWidth + 8) });
        grid.ColumnDefinitions.Add(new ColumnDefinition());
        var name = Text(label, 11, Dim, FontWeights.SemiBold);
        var fill = new Border { Height = 6, CornerRadius = new CornerRadius(3), HorizontalAlignment = HorizontalAlignment.Left, Width = 0 };
        var track = new Border
        {
            Width = TrackWidth, Height = 6, CornerRadius = new CornerRadius(3), Background = Track,
            HorizontalAlignment = HorizontalAlignment.Left, VerticalAlignment = VerticalAlignment.Center, Child = fill,
        };
        var value = Text("--", 11, Dim, FontWeights.SemiBold);
        value.HorizontalAlignment = HorizontalAlignment.Right;
        Grid.SetColumn(track, 1);
        Grid.SetColumn(value, 2);
        grid.Children.Add(name);
        grid.Children.Add(track);
        grid.Children.Add(value);
        parent.Children.Add(grid);
        TextBlock? sub = null;
        if (withSub)
        {
            sub = Text("", 10, Dim);
            sub.Margin = new Thickness(30, 2, 0, 0);
            parent.Children.Add(sub);
        }
        return new Row { Fill = fill, Value = value, Sub = sub };
    }

    private static Border Divider() => new()
    {
        Height = 1, Margin = new Thickness(0, 8, 0, 8), Background = new SolidColorBrush(Color.FromArgb(26, 255, 255, 255)),
    };
}
