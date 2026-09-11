// The control room: a small window that shows what the pet is doing, what it is
// watching, and the switches that used to be buried in the menu.
//
// Ported from apps/macos/Sources/ControlPanel.swift.
using System.Text.Json.Nodes;
using System.Windows;
using Microsoft.Web.WebView2.Core;

namespace Bitling.Windows;

public partial class ControlPanelWindow : Window
{
    /// Fired for every button, chip and link in the panel.
    public event Action<string>? ActionRequested;
    /// Asked for a fresh payload whenever the page is ready or the window comes back.
    public Func<JsonObject>? StateProvider { get; set; }

    private bool _ready;

    public ControlPanelWindow()
    {
        InitializeComponent();
        Closing += (_, e) => { e.Cancel = true; Hide(); }; // "closable" in the macOS sense: hide, don't destroy
        Loaded += async (_, _) => await InitializeWebViewAsync();
    }

    public void ShowPanel()
    {
        Show();
        Activate();
        Refresh();
    }

    /// Push the whole payload. Cheap enough at the rate the app updates.
    public void Refresh()
    {
        if (!_ready || !IsVisible || StateProvider is null) return;
        var payload = StateProvider();
        try { _ = Browser.CoreWebView2.ExecuteScriptAsync($"window.panel.update({payload.ToJsonString()})"); }
        catch { /* page not ready yet */ }
    }

    private async Task InitializeWebViewAsync()
    {
        var userData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Bitling", "WebView2Panel");
        var env = await CoreWebView2Environment.CreateAsync(userDataFolder: userData);
        await Browser.EnsureCoreWebView2Async(env);
        var core = Browser.CoreWebView2;
        await core.AddScriptToExecuteOnDocumentCreatedAsync(JsInterop.BridgeShim("panel"));
        core.WebMessageReceived += OnWebMessageReceived;
        core.NavigationCompleted += (_, args) => { if (args.IsSuccess) { _ready = true; Refresh(); } };
        var panelHtml = Path.Combine(AppContext.BaseDirectory, "Resources", "panel.html");
        core.Navigate(new Uri(panelHtml).AbsoluteUri);
    }

    private void OnWebMessageReceived(object? sender, CoreWebView2WebMessageReceivedEventArgs e)
    {
        JsonObject? body;
        try { body = JsonNode.Parse(e.WebMessageAsJson) as JsonObject; } catch { return; }
        var type = body?["type"]?.GetValue<string>();
        if (body is null || type is null) return;
        switch (type)
        {
            case "ready": _ready = true; Refresh(); break;
            case "action":
                if (body["value"]?.GetValue<string>() is { } value) ActionRequested?.Invoke(value);
                break;
        }
    }
}
