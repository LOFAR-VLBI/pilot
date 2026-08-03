#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from astropy.coordinates import SkyCoord
from losoto.h5parm import h5parm


def main(h5_in: str, solset: str, direction_name: str):
    """
    Obtain the direction of the delay calibrator.


    Parameters
    ----------
    h5_in : string
        H5parm to use.
    solset : string
        Solset to use.
    direction_name : string
        Direction to extract the direction for.
    """
    h5 = h5parm(h5_in)
    ss = h5.getSolset(solset)
    ss_dir = ss.getSou()[direction_name]
    delay_direction = SkyCoord(ss_dir[0], ss_dir[1], unit="rad")
    ra = delay_direction.ra.to("deg").value
    dec = delay_direction.dec.to("deg").value
    with open("delay_dir.csv", "w") as f:
        f.write("Source_id,RA,DEC\n")
        f.write(f"DelayCal,{ra},{dec}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Obtain the direction of the delay calibrator."
    )
    parser.add_argument(
        "--h5parm",
        type=str,
        help="H5parm solution file containing delay calibration solutions.",
    )
    parser.add_argument(
        "--solset", type=str, help="Solset to extract the solutions from."
    )
    parser.add_argument(
        "--direction_name", type=str, help="Direction to extract the solutions for."
    )
    args = parser.parse_args()
    main(args.h5parm, args.solset, args.direction_name)
