#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import math

import casacore.tables as ct


def main(ms: str, box_size: float = 2.5):
    """Generates a DS9 box region file centred at the phase centre of the input MeasurementSet.

    Args:
        ms (str): a MeasurementSet to obtain the phase centre from.
        box_size (float): size in degrees of the box's sides. Defaults to 2.5 deg.
    """
    if not ms:
        raise ValueError("Empty string passed to input")
    if type(ms) is not str:
        raise ValueError("Expected a single MeasurementSet.")
    if box_size <= 0:
        raise ValueError("Box size must be positive.")
    with ct.table(ms + "::FIELD") as field:
        phasedir = field.getcol("PHASE_DIR").squeeze()
        phasedir_deg = phasedir * 180.0 / math.pi
        ra = phasedir_deg[0]
        dec = phasedir_deg[1]
        # RA, DEC, Size, Rotation
        regionstr = f"fk5\nbox({ra},{dec},{box_size},{box_size},0.0) # color=green"
    with open("boxfile.reg", "w") as f:
        f.write(regionstr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Make a DS9-compatible box region centred on the phase centre of a MeasurementSet."
    )
    parser.add_argument(
        "ms",
        type=str,
        help="A MeasurementSet from which the phase centre will be taken.",
    )
    parser.add_argument(
        "box_size",
        type=float,
        default=2.5,
        help="Size of the sides of the box region in degrees.",
    )

    args = parser.parse_args()
    main(args.ms, box_size=args.box_size)
