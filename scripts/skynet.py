#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import glob
import os
from typing import Optional

import astropy.units as u
import bdsf
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.table import Table
from lsmtool.skymodel import SkyModel


def model_from_image(
    modelImage: str,
    smodel: float,
    opt_coords: Optional[SkyCoord] = None,
    astroSearchRadius: float = 3.0,
    outdir: str = ".",
) -> SkyModel:
    """Generate a starting model by running PyBDSF on the input image.

    The model will be scaled to the provided reference flux density. If optical coordinates
    are provided, an astrometric correction will be attempted.

    Args:
        modelImage: FITS image on which to run PyBDSF.
        smodel: reference flux density to which to scale the image.
        opt_coords: reference coordinates to which to attempt an astrometric correction.
        astroSearchRadius: radius in arcsec within which to consider offsets for astrometric correction.
        outdir: output path for PyBDSF files.

    Returns:
        sky_model (lsmtool.skymodel.SkyModel): a sky model in BBS format.

    Raises:
        ValueError: if opt_coords is given, but no match within astroSearchRadius is found.
    """
    # Sometimes if temporary directory paths are too long PyBDSF's multiprocessing
    # will fail with a `OSError: AF_UNIX path too long`, because socket paths are not
    # allowed to exceed 108 bytes. To avoid this we purposely override the usual
    # temporary paths here.
    os.environ["TMPDIR"] = "/tmp"
    os.environ["APPTAINERENV_TMPDIR"] = "/tmp"
    os.environ["SINGULARITYENV_TMPDIR"] = "/tmp"

    img = bdsf.process_image(
        modelImage, mean_map="zero", rms_map=True, rms_box=(100, 10), outdir=outdir
    )
    sources = img.sources
    maxval = 0.0
    for src in sources:
        maxval = np.max((maxval, src.total_flux))
    img = bdsf.process_image(
        modelImage,
        mean_map="zero",
        rms_map=True,
        rms_box=(100, 10),
        advanced_opts=True,
        blank_limit=0.01 * maxval,
        outdir=outdir,
    )
    img.write_catalog(
        format="bbs",
        catalog_type="gaul",
        bbs_patches="single",
        outfile="temp_skymodel.txt",
    )

    sky_model = SkyModel("temp_skymodel.txt")
    tot_flux = sum(sky_model.getColValues("I"))
    flux_scaling = smodel / tot_flux

    if opt_coords:
        # We assume the starting model is decent already.
        # Search for the source component closest to the optical coordinates
        # and use that to determine a shift.

        # Cast to string due to return type of np.str_, which crashes getRowValues
        patch = str(sky_model.getPatchNames()[0])
        rows = sky_model.getRowValues(patch)
        src_coord = SkyCoord(rows[0]["Ra"], rows[0]["Dec"], unit="degree")
        offsets = src_coord.spherical_offsets_to(opt_coords)
        separation = src_coord.separation(opt_coords)
        for comp in rows[1:]:
            src_coord = SkyCoord(comp["Ra"], comp["Dec"], unit="degree")
            new_separation = src_coord.separation(opt_coords)
            if new_separation < separation:
                separation = new_separation
                offsets = src_coord.spherical_offsets_to(opt_coords)

        if separation > astroSearchRadius * u.arcsec:
            raise ValueError(
                f"Closest match is more than the allowed distance of {astroSearchRadius} arcsec away."
            )
        delta_ra = offsets[0].deg
        delta_dec = offsets[1].deg
        sky_model.setColValues(
            "Ra", sky_model.getColValues("Ra", units="degree") + delta_ra
        )
        sky_model.setColValues(
            "I", sky_model.getColValues("Dec", units="degree") * delta_dec
        )

    sky_model.setColValues("I", sky_model.getColValues("I") * flux_scaling)
    sky_model.setColValues("ReferenceFrequency", 144e6)
    sky_model.setColValues("SpectralIndex", [-0.7])
    sky_model.setColValues("LogarithmicSI", True)
    return sky_model


################## skynet ##############################


