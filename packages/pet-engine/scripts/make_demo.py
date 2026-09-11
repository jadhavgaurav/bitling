#!/usr/bin/env python3
"""Wrap the shared creature page into a standalone demo page.

Defaults to docs/demo.html (the GitHub Pages demo); pass --out to write it
somewhere else, e.g. apps/web's prebuild step writes apps/web/public/demo.html.
"""
from pathlib import Path
import argparse
import base64

ROOT = Path(__file__).resolve().parent.parent.parent.parent
MACOS = ROOT / "apps" / "macos"
body = (MACOS / "web" / "bitling.html").read_text(encoding="utf-8")
for filename in ("shenron.png", "shenron-head.png", "shenron-body.png", "shenron-limb.png"):
    sprite = "data:image/png;base64," + base64.b64encode((MACOS / "web/assets" / filename).read_bytes()).decode("ascii")
    body = body.replace(f"assets/{filename}", sprite)

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Bitling: a desktop pet for macOS that reacts to your commits, tests, deploys and Claude Code sessions. Try the creature in your browser.">
<meta property="og:title" content="Bitling">
<meta property="og:description" content="A desktop pet for macOS that lives on your dev activity. Try it in your browser.">
<meta property="og:image" content="https://jadhavgaurav.github.io/bitling/media/hero.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>🤖</text></svg>">
<style>body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
<script>window.__demoControls = true;</script>
{body}
</body>
</html>
"""
parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path, default=ROOT / "docs" / "demo.html")
args = parser.parse_args()
out = args.out if args.out.is_absolute() else Path.cwd() / args.out
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(page, encoding="utf-8")
print(f"wrote {out} ({len(page)} bytes)")
