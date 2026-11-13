#!/usr/bin/env python

import os

if os.access("/tmp", os.W_OK):
    os.environ["TMPDIR"] = "/tmp"
    os.environ["APPTAINERENV_TMPDIR"] = "/tmp"
    os.environ["SINGULARITYENV_TMPDIR"] = "/tmp"
else:
    print("/tmp not writable to us. You may encounter `OSError: AF_UNIX path too long`")

import argparse
from pathlib import Path

import astropy.units as u
import bdsf
import json
import numpy as np
import os
import shutil
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.modeling import fitting, models
from astropy.table import Table, join
from collections.abc import Generator
from lsmtool.skymodel import SkyModel
from skimage.metrics import structural_similarity


class AstrometryDeriver:
    def __init__(self, reference_cat: Path, validation_cat: Path, image_path: Path):
        """

        Args:
            reference_cat (Path): path to a reference catalogue to which the data should be aligned.
            validation_cat (Path): path to the validation CSV from the DD calibration.
            image_path (Path): path to a directory containing FITS images of sources. Will be searched for sources
                from the reference catalogue.
        """
        self.reference_cat = reference_cat
        self.validation_cat = validation_cat
        self.image_path = image_path
        self.corrections = {}
        self.delta_ra = 0.0
        self.delta_dec = 0.0

    def crossmatch_sources(self, tolerance: float = 1.0):
        """Crossmatch the reference catalogue with the validation catalogue. Only reference sources
        that passed the validation are kept. This ensures that fitting is only done on successfully calibrated
        sources.

        Args:
            tolerance (float): tolerance to within which to match between reference sources and dd calibrators.
        """
        refcat = Table.read(self.reference_cat)
        valcat = Table.read(self.validation_cat)
        valcat = valcat[
            np.logical_and(valcat["accept_solutions"], valcat["accept_image"])
        ]
        if "source_id" in valcat.colnames:
            valcat.rename_column("source_id", "Source_id")
        self.matched = join(refcat, valcat, keys="Source_id", join_type="inner")
        print(f"{len(self.matched)} astrometric references present.")

    def derive_offsets(self):
        """Calculate the average offsets in right ascension and declination given the reference sources."""
        astroSearchRadius = 3.0
        refcat = Table.read(self.reference_cat)
        corrections: dict[str, tuple[float, float, float, float]] = {}
        for source in self.matched:
            impattern = f"*{source['Source_id']}*.fits"
            print(impattern)
            try:
                imname = list(self.image_path.glob(impattern))[0]
            except IndexError:
                continue

            # We're after compact sources for accurate positioning, so only fit the central part
            # if the image is too big.
            data = fits.getdata(imname).squeeze()
            header = fits.getheader(imname)
            pix_needed1 = int(10 / (abs(header["CDELT1"]) * 3600))
            pix_needed2 = int(10 / (abs(header["CDELT2"]) * 3600))
            low1 = 0
            high1 = header["NAXIS1"]
            low2 = 0
            high2 = header["NAXIS2"]

            if header["NAXIS1"] > pix_needed1:
                print("Axis 1 is longer than the necessary 10 arcsec; trimming.")
                low1 = int((header["NAXIS1"] // 2) - (pix_needed1 // 2))
                high1 = int((header["NAXIS1"] // 2) + (pix_needed1 // 2))
            if header["NAXIS2"] > pix_needed1:
                print("Axis 2 is longer than the necessary 10 arcsec; trimming.")
                low2 = int((header["NAXIS2"] // 2) - (pix_needed2 // 2))
                high2 = int((header["NAXIS2"] // 2) + (pix_needed2 // 2))
            data = data[low1:high1, low2:high2]

            img = bdsf.process_image(
                imname,
                mean_map="zero",
                rms_map=True,
                rms_box=(100, 10),
                outdir=".",
                atrous_do=False,
                atrous_jmax=4,
                thresh_isl=4,
                thresh_pix=5,
                trim_box=(low1, high1, low2, high2),
                quiet=True,
            )
            sm_file = f"{source['Source_id']}.skymodel"
            img.write_catalog(
                outfile=sm_file, catalog_type="gaul", bbs_patches="source", clobber=True
            )

            # We use the structural similarity (SSIM) index to assess how Gaussian the source looks.
            # a SSIM value of 1.0 means identical images. To assess this, we fit a _single_ Gaussian
            # centred on the brightest pixel in the image.
            data = (data - np.min(data)) / (np.max(data) - np.min(data))
            init_model = models.Gaussian2D(
                amplitude=np.nanmax(data),
                x_mean=data.shape[0] // 2,
                y_mean=data.shape[1] // 2,
                x_stddev=1.0,
                y_stddev=1.0,
            )
            fitter = fitting.LevMarLSQFitter()
            y, x = np.meshgrid(np.arange(data.shape[0]), np.arange(data.shape[1]))
            fit = fitter(init_model, x, y, data)

            ssim_value = structural_similarity(
                data, fit(x, y), data_range=data.max() - data.min()
            )

            # Derive offsets from the intensity-weighted ILT position to Gaia.
            opt_coords = SkyCoord(
                refcat[refcat["Source_id"] == source["Source_id"]]["gaia_RA"].item(),
                refcat[refcat["Source_id"] == source["Source_id"]]["gaia_DEC"].item(),
                unit="deg",
            )

            # We search for the source with the closest intensity-weighted position
            # to the Gaia position.
            sky_model = SkyModel(sm_file)
            sky_model.setPatchPositions(method="wmean")
            offsets = None
            separation = None
            patch_size = None
            ref_dec = None
            for i, (name, (ra, dec)) in enumerate(
                sky_model.getPatchPositions().items()
            ):
                src_coord = SkyCoord(ra, dec)
                if i == 0:
                    offsets = src_coord.spherical_offsets_to(opt_coords)
                    separation = src_coord.separation(opt_coords)
                    patch_size = sky_model.getPatchSizes(units="arcsec")[i]
                    ref_dec = dec
                else:
                    new_separation = src_coord.separation(opt_coords)
                    if new_separation < separation:
                        separation = new_separation
                        offsets = src_coord.spherical_offsets_to(opt_coords)
                        patch_size = sky_model.getPatchSizes(units="arcsec")[i]
                        ref_dec = dec

            if separation > astroSearchRadius * u.arcsec:
                print(
                    f"Closest match is more than the allowed distance of {astroSearchRadius} arcsec away. Not correcting."
                )
                delta_ra = 0
                delta_dec = 0
            else:
                delta_ra = offsets[0].deg / np.cos(np.deg2rad(ref_dec))
                delta_dec = offsets[1].deg
                print(
                    f"Found a component within {astroSearchRadius:f} arcsec of reference coordinate. Correcting with ΔRA={delta_ra*3600:f} arcsec and ΔDEC={delta_dec*3600:f} arcsec"
                )

            corrections[source["Source_id"]] = (
                delta_ra,
                delta_dec,
                patch_size,
                ssim_value,
            )

        self.corrections = corrections

    def summarise_corrections(self):
        """Summarise the sources used for the corrections and the final average astrometric correction."""
        print("== PILOT astrometric summary ==")
        N_sources = len(self.corrections)
        if N_sources == 0:
            print("No suitable astrometric refefences were found.")
            self.delta_ra = 0
            self.delta_dec = 0
            return
        dra_avg = 0
        ddec_avg = 0
        for source, (
            delta_ra,
            delta_dec,
            size,
            chi2,
        ) in self.corrections.copy().items():
            if chi2 < 0.5:
                print(
                    f"{source} ΔRA={delta_ra*3600:f} arcsec, ΔDEC={delta_dec*3600:f} arcsec; size {size:.2f} arcsec; single-Gaussian SSIM={chi2:.2f} (!! bad similarity -- source is likely not a Gaussian)"
                    # f"{source} ΔRA={delta_ra*3600:f} arcsec, ΔDEC={delta_dec*3600:f} arcsec; size {size:.2f} arcsec; single-Gaussian χ2={chi2:.2f}"
                )
                self.corrections.pop(source)
                N_sources -= 1
            else:
                print(
                    f"{source} ΔRA={delta_ra*3600:f} arcsec, ΔDEC={delta_dec*3600:f} arcsec; size {size:.2f} arcsec; single-Gaussian SSIM={chi2:.2f}"
                )
                dra_avg += delta_ra
                ddec_avg += delta_dec

        dra_avg /= N_sources
        ddec_avg /= N_sources
        self.delta_ra = dra_avg
        self.delta_dec = ddec_avg

        print()
        print(
            f'Average correction based on {N_sources} sources: ΔRA={dra_avg*3600:f}" ΔDEC={ddec_avg*3600}".'
        )

    def dump_to_json(self, filename: str = "astrometry.json"):
        """Save the offsets in right ascension and declination to a JSON file.

        Args:
            filename (str): name of the file to save to.
        """
        with open(filename, "w") as f:
            json.dump({"delta_ra": self.delta_ra, "delta_dec": self.delta_dec}, f)

    def correct_images(self, images: Generator[Path]):
        for img in images:
            with open(img, mode="update") as hdul:
                hdul[0]["CRVAL1"] += self.delta_ra
                hdul[0]["CRVAL2"] += self.delta_dec
            img.rename(img.absolute().with_suffix(".astrometry.fits"))


def main():
    parser = argparse.ArgumentParser(
        description="Derive astrometric corrections for the PILOT pipeline."
    )
    parser.add_argument(
        "--astrometric-references",
        type=Path,
        help="CSV catalogue of astrometric reference sources.",
    )
    parser.add_argument(
        "--validation-csv",
        type=Path,
        help="CSV file from the selfcal validation.",
    )
    parser.add_argument(
        "--fits-images",
        nargs="+",
        help="FITS images for source finding.",
    )
    args = parser.parse_args()

    os.mkdir("fits_images")
    fits_directory = Path("./fits_images")
    for f in args.fits_images:
        shutil.copy(f, Path(os.getcwd()) / "fits_images" / os.path.basename(f))

    astro = AstrometryDeriver(
        args.astrometric_references, args.validation_csv, fits_directory
    )
    astro.crossmatch_sources()
    astro.derive_offsets()
    astro.summarise_corrections()
    img_path = Path(os.getcwd()) / "fits_images"
    astro.correct_images(img_path.glob("*.fits"))
    astro.dump_to_json()


if __name__ == "__main__":
    main()
