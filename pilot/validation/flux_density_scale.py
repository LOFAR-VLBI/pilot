from astropy.io import fits
from numpy import mean, std
from numpy.random import normal
from pathlib import Path
from scipy.optimize import curve_fit
from typing import Optional

import argparse
import bdsf
import matplotlib.pyplot as plt
import numpy as np
import structlog
import polars

# Figure size formatting from https://walmsley.dev/posts/typesetting-mnras-figures
# in points - start with the body text size and play around
SMALL_SIZE = 9
MEDIUM_SIZE = 9
BIGGER_SIZE = 9

plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
plt.rc("figure", titlesize=BIGGER_SIZE)
plt.rc("lines", linewidth=1)
plt.rc("patch", linewidth=1)


class SpectrumFitter:
    def __init__(
        self,
        freqs: np.ndarray,
        flux: np.ndarray,
        freq_ref: float,
        labels: list[str] = [],
        name: str = "",
    ):
        self.logger = structlog.getLogger()
        self.reference_frequency = freq_ref
        self.frequency = freqs
        self.flux_density = flux
        self.labels = labels
        if len(self.frequency) < 2:
            raise ValueError(
                "Spectrum fitter needs at least two data points to fit a spectrum."
            )
        elif len(self.frequency) == 2:
            self.fit_type = "PL"
        else:
            self.fit_type = "LP"
        self.fit_params = ()
        self.plot_name = name

    def power_law(self, freq, I0, alpha, freq_ref):
        return I0 * (freq / freq_ref) ** alpha

    def log_parabola(self, freq, I0, alpha, beta, freq_ref):
        return I0 * (freq / freq_ref) ** (alpha + beta * np.log10(freq / freq_ref))

    def fit_spectrum(self) -> tuple[np.ndarray, np.ndarray]:
        if self.fit_type == "PL":
            return self.fit_power_law()
        elif self.fit_type == "LP":
            # The case for <2 is already caught on init
            return self.fit_log_parabola()
        else:
            self.logger.critical("Unknown fit type encountered. Pick PL or LP.")
            raise ValueError("Unknown fit type encountered. Pick PL or LP.")

    def fit_power_law(self) -> tuple[np.ndarray, np.ndarray]:
        # Initialise with the data point nearest to the frequency of interest
        # and a typical synchrotron spectral index.
        p0_i = self.flux_density[np.argmin(self.frequency - self.reference_frequency)]
        p0_alpha = -0.8

        popt, pcov = curve_fit(
            lambda freq, I0, alpha, beta: self.power_law(
                freq, I0, alpha, self.reference_frequency
            ),
            self.frequency,
            self.flux_density,
            p0=(p0_i, p0_alpha),
        )
        self.fit_params = popt
        self.fit_sigma = np.sqrt(np.diag(pcov))
        self.logger.info(
            "Spectrum with two data points provided. Fitted power law with",
            I_0=float(popt[0]),
            sigma_I_0=float(self.fit_sigma[0]),
            alpha=float(popt[1]),
            sigma_alpha=float(self.fit_sigma[1]),
        )
        return self.fit_params, self.fit_sigma

    def fit_log_parabola(self) -> tuple[np.ndarray, np.ndarray]:
        # Initialise with the data point nearest to the frequency of interest
        # and a typical synchrotron spectral index.
        p0_i = self.flux_density[np.argmin(self.frequency - self.reference_frequency)]
        p0_alpha = -0.8
        p0_beta = 0.0

        popt, pcov = curve_fit(
            lambda freq, I0, alpha, beta: self.log_parabola(
                freq, I0, alpha, beta, self.reference_frequency
            ),
            self.frequency,
            self.flux_density,
            p0=(p0_i, p0_alpha, p0_beta),
        )
        self.fit_params = popt
        self.fit_sigma = np.sqrt(np.diag(pcov))
        self.logger.info(
            "Spectrum with more than two data points provided. Fitted log parabola with",
            I_0=float(popt[0]),
            sigma_I_0=float(self.fit_sigma[0]),
            alpha=float(popt[1]),
            sigma_alpha=float(self.fit_sigma[1]),
            beta=float(popt[2]),
            sigma_beta=float(self.fit_sigma[2]),
        )
        return self.fit_params, self.fit_sigma

    def plot_spectrum(self):
        freq_smooth = np.linspace(10e6, 10e9, 1000)

        fig, ax_main = plt.subplots(figsize=(10 / 3, 10 / 3), dpi=300)
        ax_main.loglog()
        ax_main.set(xlabel="Frequency [Hz]", ylabel="Flux density [Jy]")
        plt.setp(ax_main.spines.values(), linewidth=1.5)
        ax_main.xaxis.set_tick_params(width=1.5, which="both")
        ax_main.yaxis.set_tick_params(width=1.5, which="both")

        ax_main.plot(
            freq_smooth,
            self.log_parabola(freq_smooth, *self.fit_params, self.reference_frequency),
            color="k",
            linestyle="--",
            linewidth=1.5,
            label="Log-parabola fit",
        )

        ax_main.scatter(
            self.frequency,
            self.flux_density,
            marker="s",
            ec="k",
            fc="gray",
            s=48,
            zorder=5,
        )
        for f, s, l in zip(self.frequency, self.flux_density, self.labels):
            ax_main.annotate(l, (f * 1.05, s * 1.15))

        # ax_main.scatter(
        #    self.reference_frequency,
        #    s_6p0,
        #    color="m",
        #    marker="H",
        #    s=64,
        #    edgecolors="k",
        #    zorder=5,
        #    label=f"bdsf 6p0 ({s_6p0:.3f} Jy)",
        # )

        # ax_main.axhline(s_ref, color="k", linestyle=":", alpha=0.3)
        # ax_main.axvline(freq_ref, color="k", linestyle=":", alpha=0.3)

        ax_main.set_xlim(10e6, 10e9)
        ax_main.set_ylim(10e-4, 10)

        if len(self.fit_params) == 2:
            textbox = (
                f"S$_{{ref}}$ = {self.fit_params[0]:.2f} +/- {self.fit_sigma[0]:.2f} Jy\n"
                f"$\\alpha$ = {self.fit_params[1]:.2f} +/- {self.fit_sigma[1]:.2f}\n"
            )
        elif len(self.fit_params) == 3:
            textbox = (
                f"S$_{{ref}}$ = {self.fit_params[0]:.2f} +/- {self.fit_sigma[0]:.2f} Jy\n"
                f"$\\alpha$ = {self.fit_params[1]:.2f} +/- {self.fit_sigma[1]:.2f}\n"
                f"$\\beta$ = {self.fit_params[2]:.2f} +/- {self.fit_sigma[2]:.2f}\n"
            )
        else:
            raise RuntimeError("Could not find fitting parameters.")
        ax_main.text(
            0.95,
            0.95,
            textbox,
            transform=ax_main.transAxes,
            va="top",
            ha="right",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )
        if self.plot_name:
            plt.savefig(f"spectrum_{self.plot_name}.png", dpi=300, bbox_inches="tight")
        else:
            plt.savefig("spectrum.png", dpi=300, bbox_inches="tight")
        print(f"\nSaved fitted spectrum to spectrum_{self.plot_name}.png")


