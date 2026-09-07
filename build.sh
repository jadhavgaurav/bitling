#!/bin/zsh
# Builds Jellykin.app from source and installs it.
#   ./build.sh                 -> build and install to /Applications
#   ./build.sh ~/Applications  -> build and install somewhere else
#   INSTALL=0 ./build.sh       -> build only (result in build/Jellykin.app)
set -euo pipefail
cd "$(dirname "$0")"

WEB_SOURCE="${WEB_SOURCE:-web/jellykin.html}"
APP=build/Jellykin.app
ARCH="$(uname -m)"

rm -rf build
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

echo "→ deriving desktop page from $WEB_SOURCE"
python3 Tools/make_pet_html.py "$WEB_SOURCE" Resources/pet.html

echo "→ compiling host app ($ARCH)"
swiftc -O -swift-version 5 -target "$ARCH-apple-macosx13.0" \
  -framework Cocoa -framework WebKit -framework ServiceManagement \
  -o "$APP/Contents/MacOS/Jellykin" Sources/main.swift Sources/GitWatcher.swift

echo "→ drawing icon"
swiftc -O -swift-version 5 -framework Cocoa -o build/makeicon Tools/makeicon.swift
build/makeicon build/Jellykin.iconset >/dev/null
iconutil -c icns build/Jellykin.iconset -o "$APP/Contents/Resources/Jellykin.icns"

cp Resources/pet.html "$APP/Contents/Resources/pet.html"
cp Resources/Info.plist "$APP/Contents/Info.plist"
printf 'APPL????' > "$APP/Contents/PkgInfo"

echo "→ signing (ad hoc)"
codesign --force --deep --sign - "$APP" >/dev/null

if [[ "${INSTALL:-1}" == "0" ]]; then
  echo "built $APP"
  exit 0
fi

DEST="${1:-/Applications}"
echo "→ installing to $DEST/Jellykin.app"
if pgrep -x Jellykin >/dev/null; then
  osascript -e 'tell application "Jellykin" to quit' >/dev/null 2>&1 || true
  sleep 1
fi
rm -rf "$DEST/Jellykin.app"
cp -R "$APP" "$DEST/Jellykin.app"
echo "installed $DEST/Jellykin.app"
