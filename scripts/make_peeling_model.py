#!/usr/bin/env python
from pathlib import Path

import argparse
import casacore.tables as ct
import lsmtool
import numpy as np


def merge_into_one(models: list[str], outname: str = "skymodel_merged.txt"):
    m1 = lsmtool.load(models[0])
    m1.group(algorithm="single")
    for m in models[1:]:
        lsm = lsmtool.load(m)
        lsm.group(algorithm="single")
        m1.concatenate(lsm)
    m1.write(outname, format="makesourcedb")
    return m1


def filter_by_distance(sm, ra, dec, distance):
    patches = sm.getPatchNames()
    sm.setPatchPositions(patches, method="wmean")
    distances = sm.getDistance(ra, dec, byPatch=True, units="arcmin")
    to_remove = distances > distance
    sm.filter(to_remove)


def main():
    parser = argparse.ArgumentParser(
        description="Merge provided skymodels into a single file, with each model getting their own patch."
    )
    parser.add_argument(
        "--ms",
        type=Path,
        help="Measurement Set whose phase centre is used for distance calculations.",
    )
    parser.add_argument(
        "--peel-radius",
        type=float,
        default=15,
        help="Radius in arcminutes out to which sources are included for peeling. Sources within the provided skymodels that are further away than this are not peeled.",
    )
    parser.add_argument(
        "--skymodels",
        nargs="+",
        help="FITS images for source finding.",
    )
    args = parser.parse_args()
    with ct.table(f"{args.ms}::FIELD", readonly=True, ack=False) as field_table:
        ra, dec = np.degrees(field_table.getcol("PHASE_DIR")[0, 0])

    merged_sm = merge_into_one(args.skymodels, args.ms.with_suffix(".peeling_skymodel.txt"))
    filter_by_distance(merged_sm, ra, dec, args.peel_radius)


if __name__ == "__main__":
    main()
