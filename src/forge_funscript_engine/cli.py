"""Command-line interface for the engine.

    forge-funscript-engine INPUT.funscript [-o OUTDIR] [--name NAME]
        [--device estim|handy|vacuglide] [--channels full|minimal]
        [--chapters N] [--ramp R]

Reads a 1-D stroke funscript and writes the selected device's channel set:
  estim     -> <OUTDIR>/estim/<NAME>.<channel>.funscript   (section 7)
  handy     -> <OUTDIR>/handy/<NAME>.funscript             (section 8)
  vacuglide -> <OUTDIR>/vacuglide/<NAME>.funscript         (section 8)
"""
import argparse
import os
import sys

from .funscript import load_funscript
from .pipeline import generate_estim, generate_single_axis
from .chapters import load_chapters_file

PROG = "forge-funscript-engine"


def build_parser():
    p = argparse.ArgumentParser(
        prog=PROG,
        description="Forge Funscript Engine: stroke funscript -> device channels.",
    )
    p.add_argument("input", help="input .funscript (1-D stroke motion)")
    p.add_argument("-o", "--out-dir", default=".",
                   help="output directory (default: .)")
    p.add_argument("--name", default=None,
                   help="output basename (default: input filename stem)")
    p.add_argument("--device", default="estim",
                   choices=["estim", "handy", "vacuglide"],
                   help="target device (default: estim)")
    p.add_argument("--channels", default="full", choices=["full", "minimal"],
                   help="e-stim channel set: full superset or minimal a/b/v (default: full)")
    p.add_argument("--chapters", type=int, default=None,
                   help="split into N equal chapters with seam stitching (e-stim only)")
    p.add_argument("--chapters-file", default=None,
                   help="standalone chapter sidecar JSON; overrides --chapters (e-stim only)")
    p.add_argument("--ramp", type=float, default=None,
                   help="Passage ramp slice R in [0,1] (default: derived from length)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not os.path.isfile(args.input):
        print(f"{PROG}: input not found: {args.input}", file=sys.stderr)
        return 2
    name = args.name or os.path.splitext(os.path.basename(args.input))[0]
    fs = load_funscript(args.input)

    chapters = args.chapters
    if args.chapters_file:
        if not os.path.isfile(args.chapters_file):
            print(f"{PROG}: chapters file not found: {args.chapters_file}",
                  file=sys.stderr)
            return 2
        clip_end = fs.actions[-1]["at"] if fs.actions else None
        chapters = load_chapters_file(args.chapters_file, clip_end)

    if args.device == "estim":
        channels = generate_estim(fs.actions, ramp=args.ramp, name=name,
                                  out_dir=args.out_dir, chapters=chapters,
                                  full=(args.channels == "full"))
        sub = "estim"
        files = [f"{name}.{ch}.funscript" for ch in channels]
    else:
        generate_single_axis(fs.actions, device=args.device, name=name,
                             out_dir=args.out_dir)
        channels = {"position": None}
        sub = args.device
        files = [f"{name}.funscript"]

    n_frames = "-" if args.device != "estim" else \
        len(next(iter(channels.values())).actions)
    print(f"{PROG}: {len(fs.actions)} input actions -> {args.device}: "
          f"{len(files)} file(s)" + (f" ({n_frames} frames each)" if args.device == "estim" else ""))
    for f in files:
        print(f"  {os.path.join(args.out_dir, sub, f)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
