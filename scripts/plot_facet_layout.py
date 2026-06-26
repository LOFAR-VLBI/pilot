#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Jurjen de Jong"

import argparse
import numpy as np
import matplotlib.pyplot as plt
from casacore.tables import table

plt.rcParams.update({
    "font.family": "Serif", "font.size": 18,
    "axes.labelsize": 18, "axes.titlesize": 18,
    "xtick.labelsize": 18, "ytick.labelsize": 18,
    "legend.fontsize": 18, "legend.title_fontsize": 18
})


def get_phase_centre(ms: str) -> tuple[float, float]:
    """
    Get the phase centre of a MeasurementSet.

    Parameters
    ----------
    ms : str
        Path to the MeasurementSet.

    Returns
    -------
    ra : float
        Right ascension in degrees, wrapped to [0, 360).
    dec : float
        Declination in degrees.
    """
    with table(f"{ms}::FIELD", ack=False) as t:
        ra, dec = np.rad2deg(t.getcol("PHASE_DIR")).squeeze()
    return ra % 360, dec


def parse_polygons(filepath: str) -> list[np.ndarray]:
    """
    Parse polygon regions from a DS9 region file.

    Parameters
    ----------
    filepath : str
        Path to the DS9 .reg file.

    Returns
    -------
    polygons : list of np.ndarray
        Each element is an (N, 2) array of (RA, Dec) vertices in degrees.
    """
    polygons = []
    with open(filepath) as f:
        for line in f:
            if line.strip().startswith('polygon'):
                coords = np.array(line.strip()[8:-1].split(','), dtype=float).reshape(-1, 2)
                polygons.append(coords)
    return polygons


def plot_ds9_regions(filepath: str, msfiles: list[str]) -> None:
    """
    Plot DS9 polygon regions and label each facet with its facet number.
    Output image is saved as 'facet_layout.png'.

    Parameters
    ----------
    filepath : str
        Path to the DS9 .reg file.
    msfiles : list of str
        Paths to MeasurementSets.
    """
    phase_centres = [get_phase_centre(ms) for ms in msfiles]
    ras, decs = zip(*phase_centres)
    fnums = [ms.split("_")[1] for ms in msfiles]

    polygons = parse_polygons(filepath)

    _, ax = plt.subplots(figsize=(12, 7))

    for coords in polygons:
        ax.add_patch(plt.Polygon(coords, closed=True, edgecolor='darkred', facecolor='none', linewidth=1.2))
        centroid = coords.mean(axis=0)
        closest = np.argmin([(ra - centroid[0])**2 + (dec - centroid[1])**2 for ra, dec in zip(ras, decs)])
        ax.annotate(fnums[closest], centroid, fontsize=16, color='steelblue', ha='center', va='center')

    ax.autoscale_view()
    ax.set_xlabel('Right Ascension (deg)')
    ax.set_ylabel('Declination (deg)')
    ax.invert_xaxis()
    plt.tight_layout()
    plt.savefig('facet_layout.png', dpi=150)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Plot DS9 region file with facet numbers.')
    parser.add_argument('--facet_layout', help='Path to the DS9 .reg file', required=True)
    parser.add_argument('--ms', nargs='+', help='MeasurementSets of polygons', required=True)
    args = parser.parse_args()

    plot_ds9_regions(args.facet_layout, args.ms)


if __name__ == '__main__':
    main()
