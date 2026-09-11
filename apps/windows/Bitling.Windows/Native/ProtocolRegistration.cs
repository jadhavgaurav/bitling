// Registers the bitling:// URL scheme so the `bitling` CLI (and git/Claude hooks) can
// reach the running app, mirroring the CFBundleURLTypes entry in the macOS Info.plist.
// Written under HKEY_CURRENT_USER so no admin elevation is needed, same as the Run key
// used for launch-at-login.
using Microsoft.Win32;

namespace Bitling.Native;

static class ProtocolRegistration
{
    private const string SchemeKey = @"Software\Classes\bitling";

    public static void Register()
    {
        var exe = Environment.ProcessPath ?? System.Reflection.Assembly.GetExecutingAssembly().Location;
        using var root = Registry.CurrentUser.CreateSubKey(SchemeKey);
        root.SetValue("", "URL:Bitling events");
        root.SetValue("URL Protocol", "");
        using var icon = root.CreateSubKey(@"DefaultIcon");
        icon.SetValue("", $"\"{exe}\",0");
        using var command = root.CreateSubKey(@"shell\open\command");
        command.SetValue("", $"\"{exe}\" \"%1\"");
    }

    public static bool IsRegistered()
    {
        using var key = Registry.CurrentUser.OpenSubKey(SchemeKey + @"\shell\open\command", writable: false);
        var value = key?.GetValue("") as string;
        var exe = Environment.ProcessPath ?? System.Reflection.Assembly.GetExecutingAssembly().Location;
        return value != null && value.Contains(exe, StringComparison.OrdinalIgnoreCase);
    }
}
