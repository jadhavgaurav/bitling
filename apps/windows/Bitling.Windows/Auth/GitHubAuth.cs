// GitHub sign-in for machines without the `gh` CLI installed, using OAuth's device flow:
// no client secret, no redirect server to host, just a one-time code the user enters at
// github.com/login/device. CIWatcher prefers `gh` when it is present and falls back to
// the token stored here.
//
// Ported from apps/macos/Sources/GitHubAuth.swift. The Keychain is replaced by Windows
// Credential Manager (CredWrite/CredRead/CredDelete) as the equivalent secure, per-user
// store; the device-flow HTTP logic is unchanged.
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json.Nodes;

namespace Bitling.Auth;

public static class GitHubAuth
{
    /// From the same "Bitling" OAuth App used by the macOS build, with Device Flow enabled.
    /// Client IDs identify the app, not the user, so committing this is normal practice
    /// (this is how the `gh` CLI itself ships its own client id).
    private const string ClientId = "Ov23liOLNPPnlqFLwSyE";
    private static readonly HttpClient Http = new();

    public sealed record DeviceCode(string DeviceCodeValue, string UserCode, Uri VerificationUri, double Interval, DateTime ExpiresAt);

    public sealed class AuthException : Exception
    {
        public AuthException(string message) : base(message) { }
    }

    // MARK: Windows Credential Manager

    private const string TargetName = "app.bitling.pet.github";

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct CREDENTIAL
    {
        public int Flags;
        public int Type;
        public string TargetName;
        public string Comment;
        public long LastWritten;
        public int CredentialBlobSize;
        public IntPtr CredentialBlob;
        public int Persist;
        public int AttributeCount;
        public IntPtr Attributes;
        public string TargetAlias;
        public string UserName;
    }

    private const int CRED_TYPE_GENERIC = 1;
    private const int CRED_PERSIST_LOCAL_MACHINE = 2;

    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredWrite(ref CREDENTIAL credential, int flags);

    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredRead(string target, int type, int flags, out IntPtr credential);

    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredDelete(string target, int type, int flags);

    [DllImport("advapi32.dll")]
    private static extern void CredFree(IntPtr buffer);

    public static string? StoredToken()
    {
        if (!CredRead(TargetName, CRED_TYPE_GENERIC, 0, out var ptr)) return null;
        try
        {
            var cred = Marshal.PtrToStructure<CREDENTIAL>(ptr);
            if (cred.CredentialBlobSize == 0) return null;
            var bytes = new byte[cred.CredentialBlobSize];
            Marshal.Copy(cred.CredentialBlob, bytes, 0, bytes.Length);
            return Encoding.Unicode.GetString(bytes);
        }
        finally { CredFree(ptr); }
    }

    public static void Store(string token)
    {
        var bytes = Encoding.Unicode.GetBytes(token);
        var blob = Marshal.AllocHGlobal(bytes.Length);
        try
        {
            Marshal.Copy(bytes, 0, blob, bytes.Length);
            var cred = new CREDENTIAL
            {
                Type = CRED_TYPE_GENERIC,
                TargetName = TargetName,
                CredentialBlobSize = bytes.Length,
                CredentialBlob = blob,
                Persist = CRED_PERSIST_LOCAL_MACHINE,
                UserName = "token",
            };
            CredWrite(ref cred, 0);
        }
        finally { Marshal.FreeHGlobal(blob); }
    }

    public static void SignOut() => CredDelete(TargetName, CRED_TYPE_GENERIC, 0);

    // MARK: Device flow
    // https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow

    public static async Task<DeviceCode> RequestDeviceCodeAsync()
    {
        var reply = await PostAsync(new Uri("https://github.com/login/device/code"), $"client_id={ClientId}&scope=repo");
        var deviceCode = reply["device_code"]?.GetValue<string>();
        var userCode = reply["user_code"]?.GetValue<string>();
        var verification = reply["verification_uri"]?.GetValue<string>();
        var interval = reply["interval"]?.GetValue<double>();
        var expiresIn = reply["expires_in"]?.GetValue<double>();
        if (deviceCode is null || userCode is null || verification is null || interval is null || expiresIn is null)
            throw new AuthException("GitHub did not return a device code");
        return new DeviceCode(deviceCode, userCode, new Uri(verification), interval.Value, DateTime.UtcNow.AddSeconds(expiresIn.Value));
    }

    /// Polls until the user approves or denies the code, or it expires. Sleeps between
    /// polls for as long as the user takes to approve, so run this off the UI thread.
    public static async Task<string> PollForTokenAsync(DeviceCode code)
    {
        var interval = code.Interval;
        while (DateTime.UtcNow < code.ExpiresAt)
        {
            await Task.Delay(TimeSpan.FromSeconds(interval));
            var reply = await PostAsync(new Uri("https://github.com/login/oauth/access_token"),
                $"client_id={ClientId}&device_code={code.DeviceCodeValue}&grant_type=urn:ietf:params:oauth:grant-type:device_code");
            var token = reply["access_token"]?.GetValue<string>();
            if (token != null) return token;
            switch (reply["error"]?.GetValue<string>())
            {
                case "authorization_pending": continue;
                case "slow_down": interval += 5; continue;
                case "access_denied": throw new AuthException("GitHub sign-in was denied");
                case "expired_token": throw new AuthException("The GitHub sign-in code expired before it was approved");
                default: throw new AuthException(reply["error_description"]?.GetValue<string>() ?? "GitHub sign-in failed");
            }
        }
        throw new AuthException("The GitHub sign-in code expired before it was approved");
    }

    public static string? FetchLogin(string token)
    {
        try
        {
            var data = Get(new Uri("https://api.github.com/user"), token);
            var json = JsonNode.Parse(data) as JsonObject;
            return json?["login"]?.GetValue<string>();
        }
        catch { return null; }
    }

    // MARK: HTTP

    public static byte[] Get(Uri url, string token)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, url);
        request.Headers.Add("Authorization", $"Bearer {token}");
        request.Headers.Add("Accept", "application/vnd.github+json");
        request.Headers.Add("User-Agent", "Bitling");
        using var response = Http.Send(request);
        response.EnsureSuccessStatusCode();
        return response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult();
    }

    private static async Task<JsonObject> PostAsync(Uri url, string body)
    {
        using var request = new HttpRequestMessage(HttpMethod.Post, url)
        {
            Content = new StringContent(body, Encoding.UTF8, "application/x-www-form-urlencoded"),
        };
        request.Headers.Add("Accept", "application/json");
        request.Headers.Add("User-Agent", "Bitling");
        try
        {
            using var response = await Http.SendAsync(request);
            var data = await response.Content.ReadAsByteArrayAsync();
            return JsonNode.Parse(data) as JsonObject ?? throw new AuthException("GitHub returned an unreadable response");
        }
        catch (HttpRequestException ex) { throw new AuthException(ex.Message); }
    }
}
