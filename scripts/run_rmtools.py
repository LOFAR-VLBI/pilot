#!/usr/bin/env python3
"""Run RM-Tools rmsynth3d."""

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits
from RMtools_3D.do_RMsynth_3D import run_rmsynth, writefits


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


def stage_inputs(stokes_q: str, stokes_u: str, freqs: str, workdir: Path = None) -> tuple[Path, Path, Path]:
    """
    Moves files from the cwl staging directory to the current
    working directory so that the next part of the workflow can
    pick it up
    """

    workdir = Path.cwd() if workdir is None else Path(workdir)

    q_local = workdir / "image-polcube-Q.fits"
    u_local = workdir / "image-polcube-U.fits"
    freq_local = workdir / "image_frequency_list.dat"

    shutil.copy2(stokes_q, q_local)
    shutil.copy2(stokes_u, u_local)
    shutil.copy2(freqs, freq_local)

    return q_local, u_local, freq_local


def do_rmsynth(qfile: str, ufile: str, freqfile: str, max_lam2: float, dlam2: float, output_prefix: str = ""):
    """Perform RMSynthesis using rmtools3d

    Parameters
    ----------
    qfile, ufile : str
        Paths to the Stokes Q/U cubes.
    freqfile : str
        Path to the frequency list (Hz, one per channel).
    max_lam2 : float
        Maximum lambda-squared (-l).
    dlam2 : float
        Lambda-squared channel width (-d).
    output_prefix : str
        Prefix to prepend to output files (passed to rmsynth3d -o).
    """

    q_header = get_header(qfile)

    q_data = get_data(qfile)
    u_data = get_data(ufile)

    freq_array = np.array(np.loadtxt(freqfile))

    phi_max = float(max_lam2)
    dphi = float(dlam2)

    dataArr = run_rmsynth(
        q_data.squeeze(),
        u_data.squeeze(),
        freq_array,
        phiMax_radm2=phi_max,
        dPhi_radm2=dphi,
        nSamples=None,
        weightType="variance",
        fitRMSF=False,
        verbose=True,
        not_rmsf=False,
    )

    writefits(
        dataArr,
        headtemplate=q_header,
        fitRMSF=False,
        prefixOut=output_prefix,
        outDir="./",
        write_seperate_FDF=True,
        verbose=True,
        not_rmsf=False,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RM-Tools rmsynth3d on Stokes Q/U cubes and a frequency list.")
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


def main():
    args = parse_args()

    print("Running rmtools3d with:", " ".join(f"{k}={v}" for k, v in vars(args).items()))

    qfile, ufile, freqfile = stage_inputs(
        stokes_q=args.stokes_q,
        stokes_u=args.stokes_u,
        freqs=args.freqs,
    )

    do_rmsynth(
        qfile=qfile,
        ufile=ufile,
        freqfile=freqfile,
        max_lam2=args.max_lam2,
        dlam2=args.dlam2,
        output_prefix=args.output_prefix,
    )


if __name__ == "__main__":
    main()