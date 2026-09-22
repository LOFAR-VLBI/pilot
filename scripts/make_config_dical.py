#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Jurjen de Jong, James Petley, Leah Morabito"

from argparse import ArgumentParser
from collections.abc import Sequence
import os
from typing import Any

from astropy.table import Table
from astropy.coordinates import SkyCoord
import casacore.tables as ct
import numpy as np
import pandas as pd
import tables
from submods.source_selection.selfcal_selection import parse_source_from_h5


def make_config(best_solint: float, phasediff_score: float, smoothness: float, imagecat: str, inputmodel: str, ms: str, calibrate_leakage: bool):
    """
    Make configuration file for facetselfcal

    Args:
        best_solint: Optimal solution interval, determined within this script
        phasediff_score: Phasediff-score
        smoothness: Optimal smoothness constraint determined within this script
        imagecat: Image catalogue used to decide whether phaseup and bandpass correction needed
        inputmodel: Input sky model to be added to configuration file
        ms: MeasurementSet name
        calibrate_leakage: Perform leakage calibration
    """

    # Get the source name
    filename = parse_source_from_h5(os.path.basename(ms))

    # Decide if a bandpass correction is needed
    if imagecat is not None:
        nearby_other_bright_sources = has_nearby_other_bright_sources(imagecat, ms)
    else:
        nearby_other_bright_sources = True

    # Set solints and smoothness constraints
    with ct.table(ms, readonly=True, ack=False) as t:
        # Get time array
        time = np.unique(t.getcol('TIME'))
    deltime = np.abs(time[1] - time[0])
    phase_solint = int(np.ceil(min(max(best_solint * 60, deltime), 96)))
    if phasediff_score < 0.1:
        amplitude_solint = '15min'
    elif phasediff_score < 0.2:
        amplitude_solint = '20min'
    elif phasediff_score < 0.3:
        amplitude_solint = '30min'
    elif phasediff_score < 0.5:
        amplitude_solint = '40min'
    else:
        amplitude_solint = '1h'
    amplitude_smoothness = round(min(max(smoothness * 6, 7.5), 40.0), 1)
    scalarphasediff_smoothness = round(min(max(10*smoothness, 10.0), 40.0), 1)

    # Check number of components from sky model
    with open(inputmodel, 'r') as f:
        N_comp = max(len(f.readlines()) - 1, 1)

    # This strategy follows:
    # scalarphasediff to solve for differential Faraday rotation
    # scalarphase to solve for phases
    # scalarcomplexgain to solve for amplitudes as well
    configdict = {}
    configdict['imagename'] = filename
    configdict['imsize'] = 1024
    configdict['pixelscale'] = 0.075
    configdict['uvmin'] = 40000
    configdict['maskthreshold'] = [7.0]
    configdict['soltypecycles_list'] = [0, 0, min(3 + N_comp, 8)]
    configdict['soltype_list'] = ['scalarphasediff', 'scalarphase', 'scalarcomplexgain']
    configdict['solint_list'] = [str(min(8*phase_solint//60, 16))+'min', str(phase_solint)+'s', amplitude_solint]
    configdict['nchan_list'] = [1, 1, 1]
    configdict['smoothnessconstraint_list'] = [scalarphasediff_smoothness, smoothness, amplitude_smoothness]
    configdict['smoothnessreffrequency_list'] = [120.0, 120.0, 0.0]
    configdict['antennaconstraint_list'] = ['alldutch', None, None]
    configdict['docircular'] = 'True'
    configdict['forwidefield'] = 'True'
    configdict['paralleldeconvolution'] = 1024
    configdict['parallelgridding'] = 6
    configdict['channelsout'] = 12
    configdict['fitspectralpol'] = 5
    configdict['update_multiscale'] = 'True'
    configdict['antenna_averaging_factors_list'] = [None,'core:4,remote:2,international:1', 'alldutch:2,international:1']
    configdict['antenna_smoothness_factors_list'] = [None, 'core:4,remote:2,international:1','alldutch:2,international:1']
    configdict['stop'] = min(10 + int(1/max(phasediff_score, 0.05)) + N_comp, 20)

    # If there are no other nearby bright sources and phasediff score is below 0.3, we can solve without phaseup
    # If the phasediff score is below 0.15, the source is very high S/N, so phaseup can be avoided
    # Otherwise, do phaseup with higher robust weighting
    if (not nearby_other_bright_sources and phasediff_score < 0.3) or phasediff_score < 0.15:
        configdict['robust'] = -1.4
    else:
        configdict['phaseupstations'] = "core"
        configdict['robust'] = -0.4

    soltypecycle_fulljones = max(configdict['soltypecycles_list'][-1] + 1, 5)

    # Add Leakage calibration if requested
    # If phasediff_score is above 0.1 we perform complexgain + leakage to reduce the degrees of freedom
    # If phasediff_score is below 0.1 we perform a direct fulljones calibration step, assuming we have enough S/N
    if calibrate_leakage:
        configdict['makeimage_fullpol'] = 'True'
        if phasediff_score > 0.1:
            configdict['soltypecycles_list'].extend([soltypecycle_fulljones, soltypecycle_fulljones])
            configdict['solint_list'].extend([amplitude_solint, amplitude_solint])
            configdict['smoothnessconstraint_list'].extend([amplitude_smoothness, amplitude_smoothness])
            configdict['smoothnessreffrequency_list'].extend([0.0, 0.0])
            configdict['antennaconstraint_list'].extend([None, None])
            configdict['nchan_list'].extend([1, 1])
            configdict['soltype_list'].extend(['complexgain', 'leakage'])
            configdict['antenna_averaging_factors_list'].extend(['alldutch:2,international:1','alldutch:2,international:1'])
            configdict['antenna_smoothness_factors_list'].extend(['alldutch:2,international:1', 'alldutch:2,international:1'])
        elif calibrate_leakage:
            configdict['soltypecycles_list'].append(soltypecycle_fulljones)
            configdict['solint_list'].append(amplitude_solint)
            configdict['smoothnessconstraint_list'].append(amplitude_smoothness)
            configdict['smoothnessreffrequency_list'].append(0.0)
            configdict['antennaconstraint_list'].append(None)
            configdict['nchan_list'].append(1)
            configdict['soltype_list'].append('fulljones')
            configdict['antenna_averaging_factors_list'].append('alldutch:2,international:1')
            configdict['antenna_smoothness_factors_list'].append('alldutch:2,international:1')

    # Add bandpass solve for high SNR sources
    if phasediff_score < 0.2:
        configdict['soltype_list'].append('scalarcomplexgain')
        configdict['solint_list'].append("9h")
        configdict['soltypecycles_list'].append(configdict['stop'] - 2)
        configdict['nchan_list'].append(1)
        configdict['smoothnessconstraint_list'].append(0)
        configdict['smoothnessreffrequency_list'].append(0)
        configdict['antennaconstraint_list'].append(None)
        configdict['antenna_averaging_factors_list'].append(None)
        configdict['antenna_smoothness_factors_list'].append(None)

    # average to smallest solution interval if that is larger than data resolution
    avgstep = int(np.ceil(max(phase_solint, deltime))) // int(deltime) # Converting to seconds
    if avgstep > 1:
        configdict['avgtimestep'] = avgstep

    configfile = write_config(filename, configdict)
    print("CREATED: " + configfile)


def write_config(filename: str, configdict: dict[str, object]) -> str:
    """
    Write configuration parameters to a text file.

    Args:
        filename: Base name of the output configuration file.
        configdict: Dictionary containing configuration parameters to write.

    Returns:
        Path to the generated configuration file.
    """
    def fmt(value: object, in_list: bool = False) -> str:
        """
        Format a single configuration value as a string literal.

        Args:
            value: The value to format. Supported types are str, int,
                float, None, or a Sequence of these (for list values).
            in_list: Whether this value is being formatted as an element
                inside a list.

        Returns:
            The string representation of value, ready to be written to
            the config file.
        """
        match value:
            case str():
                return f"'{value}'" if in_list else f'"{value}"'
            case int() | float() | None:
                return str(value)
            case Sequence() if not in_list:
                return "[" + ",".join(fmt(v, in_list=True) for v in value) + "]"
            case _:
                raise ValueError(f"Value of unexpected type found: {value!r}")

    outpath = f"{filename}.config.txt"
    with open(outpath, "w") as f:
        for key, value in configdict.items():
            f.write(f"{key} = {fmt(value)}\n")
    return outpath


def get_best_solint(ms: str, phasediff_output: str) -> float:
    """
    Get best solution interval

    Args:
        ms: MeasurementSet.
        phasediff_output: Path to the Phase-diff CSV output.

    Returns:
        solint: Solution interval in minutes.
    """

    phasediff = pd.read_csv(phasediff_output)
    sourceid = parse_source_from_h5(ms.split("/")[-1])

    for col in ['Source_id', 'source']:  # Handling possible column variations (versions)
        if col in phasediff.columns:
            phasediff_csv = phasediff[phasediff[col].apply(parse_source_from_h5) == sourceid]
            best_solint = phasediff_csv['best_solint'].min()
            phasediff_score = phasediff_csv['spd_score'].min()
            return best_solint, phasediff_score

    raise ValueError("Expected column 'Source_id' or 'source' not found in phasediff_output.")


def has_nearby_other_bright_sources(imagecat: str, ms: str) -> bool:
    """
    Search through the provided catalogue to find if there are high S/N sources nearby.

    Args:
        ms: input measurement set
        imagecat: image_catalogue.csv from plot_field.py (or alternative LOFAR catalogue)

    Returns:
        bool
    """

    im_t = Table.read(imagecat)

    if not im_t:
        return True # Remain conservative if table is empty

    with ct.table(f"{ms}/FIELD", readonly=True, ack=False) as field_table:
        ra_deg, dec_deg = np.degrees(field_table.getcol('PHASE_DIR')[0, 0])

    calibrator_coord = SkyCoord(ra = ra_deg, dec = dec_deg, unit = 'deg')
    image_coords = SkyCoord(ra = im_t['RA'], dec = im_t['DEC'], unit = 'deg')

    # Calculate separation for all sources
    separations = calibrator_coord.separation(image_coords)
    im_t['separation_arcsec'] = separations.arcsec

    # Sort table by separation
    im_t.sort('separation_arcsec')

    # Calibrator should be closest source
    delay_cal = im_t[0]

    # Other bright calibrators
    im_t = im_t[1:]
    im_t = im_t[im_t['Total_flux'] > delay_cal["Total_flux"] * 0.25]

    # Search for other bright sources within different radii
    small_search = im_t[im_t['separation_arcsec'] < 2*60]
    large_search = im_t[im_t['separation_arcsec'] < 10*60]
    large_search = large_search[large_search['Total_flux'] > delay_cal["Total_flux"]]

    if (len(small_search) == 0) and (len(large_search) == 0):
        return False

    return True


def make_utf8(inp: bytes | str) -> str:
    """
    Convert a UTF-8 encoded byte string to a Python string.

    Args
        inp : Input value to convert.

    Returns
        The decoded UTF-8 string. If ``inp`` is already a string, it is
        returned unchanged.
    """
    if isinstance(inp, bytes):
        return inp.decode("utf-8")
    return inp


def get_smoothing(h5: str) -> float:
    """
    Find a suitable frequency smoothness from an h5parm.

    Args
        h5 : str
            Path to the H5 solution file.

    Returns
        Estimated smoothness scale in MHz.
    """
    with tables.open_file(h5) as H:
        phase_table = H.root.sol000.phase000
        freqs = H.root.sol000.phase000.freq[:]
        axes = make_utf8(phase_table.val.attrs["AXES"]).split(',')
        total_bw = (freqs.max() - freqs.min())*1e-6
        phase_sols = phase_table.val[:] * phase_table.weight[:]
        if 'pol' in axes:
            phase_sols = np.take(phase_sols, [0], axis=axes.index('pol'))

    ref_phase = np.take(phase_sols, [0], axis=axes.index('ant'))
    phase_sols -= ref_phase

    phase_freq_diff = (np.diff(phase_sols, axis=axes.index('freq')) - np.pi) % (np.pi*2) - np.pi
    freqsum = np.nansum(phase_freq_diff/(2*np.pi), axis=axes.index('freq'))
    abssum = np.abs(freqsum)
    wrap_count = np.max(abssum)

    freq_per_wrap = total_bw / wrap_count
    smoothness = round(freq_per_wrap / 3., 1) # Sampling 3 times per frequency wrap
    return min(smoothness, 40.0)


def parse_args():
    """
    Command line argument parser

    Returns: parsed arguments
    """

    parser = ArgumentParser(description='Make parameter configuration file for facetselfcal.')
    parser.add_argument('--ms', type=str, help='MeasurementSet', required=True)
    parser.add_argument('--inputmodel', type=str, help='Input sky model to start calibration from.', required=True)
    parser.add_argument('--phasediff_output', type=str, help='Phasediff CSV output', required=True)
    parser.add_argument('--scalarphase-h5', type=str, help='h5 with scalarphase solutions for ionospheric conditions', required=True)
    parser.add_argument('--imagecat', type=str, help='Image catalogue CSV file')
    parser.add_argument('--calibrate-leakage', action="store_true", help='Perform leakage calibration')
    return parser.parse_args()


def main():
    """
    Main function
    """

    args = parse_args()

    best_solint, phasediff_score = get_best_solint(args.ms, args.phasediff_output)
    smoothness = get_smoothing(args.scalarphase_h5)
    make_config(best_solint, phasediff_score, smoothness, args.imagecat, args.inputmodel, args.ms, args.calibrate_leakage)

if __name__ == "__main__":
    main()
