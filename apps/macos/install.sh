#!/bin/bash
# Installs the latest Bitling release into /Applications.
#
#   curl -fsSL https://raw.githubusercontent.com/jadhavgaurav/bitling/main/install.sh | bash
#
# Bitling is signed ad hoc rather than with a paid Apple Developer ID, so macOS quarantines
# it when you download it and then refuses to open it. Because you ran this script yourself,
# it clears that quarantine flag for you and you never see the warning.
set -euo pipefail

REPO="jadhavgaurav/bitling"
APP="/Applications/Bitling.app"

echo "==> Looking up the latest release"
URL="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
  | grep -o 'https://[^"]*\.dmg' | head -1)"
if [ -z "$URL" ]; then
  echo "Could not find a .dmg in the latest release of $REPO" >&2
  exit 1
fi

TMP="$(mktemp -d)"
MOUNT=""
cleanup() {
  [ -n "$MOUNT" ] && hdiutil detach "$MOUNT" -quiet 2>/dev/null || true
  rm -rf "$TMP"
}
trap cleanup EXIT

echo "==> Downloading $(basename "$URL")"
curl -fL --progress-bar "$URL" -o "$TMP/Bitling.dmg"

echo "==> Mounting the disk image"
MOUNT="$(hdiutil attach "$TMP/Bitling.dmg" -nobrowse -readonly | tail -1 | sed 's/.*\(\/Volumes\/.*\)/\1/')"
if [ ! -d "$MOUNT/Bitling.app" ]; then
  echo "That disk image does not contain Bitling.app" >&2
  exit 1
fi

if pgrep -x Bitling >/dev/null 2>&1; then
  echo "==> Quitting the running copy"
  osascript -e 'tell application "Bitling" to quit' >/dev/null 2>&1 || true
  sleep 1
fi

echo "==> Installing to $APP"
rm -rf "$APP"
cp -R "$MOUNT/Bitling.app" "$APP"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

if [ -d /usr/local/bin ] && [ -w /usr/local/bin ]; then
  ln -sf "$APP/Contents/Resources/bitling" /usr/local/bin/bitling
  echo "==> Linked the bitling command"
else
  echo "==> To get the bitling command too, run:"
  echo "    sudo ln -sf \"$APP/Contents/Resources/bitling\" /usr/local/bin/bitling"
fi

open "$APP"
echo
echo "Bitling is running. It has no Dock icon: look for the face in your menu bar."
