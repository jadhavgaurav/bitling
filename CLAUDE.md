# Working on Bitling

One HTML canvas page (`web/bitling.html`) draws the creature. A Swift host renders it in a
borderless transparent window and supplies what a web page cannot do. `Resources/pet.html`
and `docs/index.html` are **generated** from that page by `Tools/make_pet_html.py` and
`Tools/make_demo.py`; never edit them by hand, your change will be overwritten on the next
build.

## Before you say it works

```bash
npm run lint                      # JavaScript in the pet page, the panel and the tools
npm test                          # species, rendering, walk cycle, host bridge
node Tools/check_bubble_gap.mjs   # speech bubble clearance for every pet
./build.sh                        # universal binary, installs to /Applications
```

**Watch for the launch race.** `build.sh` quits the app, writes the bundle, and only then is
it safe to reopen. Launching in the same second means the running app loaded the *previous*
`pet.html`, and your change will look like it did nothing. If something seems not to have
landed, compare these before debugging the code:

```bash
ps -o lstart= -p $(pgrep -x Bitling)
stat -f "%Sm" /Applications/Bitling.app/Contents/Resources/pet.html
```

## Adding a pet

A species owns its look, proportions, movement, voice and attack. Everything else, the
needs and growth and events and speech bubbles, is shared. Register it in `SPECIES` in
`web/bitling.html`.

```js
defineSpecies({
  id: 'newt', name: 'Newt', kind: 'ground',   // or 'float'
  blurb: 'One line for the picker.',
  accent: '#7ee7d7',
  radius: [46, 44, 52, 60],   // body radius per growth stage
  reach: () => 3.4,           // how far it draws ABOVE its feet, in radii
  half: (r) => r * 1.8,       // how far it reaches SIDEWAYS, in pixels
  draw: () => drawNewt(),
  trail: null,                // 'thruster' and 'flamejet' exist; most pets have none
  attack: { style: 'beam', charge: 0.3, origin: (r) => [...], draw(r, k) {...} },
  voice: { happy: [...], zapped: [...] },     // replaces any key of the shared script
});
```

**Every definition must run before the first `resize()`.** `resize()` asks the current
species whether it walks or floats. A species registered further down the file is still
unknown at that moment, and a floater will come up sized as a walker. Keep them together.

### `reach` and `half` are measured, never guessed

These two numbers are the whole contract between a drawing and the code around it. `reach`
places the speech bubble; `half` keeps the creature inside its window. Both have been wrong
on every pet at least once, and neither is visible from reading the code.

Run `node Tools/check_bubble_gap.mjs` after any change to a pet's art, proportions or
growth stages. It renders each species, shows it a short line and a long one, and compares
the topmost painted pixel with the bottom of the bubble's tail across a whole animation.
The gap must land between 8 and 24 pixels.

- Too small and the bubble sits on the creature's horns.
- Too large and it floats with an obvious hole underneath. Pets shipped with 39 and 45
  pixels of dead space because their `reach` was copied from a taller pet.

The gap moves by `r * delta-reach`, so a pet 20px too generous with a radius of 40 needs
0.5 taken off its `reach`. The tool prints the correction for you.

Two traps behind that number:

- **A floater can hit the ceiling.** Its bubble is clamped to stay on screen, so if the
  creature hangs too high the bubble is pushed back down onto its head and `reach` stops
  having any effect at all. Floaters rest at `H * 0.66` for this reason.
- **Sprite pets** have transparent padding. Measure the drawn pixels, not the sprite box.

### Anything derived from the art must be measured off the art

The kaiju's breath came out of the back of its skull for a while because the mouth was a
hard-coded constant that landed two thirds of the way back along the tooth row. The tooth
paths say where the teeth are: read them.

If a pose applies a rotation, **every** consumer of that pose must use the same rotation.
The same breath drifted off the head in flight because the body rotated by the pitch and
the mouth position did not. Put it in `kaijuPose()` so there is one source of truth.

### Voice

`line(key)` draws from a shuffle bag keyed by **species and phrase**. Keyed by phrase alone,
a bag filled while one pet was out keeps being drawn from after switching, and your kaiju
starts saying the electric mouse's lines.

### Movement

- A limb hinges. Rotate it about the joint and shorten it for the lift; translating the
  whole limb by the foot's offset drags the hip out of the body and reads as detached.
- A trail belongs to the species, not to flight mode. The robot has rockets; a floating
  pet that borrowed that code dripped burning fuel out of its underside for ever.
- `canFire` gates attacks on being grounded, which is right for a walker that flies off on
  errands and wrong for a floater, whose ground *is* hovering.

## Verifying without screen capture

Screen capture is blocked on this machine, so drive the page directly instead. `petNative`
exposes `advance(seconds)` to step the simulation deterministically, `place(x)`,
`setSpecies(id)`, `flight(state)`, `flightVec(x, y)` and `debug()` for a state snapshot.
Serve `Resources/pet.html` over http with a stub `window.webkit` and a seeded
`window.__petSavedState`, then read pixels back off the canvas. `Tools/check_bubble_gap.mjs`
is a worked example.

Measure the thing the user can see. Several checks have passed while the bug was plainly
visible: "is the beam touching the body" is trivially true when the beam lies *across* the
body, and "the topmost bright pixel" finds a beam's far end, not its root.

## Assets and likeness

Pets modelled on characters someone else owns are a decision for the repo's owner, not a
default. This repository is public and MIT licensed. Traced or extracted sprite art carries
more risk than an original drawing in a similar style.
