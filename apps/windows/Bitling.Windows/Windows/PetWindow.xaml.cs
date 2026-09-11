// The creature itself is a web page (Resources\pet.html) rendered in a transparent,
// borderless, always-on-top window. This host owns everything the page cannot: moving
// the window when you drag the pet, throw physics against the real screen edges, idle
// strolls along the bottom of the screen, and durable state.
//
// Ported from apps/macos/Sources/main.swift (AppDelegate + PetWindow). V1 scope cut,
// documented in apps/windows/README.md: the full-screen "desktop stage" mode (Shenron
// dragon, Spider-Man rooftop web-slinging) and the cross-screen bug-swarm/laser/rocket
// overlay (Overlay.swift) are not ported yet — every species falls back to ordinary
// walker/floater window physics, and "bugs"/"tests"/"boss"/"zap"/"rocketScreen" bridge
// messages are accepted but currently no-op.
//
// COORDINATE SYSTEM WARNING: macOS screen coordinates are Y-up (origin bottom-left);
// Windows/WPF are Y-down (origin top-left). Every vertical physics formula below was
// re-derived for Y-down rather than copied, and is the single highest-risk area in this
// port to get subtly wrong. Verify on real hardware before trusting it: an object should
// fall DOWN the screen and land on top of the taskbar, not float upward.
using System.Text.Json.Nodes;
using System.Windows;
using System.Windows.Threading;
using Bitling.Models;
using Bitling.Native;
using Bitling.Settings;
using Microsoft.Web.WebView2.Core;

namespace Bitling.Windows;

public partial class PetWindow : Window
{
    private const string StateDefaultsKey = "petState";
    private const string WindowXDefaultsKey = "petWindowX";
    private const string PetSizeDefaultsKey = "petSize";
    // Tall enough for the full robot plus a deployed parachute, wide enough for its arms.
    private static readonly Size PetBaseSize = new(300, 340);

    private double _petSizeScale = AppSettings.GetDouble(PetSizeDefaultsKey, 1);
    private Size PetWindowSize => new(
        Math.Round(PetBaseSize.Width * _petSizeScale), Math.Round(PetBaseSize.Height * _petSizeScale));

    private bool _pageReady;
    public PetSnapshot Snapshot { get; private set; } = new();
    public JsonArray SpeciesCatalogue { get; private set; } = new();

    private enum Flight { None, Flying, Hovering, Landing }

    private bool _dragging, _airborne;
    private double _velocityX, _velocityY; // +Y = downward, screen convention
    private double _walkRemaining, _walkDirection;
    private Flight _flight = Flight.None;
    private Point _flyTarget, _hoverBase;
    private double _hoverT;
    private bool _wasFlying, _chuteOpen;
    private double _chuteSway;
    private bool _floating;
    private DateTime _lastHoverReport = DateTime.MinValue;
    private int _dragEventCount;
    private int _tickCount;
    private Point _lastCursor = new(-1, -1);

    private readonly MouseHook _mouseHook = new();
    private bool _mouseDown, _isDraggingPet;
    private Point _downPoint, _lastPoint;
    private DateTime _lastMoveTime;
    private double _rawVx, _rawVy;
    private bool _clickThrough;

    private DispatcherTimer? _tick;

    public event Action? SnapshotChanged;
    public event Action? SpeciesCatalogueChanged;
    public event Action<bool, string>? NameRequested; // (first, suggestion)
    public event Action? RightClicked;

    public PetWindow()
    {
        InitializeComponent();
        Width = PetWindowSize.Width;
        Height = PetWindowSize.Height;
        Loaded += OnLoaded;
        Closed += (_, _) => _mouseHook.Dispose();
    }

