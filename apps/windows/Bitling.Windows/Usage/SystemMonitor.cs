// Whole-machine CPU and memory use, sampled once a second. Ported from
// apps/macos/Sources/SystemMonitor.swift; uses the same two Win32 calls Task Manager's
// numbers come from.
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;

namespace Bitling.Usage;

public sealed class SystemMonitor : IDisposable
{
    /// <param name="Cpu">Share of CPU time spent busy since the previous sample, 0 to 100. Null until there is a baseline.</param>
    /// <param name="Memory">Share of physical memory in use, 0 to 100.</param>
    public readonly record struct Sample(double? Cpu, double? Memory);

    /// <summary>Raised on a timer thread.</summary>
    public event Action<Sample>? Sampled;

    private System.Threading.Timer? _timer;
    private ulong _previousBusy, _previousTotal;
    private bool _hasBaseline;

    public void Start(TimeSpan? interval = null)
    {
        if (_timer is not null) return;
        var period = interval ?? TimeSpan.FromSeconds(1);
        _timer = new System.Threading.Timer(_ => Tick(), null, TimeSpan.Zero, period);
    }

    public void Stop()
    {
        _timer?.Dispose();
        _timer = null;
        _hasBaseline = false;
    }

    public void Dispose() => Stop();

    private void Tick()
    {
        try { Sampled?.Invoke(new Sample(CpuPercent(), MemoryPercent())); }
        catch { /* a failed sample must not stop the timer */ }
    }

    private double? CpuPercent()
    {
        if (!GetSystemTimes(out var idle, out var kernel, out var user)) return null;
        // Kernel time already includes idle time.
        var idleTicks = ToTicks(idle);
        var total = ToTicks(kernel) + ToTicks(user);
        var busy = total - idleTicks;
        double? percent = null;
        if (_hasBaseline && total > _previousTotal)
            percent = Math.Clamp((double)(busy - _previousBusy) / (total - _previousTotal) * 100, 0, 100);
        _previousBusy = busy;
        _previousTotal = total;
        _hasBaseline = true;
        return percent;
    }

    private static double? MemoryPercent()
    {
        var status = new MemoryStatusEx { Length = (uint)Marshal.SizeOf<MemoryStatusEx>() };
        if (!GlobalMemoryStatusEx(ref status) || status.TotalPhys == 0) return null;
        return Math.Clamp((double)(status.TotalPhys - status.AvailPhys) / status.TotalPhys * 100, 0, 100);
    }

    private static ulong ToTicks(FILETIME time) => ((ulong)(uint)time.dwHighDateTime << 32) | (uint)time.dwLowDateTime;

    [StructLayout(LayoutKind.Sequential)]
    private struct MemoryStatusEx
    {
        public uint Length;
        public uint MemoryLoad;
        public ulong TotalPhys;
        public ulong AvailPhys;
        public ulong TotalPageFile;
        public ulong AvailPageFile;
        public ulong TotalVirtual;
        public ulong AvailVirtual;
        public ulong AvailExtendedVirtual;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetSystemTimes(out FILETIME idle, out FILETIME kernel, out FILETIME user);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GlobalMemoryStatusEx(ref MemoryStatusEx status);
}
