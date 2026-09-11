using System.Text.Json;

namespace Bitling;

static class JsInterop
{
    /// JSON-encode a single string so it can be embedded as a JS literal, mirroring
    /// jsString(_:) in apps/macos/Sources/main.swift.
    public static string EncodeString(string value) => JsonSerializer.Serialize(value);

    /// The bridge shim injected into both pet.html and panel.html before any page script
    /// runs (WebView2's AddScriptToExecuteOnDocumentCreatedAsync, the equivalent of WKWebView's
    /// WKUserScript at .atDocumentStart). The pages call `window.webkit.messageHandlers.<name>
    /// .postMessage(obj)`; WebView2's own bridge is `window.chrome.webview.postMessage(obj)`,
    /// which accepts any JSON-serializable value directly, no manual stringify needed.
    public static string BridgeShim(string handlerName) =>
        $$"""
        (function() {
          window.webkit = window.webkit || {};
          window.webkit.messageHandlers = window.webkit.messageHandlers || {};
          window.webkit.messageHandlers.{{handlerName}} = {
            postMessage: function(msg) {
              try { window.chrome.webview.postMessage(msg); } catch (e) { /* host gone */ }
            }
          };
        })();
        """;

    public static string InjectSavedState(string savedJson) => $"window.__petSavedState = {EncodeString(savedJson)};";
}