    private async void OnLoaded(object? sender, EventArgs e)
    {
        var visible = WindowInterop.WorkAreaInDips(this);
        var savedX = AppSettings.GetDouble(WindowXDefaultsKey, double.NaN);
        Left = ClampX(double.IsNaN(savedX) ? (visible.Right - PetWindowSize.Width - 48) : savedX, visible);
        Top = visible.Bottom - PetWindowSize.Height;

        await InitializeWebViewAsync();
        WindowInterop.HideFromAltTab(this);

        _mouseHook.LeftButtonDown += OnHookLeftDown;
        _mouseHook.MouseMove += OnHookMove;
        _mouseHook.LeftButtonUp += OnHookLeftUp;
        _mouseHook.RightButtonDown += OnHookRightDown;
        _mouseHook.Install();

        _tick = new DispatcherTimer(DispatcherPriority.Render) { Interval = TimeSpan.FromSeconds(1.0 / 60.0) };
        _tick.Tick += (_, _) => Tick();
        _tick.Start();
    }

    // MARK: WebView2 setup

    private async Task InitializeWebViewAsync()
    {
        var userData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Bitling", "WebView2");
        var env = await CoreWebView2Environment.CreateAsync(userDataFolder: userData);
        await Browser.EnsureCoreWebView2Async(env);
        var core = Browser.CoreWebView2;
        core.Settings.IsStatusBarEnabled = false;
        core.Settings.AreDefaultContextMenusEnabled = false;
        await core.AddScriptToExecuteOnDocumentCreatedAsync(JsInterop.BridgeShim("pet"));
        var saved = AppSettings.GetString(StateDefaultsKey);
        if (saved != null) await core.AddScriptToExecuteOnDocumentCreatedAsync(JsInterop.InjectSavedState(saved));
        core.WebMessageReceived += OnWebMessageReceived;
        core.NavigationCompleted += (_, args) => { if (args.IsSuccess) _pageReady = true; };

        var exeDir = AppContext.BaseDirectory;
        var petHtml = Path.Combine(exeDir, "Resources", "pet.html");
        core.Navigate(new Uri(petHtml).AbsoluteUri);
    }

    /// Watcher events arrive from background threads (GitWatcher/CIWatcher/ClaudeWatcher
    /// all poll off the UI thread), so every entry point that can reach here needs to hop
    /// back onto the dispatcher before touching WebView2 or window geometry.
    private void Js(string code)
    {
        if (!Dispatcher.CheckAccess()) { Dispatcher.BeginInvoke(() => Js(code)); return; }
        if (!_pageReady) return;
        try { _ = Browser.CoreWebView2.ExecuteScriptAsync(code); } catch { /* the page may be mid-navigation */ }
    }

    private void OnWebMessageReceived(object? sender, CoreWebView2WebMessageReceivedEventArgs e)
    {
        JsonObject? body;
        try { body = JsonNode.Parse(e.WebMessageAsJson) as JsonObject; } catch { return; }
        var type = body?["type"]?.GetValue<string>();
        if (body is null || type is null) return;
        HandleBridgeMessage(type, body);
    }

    // MARK: Bridge (page -> host)

