# @bitling/pet-engine

The build tooling shared by the macOS app and the website: both derive their copy of the
creature from `apps/macos/web/bitling.html` through the scripts here.

- `scripts/make_pet_html.py` — string-patches the shared page into desktop mode (transparent
  background, native bridge, host-driven drag) for `apps/macos/Resources/pet.html`.
- `scripts/make_demo.py` — wraps the same page into a standalone demo page. Defaults to
  `docs/demo.html` (the GitHub Pages demo); `apps/web` calls it with `--out public/demo.html`
  as a `predev`/`prebuild` step so the Next.js site's simulator iframe always embeds the
  current engine.

## Scope note

The engine's source, `apps/macos/web/bitling.html`, stays a single hand-edited file for now
rather than being split into `src/species/*.js` modules as originally sketched. Two things
about this repo made that call: `AGENTS.md` documents several past regressions (`reach`,
`half`, speech-bubble clearance) that were invisible from reading the code and only caught by
rendering the actual page, and the same file is the live, concurrently-edited surface for
every agent working in this repo — turning it into a generated build artifact out of a set of
new source modules would change how everyone edits it mid-flight, not just where it lives.
Extracting the *build tooling* into this package (this step) was safe and mechanical; hand-
splitting ~10,000 lines of tightly coupled canvas/physics code across 12 species without being
able to fully re-verify every one visually was not, and is left as a deliberate follow-up
scoped and done one species at a time, each re-checked with `node tools/check_bubble_gap.mjs`
and its test file before moving to the next.
