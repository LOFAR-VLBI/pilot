#!/usr/bin/env python3
"""Run RM-Tools rmsynth3d."""

import argparse
import glob
import os
import shutil
import subprocess
import sys
from typing import List
from pathlib import Path
from RMtools_3D.do_RMsynth_3D import run_rmsynth,writefits
from utils.fits_handling import get_header


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

def stage_inputs(args: argparse.Namespace):
	"""
	Moves files from the cwl staging directory to the current 
	working directory so that the next part of the workflow can 
	pick it up
	"""

    workdir = Path.cwd()

    q_local = workdir / "image-polcube-Q.fits"
    u_local = workdir / "image-polcube-U.fits"
    freq_local = workdir / "image_frequency_list.dat"

    shutil.copy2(args.stokes_q, q_local)
    shutil.copy2(args.stokes_u, u_local)
    shutil.copy2(args.freqs, freq_local)

    return str(q_local), str(u_local), str(freq_local)

def do_rmsynth(args: argparse.Namespace, qfile: str, ufile: str, freqfile: str,) -> List[str]:
    
    """Perform RMSynthesis using rmtools3d

    See args in parse_args()

    """ 

    q_header = get_header(q_local)

    dataArr=run_rmsynth(qfile,
    	ufile,
    	freqfile,
    	phiMax_radm2=args.max_lam2,
    	dPhi_radm2=dlam2,
    	verbose=True,
    	not_rmsf=False)


    writefits(dataArr,
    	headtemplate=q_header,
    	fitRMSF=false,
    	prefixOut=args,output_prefix,
    	outDir='./',
    	write_separate_FDF=True,
    	not_rmsf=False,
    	verbose=True)

def main() -> int:
    args = parse_args()
    qfile,ufile,freqfile = stage_inputs(args)
    do_rmsynth(args,qfile,ufile,freqfile,)
    print("Running rmtools3d with:", " ".join(print(args)))
    print("Working directory: ", Path.cwd())

if __name__ == "__main__":
    sys.exit(main())