    private void HandleBridgeMessage(string type, JsonObject body)
    {
        switch (type)
        {
            case "save":
                if (body["json"]?.GetValue<string>() is { } json) AppSettings.Set(StateDefaultsKey, json);
                break;
            case "state":
                if (PetSnapshot.FromMessage(body) is { } snap)
                {
                    Snapshot = snap;
                    ApplyLocomotion(snap.Locomotion == "float");
                    SnapshotChanged?.Invoke();
                }
                break;
            case "walk":
                StartWalk((body["dir"]?.GetValue<double>() ?? 1) < 0 ? -1 : 1);
                break;
            case "rest":
                if (_dragging || _airborne) break;
                _walkRemaining = 0;
                if (_walkDirection != 0) { _walkDirection = 0; Js("petNative.walking(0)"); }
                if (_flight is Flight.Flying or Flight.Hovering)
                {
                    _flight = Flight.Hovering;
                    _hoverBase = new Point(Left, Top);
                    _flyTarget = _hoverBase;
                    Js("petNative.flight('hover')");
                }
                break;
            case "roam":
                if (!_floating || _dragging || _airborne || _flight != Flight.Hovering) break;
                {
                    var visible = ScreenForWindow();
                    var direction = (body["dir"]?.GetValue<double>() ?? 1) < 0 ? -1 : 1;
                    var proposed = Left + direction * 96;
                    var target = ClampX(proposed, visible);
                    var x = Math.Abs(target - Left) < 24 ? ClampX(Left - direction * 96, visible) : target;
                    _flyTarget = new Point(x, Top);
                    _flight = Flight.Flying;
                    Js("petNative.flight('takeoff')");
                }
                break;
            case "fly":
                if (_dragging || _airborne || _flight is not (Flight.None or Flight.Hovering)) break;
                {
                    var visible = ScreenForWindow();
                    var fx = Math.Clamp(body["x"]?.GetValue<double>() ?? 0.5, 0, 1);
                    var fy = Math.Clamp(body["y"]?.GetValue<double>() ?? 0.5, 0, 1);
                    _flyTarget = new Point(
                        visible.Left + fx * Math.Max(0, visible.Width - PetWindowSize.Width),
                        visible.Top + fy * Math.Max(0, visible.Height - PetWindowSize.Height));
                    _walkRemaining = 0;
                    if (_walkDirection != 0) { _walkDirection = 0; Js("petNative.walking(0)"); }
                    _flight = Flight.Flying;
                    Js("petNative.flight('takeoff')");
                }
                break;
            case "land":
                if (_flight == Flight.None) break;
                _flight = Flight.Landing;
                Js("petNative.flight('landing')");
                break;
            case "bugs": case "tests": case "doomAll": case "boss": case "clearBugs": case "zap": case "rocketScreen":
                // V2: the cross-screen bug swarm / laser / rocket overlay isn't ported yet (see README).
                break;
            case "askName":
                var first = body["first"]?.GetValue<bool>() ?? false;
                var suggestion = body["suggestion"]?.GetValue<string>() ?? "Pip";
                NameRequested?.Invoke(first, suggestion);
                break;
            case "hover":
                _lastHoverReport = DateTime.Now;
                SetClickThrough(!(body["on"]?.GetValue<bool>() ?? true));
                break;
            case "species":
                if (body["list"] is JsonArray list) { SpeciesCatalogue = (JsonArray)list.DeepClone()!; SpeciesCatalogueChanged?.Invoke(); }
                break;
            case "ready":
                _pageReady = true;
                Js("petNative.swarmMode(false)");
                break;
        }
    }

    // MARK: Bridge (host -> page)

    public void PatAction() => Js("petNative.action('pat')");
    public void FeedAction() => Js("petNative.action('feed')");
    public void PlayAction() => Js("petNative.action('play')");
    public void SleepAction() => Js("petNative.action('sleep')");
    public void SoundAction() => Js("petNative.action('sound')");
    public void SetName(string name) => Js($"petNative.setName({JsInterop.EncodeString(name)})");
    public void SetSpecies(string id) => Js($"petNative.setSpecies({JsInterop.EncodeString(id)})");

    public void DeliverGitEvent(GitEvent e) => Js($"petNative.gitEvent({e.ToJson().ToJsonString()})");
    public void DeliverGitStatus(GitStatus s) => Js($"petNative.gitStatus({s.ToJson().ToJsonString()})");

    public void ResetAction()
    {
        AppSettings.Remove(StateDefaultsKey);
        Js("petNative.reset()");
    }

    public void ApplyPetSize(double scale)
    {
        var wanted = Math.Clamp(scale, 0.7, 2.0);
        if (Math.Abs(wanted - _petSizeScale) <= 0.01) return;
        _petSizeScale = wanted;
        AppSettings.Set(PetSizeDefaultsKey, wanted);
        var visible = ScreenForWindow();
        var centerX = Left + Width / 2;
        var onFloor = Math.Abs(Top + Height - visible.Bottom) < 2;
        var size = PetWindowSize;
        Width = size.Width;
        Height = size.Height;
        Left = ClampX(centerX - size.Width / 2, visible);
        Top = onFloor ? visible.Bottom - size.Height : Math.Min(Top, visible.Bottom - size.Height);
        _hoverBase = new Point(Left, Top);
        SaveWindowX();
    }

