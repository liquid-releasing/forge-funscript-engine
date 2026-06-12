"""Command-line interface for the Phase-1 engine.

    forge-funscript-engine INPUT.funscript [-o OUTDIR] [--name NAME] [--ramp R]

Reads a 1-D stroke funscript and writes the e-stim channel set
(<OUTDIR>/estim/<NAME>.{alpha,beta,volume}.funscript). See spec section 11.
"""
import argparse
import os
import sys

from .funscript import load_funscript
from .pipeline import generate_estim

PROG = "forge-funscript-engine"


def build_parser():
    p = argparse.ArgumentParser(
        prog=PROG,
        description="Forge Funscript Engine: stroke funscript -> e-stim alpha/beta/volume.",
    )
    p.add_argument("input", help="input .funscript (1-D stroke motion)")
    p.add_argument("-o", "--out-dir", default=".",
                   help="output directory; channels go in <out-dir>/estim/ (default: .)")
    p.add_argument("--name", default=None,
                   help="output basename (default: input filename stem)")
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
    channels = generate_estim(fs.actions, ramp=args.ramp, name=name,
                              out_dir=args.out_dir)

    estim_dir = os.path.join(args.out_dir, "estim")
    n_frames = len(next(iter(channels.values())).actions)
    print(f"{PROG}: {len(fs.actions)} input actions -> {len(channels)} channels "
          f"({n_frames} frames each)")
    for ch in channels:
        print(f"  {os.path.join(estim_dir, f'{name}.{ch}.funscript')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
