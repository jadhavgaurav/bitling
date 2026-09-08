# Godzilla reference and motion implementation plan

**Goal:** Replace Rumble's narrow dinosaur silhouette with an articulated Canvas drawing following the supplied Godzilla illustration, and make its movement carry weight.

**Architecture:** Keep `web/bitling.html` as the shared drawing source. Cache reference-coordinate paths, separate the tail, legs, torso, arms and jaw, and derive all movement from the existing pet state. The native host continues owning desktop travel. Preserve species switching and the existing event system.

**Reference audit:** The illustration uses charcoal gray (#60616b), deep slate shadows (#323644), taupe abdominal armor (#a09279), black contours, blue-edged cyan/white dorsal cores, an angular short skull, hanging clawed arms, wide columnar legs, and an upward-curled segmented tail. The current rendering has a thin profile, horizontal tail, rounded narrow legs, pale plates, pale eye with pupil, and orange fire. These are the primary mismatches.

**Motion:** Use a 62% grounded stance and 38% recovery. The foot moves opposite screen travel during stance; recovery lifts at most 0.12 radii. Offset the two feet by half a cycle to maintain support. Drive phase from traveled distance and match the host's slower kaiju speed. Use subtle shoulder settling and delayed tail sway; open the jaw and brighten dorsal cores on attacks. Use cyan atomic breath for attacks and the existing flight action.

**Implementation steps:**

- [x] Add gait regression tests and establish the failing baseline.
- [x] Replace the old artwork with cached articulated paths based on reference landmarks.
- [x] Synchronize walking cadence with screen travel; preserve feet contact, attack origin and desktop bounds.
- [x] Render idle, walking, charge, fire, held, sleeping and flight states in both directions; inspect at desktop size and enlarged.
- [x] Run npm lint, gait tests, browser verification and the native app build. Review the diff and generated desktop/demo pages.

**Acceptance limits:** A hand-traced animated drawing can closely match visible landmarks, but cannot truthfully be called pixel-identical to a raster illustration. A still image does not specify a canonical walk or unseen anatomy. Keep these limitations explicit in the result.

## Verification results

- `npm run lint`: passed for shared web scripts, panel and verification tools.
- `npm test`: all five tests passed. Gait stance, support and continuity were checked; 258 desktop frames covered both directions and all three growth sizes. Browser tests exercised the real generated host bridge, native walking, species changes, feeding and test-failure actions.
- Native Core Graphics probe: the actual attack style emitted substantial cyan pixels (the original orange `blaze` renderer failed this regression test).
- `npm run build`: derived desktop/demo pages, compiled the arm64 macOS app and signed it successfully.
- `git diff --check`: passed.
- Review fixed the native orange-fire path, the hovering-shadow regression, and inflated throw bounds.
- Visual inspection covered enlarged idle/fire/walk/sleep/held/flight captures and a live side-by-side comparison with the supplied reference.

The build is at `build/Bitling.app`; the installed app was not replaced. Separate concurrent edits to Goku's native attack renderer were preserved.