class SpectrumFluxScaler:
    """Class to determine the flux density scale starting from a set of FITS images."""

    def __init__(self, image: Path, ref_spectrum: Path):
        self.logger = structlog.getLogger()
        self.image = image

        self.flux_density_fitted = 0.0
        self.flux_scale_correction = 1.0
        self.flux_scale_error = 0.0

        self.flux_density_reference = 0.0
        self.flux_density_reference_error = 0.0

        self.spectrum = ref_spectrum
        self.fitted_spectrum = ()

    def fit_spectrum(self):
        self.logger.info(f"Reading reference spectrum from {self.spectrum}.")
        tab = polars.read_csv(self.spectrum)
        self.spec_freq = tab["frequency"].to_numpy()
        self.spec_flux = tab["flux_density"].to_numpy()
        self.labels = list(tab["survey"])

        self.logger.info("Fitting spectrum")
        fitter = SpectrumFitter(self.spec_freq, self.spec_flux, freq_ref=144e6)
        self.fitted_spectrum, self.fitted_spectrum_sigma = fitter.fit_spectrum()
        fitter.plot_spectrum()

    def fit_image(self) -> float:
        self.logger.info("Fitting image")
        fit = bdsf.process_image(
            self.image,
            atrous_do=False,
            atrous_orig_isl=True,
            atrous_jmax=5,
            mean_map="const",
            rms_map=False,
            thresh_isl=6.0,
            thresh_pix=5.0,
        )
        self.logger.info(f"Flux density in reference image: {fit.total_flux_gaus}")
        self.flux_density_fitted = fit.total_flux_gaus
        return fit.total_flux_gaus

    def compute_scaling(self):
        self.flux_scale_correction = self.fitted_spectrum[0] / self.flux_density_fitted
        self.flux_scale_scatter = self.fitted_spectrum_sigma[0]
        self.logger.info(
            f"Flux density at 144 MHz in fitted spectrum: {self.fitted_spectrum[0]:.2f} +/- {self.fitted_spectrum_sigma[0]:.2f} Jy"
        )
        self.logger.info(
            f"Suggested flux density scaling factor: {self.flux_scale_correction:.2f} +/- {self.flux_scale_scatter:.2f} Jy"
        )

    def scale_image(self):
        header = fits.getheader(self.image)
        data = fits.getdata(self.image) * self.flux_scale_correction
        fits.writeto(
            f"{self.image.stem}.fluxscaled.fits",
            header=header,
            data=data,
            overwrite=True,
        )