def main(
    MS,
    delayCalFile: str,
    modelImage: str = "",
    astroSearchRadius: float = 3.0,
    skip_vlass: bool = False,
    outdir: str = ".",
    process_all: bool = False,
):
    """
    Generates a skymodel for sources in delayCalFile for delay calibration.
    Uses modelImage as a base model if provided, otherwise will construct a
    point-source model. Will include contributions from Gaia or panstarrs if
    these are available in the catalogue and are within astroSearchRadius of
    the target.
    """
    # From phase shifting, the MS's naming scheme should follow something like
    # <name>_L<sasid>_144MHz_uv.dp3concat
    MS_src = os.path.basename(MS.rstrip("/")).split("_")[0]

    t = Table.read(delayCalFile, format="csv")

    # Check if the skymodel uses a LBCS-format catalogue,
    # which has coordinates in columns 'RA' and 'DEC',
    # or if it uses a LoTSS catalogue, which has its
    # coordinates in columns called 'RA_LOTSS' and 'DEC_LOTSS'
    if ("RA" in t.colnames) and ("DEC" in t.colnames):
        ra_col = "RA"
        de_col = "DEC"
    else:
        ra_col = "RA_LOTSS"
        de_col = "DEC_LOTSS"
    src_ids = t["Source_id"]

    # MS name will always be a string, so every name should be checked as a string.
    src_names = list(map(str, src_ids))
    if not src_names:
        raise RuntimeError(
            f"Delay calibrator list is empty. Please inspect {delayCalFile}."
        )
    if not process_all:
        source_indices = [i for i, val in enumerate(src_names) if MS_src == val]
        if not source_indices:
            raise RuntimeError(
                f"No entry matching Source_id entry for {MS_src} found in {delayCalFile}."
            )
    else:
        source_indices = [i for i, val in enumerate(src_names)]

    for src_idx in source_indices:
        # get the coordinate values and the flux from the skymodel
        # and convert the flux from mJy to Jy.
        ra = t[ra_col].data[src_idx]
        dec = t[de_col].data[src_idx]
        smodel = t["Total_flux"].data[src_idx] * 1.0e-3

        ## gaia information if available - else use panstarrs if it is available
        if "gaia_id" in t.keys() and t["gaia_id"].data[src_idx] != "--":
            opt_coords = SkyCoord(
                t["gaia_RA"].data[src_idx], t["gaia_DEC"].data[src_idx], unit="deg"
            )
        elif "ps_id" in t.keys() and t["ps_id"].data[src_idx] != "--":
            opt_coords = SkyCoord(
                t["ps_RA"].data[src_idx], t["ps_DEC"].data[src_idx], unit="deg"
            )
        else:
            opt_coords = None

        ## spectral index information
        if {"alpha_1", "alpha_2"}.issubset(t.keys()) and t["alpha_1"].data[
            src_idx
        ] != "--":
            a_1 = t["alpha_1"].data[src_idx]
            a_2 = t["alpha_2"].data[src_idx]
        else:
            a_1, a_2 = None, None

        if os.path.isfile(modelImage):
            print("Using user-specified model {:s}".format(modelImage))
            sky_model = model_from_image(
                modelImage, smodel, opt_coords, astroSearchRadius=astroSearchRadius
            )
        else:
            used_vlass = False
            if not skip_vlass:
                ## search for a vlass image
                lbcs_id = t[src_idx]["Observation"]
                vlass_file = glob.glob(
                    os.path.join(
                        os.path.dirname(delayCalFile),
                        "{:s}_vlass.fits".format(lbcs_id[0]),
                    )
                )
                if len(vlass_file) > 0 and os.path.isfile(vlass_file[0]):
                    print("Generating a model from image {:s}.".format(vlass_file[0]))
                    sky_model = model_from_image(
                        vlass_file[0],
                        smodel,
                        opt_coords,
                        astroSearchRadius=astroSearchRadius,
                    )
                    used_vlass = True
                else:
                    print("No VLASS image found.")
            if not used_vlass:
                print("Generating a small Gaussian source model.")
                sky_model = SkyModel(
                    dict(
                        Name="ME0",
                        Type="GAUSSIAN",
                        Patch="P0",
                        Ra=opt_coords.ra.value if opt_coords is not None else ra,
                        Dec=opt_coords.dec.value if opt_coords is not None else dec,
                        I=smodel,
                        Q=0.0,
                        U=0.0,
                        V=0.0,
                        MajorAxis=0.1,
                        MinorAxis=0.0,
                        Orientation=0.0,
                        ReferenceFrequency="144e+06",
                        SpectralIndex=[-0.5],
                        LogarithmicSI=True,
                    )
                )
                sky_model.write(f"skymodel_{src_ids[src_idx]}.txt")

        ## edit spectral index information if necessary
        if (a_1 is not None) and (a_2 is not None):
            sky_model.setColValues("SpectralIndex", [a_1, a_2])

        sky_model.write(f"skymodel_{src_ids[src_idx]}.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Skynet script to handle LBCS calibrators."
    )

    parser.add_argument("MS", type=str, help="Measurement set for which to run skynet")
    parser.add_argument(
        "--delay-cal-file", required=True, type=str, help="delay calibrator information"
    )
    parser.add_argument(
        "--model-image",
        type=str,
        help="image for generating starting model",
        default="",
    )
    parser.add_argument(
        "--astrometric-search-radius",
        type=float,
        help="search radius in arcsec to accept a match",
        default=3.0,
    )
    parser.add_argument(
        "--skip-vlass",
        action="store_true",
        dest="skip_vlass",
        help="skip vlass search and generate point source model",
    )
    parser.add_argument(
        "--process-all",
        action="store_true",
        dest="process_all",
        help="Process all sources in the delay calibrator file.",
    )
    parser.add_argument("--outdir", type=str, help="Output directory", default=".")

    args = parser.parse_args()

    main(
        args.MS,
        delayCalFile=args.delay_cal_file,
        modelImage=args.model_image,
        skip_vlass=args.skip_vlass,
        outdir=args.outdir,
        process_all=args.process_all,
    )
