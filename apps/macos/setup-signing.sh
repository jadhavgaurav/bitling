#!/bin/zsh
# Creates a stable local code-signing identity for development builds.
#
# Why: an ad hoc signature identifies the app to macOS by the hash of its exact binary, so
# every rebuild looks like a brand new app and macOS asks again for every folder permission
# (Desktop, Documents, Downloads) and every keychain approval. Signing with one certificate
# gives the app an identity that survives rebuilds, so each question is asked once.
#
# This is for your own builds on this Mac. The certificate is self-signed and trusted by
# nothing else, and release.sh never uses it.
#
#   ./setup-signing.sh            create the identity (safe to run again)
#   ./setup-signing.sh --remove   delete it
#
# Everything lives in ~/.bitling-signing: a dedicated keychain, so your login keychain and
# keychain search list are left alone, plus a file holding that keychain's random password
# (mode 600) so build.sh can unlock it without asking.
set -euo pipefail

DIR="$HOME/.bitling-signing"
KEYCHAIN="$DIR/bitling-signing.keychain-db"
PASS_FILE="$DIR/keychain-password"
NAME="Bitling Local Signing"

if [[ "${1:-}" == "--remove" ]]; then
  [[ -f "$KEYCHAIN" ]] && security delete-keychain "$KEYCHAIN" || true
  rm -rf "$DIR"
  echo "removed the local signing identity"
  exit 0
fi

if [[ -f "$KEYCHAIN" && -f "$PASS_FILE" ]] \
   && security unlock-keychain -p "$(<"$PASS_FILE")" "$KEYCHAIN" 2>/dev/null \
   && security find-identity -p codesigning "$KEYCHAIN" | grep -q "$NAME"; then
  echo "already set up: \"$NAME\" in $KEYCHAIN"
  exit 0
fi

mkdir -p "$DIR"
chmod 700 "$DIR"
[[ -f "$KEYCHAIN" ]] && security delete-keychain "$KEYCHAIN" 2>/dev/null || true
umask 077
# The system openssl on purpose: a Homebrew OpenSSL 3 writes PKCS12 files that the macOS
# keychain importer rejects with "MAC verification failed".
/usr/bin/openssl rand -hex 24 > "$PASS_FILE"
PASS="$(<"$PASS_FILE")"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cat > "$WORK/openssl.cnf" <<CNF
[req]
distinguished_name = dn
x509_extensions = ext
prompt = no
[dn]
CN = $NAME
[ext]
basicConstraints = critical,CA:false
keyUsage = critical,digitalSignature
extendedKeyUsage = critical,codeSigning
CNF

/usr/bin/openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -config "$WORK/openssl.cnf" \
  -keyout "$WORK/key.pem" -out "$WORK/cert.pem" 2>/dev/null
/usr/bin/openssl pkcs12 -export -inkey "$WORK/key.pem" -in "$WORK/cert.pem" \
  -out "$WORK/identity.p12" -passout "pass:$PASS"

security create-keychain -p "$PASS" "$KEYCHAIN"
security set-keychain-settings "$KEYCHAIN"            # never auto-lock
security unlock-keychain -p "$PASS" "$KEYCHAIN"
security import "$WORK/identity.p12" -k "$KEYCHAIN" -P "$PASS" -T /usr/bin/codesign >/dev/null
# Lets codesign use the key without a dialog on every build.
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$PASS" "$KEYCHAIN" >/dev/null

security find-identity -p codesigning "$KEYCHAIN" | grep "$NAME" >/dev/null \
  || { echo "the identity was not created" >&2; exit 1; }
echo "created \"$NAME\" in $KEYCHAIN"
echo "build.sh will now sign with it. macOS asks about folder access once more for the"
echo "first build signed this way, and not again on later rebuilds."
