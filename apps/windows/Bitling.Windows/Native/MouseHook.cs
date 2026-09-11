// WebView2 hosts a real Chromium child HWND, so WPF's own Preview* mouse routed events
// do not reliably see input while the cursor is over the pet's WebView2 control (a known
// WPF+WebView2 limitation, not specific to this app). PetWindow.swift's sendEvent()
// override taps NSEvent at the window level for exactly the same reason: to detect
// "drag the window" vs. "let the page handle the click" without owning every pixel.
// The Windows equivalent is a low-level mouse hook (WH_MOUSE_LL), which sees every mouse
// event system-wide before any window's own message loop does.
//
// NEEDS VERIFICATION ON REAL HARDWARE: low-level hooks are timing-sensitive (a slow
// callback gets silently unhooked by Windows) and this has not been exercised outside
// this write-up.
using System.Runtime.InteropServices;

namespace Bitling.Native;

sealed class MouseHook : IDisposable
{
    private const int WH_MOUSE_LL = 14;
    private const int WM_LBUTTONDOWN = 0x0201;
    private const int WM_LBUTTONUP = 0x0202;
    private const int WM_MOUSEMOVE = 0x0200;
    private const int WM_RBUTTONDOWN = 0x0204;

    [StructLayout(LayoutKind.Sequential)]
    private struct POINT { public int X; public int Y; }

    [StructLayout(LayoutKind.Sequential)]
    private struct MSLLHOOKSTRUCT
    {
        public POINT pt;
        public uint mouseData;
        public uint flags;
        public uint time;
        public IntPtr dwExtraInfo;
    }

    private delegate IntPtr HookProc(int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook, HookProc lpfn, IntPtr hMod, uint dwThreadId);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);

    [DllImport("user32.dll")]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

    public event Action<System.Windows.Point>? LeftButtonDown;
    public event Action<System.Windows.Point>? MouseMove;
    public event Action<System.Windows.Point>? LeftButtonUp;
    public event Action<System.Windows.Point>? RightButtonDown;

    private readonly HookProc _proc;
    private IntPtr _hookId = IntPtr.Zero;

    public MouseHook()
    {
        _proc = HookCallback; // keep the delegate alive for the hook's lifetime
    }

    public void Install()
    {
        if (_hookId != IntPtr.Zero) return;
        using var process = System.Diagnostics.Process.GetCurrentProcess();
        using var module = process.MainModule!;
        _hookId = SetWindowsHookEx(WH_MOUSE_LL, _proc, Marshal.GetHINSTANCE(typeof(MouseHook).Module), 0);
    }

    private IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0)
        {
            var data = Marshal.PtrToStructure<MSLLHOOKSTRUCT>(lParam);
            var point = new System.Windows.Point(data.pt.X, data.pt.Y);
            switch ((int)wParam)
            {
                case WM_LBUTTONDOWN: LeftButtonDown?.Invoke(point); break;
                case WM_MOUSEMOVE: MouseMove?.Invoke(point); break;
                case WM_LBUTTONUP: LeftButtonUp?.Invoke(point); break;
                case WM_RBUTTONDOWN: RightButtonDown?.Invoke(point); break;
            }
        }
        return CallNextHookEx(_hookId, nCode, wParam, lParam);
    }

    public void Dispose()
    {
        if (_hookId != IntPtr.Zero) { UnhookWindowsHookEx(_hookId); _hookId = IntPtr.Zero; }
    }
}
