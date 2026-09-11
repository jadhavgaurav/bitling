# Legacy tools

One-off scripts from past feature migrations (Goku forms, HD Pikachu, Iron Man, Mario,
Spider-Man, Thor, and various sprite/patch cleanups). Each one already ran once against
`apps/macos/web/bitling.html` and its change is now part of that file; nothing in the build,
test, or lint pipeline calls any of these anymore. Kept for reference only — safe to delete
in a future cleanup once confirmed nobody still needs them as a worked example.

`artifacts/` and `scratch/` here are debug images and throwaway verification scripts from the
same era, moved alongside for the same reason. Both were already gitignored, so this move
has no effect on the tracked repo history.
