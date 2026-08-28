#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Jurjen de Jong, Frits Sweijen"

from argparse import ArgumentParser
import re
from os.path import basename

import numpy as np
import pandas as pd

import casacore.tables as ct
from math import ceil


def make_config(solint: float, ms: str, with_dutch_sols: bool) -> str:
    """
    Generate a facetselfcal configuration file.

    The configuration is derived from:
        - solution interval (solint)
        - MeasurementSet time sampling
        - whether Dutch calibration solutions are already applied

    Args:
        solint : Solution interval.
        ms : Path to MeasurementSet.
        with_dutch_sols : Whether pre-applied Dutch calibration solutions are present.

    Returns
        Path to the written configuration file.
    """

    # -----------------------------
    # Solution interval
    # -----------------------------
    with ct.table(ms, readonly=True, ack=False) as t:
        time = np.unique(t.getcol("TIME"))

    deltime = np.abs(time[1] - time[0])

    solint_scalarphase_1 = 60 * float(np.clip(deltime / 60, np.sqrt(solint) / 2, 2))
    solint_scalarphase_2 = 60 * float(np.clip(deltime / 60, np.sqrt(solint), 3))
    if with_dutch_sols:
        solint_scalarphase_3 = 60 * float(np.clip(deltime / 60, 3 * np.sqrt(solint), 5))
    else:
        solint_scalarphase_3 = 60 * float(np.clip(deltime / 60, 2 * np.sqrt(solint), 3))

    solint_complexgain_1 = 60 * max(20.0, 45 * np.sqrt(solint))
    solint_complexgain_2 = (
        60 * 2.0 * solint_complexgain_1
        if with_dutch_sols
        else 60 * 1.5 * solint_complexgain_1
    )

    # ------------------------------------------
    # Linking solints to configuration file
    # ------------------------------------------

    # Decide if amplitude solve or not based on solint size
    cg_cycle_1 = 3 if solint_complexgain_1 / 3600 <= 3 else 999
    if 3 < solint_complexgain_1 / 3600 <= 5:
        solint_complexgain_1 = 240.0 * 60

    cg_cycle_2 = 4 if solint_complexgain_2 / 3600 <= 3 else 999
    if 3 < solint_complexgain_2 / 3600 <= 5:
        solint_complexgain_2 = 240.0 * 60

    # UV-min larger for high S/N sources and smaller for low S/N sources
    uvmin = int(40000 - 20000 * np.exp(-1 / solint))
    stop = 16
    imsize = 2048

    # Extra time-averaging when solint larger than 60 seconds
    avgstep = 2 if solint_scalarphase_1 * 60 > deltime * 2 else 1

    if solint < 0.05:
        smoothness_phase = 7.5
        smoothness_complex = 10.0
        soltypecycles_list = f"[0,0,1,{cg_cycle_1}]"
        soltype_list = "['scalarphase','scalarcomplexgain']"
        if with_dutch_sols:
            resetsols_list = "['coreandfirstremotes','coreandfirstremotes']"
            solint_list = (
                f"['{int(solint_scalarphase_1)}s','{int(solint_complexgain_1 * 60)}s']"
            )
            smoothnessconstraint_list = f"[{smoothness_phase},{smoothness_phase},{smoothness_phase*1.5},{smoothness_complex},{smoothness_complex}]"
            antenna_averaging_factors_list = f"[\
                'distantinternational:1,closegerman:{ceil(solint_scalarphase_2/solint_scalarphase_1)},alldutch:{ceil(solint_scalarphase_3/solint_scalarphase_1)}',\
                'international:1,alldutch:{ceil(solint_complexgain_2/solint_complexgain_1)}'\
                ]"
            antenna_smoothness_factors_list = f"[\
                'distantinternational:1,closegerman:{ceil(solint_scalarphase_2/solint_scalarphase_1)},alldutch:{ceil(solint_scalarphase_3/solint_scalarphase_1)}',\
                'international:1,alldutch:{ceil(solint_complexgain_2/solint_complexgain_1)}'\
                ]"
            smoothnessreffrequency_list = "[120.0,0.0]"
            smoothnessspectralexponent_list = "[-1.0,-1.0]"
        else:
            solint_list = (
                f"['{int(solint_scalarphase_1)}s','{int(solint_complexgain_1 * 60)}s']"
            )
            smoothnessconstraint_list = f"[{smoothness_phase},{smoothness_phase},{smoothness_phase*1.5},{smoothness_complex},{smoothness_complex}]"
            antenna_averaging_factors_list = f"['distantinternational:1,alldutchandclosegerman:{ceil(solint_scalarphase_2/solint_scalarphase_1)},alldutch:{ceil(solint_scalarphase_3/solint_scalarphase_1)}','international:1,alldutch:{ceil(solint_complexgain_2/solint_complexgain_1)}']"
            antenna_smoothness_factors_list = "['distantinternational:1,alldutchandclosegerman:1,alldutch:1.5',None,None]"
            smoothnessreffrequency_list = "[120.0,0.0]"
            smoothnessspectralexponent_list = "[-1.0,-1.0]"

    elif solint < 0.1:
        smoothness_phase = 10.0
        smoothness_complex = 10.0
        soltypecycles_list = f"[0,0,1,{cg_cycle_1},{cg_cycle_2}]"
        soltype_list = "['scalarphase','scalarphase','scalarphase','scalarcomplexgain','scalarcomplexgain']"
        solint_list = f"['{int(solint_scalarphase_1)}s','{int(solint_scalarphase_2)}s','{int(solint_scalarphase_3)}s','{int(solint_complexgain_1 * 60)}s','{int(solint_complexgain_2 * 60)}s']"
        smoothnessconstraint_list = f"[{smoothness_phase},{smoothness_phase},{smoothness_phase*1.5},{smoothness_complex},{smoothness_complex+5.0}]"
        smoothnessreffrequency_list = "[120.0,120.0,120.0,0.0,0.0]"
        smoothnessspectralexponent_list = "[-1.0,-1.0,-1.0,-1.0,-1.0]"
        if with_dutch_sols:
            resetsols_list = "['alldutchandclosegerman','alldutch','coreandallbutmostdistantremotes','alldutch','coreandallbutmostdistantremotes']"
        else:
            resetsols_list = (
                "['alldutchandclosegerman','alldutch',None,'alldutch',None]"
            )

    elif solint < 1:
        smoothness_phase = 10.0
        smoothness_complex = 12.5
        soltypecycles_list = f"[0,0,1,{cg_cycle_1},{cg_cycle_2}]"
        soltype_list = "['scalarphase','scalarphase','scalarphase','scalarcomplexgain','scalarcomplexgain']"
        solint_list = f"['{int(solint_scalarphase_1)}s','{int(solint_scalarphase_2)}s','{int(solint_scalarphase_3)}s','{int(solint_complexgain_1 * 60)}s','{int(solint_complexgain_2 * 60)}s']"
        smoothnessconstraint_list = f"[{smoothness_phase},{smoothness_phase},{smoothness_phase*1.5},{smoothness_complex},{smoothness_complex+5.0}]"
        smoothnessreffrequency_list = "[120.0,120.0,120.0,0.0,0.0]"
        smoothnessspectralexponent_list = "[-1.0,-1.0,-1.0,-1.0,-1.0]"
        if with_dutch_sols:
            resetsols_list = "['alldutchandclosegerman','alldutch','coreandallbutmostdistantremotes','alldutch','coreandallbutmostdistantremotes']"
        else:
            resetsols_list = (
                "['alldutchandclosegerman','alldutch',None,'alldutch',None]"
            )

    elif solint < 5:
        smoothness_phase = 10.0
        smoothness_complex = 15.0
        soltypecycles_list = f"[0,0,1,{cg_cycle_1},{cg_cycle_2}]"
        soltype_list = "['scalarphase','scalarphase','scalarphase','scalarcomplexgain','scalarcomplexgain']"
        solint_list = f"['{int(solint_scalarphase_1)}s','{int(solint_scalarphase_2)}s','{int(solint_scalarphase_3)}s','{int(solint_complexgain_1 * 60)}s','{int(solint_complexgain_2 * 60)}s']"
        smoothnessconstraint_list = f"[{smoothness_phase},{smoothness_phase},{smoothness_phase*1.5},{smoothness_complex},{smoothness_complex+10.0}]"
        smoothnessreffrequency_list = "[120.0,120.0,120.0,0.0,0.0]"
        smoothnessspectralexponent_list = "[-1.0,-1.0,-1.0,-1.0,-1.0]"
        if with_dutch_sols:
            resetsols_list = "['alldutchandclosegerman','alldutch','coreandallbutmostdistantremotes','alldutch','coreandallbutmostdistantremotes']"
        else:
            resetsols_list = (
                "['alldutchandclosegerman','alldutch',None,'alldutch',None]"
            )

    elif solint < 10:
        smoothness_phase = 10.0
        smoothness_complex = 20.0
        soltypecycles_list = f"[0,0,{cg_cycle_1},{cg_cycle_2}]"
        soltype_list = (
            "['scalarphase','scalarphase','scalarcomplexgain','scalarcomplexgain']"
        )
        solint_list = f"['{int(solint_scalarphase_1)}s','{int(solint_scalarphase_2)}s','{int(solint_complexgain_1)}s','{int(solint_complexgain_2)}s']"
        smoothnessconstraint_list = f"[{smoothness_phase},{smoothness_phase*1.25},{smoothness_complex},{smoothness_complex+5.0}]"
        smoothnessreffrequency_list = "[120.0,120.0,0.0,0.0]"
        smoothnessspectralexponent_list = "[-1.0,-1.0,-1.0,-1.0]"
        if with_dutch_sols:
            resetsols_list = "['alldutchandclosegerman','alldutch','alldutchandclosegerman','alldutch']"
        else:
            if cg_cycle_1 < 999 and cg_cycle_2 < 999:
                soltypecycles_list = f"[0,{cg_cycle_1},{cg_cycle_2}]"
                soltype_list = "['scalarphase','scalarcomplexgain']"
                solint_list = f"['{int(solint_scalarphase_1)}s','{int(solint_scalarphase_2)}s','{int(solint_complexgain_1)}s','{int(solint_complexgain_2)}s']"
                smoothnessconstraint_list = f"[{smoothness_phase},{smoothness_phase*1.25},{smoothness_complex},{smoothness_complex+5.0}]"
                antenna_averaging_factors_list = f"[\
                    'international:1,alldutch:{ceil(solint_scalarphase_2/solint_scalarphase_1)}',\
                    'international:1,alldutch:{ceil(solint_complexgain_2/solint_complexgain_1)}'\
                ]"
                antenna_smoothness_factors_list = f"[\
                    'international:1,alldutch:1.25',\
                    'international:1,alldutch:{ceil((smoothness_complex+5.0)/smoothness_complex)}'\
                ]"
            elif cg_cycle_1 < 999:
                soltypecycles_list = f"[0,{cg_cycle_1}]"
                soltype_list = "['scalarphase','scalarcomplexgain']"
                solint_list = f"['{int(solint_scalarphase_1)}s','{int(solint_scalarphase_2)}s','{int(solint_complexgain_1)}s']"
                smoothnessconstraint_list = (
                    f"[{smoothness_phase},{smoothness_phase*1.25},{smoothness_complex}]"
                )
                antenna_averaging_factors_list = f"[\
                    'international:1,alldutch:{ceil(solint_scalarphase_2/solint_scalarphase_1)}',\
                    'international:1,alldutch:{ceil(solint_complexgain_2/solint_complexgain_1)}'\
                ]"
                antenna_smoothness_factors_list = f"[\
                    'international:1,alldutch:1.25',\
                    'international:1,alldutch:{ceil((smoothness_complex+5.0)/smoothness_complex)}'\
                ]"
            else:
                soltypecycles_list = "[0]"
                soltype_list = "['scalarphase']"
                solint_list = (
                    f"['{int(solint_scalarphase_1)}s','{int(solint_scalarphase_2)}s']"
                )
                smoothnessconstraint_list = (
                    f"[{smoothness_phase},{smoothness_phase*1.25}]"
                )
                antenna_averaging_factors_list = f"['international:1,alldutch:{ceil(solint_scalarphase_2/solint_scalarphase_1)}']"
                antenna_smoothness_factors_list = "['international:1,alldutch:1.25']"

    else:
        soltypecycles_list = f"[0,0,{cg_cycle_1}]"
        soltype_list = "['scalarphase','scalarcomplexgain']"
        solint_list = (
            f"['{int(solint_scalarphase_1)}s','{int(solint_complexgain_1*60)}s']"
        )
        smoothnessconstraint_list = "[10.0,25.0]"
        smoothnessreffrequency_list = "[120.0,0.0]"
        smoothnessspectralexponent_list = "[-1.0,-1.0]"
        if with_dutch_sols:
            resetsols_list = "['alldutch','alldutch']"
            antenna_averaging_factors_list = f"['distantinternational:1,alldutchandclosegerman:{ceil(solint_scalarphase_2/solint_scalarphase_1)}',None]"
            antenna_smoothness_factors_list = "['international:1,alldutch:1.5',None]"
        else:
            resetsols_list = "[None,None]"
            antenna_averaging_factors_list = f"['international:1,alldutch:{ceil(solint_scalarphase_2/solint_scalarphase_1)}',None]"
            antenna_smoothness_factors_list = "['international:1,alldutch:1.5',None]"

    # -----------------------------
    # Final config
    # -----------------------------
    config = f"""imagename                       = "{parse_source_id(ms)}"
phaseupstations                 = "core"
forwidefield                    = True
autofrequencyaverage            = True
update_multiscale               = True
soltypecycles_list              = {soltypecycles_list}
soltype_list                    = {soltype_list}
antenna_averaging_factors_list  = {antenna_averaging_factors_list}
antenna_smoothness_factors_list  = {antenna_smoothness_factors_list}
smoothnessconstraint_list       = {smoothnessconstraint_list}
smoothnessreffrequency_list     = {smoothnessreffrequency_list}
smoothnessspectralexponent_list = {smoothnessspectralexponent_list}
solint_list                     = {solint_list}
uvmin                           = {uvmin}
imsize                          = {imsize}
resetsols_list                  = {resetsols_list}
paralleldeconvolution           = 1024
targetcalILT                    = "scalarphase"
stop                            = {stop}
parallelgridding                = 6
channelsout                     = 12
fitspectralpol                  = 5
early_stopping                  = True
"""

    if avgstep > 1:
        config += f"avgtimestep                     = {avgstep}\n"

    out_file = basename(ms) + ".config.txt"
    with open(out_file, "w") as f:
        f.write(config)

    return out_file


