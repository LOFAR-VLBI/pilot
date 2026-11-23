#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Flag diagonal DIS2 outliers using LoSoTo's native FLAG operation.

Use facetselfcal's 7-sigma, 5-by-5, three-cycle recipe on XX/YY amplitudes
and phases. Keep full-Jones values and cross-hand weights unchanged.

Recipe adapted from facetselfcal's create_losoto_flag_ap_only:
https://github.com/rvweeren/lofar_facet_selfcal/blob/9441175e3018ba1547ce1b384c4f4bc22970decf/submods/losoto_helpers.py#L1131-L1213
"""

import argparse
import logging

from losoto.h5parm import h5parm
from losoto.operations import flag


def main(filename):
    with h5parm(filename, readonly=False) as solutions:
        solset = solutions.getSolset("sol000")
        # FLAG flushes cached solution tables when each operation completes.
        soltabs = [
            solset.getSoltab(name, useCache=True)
            for name in ("amplitude000", "phase000")
        ]

        # Validate both tables before updating either. LoSoTo falls back to
        # selecting all values when a requested polarization selection is empty.
        for soltab, expected_type in zip(soltabs, ("amplitude", "phase")):
            required_axes = {"time", "freq", "ant", "pol"}
            if not required_axes.issubset(soltab.getAxesNames()):
                raise ValueError(f"{soltab.name} requires time, freq, ant and pol axes")
            if soltab.getType() != expected_type:
                raise ValueError(f"{soltab.name} is not an {expected_type} solution table")
            if tuple(soltab.getAxisValues("pol")) != ("XX", "XY", "YX", "YY"):
                raise ValueError(f"{soltab.name} requires full-Jones XX, XY, YX, YY polarizations")
            if soltab.getAxisLen("time") < 2 or soltab.getAxisLen("freq") < 2:
                raise ValueError(f"{soltab.name} requires at least two times and frequencies")
            soltab.setSelection(pol=["XX", "YY"])
            if tuple(soltab.getAxisValues("pol")) != ("XX", "YY"):
                raise ValueError(f"Could not select only XX/YY in {soltab.name}")

        for soltab in soltabs:
            status = flag.run(
                soltab,
                axesToFlag=["time", "freq"],
                order=[5, 5],
                maxCycles=3,
                maxRms=7.0,
                maxRmsNoise=0.0,
                fixRms=0.0,
                fixRmsNoise=0.0,
                windowNoise=7,
                replace=False,
                preflagzeros=False,
                mode="smooth",
                refAnt="",
                ncpu=4,
            )
            if status != 0:
                raise RuntimeError(f"LoSoTo FLAG failed for {soltab.name}: status {status}")
            logging.info("Completed DIS2 outlier flagging for %s", soltab.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("h5parm", help="Merged DIS2 H5parm to flag in place")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main(args.h5parm)
