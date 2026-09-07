#!/usr/bin/env python3
"""Wrap the shared creature page into docs/index.html for the GitHub Pages demo."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
body = (ROOT / "web" / "bitling.html").read_text(encoding="utf-8")

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
out = ROOT / "docs" / "index.html"
out.write_text(page, encoding="utf-8")
print(f"wrote {out} ({len(page)} bytes)")
