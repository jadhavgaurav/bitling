// Entry point. Mirrors main.swift's tail (`let app = NSApplication.shared; ...; app.run()`)
// plus the bitling:// single-instance forwarding that macOS gets for free from
// `application(_:open:)` on an already-running LSUIElement app.
using System.Windows;
using Bitling.Native;

namespace Bitling;

public partial class App : Application
{
    private SingleInstance? _singleInstance;
    private AppController? _controller;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        ShutdownMode = ShutdownMode.OnExplicitShutdown;

        var activationUrl = e.Args.FirstOrDefault(a => a.StartsWith("bitling://", StringComparison.OrdinalIgnoreCase));

        _singleInstance = new SingleInstance();
        if (!_singleInstance.IsPrimaryInstance)
        {
            if (activationUrl != null) SingleInstance.ForwardToRunningInstance(activationUrl);
            _singleInstance.Dispose();
            Shutdown();
            return;
        }

        _controller = new AppController();
        _controller.Start();
        _singleInstance.ListenForActivations(url => Dispatcher.Invoke(() => _controller.HandleActivationUrl(url)));
        if (activationUrl != null) _controller.HandleActivationUrl(activationUrl);
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _controller?.Dispose();
        _singleInstance?.Dispose();
        base.OnExit(e);
    }
}