    public void ToggleShown()
    {
        if (IsVisible) Hide(); else { Show(); Activate(); }
    }

    public void BringHere()
    {
        var visible = WindowInterop.WorkAreaUnderPoint(WindowInterop.CursorPositionDips(WindowInterop.DpiScale(this)), WindowInterop.DpiScale(this));
        _airborne = false;
        _flight = Flight.None;
        Js("petNative.flight('landed')");
        _walkRemaining = 0;
        _velocityX = 0;
        _velocityY = 0;
        Left = visible.Left + visible.Width / 2 - PetWindowSize.Width / 2;
        Top = visible.Bottom - PetWindowSize.Height;
        Show();
        Activate();
        SaveWindowX();
    }

    // MARK: Screen / geometry helpers

    private Rect ScreenForWindow() => WindowInterop.WorkAreaInDips(this);

    private double ClampX(double x, Rect visible) =>
        Math.Min(Math.Max(x, visible.Left), Math.Max(visible.Left, visible.Right - PetWindowSize.Width));

    private void SaveWindowX() => AppSettings.Set(WindowXDefaultsKey, Left);

    private void SetClickThrough(bool through)
    {
        var value = through && !_dragging;
        if (_clickThrough == value) return;
        _clickThrough = value;
        WindowInterop.SetClickThrough(this, value);
    }

    // MARK: Motion (host -> page notifications)

    private void StartWalk(double direction)
    {
        if (_floating || _dragging || _airborne || _flight != Flight.None || _walkRemaining > 0 || !IsVisible) return;
        var visible = ScreenForWindow();
        const double distance = 96;
        var dir = direction;
        var target = Left + dir * distance;
        if (target < visible.Left || target + PetWindowSize.Width > visible.Right) dir = -dir;
        _walkDirection = dir;
        _walkRemaining = distance;
        Js($"petNative.walking({(int)dir})");
    }

    /// Switching between a walker and a floater has to move the creature: one belongs on
    /// the floor, the other in the air.
    private void ApplyLocomotion(bool isFloat)
    {
        if (isFloat == _floating) return;
        _floating = isFloat;
        if (_dragging) return;
        if (isFloat)
        {
            _airborne = false;
            _chuteOpen = false;
            _velocityX = 0;
            _velocityY = 0;
            _walkRemaining = 0;
            if (_walkDirection != 0) { _walkDirection = 0; Js("petNative.walking(0)"); }
            var visible = ScreenForWindow();
            _flyTarget = new Point(ClampX(Left, visible), visible.Top + visible.Height * 0.42);
            _flight = Flight.Flying;
            Js("petNative.flight('takeoff')");
        }
        else if (_flight != Flight.None)
        {
            _flight = Flight.Landing;
            Js("petNative.flight('landing')");
        }
    }

    // MARK: Drag (low-level mouse hook: WebView2 owns its own HWND, see MouseHook.cs)

    private Point ToDips(Point physical) => new(physical.X / WindowInterop.DpiScale(this), physical.Y / WindowInterop.DpiScale(this));

    private bool WithinWindow(Point dips) => dips.X >= Left && dips.X <= Left + Width && dips.Y >= Top && dips.Y <= Top + Height;

    private void OnHookLeftDown(Point physical)
    {
        if (_clickThrough) return;
        var p = ToDips(physical);
        if (!WithinWindow(p)) return;
        _mouseDown = true;
        _isDraggingPet = false;
        _downPoint = p;
        _lastPoint = p;
        _lastMoveTime = DateTime.Now;
        _rawVx = 0; _rawVy = 0;
    }

