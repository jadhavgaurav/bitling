// Windows has no equivalent of macOS routing a second `open bitling://...` into the
// already-running app for free. This does it by hand: a named mutex says whether an
// instance is already running, and a named pipe forwards each bitling:// argv from a
// newly launched (and immediately exiting) process into the one that stays resident.
using System.IO.Pipes;
using System.Text;

namespace Bitling.Native;

sealed class SingleInstance : IDisposable
{
    private const string MutexName = "Global\\BitlingSingleInstance";
    private const string PipeName = "BitlingIpcPipe";

    private readonly Mutex _mutex;
    private CancellationTokenSource? _cts;

    public bool IsPrimaryInstance { get; }

    public SingleInstance()
    {
        _mutex = new Mutex(initiallyOwned: true, MutexName, out var createdNew);
        IsPrimaryInstance = createdNew;
    }

    /// Sends a single string (the bitling:// URL) to the already-running instance.
    /// Fire-and-forget with a short timeout: the caller is about to exit either way.
    public static void ForwardToRunningInstance(string payload)
    {
        try
        {
            using var client = new NamedPipeClientStream(".", PipeName, PipeDirection.Out);
            client.Connect(2000);
            var bytes = Encoding.UTF8.GetBytes(payload);
            client.Write(bytes, 0, bytes.Length);
            client.Flush();
        }
        catch { /* the other instance is gone or unreachable; nothing more to do */ }
    }

    /// Starts listening for forwarded URLs from future launches. `onReceived` runs on a
    /// background thread; marshal to the UI thread yourself.
    public void ListenForActivations(Action<string> onReceived)
    {
        _cts = new CancellationTokenSource();
        var token = _cts.Token;
        Task.Run(async () =>
        {
            while (!token.IsCancellationRequested)
            {
                try
                {
                    using var server = new NamedPipeServerStream(PipeName, PipeDirection.In, 1);
                    await server.WaitForConnectionAsync(token);
                    using var reader = new StreamReader(server, Encoding.UTF8);
                    var payload = await reader.ReadToEndAsync(token);
                    if (!string.IsNullOrEmpty(payload)) onReceived(payload);
                }
                catch (OperationCanceledException) { break; }
                catch { /* a broken client connection just means try again */ }
            }
        }, token);
    }

    public void Dispose()
    {
        _cts?.Cancel();
        if (IsPrimaryInstance) _mutex.ReleaseMutex();
        _mutex.Dispose();
    }
}
