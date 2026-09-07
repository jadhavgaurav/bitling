#!/bin/zsh
# Builds Bitling.app from source and installs it.
#   ./build.sh                 -> build and install to /Applications
#   ./build.sh ~/Applications  -> build and install somewhere else
#   INSTALL=0 ./build.sh       -> build only (result in build/Bitling.app)
#   NATIVE=1 ./build.sh        -> build only this Mac's architecture (faster, for development)
#
# The default build is a universal binary (Apple Silicon + Intel) so the app can be
# handed to anyone. Signing is ad hoc unless a Developer ID is available: set
# SIGN_ID="Developer ID Application: Your Name (TEAMID)" to sign properly.
set -euo pipefail
cd "$(dirname "$0")"

WEB_SOURCE="${WEB_SOURCE:-web/bitling.html}"
APP=build/Bitling.app
MIN_MACOS=13.0

rm -rf build
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

echo "-> deriving desktop page from $WEB_SOURCE"
python3 Tools/make_pet_html.py "$WEB_SOURCE" Resources/pet.html
python3 Tools/make_demo.py

SOURCES=(Sources/main.swift Sources/GitWatcher.swift Sources/CIWatcher.swift Sources/ClaudeWatcher.swift Sources/Overlay.swift)
compile() {  # compile <arch> <output>
  swiftc -O -swift-version 5 -target "$1-apple-macosx$MIN_MACOS" \
    -framework Cocoa -framework WebKit -framework ServiceManagement \
    -o "$2" "${SOURCES[@]}"
}

if [[ "${NATIVE:-0}" == "1" ]]; then
  echo "-> compiling host app ($(uname -m) only)"
  compile "$(uname -m)" "$APP/Contents/MacOS/Bitling"
else
  echo "-> compiling host app (arm64 + x86_64)"
  compile arm64 build/Bitling-arm64
  compile x86_64 build/Bitling-x86_64
  lipo -create build/Bitling-arm64 build/Bitling-x86_64 -output "$APP/Contents/MacOS/Bitling"
  rm -f build/Bitling-arm64 build/Bitling-x86_64
  echo "  architectures: $(lipo -archs "$APP/Contents/MacOS/Bitling")"
fi

echo "-> drawing icon"
swiftc -O -swift-version 5 -framework Cocoa -o build/makeicon Tools/makeicon.swift
build/makeicon build/Bitling.iconset >/dev/null
iconutil -c icns build/Bitling.iconset -o "$APP/Contents/Resources/Bitling.icns"

cp Resources/pet.html "$APP/Contents/Resources/pet.html"
cp Resources/Info.plist "$APP/Contents/Info.plist"
cp Resources/bitling "$APP/Contents/Resources/bitling"
chmod +x "$APP/Contents/Resources/bitling"
printf 'APPL????' > "$APP/Contents/PkgInfo"

if [[ -n "${SIGN_ID:-}" ]]; then
  echo "-> signing with $SIGN_ID"
  codesign --force --deep --options runtime --timestamp --sign "$SIGN_ID" "$APP"
else
  echo "-> signing (ad hoc: first launch on another Mac needs Open Anyway)"
  codesign --force --deep --sign - "$APP" >/dev/null
fi

if [[ "${INSTALL:-1}" == "0" ]]; then
  echo "built $APP"
  exit 0
fi

DEST="${1:-/Applications}"
echo "-> installing to $DEST/Bitling.app"
if pgrep -x Bitling >/dev/null; then
  osascript -e 'tell application "Bitling" to quit' >/dev/null 2>&1 || true
  sleep 1
fi
rm -rf "$DEST/Bitling.app"
cp -R "$APP" "$DEST/Bitling.app"
echo "installed $DEST/Bitling.app"
if [[ -d /usr/local/bin && -w /usr/local/bin ]]; then
  ln -sf "$DEST/Bitling.app/Contents/Resources/bitling" /usr/local/bin/bitling
  echo "linked /usr/local/bin/bitling"
else
  echo "to use the CLI: sudo ln -sf \"$DEST/Bitling.app/Contents/Resources/bitling\" /usr/local/bin/bitling"
fi