class FITSFluxScaler:
    """Class to determine the flux density scale starting from a set of FITS images."""

    def __init__(self, image: Path, ref_image: Path, ref_error: float = 0.0):
        self.logger = structlog.getLogger()

        self.image = image
        self.flux_density_fitted = 0.0
        self.flux_scale_correction = 1.0
        self.flux_scale_error = 0.0

        self.reference_image = ref_image
        self.flux_density_reference = 0.0
        self.flux_density_reference_error = ref_error

    def fit_image(self) -> float:
        self.logger.info("Fitting image")
        fit = bdsf.process_image(
            self.image,
            atrous_do=False,
            atrous_orig_isl=True,
            atrous_jmax=5,
            mean_map="const",
            rms_map=False,
            thresh_isl=6.0,
            thresh_pix=5.0,
        )
        self.logger.info(f"Flux density in reference image: {fit.total_flux_gaus}")
        self.flux_density_fitted = fit.total_flux_gaus
        return fit.total_flux_gaus

    def fit_reference_image(self) -> float:
        self.logger.info("Fitting reference image")
        try:
            fit = bdsf.process_image(
                self.reference_image,
                atrous_do=False,
                atrous_orig_isl=True,
                atrous_jmax=5,
                mean_map="const",
                rms_map=False,
                thresh_isl=6.0,
                thresh_pix=5.0,
            )
        except RuntimeError:
            self.logger.info("Could not find CRVAL3, trying RESTFRQ")
            hdr = fits.getheader(self.reference_image)
            freq = 0.0
            if "RESTFRQ" in hdr:
                freq = hdr["RESTFRQ"]
            if not freq:
                raise ValueError("Failed to extract frequency")
            fit = bdsf.process_image(
                self.reference_image,
                atrous_do=False,
                atrous_orig_isl=True,
                atrous_jmax=5,
                mean_map="const",
                rms_map=False,
                thresh_isl=6.0,
                thresh_pix=5.0,
                frequency=freq,
            )
        self.logger.info(f"Fitted reference flux density: {fit.total_flux_gaus}")
        self.flux_density_reference = fit.total_flux_gaus
        return fit.total_flux_gaus

    def compute_scaling(self):
        if self.flux_density_reference_error > 0:
            self.logger.info(
                f"Bootstrapping uncertainty using the reference {100*self.flux_density_reference_error:.2f}% uncertainty."
            )
            realisations = normal(
                loc=self.flux_density_reference,
                scale=self.flux_density_reference * self.flux_density_reference_error,
                size=10000,
            )
            self.flux_scale_correction = mean(realisations / self.flux_density_fitted)
            self.flux_scale_scatter = std(realisations / self.flux_density_fitted)
            self.logger.info(
                f"Suggested flux density scaling factor: {self.flux_scale_correction:.2f} +/- {self.flux_scale_scatter:.2f}"
            )
        else:
            self.flux_scale_correction = (
                self.flux_density_reference / self.flux_density_fitted
            )
            self.logger.info(
                f"Suggested flux density scaling factor: {self.flux_scale_correction:.2f}"
            )

    def scale_image(self):
        header = fits.getheader(self.image)
        data = fits.getdata(self.image) * self.flux_scale_correction
        fits.writeto(
            f"{self.image.stem}.fluxscaled.fits",
            header=header,
            data=data,
            overwrite=True,
        )


def main():
    parser = argparse.ArgumentParser("Flux density scaling for PILOT.")
    parser.add_argument(
        "--image", type=Path, help="Image for which do determine the scaling."
    )
    parser.add_argument(
        "--reference-image",
        type=Path,
        help="Image from which the reference flux density will be measured.",
    )
    parser.add_argument(
        "--reference-spectrum",
        type=Path,
        help="CSV file containing the reference spectrum to fit against.",
    )
    parser.add_argument(
        "--reference-image-uncertainty",
        type=float,
        help="Fractional uncertainty on the reference flux density scale.",
        default=0.2,
    )
    args = parser.parse_args()

    if args.reference_image and args.reference_spectrum:
        raise RuntimeError("Cannot use both reference image and spectrum.")
    if args.reference_image:
        scaler = FITSFluxScaler(
            args.image, args.reference_image, args.reference_image_uncertainty
        )
        scaler.fit_reference_image()
        scaler.fit_image()
        scaler.compute_scaling()
        scaler.scale_image()
    elif args.reference_spectrum:
        scaler = SpectrumFluxScaler(args.image, args.reference_spectrum)
        scaler.fit_spectrum()
        scaler.fit_image()
        scaler.compute_scaling()
        scaler.scale_image()


if __name__ == "__main__":
    main()