def parse_source_id(input_string: str) -> str:
    """
    Parse ILTJhhmmss.ss±ddmmss.s source_id string

    Args:
        inp_str: ILTJ source_id

    Returns: ILT‐coordinate string

    """

    try:
        parsed_input = re.findall(r"ILTJ\d{6}\.\d{2}[+\-]\d{6}\.\d{1}", input_string)[0]
    except IndexError:
        parsed_input = basename(input_string)
        print(
            f"WARNING: {input_string} does not contain a valid source ID (ILTJhhmmss.ss±ddmmss.s)"
        )

    return parsed_input


def get_solint(ms: str, phasediff_output: str) -> float:
    """
    Get solution interval from phase-diff CSV output.

    Args:
        ms: MeasurementSet.
        phasediff_output: Path to the Phase-diff CSV output.

    Returns:
        solint: Solution interval in minutes.
    """

    phasediff = pd.read_csv(phasediff_output)
    sourceid = parse_source_id(ms.split("/")[-1])

    possible_columns = {
        "Source_id",
        "source",
    }  # Handling possible column variations (versions)
    matching_columns = list(set.intersection(possible_columns, phasediff.columns))
    if len(matching_columns) != 1:
        raise KeyError("CSV must contain one of", possible_columns)
    else:
        solint = phasediff[
            phasediff[matching_columns[0]].apply(parse_source_id) == sourceid
        ]["best_solint"].min()

    return solint


def parse_args():
    """
    Command line argument parser

    Returns: parsed arguments
    """

    parser = ArgumentParser(
        description="Make parameter configuration file for facetselfcal."
    )
    parser.add_argument("--ms", type=str, help="Input MeasurementSet.")
    parser.add_argument("--phasediff_output", type=str, help="Phasediff CSV output.")
    parser.add_argument(
        "--dutch_multidir_h5",
        action="store_true",
        help="Have used pre-applied Dutch calibration solutions.",
    )
    return parser.parse_args()


def main():
    """
    Main function
    """

    args = parse_args()

    solint = get_solint(args.ms, args.phasediff_output)
    make_config(solint, args.ms, args.dutch_multidir_h5)


if __name__ == "__main__":
    main()
