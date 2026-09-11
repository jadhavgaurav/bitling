// Orchestrates the pieces that macOS's AppDelegate owned directly: the tray icon and its
// menu (NSStatusItem's Windows equivalent), the pet and control-room windows, the three
// watchers, the activity log, and the bitling:// command dispatch (both from this
// process's own argv and forwarded from a second launch via SingleInstance).
//
// Ported from apps/macos/Sources/main.swift's AppDelegate. Deferred to V2 (see README):
// desktop-stage species, cross-screen bug swarm/laser/rocket effects, and the
// "watch a folder" picker only supports one folder per pick (WinForms has no built-in
// multi-select folder dialog, unlike NSOpenPanel).
using System.Text.Json.Nodes;
using System.Web;
using System.Windows;
using Bitling.Auth;
using Bitling.Models;
using Bitling.Native;
using Bitling.Settings;
using Bitling.Watchers;
using Bitling.Windows;
using Application = System.Windows.Application;
using MessageBox = System.Windows.MessageBox;

namespace Bitling;

sealed class AppController : IDisposable
{
    private readonly PetWindow _petWindow = new();
    private readonly ControlPanelWindow _panel = new();
    private readonly System.Windows.Forms.NotifyIcon _tray = new();
    private readonly System.Windows.Forms.ContextMenuStrip _menu = new();
    private readonly GitWatcher _git = new();
    private readonly CIWatcher _ci = new();
    private readonly ClaudeWatcher _claude = new();
    private readonly ActivityLog _activity = new();
    private readonly Dictionary<string, DateTime> _recentEvents = new();
    private System.Windows.Threading.DispatcherTimer? _panelRefreshTimer;

    private static string BitlingPs1Path => Path.Combine(AppContext.BaseDirectory, "bitling.ps1");

    public void Start()
    {
        BuildTray();
        _petWindow.NameRequested += OnNameRequested;
        _petWindow.RightClicked += () => _menu.Show(System.Windows.Forms.Cursor.Position);
        _petWindow.SnapshotChanged += () => _panel.Refresh();
        _petWindow.Show();

        _panel.StateProvider = BuildPanelPayload;
        _panel.ActionRequested += OnPanelAction;

        _git.OnEvent += DeliverGitEvent;
        _git.OnStatus += e => _petWindow.DeliverGitStatus(e);
        _git.Start();

        _ci.Repositories = () => _git.Repositories();
        _ci.OnEvent += DeliverGitEvent;
        _ci.Start();

        _claude.OnEvent += DeliverGitEvent;
        _claude.Start();

        _panelRefreshTimer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromSeconds(0.5) };
        _panelRefreshTimer.Tick += (_, _) => _panel.Refresh();
        _panelRefreshTimer.Start();

