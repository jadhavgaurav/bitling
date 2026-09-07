#!/bin/zsh
# Builds Bitling.app from source and installs it.
#   ./build.sh                 -> build and install to /Applications
#   ./build.sh ~/Applications  -> build and install somewhere else
#   INSTALL=0 ./build.sh       -> build only (result in build/Bitling.app)
set -euo pipefail
cd "$(dirname "$0")"

WEB_SOURCE="${WEB_SOURCE:-web/bitling.html}"
APP=build/Bitling.app
ARCH="$(uname -m)"

rm -rf build
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

echo "→ deriving desktop page from $WEB_SOURCE"
python3 Tools/make_pet_html.py "$WEB_SOURCE" Resources/pet.html

echo "→ compiling host app ($ARCH)"
swiftc -O -swift-version 5 -target "$ARCH-apple-macosx13.0" \
  -framework Cocoa -framework WebKit -framework ServiceManagement \
  -o "$APP/Contents/MacOS/Bitling" Sources/main.swift Sources/GitWatcher.swift Sources/CIWatcher.swift Sources/ClaudeWatcher.swift

echo "→ drawing icon"
swiftc -O -swift-version 5 -framework Cocoa -o build/makeicon Tools/makeicon.swift
build/makeicon build/Bitling.iconset >/dev/null
iconutil -c icns build/Bitling.iconset -o "$APP/Contents/Resources/Bitling.icns"

cp Resources/pet.html "$APP/Contents/Resources/pet.html"
cp Resources/Info.plist "$APP/Contents/Info.plist"
cp Resources/bitling "$APP/Contents/Resources/bitling"
chmod +x "$APP/Contents/Resources/bitling"
printf 'APPL????' > "$APP/Contents/PkgInfo"

echo "→ signing (ad hoc)"
codesign --force --deep --sign - "$APP" >/dev/null

if [[ "${INSTALL:-1}" == "0" ]]; then
  echo "built $APP"
  exit 0
fi

DEST="${1:-/Applications}"
echo "→ installing to $DEST/Bitling.app"
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
  echo "to use the CLI: ln -s \"$DEST/Bitling.app/Contents/Resources/bitling\" /usr/local/bin/bitling"
fi