    private void OnHookMove(Point physical)
    {
        if (!_mouseDown) return;
        var p = ToDips(physical);
        if (!_isDraggingPet)
        {
            if ((p - _downPoint).Length < 6) return;
            _isDraggingPet = true;
            DragStarted();
        }
        var now = DateTime.Now;
        var dt = Math.Max(0.004, (now - _lastMoveTime).TotalSeconds);
        _rawVx = (p.X - _lastPoint.X) / dt;
        _rawVy = (p.Y - _lastPoint.Y) / dt;
        Left += p.X - _lastPoint.X;
        Top += p.Y - _lastPoint.Y;
        var visible = ScreenForWindow();
        Left = ClampX(Left, visible);
        if (Top < visible.Top) Top = visible.Top;
        if (Top + Height > visible.Bottom) Top = visible.Bottom - Height;
        _lastPoint = p;
        _lastMoveTime = now;
        DragMoved(_rawVx, _rawVy);
    }

    private void OnHookLeftUp(Point physical)
    {
        if (!_mouseDown) return;
        var wasDragging = _isDraggingPet;
        var stale = (DateTime.Now - _lastMoveTime).TotalSeconds > 0.1;
        _mouseDown = false;
        _isDraggingPet = false;
        if (wasDragging) DragEnded(stale ? 0 : _rawVx, stale ? 0 : _rawVy);
    }

    private void OnHookRightDown(Point physical)
    {
        var p = ToDips(physical);
        if (_clickThrough || !WithinWindow(p)) return;
        RightClicked?.Invoke();
    }

    private void DragStarted()
    {
        _dragging = true;
        _chuteOpen = false;
        _wasFlying = _flight != Flight.None;
        _flight = Flight.None;
        _airborne = false;
        _walkRemaining = 0;
        if (_walkDirection != 0) { _walkDirection = 0; Js("petNative.walking(0)"); }
        _dragEventCount = 0;
        Js("petNative.grab()");
    }

    private void DragMoved(double vx, double vy)
    {
        _dragEventCount++;
        if (_dragEventCount % 3 == 0) Js($"petNative.drag({(int)vx}, {(int)vy})");
    }

    private void DragEnded(double vx, double vy)
    {
        _lastHoverReport = DateTime.Now;
        _dragging = false;
        Js("petNative.release()");
        if (_floating)
        {
            // Dropped a floater: it simply stays in the air where you left it.
            _flight = Flight.Hovering;
            _hoverBase = new Point(Left, Top);
            _hoverT = 0;
            _airborne = false;
            _velocityX = 0;
            _velocityY = 0;
            Js("petNative.flight('hover')");
            return;
        }
        var visible = ScreenForWindow();
        var onFloor = Math.Abs(Top + Height - visible.Bottom) < 2;
        if (_wasFlying && Math.Sqrt(vx * vx + vy * vy) < 260 && !onFloor)
        {
            // Let go gently mid-air while it was flying: it hovers where it was left.
            _flight = Flight.Hovering;
            _hoverBase = new Point(Left, Top);
            _hoverT = 0;
            Js("petNative.flight('hover')");
            return;
        }
        _velocityX = Math.Clamp(vx, -2200, 2200);
        _velocityY = Math.Clamp(vy, -2200, 2200);
        _airborne = true;
        Js("petNative.flight('thrown')");
    }

    // MARK: 60Hz tick

