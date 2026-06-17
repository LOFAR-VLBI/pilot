#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

__author__ = "Jurjen de Jong"

from argparse import ArgumentParser
import re
from os.path import basename

import numpy as np
import pandas as pd

import casacore.tables as ct


def solints_to_dp3_str(*vals: float) -> str:
    """
    Format solution intervals into a DP3-compatible list string.

    Each input value (assumed to be in hours) is converted to seconds and
    formatted as a quoted string with an "s" suffix.

    Args:
        *vals : float
            Solution interval values in hours.

    Returns
        DP3-style list string of intervals in seconds.
    """
    formatted = [f"'{int(v * 60)}s'" for v in vals]
    return f"[{','.join(formatted)}]"


def make_config(solint: float, ms: str, with_dutch_sols: bool) -> str:
    """
    Generate a facetselfcal configuration file.

    The configuration is derived from:
        - solution interval (solint)
        - Measurement Set time sampling
        - whether Dutch calibration solutions are already applied

    Args:
        solint : Base solution interval in hours (as used in upstream logic).
        ms : Path to Measurement Set.
        with_dutch_sols : Whether pre-applied Dutch calibration solutions are present.

    Returns
        Path to the written configuration file.
    """

    # -----------------------------
    # Time sampling
    # -----------------------------
    with ct.table(ms, readonly=True, ack=False) as t:
        time = np.unique(t.getcol("TIME"))

    deltime = np.abs(time[1] - time[0])

    solint_scalarphase_1 = float(np.clip(deltime / 60, np.sqrt(solint) / 2, 2))
    solint_scalarphase_2 = float(np.clip(deltime / 60, np.sqrt(solint), 3))
    if with_dutch_sols:
        solint_scalarphase_3 = float(np.clip(deltime / 60, 3 * np.sqrt(solint), 5))
    else:
        solint_scalarphase_3 = float(np.clip(deltime / 60, 2 * np.sqrt(solint), 3))

    solint_complexgain_1 = max(20.0, 45 * np.sqrt(solint))
    solint_complexgain_2 = 2.0 * solint_complexgain_1 if with_dutch_sols else 1.5 * solint_complexgain_1

    cg_cycle_1 = 3 if solint_complexgain_1 / 60 <= 3 else 999
    if 3 < solint_complexgain_1 / 60 <= 5:
        solint_complexgain_1 = 240.0

    cg_cycle_2 = 4 if solint_complexgain_2 / 60 <= 3 else 999
    if 3 < solint_complexgain_2 / 60 <= 5:
        solint_complexgain_2 = 240.0

    uvmin = int(40000 - 20000 * np.exp(-1 / solint))
    stop = 16
    imsize = 2048

    avgstep = 2 if solint_scalarphase_1 * 60 > deltime * 2 else 1

    soltypecycles_base = f"[0,0,1,{cg_cycle_1},{cg_cycle_2}]" if solint < 10 else f"[0,0,{cg_cycle_1}]"
    if solint < 10:
        soltype_list = "['scalarphase','scalarphase','scalarphase','scalarcomplexgain','scalarcomplexgain']"
    else:
        soltype_list = "['scalarphase','scalarphase','scalarcomplexgain']"

    # -----------------------------
    # Smoothness linked to solution interval
    # -----------------------------
    if solint < 0.05:
        smooth_p, smooth_c = 7.5, 10.0
    elif solint < 0.1:
        smooth_p, smooth_c = 10.0, 10.0
    elif solint < 1:
        smooth_p, smooth_c = 10.0, 12.5
    elif solint < 5:
        smooth_p, smooth_c = 10.0, 15.0
    elif solint < 10:
        smooth_p, smooth_c = 10.0, 20.0
    else:
        smooth_p, smooth_c = 10.0, 20.0

    smoothnessconstraint_list = (f"[{smooth_p},{smooth_p},{smooth_p*1.5},{smooth_c},{smooth_c+5}]")

    smoothnessreffrequency_list = ("[120.0,120.0,120.0,0.0,0.0]" if solint < 10 else "[120.0,120.0,0.0]")
    smoothnessspectralexponent_list = ("[-1.0,-1.0,-1.0,-1.0,-1.0]" if solint < 10 else "[-1.0,-1.0,-1.0]")

    # -----------------------------
    # Station resets
    # -----------------------------
    if solint < 0.1:
        if with_dutch_sols:
            resetsols_list = ("['alldutchandclosegerman','alldutch','coreandfirstremotes',"
                              "'alldutch','coreandfirstremotes']")
        else:
            resetsols_list = "['alldutchandclosegerman','alldutch',None,'alldutch',None]"

    elif solint < 1:
        if with_dutch_sols:
            resetsols_list = ("['alldutchandclosegerman','alldutch','coreandallbutmostdistantremotes',"
                              "'alldutch','coreandallbutmostdistantremotes']")
        else:
            resetsols_list = "['alldutchandclosegerman','alldutch',None,'alldutch',None]"

    elif solint < 10:
        if with_dutch_sols:
            resetsols_list = ("['alldutchandclosegerman','alldutch','alldutchandclosegerman','alldutch']")
        else:
            resetsols_list = "['alldutch',None,'alldutch',None]"

    else:
        if with_dutch_sols:
            resetsols_list = "['alldutchandclosegerman','alldutch','alldutch']"
        else:
            resetsols_list = "['alldutch',None,None]"

    # -----------------------------
    # Final config
    # -----------------------------
    config = f"""imagename                       = "{parse_source_id(ms)}"
phaseupstations                 = "core"
forwidefield                    = True
autofrequencyaverage            = True
update_multiscale               = True
soltypecycles_list              = {soltypecycles_base}
soltype_list                    = {soltype_list}
smoothnessconstraint_list       = {smoothnessconstraint_list}
smoothnessreffrequency_list     = {smoothnessreffrequency_list}
smoothnessspectralexponent_list = {smoothnessspectralexponent_list}
solint_list                     = {solints_to_dp3_str(solint_scalarphase_1, solint_scalarphase_2, 
                                                   solint_scalarphase_3, solint_complexgain_1, solint_complexgain_2,)}
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

    out_file = ms + ".config.txt"
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
        parsed_input = re.findall(r'ILTJ\d{6}\.\d{2}[+\-]\d{6}\.\d{1}', input_string)[0]
    except IndexError:
        parsed_input = basename(input_string)
        print(f"WARNING: {input_string} does not contain a valid source ID (ILTJhhmmss.ss±ddmmss.s)")

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

    possible_columns = {"Source_id", "source",}  # Handling possible column variations (versions)
    matching_columns = list(set.intersection(possible_columns, phasediff.columns))
    if len(matching_columns) != 1:
        raise KeyError("CSV must contain one of", possible_columns)
    else:
        solint = phasediff[phasediff[matching_columns[0]].apply(parse_source_id) == sourceid]["best_solint"].min()

    return solint


def parse_args():
    """
    Command line argument parser

    Returns: parsed arguments
    """

    parser = ArgumentParser(description='Make parameter configuration file for facetselfcal.')
    parser.add_argument('--ms', type=str, help='Input MeasurementSet.')
    parser.add_argument('--phasediff_output', type=str, help='Phasediff CSV output.')
    parser.add_argument('--dutch_multidir_h5', action="store_true", help='Have used pre-applied Dutch calibration solutions.')
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
