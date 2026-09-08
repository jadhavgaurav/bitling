#!/usr/bin/env python3
"""Assemble captured pet frames into the README animation.

Frames come from the capture harness: transparent PNGs of the pet canvas, one per
tick. This composites them on the app's own dark ground, crops to the union of
everything drawn across the whole sequence so nothing pops in or out of frame,
and writes a palette-quantised GIF.

    python3 Tools/make_gif.py <frame-dir> <out.gif> [--width 640] [--fps 20]
"""
import sys
from pathlib import Path
from PIL import Image

BACKDROP = (18, 20, 26)


def bounds(frames):
    """Union of the drawn area across every frame, so the crop never clips a pose."""
    box = None
    for im in frames:
        b = im.getchannel("A").getbbox()
        if not b:
            continue
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]),
                                     max(box[2], b[2]), max(box[3], b[3]))
    return box


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    src, out = Path(args[0]), Path(args[1])
    width = int(args[args.index("--width") + 1]) if "--width" in args else 640
    fps = int(args[args.index("--fps") + 1]) if "--fps" in args else 20
    colors = int(args[args.index("--colors") + 1]) if "--colors" in args else 64

    paths = sorted(src.glob("*.png"))
    if not paths:
        print(f"no frames in {src}")
        return 1
    frames = [Image.open(p).convert("RGBA") for p in paths]

    box = bounds(frames)
    pad = 12
    box = (max(0, box[0] - pad), max(0, box[1] - pad),
           min(frames[0].width, box[2] + pad), min(frames[0].height, box[3] + pad))

    shots = []
    for im in frames:
        flat = Image.new("RGB", im.size, BACKDROP)
        flat.paste(im, (0, 0), im)
        flat = flat.crop(box)
        height = round(flat.height * width / flat.width)
        shots.append(flat.resize((width, height), Image.LANCZOS))

    # One palette for the whole run, or the background shimmers between frames. No
    # dithering: this art is flat shaded, and dither noise wrecks the frame to frame
    # compression a GIF depends on. It cost ten megabytes here.
    sample = Image.new("RGB", (shots[0].width, shots[0].height * min(6, len(shots))))
    for i, s in enumerate(shots[:: max(1, len(shots) // 6)][:6]):
        sample.paste(s, (0, i * shots[0].height))
    palette = sample.quantize(colors=colors, method=Image.MEDIANCUT)
    quantised = [s.quantize(palette=palette, dither=Image.NONE) for s in shots]
    quantised[0].save(
        out, save_all=True, append_images=quantised[1:],
        duration=round(1000 / fps), loop=0, optimize=True,
    )
    size = out.stat().st_size
    print(f"{out}  {quantised[0].width}x{quantised[0].height}  "
          f"{len(quantised)} frames  {size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
