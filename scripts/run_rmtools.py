#!/usr/bin/env python3
"""Run RM-Tools rmsynth3d."""

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
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


def stage_inputs(stokes_q: str, stokes_u: str, freqs: str | None, workdir: Path = None) -> tuple[Path, Path, Path | None]:
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
    if freqs is not None:
        shutil.copy2(freqs, freq_local)
    else:
        freq_local = None

    return q_local, u_local, freq_local


def load_channel_rms(noise_file, q_data, u_data):
    """Validate one RMS per channel; give fully blanked pairs zero weight."""
    nchan = q_data.shape[-3]
    rms = np.atleast_1d(np.loadtxt(noise_file))
    if rms.ndim != 1 or len(rms) != nchan:
        raise ValueError("RMS file must contain exactly one value per cube channel")
    blank_q = np.isnan(q_data.reshape(nchan, -1)).all(axis=1)
    blank_u = np.isnan(u_data.reshape(nchan, -1)).all(axis=1)
    if not np.array_equal(blank_q, blank_u):
        raise ValueError("Q/U cubes must have the same blanked channel pairs")
    invalid = ~np.isfinite(rms) | (rms <= 0)
    if np.any(invalid & ~blank_q):
        raise ValueError("Unblanked channels require finite, strictly positive RMS estimates")
    if blank_q.all():
        raise ValueError("No unblanked channels are available for RM synthesis")
    # 1 / inf**2 = 0. Avoid NaN or infinite inverse-variance weights.
    return np.where(blank_q, np.inf, rms)


def do_rmsynth(qfile: str, ufile: str, freqfile: str | None, max_lam2: float, dlam2: float,
              output_prefix: str = "", noise_file: str | None = None, weighting: str = "variance"):
    """Perform RMSynthesis using rmtools3d

    Parameters
    ----------
    qfile, ufile : str
        Paths to the Stokes Q/U cubes.
    freqfile : str or None
        Optional frequency list (Hz); None uses the cubes' FITS spectral WCS.
    max_lam2 : float
        Maximum absolute Faraday depth in rad/m^2 (-l).
    dlam2 : float
        Faraday-depth sampling interval in rad/m^2 (-d).
    output_prefix : str
        Prefix to prepend to output files (passed to rmsynth3d -o).
    noise_file : str or None
        One channel RMS in Jy/beam per line, required for variance weighting.
    weighting : str
        "variance" (default) or explicitly requested "uniform".
    """

    q_header = get_header(qfile)

    q_data = get_data(qfile)
    u_data = get_data(ufile)
    if q_data.shape != u_data.shape:
        raise ValueError("Q/U cubes must have the same dimensions")

    if freqfile is None:
        channels = np.arange(q_data.shape[-3])
        freq_array = np.asarray(WCS(q_header).spectral.pixel_to_world_values(channels))
        u_freqs = WCS(get_header(ufile)).spectral.pixel_to_world_values(channels)
        if not np.allclose(freq_array, u_freqs, rtol=0, atol=0.01):
            raise ValueError("Q/U cubes have different spectral WCS")
        print("Reconstructed channel frequencies from FITS spectral WCS")
    else:
        freq_array = np.atleast_1d(np.loadtxt(freqfile))
    if len(freq_array) != q_data.shape[-3] or not np.isfinite(freq_array).all():
        raise ValueError("Frequency axis must match the cube depth and contain finite values")

    phi_max = float(max_lam2)
    dphi = float(dlam2)
    if weighting not in ("variance", "uniform"):
        raise ValueError("Weighting must be variance or uniform")
    rms_array = None
    if weighting == "variance":
        if noise_file is None:
            raise ValueError("Variance weighting requires --rms; use --weighting uniform for equal weights")
        rms_array = load_channel_rms(noise_file, q_data, u_data)
        usable = np.isfinite(rms_array)
        print(f"Inverse-variance weighting: {usable.sum()} usable channels, {(~usable).sum()} zero-weight channels")

    dataArr = run_rmsynth(
        q_data.squeeze(),
        u_data.squeeze(),
        freq_array,
        rmsArr=rms_array,
        phiMax_radm2=phi_max,
        dPhi_radm2=dphi,
        nSamples=None,
        weightType=weighting,
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
    parser.add_argument("--freqs", help="Optional frequency list in Hz; defaults to the cube's FITS spectral WCS.")
    parser.add_argument("--rms", help="Channel RMS file in Jy/beam (one value per cube plane); required for variance weighting.")
    parser.add_argument("--weighting", choices=["variance", "uniform"], default="variance", help="Channel weighting (default: variance).")
    parser.add_argument("--l", dest="max_lam2", default="150", help="Maximum absolute Faraday depth in rad/m^2 (-l).")
    parser.add_argument("--d", dest="dlam2", default="0.3", help="Faraday-depth sampling interval in rad/m^2 (-d).")
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
        noise_file=args.rms,
        weighting=args.weighting,
    )


if __name__ == "__main__":
    main()