    private void Tick()
    {
        _tickCount++;
        if (_dragging) return;
        const double dt = 1.0 / 60.0;
        var visible = ScreenForWindow();
        var floorTop = visible.Bottom - Height;

        switch (_flight)
        {
            case Flight.Flying:
                _chuteOpen = false;
                var dx = _flyTarget.X - Left;
                var dy = _flyTarget.Y - Top;
                var dist = Math.Sqrt(dx * dx + dy * dy);
                if (dist < 3)
                {
                    _flight = Flight.Hovering;
                    _hoverBase = new Point(Left, Top);
                    _hoverT = 0;
                    Js("petNative.flight('hover')");
                    SaveWindowX();
                }
                else
                {
                    var speed = Math.Min(380, 70 + dist * 2.2);
                    Left += dx / dist * speed * dt;
                    Top += dy / dist * speed * dt;
                    if (_tickCount % 6 == 0)
                        // macOS negates dy here because its AppKit frame is Y-up but the page's
                        // flightVec wants canvas convention (+Y = down); WPF's Top is already
                        // Y-down, i.e. already canvas convention, so no flip is needed here.
                        Js($"petNative.flightVec({(dx / dist):F2}, {(dy / dist):F2})");
                }
                break;
            case Flight.Hovering:
                if (_tickCount % 12 == 0) Js("petNative.flightVec(0, 0)");
                _hoverT += dt;
                Left = _hoverBase.X;
                Top = _hoverBase.Y;
                break;
            case Flight.Landing:
                Top += 230 * dt;
                Left = ClampX(Left, visible);
                if (Top >= floorTop)
                {
                    Top = floorTop;
                    _flight = Flight.None;
                    _airborne = false;
                    _velocityX = 0;
                    _velocityY = 0;
                    Js("petNative.flight('landed')");
                    SaveWindowX();
                }
                break;
            case Flight.None:
                if (_airborne)
                {
                    var heightAboveFloor = floorTop - Top;
                    if (_chuteOpen)
                    {
                        // Under canopy: slow terminal descent with a gentle side-to-side drift.
                        _velocityY -= Math.Max(0, _velocityY - 140) * Math.Min(1, dt * 3);
                        _velocityY = Math.Min(_velocityY, 170);
                        _chuteSway += dt * 1.7;
                        _velocityX += (Math.Sin(_chuteSway) * 70 - _velocityX) * Math.Min(1, dt * 2);
                    }
                    else
                    {
                        _velocityY += 2600 * dt;
                        // Falling fast with room to spare: pop the chute.
                        if (_velocityY > 620 && heightAboveFloor > Math.Max(220, visible.Height * 0.22))
                        {
                            _chuteOpen = true;
                            Js("petNative.flight('chute')");
                        }
                    }
                    Left += _velocityX * dt;
                    Top += _velocityY * dt;
                    if (Left < visible.Left) { Left = visible.Left; _velocityX = Math.Abs(_velocityX) * (_chuteOpen ? 0.4 : 0.5); }
                    if (Left + Width > visible.Right) { Left = visible.Right - Width; _velocityX = -Math.Abs(_velocityX) * (_chuteOpen ? 0.4 : 0.5); }
                    if (Top < visible.Top) { Top = visible.Top; _velocityY = Math.Abs(_velocityY) * 0.3; }
                    if (Top >= floorTop)
                    {
                        // Robots land on their feet: no bounce, a knee bend instead.
                        Top = floorTop;
                        var impact = _chuteOpen ? 0.12 : Math.Min(0.45, Math.Abs(_velocityY) / 2600);
                        _velocityY = 0;
                        _velocityX = 0;
                        _airborne = false;
                        if (_chuteOpen) { _chuteOpen = false; Js("petNative.flight('chute-cut')"); }
                        Js($"petNative.land({impact:F2})");
                        SaveWindowX();
                    }
                }
                else if (_walkRemaining > 0)
                {
                    var speed = Snapshot.Species == "kaiju" ? 32 : 70;
                    var step = Math.Min(_walkRemaining, speed * dt);
                    Left += step * _walkDirection;
                    _walkRemaining -= step;
                    if (Left < visible.Left || Left + Width > visible.Right) { Left = ClampX(Left, visible); _walkRemaining = 0; }
                    if (_walkRemaining <= 0) { _walkDirection = 0; Js("petNative.walking(0)"); SaveWindowX(); }
                }
                else if (Math.Abs(Top - floorTop) > 1)
                {
                    _airborne = true;
                    Js("petNative.flight('thrown')");
                }
                break;
        }

        if ((DateTime.Now - _lastHoverReport).TotalSeconds > 3)
        {
            // A failed hover reporter must never block every app underneath.
            SetClickThrough(false);
        }

        if (_tickCount % 2 == 0 && IsVisible)
        {
            var scale = WindowInterop.DpiScale(this);
            var cursor = WindowInterop.CursorPositionDips(scale);
            if (cursor != _lastCursor)
            {
                _lastCursor = cursor;
                var localX = cursor.X - Left;
                var localY = cursor.Y - Top;
                Js($"petNative.cursor({(int)localX}, {(int)localY})");
            }
        }
    }
}
