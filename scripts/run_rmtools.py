#!/usr/bin/env python3
"""Run RM-Tools rmsynth3d locally or in an Apptainer/Singularity container."""

import argparse
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
    parser.add_argument(
        "--apptainer-bin",
        default="apptainer",
        help="Apptainer/Singularity executable name or path.",
    )
    parser.add_argument(
        "--apptainer-image",
        default="",
        help="Path to an Apptainer/Singularity image (.sif).",
    )
    parser.add_argument(
        "--apptainer-bind",
        action="append",
        default=[],
        help="Bind mount(s) for Apptainer/Singularity, e.g. /data:/mnt. Can be repeated.",
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
        cmd += ["-o", args.output_prefix]
    if args.extra_args:
        cmd += args.extra_args.split()
    return cmd


def main() -> int:
    args = parse_args()
    rmsynth_cmd = build_rmsynth_cmd(args)

    if args.apptainer_image:
        apptainer_cmd = [args.apptainer_bin, "exec"]
        for bind in args.apptainer_bind:
            apptainer_cmd += ["--bind", bind]
        apptainer_cmd.append(args.apptainer_image)
        cmd = apptainer_cmd + rmsynth_cmd
    else:
        cmd = rmsynth_cmd

    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
