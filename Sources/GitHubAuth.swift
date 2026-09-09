// GitHub sign-in for machines without the `gh` CLI installed, using OAuth's device flow:
// no client secret, no redirect server to host, just a one-time code the user enters at
// github.com/login/device. CIWatcher prefers `gh` when it is present and falls back to
// the token stored here.

import Foundation
import Security

enum GitHubAuth {
    /// From the "Bitling" OAuth App in GitHub's developer settings, with Device Flow
    /// enabled. Client IDs identify the app, not the user, so committing this is normal
    /// practice (this is how the `gh` CLI itself ships its own client id).
    private static let clientID = "Ov23liOLNPPnlqFLwSyE"

    struct DeviceCode {
        let deviceCode: String
        let userCode: String
        let verificationURI: URL
        let interval: TimeInterval
        let expiresAt: Date
    }

    enum AuthError: LocalizedError {
        case notConfigured
        case network(String)
        case denied
        case expired

        var errorDescription: String? {
            switch self {
            case .notConfigured: return "GitHub sign-in has not been set up in this build yet"
            case .network(let message): return message
            case .denied: return "GitHub sign-in was denied"
            case .expired: return "The GitHub sign-in code expired before it was approved"
            }
        }
    }

    // MARK: Keychain

    private static let service = "app.bitling.pet.github"
    private static let account = "token"

    private static func keychainQuery() -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
    }

    static func storedToken() -> String? {
        var query = keychainQuery()
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne
        var result: AnyObject?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(decoding: data, as: UTF8.self)
    }

    static func store(_ token: String) {
        SecItemDelete(keychainQuery() as CFDictionary)
        var attributes = keychainQuery()
        attributes[kSecValueData as String] = Data(token.utf8)
        attributes[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
        SecItemAdd(attributes as CFDictionary, nil)
    }

    static func signOut() {
        SecItemDelete(keychainQuery() as CFDictionary)
    }

    // MARK: Device flow
    // https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow

    /// Blocking network call; device-code requests return in well under a second, and every
    /// other synchronous git/gh call in this app already blocks its caller the same way.
    static func requestDeviceCode() throws -> DeviceCode {
        guard !clientID.isEmpty else { throw AuthError.notConfigured }
        let reply = try post(url: URL(string: "https://github.com/login/device/code")!,
                              body: "client_id=\(clientID)&scope=repo")
        guard let deviceCode = reply["device_code"] as? String,
              let userCode = reply["user_code"] as? String,
              let verificationString = reply["verification_uri"] as? String,
              let verificationURI = URL(string: verificationString),
              let interval = reply["interval"] as? Double,
              let expiresIn = reply["expires_in"] as? Double else {
            throw AuthError.network("GitHub did not return a device code")
        }
        return DeviceCode(deviceCode: deviceCode, userCode: userCode, verificationURI: verificationURI,
                           interval: interval, expiresAt: Date().addingTimeInterval(expiresIn))
    }

    /// Polls until the user approves or denies the code, or it expires. Call this off the
    /// main thread: it sleeps between polls for as long as the user takes to approve.
    static func pollForToken(_ code: DeviceCode) throws -> String {
        var interval = code.interval
        while Date() < code.expiresAt {
            Thread.sleep(forTimeInterval: interval)
            let reply = try post(url: URL(string: "https://github.com/login/oauth/access_token")!,
                                  body: "client_id=\(clientID)&device_code=\(code.deviceCode)"
                                      + "&grant_type=urn:ietf:params:oauth:grant-type:device_code")
            if let token = reply["access_token"] as? String { return token }
            switch reply["error"] as? String {
            case "authorization_pending": continue
            case "slow_down": interval += 5; continue
            case "access_denied": throw AuthError.denied
            case "expired_token": throw AuthError.expired
            default: throw AuthError.network(reply["error_description"] as? String ?? "GitHub sign-in failed")
            }
        }
        throw AuthError.expired
    }

    static func fetchLogin(token: String) -> String? {
        guard let data = try? get(url: URL(string: "https://api.github.com/user")!, token: token),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return nil }
        return json["login"] as? String
    }

    // MARK: HTTP

    static func get(url: URL, token: String) throws -> Data {
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        return try syncData(request: request)
    }

    private static func post(url: URL, body: String) throws -> [String: Any] {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.httpBody = Data(body.utf8)
        let data = try syncData(request: request)
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw AuthError.network("GitHub returned an unreadable response")
        }
        return json
    }

    private static func syncData(request: URLRequest) throws -> Data {
        let semaphore = DispatchSemaphore(value: 0)
        var result: Result<Data, Error> = .failure(AuthError.network("no response from GitHub"))
        URLSession.shared.dataTask(with: request) { data, _, error in
            if let error {
                result = .failure(AuthError.network(error.localizedDescription))
            } else if let data {
                result = .success(data)
            }
            semaphore.signal()
        }.resume()
        semaphore.wait()
        return try result.get()
    }
}
