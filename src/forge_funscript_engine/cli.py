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
from .bundle import load_bundle

PROG = "forge-funscript-engine"


def build_parser():
    p = argparse.ArgumentParser(
        prog=PROG,
        description="Forge Funscript Engine: stroke funscript -> device channels.",
    )
    p.add_argument("input", nargs="?", default=None,
                   help="input .funscript (1-D stroke motion); omit when using --bundle")
    p.add_argument("--bundle", default=None,
                   help="a .forge bundle: manifest.ffmeta path or its directory "
                        "(supplies motion + chapters + name)")
    p.add_argument("--no-carrier", action="store_true",
                   help="omit the automated frequency channel (restim uses its static carrier)")
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

    # Resolve motion + chapters + name from either a .forge bundle or a loose funscript.
    if args.bundle:
        if not os.path.exists(args.bundle):
            print(f"{PROG}: bundle not found: {args.bundle}", file=sys.stderr)
            return 2
        b = load_bundle(args.bundle)
        actions, chapters = b.motion_actions, b.chapters
        name = args.name or b.stem
    elif args.input:
        if not os.path.isfile(args.input):
            print(f"{PROG}: input not found: {args.input}", file=sys.stderr)
            return 2
        actions = load_funscript(args.input).actions
        name = args.name or os.path.splitext(os.path.basename(args.input))[0]
        chapters = args.chapters
        if args.chapters_file:
            if not os.path.isfile(args.chapters_file):
                print(f"{PROG}: chapters file not found: {args.chapters_file}",
                      file=sys.stderr)
                return 2
            clip_end = actions[-1]["at"] if actions else None
            chapters = load_chapters_file(args.chapters_file, clip_end)
    else:
        print(f"{PROG}: provide an input .funscript or --bundle", file=sys.stderr)
        return 2

    if args.device == "estim":
        channels = generate_estim(actions, ramp=args.ramp, name=name,
                                  out_dir=args.out_dir, chapters=chapters,
                                  full=(args.channels == "full"),
                                  emit_carrier=not args.no_carrier)
        sub = "estim"
        files = [f"{name}.{ch}.funscript" for ch in channels]
    else:
        generate_single_axis(actions, device=args.device, name=name,
                             out_dir=args.out_dir)
        channels = {"position": None}
        sub = args.device
        files = [f"{name}.funscript"]

    n_frames = "-" if args.device != "estim" else \
        len(next(iter(channels.values())).actions)
    print(f"{PROG}: {len(actions)} input actions -> {args.device}: "
          f"{len(files)} file(s)" + (f" ({n_frames} frames each)" if args.device == "estim" else ""))
    for f in files:
        print(f"  {os.path.join(args.out_dir, sub, f)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
