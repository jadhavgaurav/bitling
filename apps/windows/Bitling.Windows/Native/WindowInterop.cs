// Win32 interop that WPF has no managed surface for: click-through (WS_EX_TRANSPARENT),
// and translating between WPF's device-independent window coordinates and the physical
// pixel rectangles Screen/monitor APIs use. NEEDS VERIFICATION ON REAL HARDWARE: the DPI
// math here is written to be correct for the common cases (100%/125%/150% scaling, single
// and multiple monitors) but has not been run on an actual multi-DPI Windows setup.
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;

namespace Bitling.Native;

static class WindowInterop
{
    private const int GWL_EXSTYLE = -20;
    private const int WS_EX_TRANSPARENT = 0x00000020;
    private const int WS_EX_LAYERED = 0x00080000;
    private const int WS_EX_TOOLWINDOW = 0x00000080; // keeps the borderless pet out of Alt+Tab

    [DllImport("user32.dll", SetLastError = true)]
    private static extern int GetWindowLong(IntPtr hWnd, int nIndex);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern int SetWindowLong(IntPtr hWnd, int nIndex, int dwNewLong);

    /// Toggles whether mouse input passes through the window to whatever is behind it.
    /// Mirrors NSWindow.ignoresMouseEvents: the page reports, via the "hover" bridge
    /// message, whether the cursor is over a drawn (non-transparent) pixel of the pet.
    public static void SetClickThrough(Window window, bool through)
    {
        var hwnd = new WindowInteropHelper(window).Handle;
        if (hwnd == IntPtr.Zero) return;
        var style = GetWindowLong(hwnd, GWL_EXSTYLE);
        var wanted = through ? (style | WS_EX_TRANSPARENT | WS_EX_LAYERED) : (style & ~WS_EX_TRANSPARENT);
        if (wanted != style) SetWindowLong(hwnd, GWL_EXSTYLE, wanted);
    }

    public static void HideFromAltTab(Window window)
    {
        var hwnd = new WindowInteropHelper(window).Handle;
        if (hwnd == IntPtr.Zero) return;
        var style = GetWindowLong(hwnd, GWL_EXSTYLE);
        SetWindowLong(hwnd, GWL_EXSTYLE, style | WS_EX_TOOLWINDOW | WS_EX_LAYERED);
    }

    /// The DPI scale factor (1.0 = 96 DPI = 100%) for the monitor a window is currently on.
    public static double DpiScale(Window window) => VisualTreeHelper.GetDpi(window).DpiScaleX;

    /// The work area (excludes the taskbar) of the monitor under a window, in that
    /// window's own device-independent units so it can be compared directly to
    /// window.Left/Top/Width/Height.
    public static Rect WorkAreaInDips(Window window)
    {
        var screen = System.Windows.Forms.Screen.FromHandle(new WindowInteropHelper(window).Handle);
        var scale = DpiScale(window);
        var wa = screen.WorkingArea;
        return new Rect(wa.X / scale, wa.Y / scale, wa.Width / scale, wa.Height / scale);
    }

    public static Rect WorkAreaUnderPoint(System.Windows.Point dipPoint, double scale)
    {
        var physical = new System.Drawing.Point((int)(dipPoint.X * scale), (int)(dipPoint.Y * scale));
        var screen = System.Windows.Forms.Screen.FromPoint(physical);
        var wa = screen.WorkingArea;
        return new Rect(wa.X / scale, wa.Y / scale, wa.Width / scale, wa.Height / scale);
    }

    public static System.Windows.Point CursorPositionDips(double scale)
    {
        var p = System.Windows.Forms.Cursor.Position;
        return new System.Windows.Point(p.X / scale, p.Y / scale);
    }
}
