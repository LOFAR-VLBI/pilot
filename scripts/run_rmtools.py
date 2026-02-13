#!/usr/bin/env python3
"""Run RM-Tools rmsynth3d locally."""

import argparse
import glob
import os
import shutil
import subprocess
import sys
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RM-Tools rmsynth3d on Stokes Q/U cubes and a frequency list.",
    )
    parser.add_argument("--stokes-q", required=True, help="Stokes Q cube (per-channel).")
    parser.add_argument("--stokes-u", required=True, help="Stokes U cube (per-channel).")
    parser.add_argument("--freqs", required=True, help="Frequency list in Hz (one per channel).")
    parser.add_argument("--l", dest="max_lam2", default="150", help="Maximum lambda-squared (-l).")
    parser.add_argument("--d", dest="dlam2", default="0.3", help="Lambda-squared channel width (-d).")
    parser.add_argument(
        "--output-prefix",
        dest="output_prefix",
        default="",
        help="Prefix to prepend to output files (passed to rmsynth3d -o).",
    )
    parser.add_argument(
        "--extra-args",
        default="",
        help="Extra arguments passed to rmsynth3d (as a single string).",
    )
    return parser.parse_args()


def build_rmsynth_cmd(args: argparse.Namespace) -> List[str]:
    cmd = [
        "rmsynth3d",
        args.stokes_q,
        args.stokes_u,
        args.freqs,
        "-l",
        str(args.max_lam2),
        "-d",
        str(args.dlam2),
        "-v",
        "-R",
    ]
    if args.output_prefix:
        out_prefix = f"./{args.output_prefix}"
        cmd += ["-o", out_prefix]
    if args.extra_args:
        cmd += args.extra_args.split()
    return cmd


def move_outputs(stokes_q_path: str) -> None:
    # RM-Tools writes outputs into the same directory as the staged input FITS.
    input_dir = os.path.dirname(stokes_q_path)
    moved = []

    for path in glob.glob(os.path.join(input_dir, "*FDF_*.fits")):
        dest = os.path.basename(path)
        shutil.move(path, dest)
        moved.append(dest)

    if moved:
        print("Moved outputs to workdir:")
        for name in moved:
            print(f"  {name}")
    else:
        print("No staged outputs found to move.")


def main() -> int:
    args = parse_args()
    rmsynth_cmd = build_rmsynth_cmd(args)
    rc = subprocess.call(rmsynth_cmd)
    move_outputs(args.stokes_q)
    return rc


if __name__ == "__main__":
    sys.exit(main())