        Task.Run(() =>
        {
            try { ProtocolRegistration.Register(); } catch { /* best effort; the CLI still works via a running instance */ }
        });
    }

    // MARK: bitling:// dispatch

    public void HandleActivationUrl(string url)
    {
        if (!Uri.TryCreate(url, UriKind.Absolute, out var uri) || !uri.Scheme.Equals("bitling", StringComparison.OrdinalIgnoreCase)) return;
        var kind = uri.Host.ToLowerInvariant();
        var query = HttpUtility.ParseQueryString(uri.Query);
        Application.Current.Dispatcher.Invoke(() =>
        {
            if (kind == "panel") { _panel.ShowPanel(); return; }
            if (kind == "pet") { var id = query["id"]; if (!string.IsNullOrEmpty(id)) _petWindow.SetSpecies(id); return; }
            if (kind == "size") { if (double.TryParse(query["v"], out var v)) _petWindow.ApplyPetSize(v); return; }
            var e = new GitEvent
            {
                Kind = kind, Repo = query["repo"] ?? "", Branch = query["branch"] ?? "",
                Message = query["message"] ?? query["text"] ?? "", Hash = query["hash"] ?? "",
                Count = int.TryParse(query["count"], out var c) ? c : 0, Target = query["target"] ?? "", Name = query["name"] ?? "",
                Tests = (query["tests"] ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries),
            };
            DeliverGitEvent(e);
        });
    }

    private void DeliverGitEvent(GitEvent e)
    {
        // Hooks and transcript tailing can report the same moment; keep the first within 3 seconds.
        if (e.Kind.StartsWith("claude-"))
        {
            var key = $"{e.Kind}|{e.Name}";
            var now = DateTime.Now;
            foreach (var stale in _recentEvents.Where(kv => (now - kv.Value).TotalSeconds >= 30).Select(kv => kv.Key).ToList())
                _recentEvents.Remove(stale);
            if (_recentEvents.TryGetValue(key, out var last) && (now - last).TotalSeconds < 3) return;
            _recentEvents[key] = now;
        }
        _activity.Record(e);
        _panel.Refresh();
        if (e.CommitsToday == 0 && _git.CommitsToday > 0) e.CommitsToday = _git.CommitsToday;
        if (e.PushesToday == 0 && _git.PushesToday > 0) e.PushesToday = _git.PushesToday;
        _petWindow.DeliverGitEvent(e);
    }

    // MARK: Naming

    private void OnNameRequested(bool first, string suggestion)
    {
        var dialog = new NameDialog(first, suggestion) { Owner = null };
        dialog.ShowDialog();
        if (dialog.Result is { } name) _petWindow.SetName(name);
    }

    // MARK: Panel payload / actions

    private JsonObject BuildPanelPayload()
    {
        var snapshot = _petWindow.Snapshot;
        var ghConnected = _ci.GhStatus.StartsWith("GitHub Actions");
        var githubLinked = GitHubAuth.StoredToken() != null;
        var version = System.Reflection.Assembly.GetExecutingAssembly().GetName().Version?.ToString() ?? "?";
        return new JsonObject
        {
            ["pet"] = new JsonObject
            {
                ["name"] = snapshot.Name, ["stage"] = snapshot.Stage, ["age"] = snapshot.Age,
                ["full"] = snapshot.Full, ["energy"] = snapshot.Energy, ["joy"] = snapshot.Joy,
                ["asleep"] = snapshot.Asleep, ["hatched"] = snapshot.Hatched,
                ["working"] = snapshot.Working, ["screen"] = snapshot.Screen,
                ["sound"] = snapshot.Sound, ["species"] = snapshot.Species,
                ["shenron"] = snapshot.ShenronSettings.DeepClone(),
                ["goku"] = snapshot.Goku.DeepClone(),
                ["thor"] = snapshot.Thor.DeepClone(),
            },
            ["today"] = new JsonObject
            {
                ["commits"] = _git.CommitsToday, ["pushes"] = _git.PushesToday,
                ["prompts"] = _claude.PromptsToday, ["tools"] = _claude.ToolsToday,
                ["zapped"] = snapshot.BugsToday,
            },
            ["lifetime"] = new JsonObject { ["commits"] = snapshot.Commits, ["pushes"] = snapshot.Pushes, ["bugs"] = snapshot.Bugs },
            ["watch"] = new JsonObject
            {
                ["repos"] = _git.RepositoryCount,
                ["roots"] = _git.ExtraRoots.Count,
                ["claudeActive"] = _claude.ActiveSessionCount,
                ["login"] = LoginItem.IsEnabled(),
                ["ci"] = ghConnected ? "GitHub Actions" : "CI needs gh",
                ["ciOn"] = ghConnected,
                ["ciDetail"] = $"{_ci.GhStatus}. Last: {_ci.LastSummary}",
                ["githubLinked"] = githubLinked,
                ["claudeHooks"] = ClaudeHooks.Installed(BitlingPs1Path),
                ["gitHooks"] = GitHooks.Installed(),
                ["petVisible"] = _petWindow.IsVisible,
                ["version"] = version,
            },
            ["species"] = _petWindow.SpeciesCatalogue.DeepClone(),
            ["events"] = _activity.ToJsonArray(),
        };
    }

    private void OnPanelAction(string action)
    {
        switch (action)
        {
            case "pat": _petWindow.PatAction(); break;
            case "feed": _petWindow.FeedAction(); break;
            case "play": _petWindow.PlayAction(); break;
            case "sleep": _petWindow.SleepAction(); break;
            case "rescan": _git.Rescan(); break;
            case "gitHooks": ToggleGitHooks(); break;
            case "githubConnect": ToggleGitHubConnection(); break;
            case "claudeHooks": ToggleClaudeHooks(); break;
            case "hide": _petWindow.ToggleShown(); break;
            case "rename": RenameAction(); break;
            case "sound": _petWindow.SoundAction(); break;
            case "login": LoginItem.SetEnabled(!LoginItem.IsEnabled()); break;
            case "reset": ResetAction(); break;
            case "watchFolder": WatchFolder(); break;
            case "bringHere": _petWindow.BringHere(); break;
            case "repo": Process_OpenUrl("https://github.com/jadhavgaurav/bitling"); break;
            case "quit": Application.Current.Shutdown(); break;
            default:
                if (action.StartsWith("size:") && double.TryParse(action[5..], out var scale)) _petWindow.ApplyPetSize(scale);
                else if (action.StartsWith("pet:")) _petWindow.SetSpecies(action[4..]);
                break;
        }
        _panel.Refresh();
    }

    private static void Process_OpenUrl(string url) =>
        System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(url) { UseShellExecute = true });

    private void RenameAction() => OnNameRequested(false, _petWindow.Snapshot.Name);

    private void ResetAction()
    {
        var name = _petWindow.Snapshot.Name;
        var text = _petWindow.Snapshot.Hatched
            ? $"{name} and its history will be gone for good. A new egg will take its place."
            : "The box will be replaced with a fresh one.";
        var result = MessageBox.Show(text, "Start over?", MessageBoxButton.YesNo, MessageBoxImage.Warning);
        if (result != MessageBoxResult.Yes) return;
        _activity.Clear();
        _petWindow.ResetAction();
        _panel.Refresh();
    }

    /// WinForms has no built-in multi-select folder dialog (unlike NSOpenPanel on macOS),
    /// so this picks one folder at a time; pick again to add more.
    private void WatchFolder()
    {
        using var dialog = new System.Windows.Forms.FolderBrowserDialog { Description = "Bitling will look for git repositories up to three folders deep." };
        if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK) _git.AddRoot(dialog.SelectedPath);
    }

    private void ToggleGitHooks()
    {
        var installed = GitHooks.Installed();
        var text = installed
            ? "Restores your previous global core.hooksPath setting. Bitling keeps noticing git activity by watching repositories directly."
            : "Sets git's global core.hooksPath to Bitling's hook folder so every repository on this PC reports commits, merges, checkouts, rebases and pushes the moment they happen. Each hook calls your repository's own hook afterwards, and any global hooks path you already use is chained too.";
        var result = MessageBox.Show(text, installed ? "Disconnect global git hooks?" : "Connect global git hooks?", MessageBoxButton.OKCancel);
        if (result != MessageBoxResult.OK) return;
        try
        {
            if (installed) GitHooks.Uninstall(); else GitHooks.Install(BitlingPs1Path);
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Could not update the git hooks setting", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void ToggleClaudeHooks()
    {
        var installed = ClaudeHooks.Installed(BitlingPs1Path);
        var text = installed
            ? "Removes the Bitling entries from the hooks section of .claude\\settings.json. Other hooks stay untouched. Bitling keeps watching transcripts."
            : "Adds Bitling to the hooks section of .claude\\settings.json for SessionStart, UserPromptSubmit, PreToolUse, Stop, Notification and SessionEnd. Existing hooks are kept, and a backup is written next to the file.";
        var result = MessageBox.Show(text, installed ? "Disconnect Claude Code hooks?" : "Connect Claude Code hooks?", MessageBoxButton.OKCancel);
        if (result != MessageBoxResult.OK) return;
        try
        {
            if (installed) ClaudeHooks.Uninstall(BitlingPs1Path); else ClaudeHooks.Install(BitlingPs1Path);
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Could not update .claude\\settings.json", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    /// Disconnects Bitling's own stored token, or starts the device-flow sign-in when
    /// nothing is connected yet.
    private async void ToggleGitHubConnection()
    {
        if (GitHubAuth.StoredToken() != null)
        {
            var result = MessageBox.Show(
                "Bitling forgets this sign-in. Actions runs and deployments still show up if the gh CLI is installed and logged in.",
                "Disconnect GitHub?", MessageBoxButton.OKCancel);
            if (result != MessageBoxResult.OK) return;
            GitHubAuth.SignOut();
            _ci.RefreshGitHubConnection();
            _panel.Refresh();
            return;
        }
        var connect = MessageBox.Show(
            "Opens github.com in your browser to approve a one-time code, so Bitling can watch Actions runs and deployments without the gh CLI installed.",
            "Connect GitHub?", MessageBoxButton.OKCancel);
        if (connect != MessageBoxResult.OK) return;
        GitHubAuth.DeviceCode code;
        try { code = await GitHubAuth.RequestDeviceCodeAsync(); }
        catch (Exception ex) { MessageBox.Show(ex.Message, "Could not start GitHub sign-in", MessageBoxButton.OK, MessageBoxImage.Error); return; }
        System.Windows.Clipboard.SetText(code.UserCode);
        var proceed = MessageBox.Show(
            $"{code.UserCode}\n\nAlready copied to your clipboard - paste it (Ctrl+V) into the boxes on github.com/login/device, which Bitling opens next.",
            "Enter this code on GitHub", MessageBoxButton.OKCancel);
        if (proceed != MessageBoxResult.OK) return;
        Process_OpenUrl(code.VerificationUri.ToString());
        try
        {
            var token = await GitHubAuth.PollForTokenAsync(code);
            GitHubAuth.Store(token);
            var login = GitHubAuth.FetchLogin(token) ?? "your account";
            _ci.RefreshGitHubConnection();
            _panel.Refresh();
            MessageBox.Show($"GitHub connected as {login}", "Bitling");
        }
        catch (Exception ex)
        {
            MessageBox.Show($"GitHub sign-in didn't finish: {ex.Message}", "Bitling");
        }
    }

    // MARK: Tray

    private void BuildTray()
    {
        _tray.Icon = LoadTrayIcon();
        _tray.Text = "Bitling";
        _tray.Visible = true;
        _tray.MouseClick += (_, e) => { if (e.Button == System.Windows.Forms.MouseButtons.Left) _menu.Show(System.Windows.Forms.Cursor.Position); };
        _menu.Opening += (_, _) => RefreshMenu();
        _tray.ContextMenuStrip = _menu;
        RefreshMenu();
    }

    private static System.Drawing.Icon LoadTrayIcon()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "Resources", "Bitling.ico");
        return File.Exists(path) ? new System.Drawing.Icon(path) : System.Drawing.SystemIcons.Application;
    }

    private static string Meter(string label, int value)
    {
        var filled = Math.Clamp((int)Math.Round(value / 10.0), 0, 10);
        var bar = new string('●', filled) + new string('○', 10 - filled);
        return $"{label}  {bar}  {value}%";
    }

    /// Rebuilds the whole menu on every open. Simpler than tracking individual item
    /// references like AppDelegate.menuNeedsUpdate does, and this menu opens rarely
    /// enough (a user click) that the cost is irrelevant.
    private void RefreshMenu()
    {
        var snap = _petWindow.Snapshot;
        _menu.Items.Clear();
        void Add(string text, EventHandler? onClick = null, bool enabled = true)
        {
            var item = new System.Windows.Forms.ToolStripMenuItem(text) { Enabled = enabled };
            if (onClick != null) item.Click += onClick;
            _menu.Items.Add(item);
        }

        Add(snap.Hatched ? snap.Name : "A mysterious box", enabled: false);
        Add(snap.Hatched ? $"{snap.Stage} · {snap.Age}" : "Tap it three times to unbox", enabled: false);
        if (snap.Hatched)
        {
            Add(Meter("Tummy ", snap.Full), enabled: false);
            Add(Meter("Energy", snap.Energy), enabled: false);
            Add(Meter("Joy   ", snap.Joy), enabled: false);
        }
        _menu.Items.Add(new System.Windows.Forms.ToolStripSeparator());
        Add("Control room…", (_, _) => _panel.ShowPanel());
        _menu.Items.Add(new System.Windows.Forms.ToolStripSeparator());
        Add(snap.Hatched ? (snap.Asleep ? "Wake with a pat" : "Pat") : "Tap the box", (_, _) => _petWindow.PatAction());
        Add("Feed", (_, _) => _petWindow.FeedAction(), enabled: snap.Hatched && !snap.Asleep);
        Add("Debug bugs", (_, _) => _petWindow.PlayAction(), enabled: snap.Hatched && !snap.Asleep);
        Add(snap.Asleep ? "Wake" : "Sleep", (_, _) => _petWindow.SleepAction(), enabled: snap.Hatched);
        _menu.Items.Add(new System.Windows.Forms.ToolStripSeparator());
        Add(_petWindow.IsVisible ? "Hide pet" : "Show pet", (_, _) => _petWindow.ToggleShown());
        Add("Bring pet to this screen", (_, _) => _petWindow.BringHere());
        Add("Rename…", (_, _) => RenameAction(), enabled: snap.Hatched);
        var sound = new System.Windows.Forms.ToolStripMenuItem("Sound") { Checked = snap.Sound };
        sound.Click += (_, _) => _petWindow.SoundAction();
        _menu.Items.Add(sound);
        Add("Start over…", (_, _) => ResetAction());
        _menu.Items.Add(new System.Windows.Forms.ToolStripSeparator());

        var gitMenu = new System.Windows.Forms.ToolStripMenuItem("Dev activity");
        var extras = _git.ExtraRoots.Count;
        var scope = extras == 0 ? "this PC" : $"this PC + {extras} extra folder{(extras == 1 ? "" : "s")}";
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripMenuItem($"Watching {_git.RepositoryCount} repositories across {scope}") { Enabled = false });
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripMenuItem($"Today: {_git.CommitsToday} commit{(_git.CommitsToday == 1 ? "" : "s")} · {_git.PushesToday} push{(_git.PushesToday == 1 ? "" : "es")}") { Enabled = false });
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripMenuItem($"Last: {_git.LastEventSummary}") { Enabled = false });
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripMenuItem($"Lifetime: {snap.Commits} commits caught · {snap.Pushes} pushes · {snap.Bugs} bugs squashed") { Enabled = false });
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripSeparator());
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripMenuItem($"CI: {_ci.GhStatus}") { Enabled = false });
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripMenuItem($"Last CI: {_ci.LastSummary}") { Enabled = false });
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripSeparator());
        var hooked = ClaudeHooks.Installed(BitlingPs1Path);
        var active = _claude.ActiveSessionCount;
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripMenuItem($"Claude Code: {active} active session{(active == 1 ? "" : "s")} · {(hooked ? "hooks connected" : "transcripts only")}") { Enabled = false });
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripMenuItem($"Today: {_claude.PromptsToday} prompt{(_claude.PromptsToday == 1 ? "" : "s")} · {_claude.ToolsToday} tool calls · {_claude.SessionsToday} new session{(_claude.SessionsToday == 1 ? "" : "s")}") { Enabled = false });
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripMenuItem($"Last: {_claude.LastSummary}") { Enabled = false });
        var hooksItem = new System.Windows.Forms.ToolStripMenuItem(hooked ? "Disconnect Claude Code hooks" : "Connect Claude Code hooks…");
        hooksItem.Click += (_, _) => ToggleClaudeHooks();
        gitMenu.DropDownItems.Add(hooksItem);
        gitMenu.DropDownItems.Add(new System.Windows.Forms.ToolStripSeparator());
        var gitHooksItem = new System.Windows.Forms.ToolStripMenuItem(GitHooks.Installed() ? "Disconnect global git hooks" : "Connect global git hooks…");
        gitHooksItem.Click += (_, _) => ToggleGitHooks();
        gitMenu.DropDownItems.Add(gitHooksItem);
        var rescan = new System.Windows.Forms.ToolStripMenuItem("Rescan for repositories now");
        rescan.Click += (_, _) => _git.Rescan();
        gitMenu.DropDownItems.Add(rescan);
        var watch = new System.Windows.Forms.ToolStripMenuItem("Also watch a folder outside home…");
        watch.Click += (_, _) => WatchFolder();
        gitMenu.DropDownItems.Add(watch);
        if (_git.ExtraRoots.Count > 0)
        {
            var stop = new System.Windows.Forms.ToolStripMenuItem("Stop watching extra folder");
            foreach (var root in _git.ExtraRoots)
            {
                var item = new System.Windows.Forms.ToolStripMenuItem(root.Replace(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "~"));
                item.Click += (_, _) => _git.RemoveRoot(root);
                stop.DropDownItems.Add(item);
            }
            gitMenu.DropDownItems.Add(stop);
        }
        _menu.Items.Add(gitMenu);
        _menu.Items.Add(new System.Windows.Forms.ToolStripSeparator());

        var loginItem = new System.Windows.Forms.ToolStripMenuItem("Open at login") { Checked = LoginItem.IsEnabled() };
        loginItem.Click += (_, _) => LoginItem.SetEnabled(!LoginItem.IsEnabled());
        _menu.Items.Add(loginItem);
        Add("Quit Bitling", (_, _) => Application.Current.Shutdown());
    }

    public void Dispose()
    {
        _panelRefreshTimer?.Stop();
        _tray.Visible = false;
        _tray.Dispose();
    }
}
