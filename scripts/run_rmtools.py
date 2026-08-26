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
from astropy.io import fits
import numpy as np

def get_header(fits_file):
    """
    Use astropy to return the header of a FITS file
    """
    with fits.open(fits_file) as hdu1:
        return hdu1[0].header

def get_data(fits_file):
    """
    Use astropy to return the data of a FITS file
    """
    with fits.open(fits_file) as hdu1:
        return hdu1[0].data


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

    return q_local, u_local, freq_local

def do_rmsynth(args: argparse.Namespace, qfile: str, ufile: str, freqfile: str,) -> List[str]:
    
    """Perform RMSynthesis using rmtools3d

    See args in parse_args()

    """ 

    q_header = get_header(qfile)

    q_data = get_data(qfile)
    u_data = get_data(ufile)

    freq_array = np.array(np.loadtxt(freqfile))

    phi_max = float(args.max_lam2)
    dphi = float(args.dlam2)

    dataArr=run_rmsynth(q_data.squeeze(),
    	u_data.squeeze(),
    	freq_array,
    	phiMax_radm2=phi_max,
    	dPhi_radm2=dphi,
        nSamples=None,
        weightType="variance",
        fitRMSF=False,
    	verbose=True,
    	not_rmsf=False)


    writefits(dataArr,
    	headtemplate=q_header,
    	fitRMSF=False,
    	prefixOut=args.output_prefix,
    	outDir='./',
    	write_separate_FDF=True,
        verbose=True,
    	not_rmsf=False)

def main() -> int:
    args = parse_args()
    qfile,ufile,freqfile = stage_inputs(args)
    do_rmsynth(args,qfile,ufile,freqfile,)
    print("Running rmtools3d with:", " ".join(print(args)))
    print("Working directory: ", Path.cwd())

if __name__ == "__main__":
    sys.exit(main())
