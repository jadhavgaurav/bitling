#!/bin/zsh
# Packages Bitling.app into a drag-to-install disk image.
#   ./release.sh            -> build/Bitling-<version>.dmg
#   ./release.sh --publish  -> also create the matching GitHub release and upload it
#
# Set SIGN_ID (and NOTARY_PROFILE, for a notarytool keychain profile) to produce a
# build that opens without the Gatekeeper warning. Without them the DMG still works,
# but the first launch needs Open Anyway.
set -euo pipefail
cd "$(dirname "$0")"

VERSION="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' Resources/Info.plist)"
DMG="build/Bitling-$VERSION.dmg"
STAGE=build/dmg

INSTALL=0 ./build.sh

echo "-> staging disk image"
rm -rf "$STAGE" "$DMG"
mkdir -p "$STAGE"
cp -R build/Bitling.app "$STAGE/Bitling.app"
ln -s /Applications "$STAGE/Applications"
cat > "$STAGE/Read me first.txt" <<'TXT'
Bitling

1. Drag Bitling to the Applications folder.
2. Open it from Applications.

macOS will say the app "cannot be opened because Apple cannot check it for
malicious software". That is because this build is not signed with a paid Apple
Developer ID, not because anything is wrong with it. To open it anyway:

  System Settings -> Privacy & Security -> scroll down -> Open Anyway

or, in Terminal:

  xattr -dr com.apple.quarantine /Applications/Bitling.app

Bitling has no Dock icon. Look for the smiling face in the menu bar.
Source: https://github.com/jadhavgaurav/bitling
TXT

hdiutil create -quiet -volname "Bitling $VERSION" -srcfolder "$STAGE" -ov -format ULFO "$DMG"
rm -rf "$STAGE"

if [[ -n "${SIGN_ID:-}" ]]; then
  codesign --force --sign "$SIGN_ID" "$DMG"
  if [[ -n "${NOTARY_PROFILE:-}" ]]; then
    echo "-> notarizing (this takes a few minutes)"
    xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY_PROFILE" --wait
    xcrun stapler staple "$DMG"
  fi
fi

echo "-> $DMG"
shasum -a 256 "$DMG"

if [[ "${1:-}" == "--publish" ]]; then
  TAG="v$VERSION"
  echo "-> creating GitHub release $TAG"
  git tag -f "$TAG"
  git push -f origin "$TAG"
  gh release create "$TAG" "$DMG" \
    --title "Bitling $VERSION" \
    --notes-file .github/RELEASE_NOTES.md
  gh release view "$TAG" --json url -q .url
fi
