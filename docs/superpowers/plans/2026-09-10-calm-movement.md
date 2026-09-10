# Calm pet movement implementation plan

Goal: all ten pets remain pleasant peripheral companions, with long uninterrupted rests and occasional short purposeful relocations.

Architecture: one shared ambient rest/travel policy in web/bitling.html. Keep interaction and event movement separate. Swift owns compact-window travel; Shenron owns full-screen body travel. Generated pages come from the existing generators.

Decisions: slowing perpetual motion would still distract; disabling all autonomous life would lose character. Use 120 seconds of rest (180 for Rumble, 150 for Shenron), at most eight seconds of nearby travel, then a full rest measured from arrival. Retain facing until a boundary requires turning. No spontaneous ground-pet flights. Suppress autonomous travel during care, work, sleep, attacks and reduced motion. Dragging and species changes restart rest. Idle expressions every 25–40 seconds; no idle speech spam. Ronaldo only kicks on actual walking contact or explicit play/attack. Floating hover has a fixed screen anchor.

- [x] Add generated-page browser tests for every species: initial rest, bounded trip, full rest after arrival, hover expiration, dragging, species changes, activity and reduced-motion suppression. Run and observe failures.
- [x] Add shared rest/travel helpers and quiet idle expressions. Connect landing/release/host arrival to rest. Remove automatic random takeoff and floater redirection.
- [x] Apply bounded ambient travel to Shenron; remove his independent random target loop. Remove Ronaldo's independent play timer and require walking for dribble contact. Keep species art and event actions.
- [x] Implement relative compact-window float travel and stationary native hover. Generate desktop/demo pages through tools.
- [x] Run lint, all tests, bubble-gap measurement, npm build and universal installed build. Review changes against the saved initial dirty files; update graphify.

Species audit: Bitling, Pikachu, Rumble, Naruto, Mario and CR7 use shared ground travel; Goku, Iron Man and Nimbo use shared hover travel; Shenron uses shared scheduling with his spine animation. Goku form transitions, Mario power-ups, all attacks, feeding and Git event responses stay event-driven.

Validation: JavaScript lint and repository Ruff passed; all 24 Node tests passed, including generator/browser/native coverage. All ten bubble gaps are within 8–24 px. Native and universal builds passed and the universal app was installed. Pytest collected no tests: this repository uses the Node suite for its generator. Native stationary hover and dropped-floater probes passed. Graphify updated. Existing asset-tool lint failures were repaired with minimal import/format fixes; Pikachu verification now accesses the page closure correctly.
