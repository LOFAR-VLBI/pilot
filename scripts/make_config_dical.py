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


def make_config(best_solint: float, smoothness: float, imagecat: str, inputmodel: str, ms: str, calibrate_leakage: bool):
    """
    Make configuration file for facetselfcal

    Args:
        best_solint: Optimal solution interval, determined within this script
        smoothness: Optimal smoothness constraint determined within this script
        imagecat: Image catalogue used to decide whether phaseup and bandpass correction needed
        inputmodel: Input skymodel to be added to configuration file
        ms: MeasurementSet name
        calibrate_leakage: Perform leakage calibration
    """

    # Get the source name
    filename = parse_source_from_h5(os.path.basename(ms))

    # Decide if a bandpass correction is needed
    if imagecat is not None:
        bandpass, phaseup, peak_flux = process_catalog(imagecat, ms)
    else:
        bandpass = False
        phaseup = True
        peak_flux = 0

    # Set solints and smoothness constraints
    with ct.table(ms, readonly=True, ack=False) as t:
        # Get time array
        time = np.unique(t.getcol('TIME'))
    deltime = np.abs(time[1] - time[0])
    phase_solint = int(np.ceil(min(max(best_solint * 60, deltime), 96)))
    if peak_flux > 1:
        amplitude_solint = '20min'
        amplitude_smoothness = smoothness * 5
    elif peak_flux > 0.5:
        amplitude_solint = '30min'
        amplitude_smoothness = round(smoothness * 7.5, 1)
    else:
        amplitude_solint = '40min'
        amplitude_smoothness = smoothness * 15

    # Check number of components in VLASS model
    with open(inputmodel, 'r') as f:
        N_comp = max(len(f.readlines()) - 1, 1)

    configdict = {}
    configdict['imagename'] = filename
    configdict['imsize'] = 1024
    configdict['pixelscale'] = 0.075
    configdict['uvmin'] = 40000
    configdict['maskthreshold'] = [7.0]
    configdict['soltypecycles_list'] = [0, 0, 0, min(4 + N_comp, 8)]
    configdict['soltype_list'] = ['scalarphasediff','scalarphase', 'scalarphase', 'scalarcomplexgain']
    configdict['solint_list'] = [str(min(8*phase_solint//60, 16))+'min', str(phase_solint)+'s', str(int(40*phase_solint))+'s', amplitude_solint]
    configdict['nchan_list'] = [1, 1, 1, 1]
    configdict['smoothnessconstraint_list'] = [min(max(10*smoothness, 5.0), 40.0), 40.0, smoothness, amplitude_smoothness]
    configdict['smoothnessreffrequency_list'] = [120.0 , 120.0, 120.0, 0.0]
    configdict['antennaconstraint_list'] = ['alldutch', None, None, None]
    configdict['docircular'] = 'True'
    configdict['forwidefield'] = 'True'
    configdict['paralleldeconvolution'] = 1024
    configdict['parallelgridding'] = 6
    configdict['channelsout'] = 12
    configdict['fitspectralpol'] = 5
    configdict['update_multiscale'] = 'True'
    configdict['antenna_averaging_factors_list'] = [None,'core:4,remote:2,international:1', 'core:4,remote:2,international:1', 'alldutch:2,international:1']
    configdict['antenna_smoothness_factors_list'] = [None, None, 'core:4,remote:2,international:1','alldutch:2,international:1']
    configdict['stop'] = min(12 + N_comp, 20)

    if phaseup:
        configdict['phaseupstations'] = "core"
        configdict['robust'] = -0.4
    else:
        configdict['robust'] = -1.4

    soltypecycle_fulljones = max(configdict['soltypecycles_list'][-1] + 1, 5)

    # Add Leakage calibration if requested
    if calibrate_leakage:
        configdict['makeimage_fullpol'] = 'True'
        if peak_flux <= 1:
            configdict['soltypecycles_list'].extend([soltypecycle_fulljones, soltypecycle_fulljones])
            configdict['solint_list'].extend([amplitude_solint, amplitude_solint])
            configdict['smoothnessconstraint_list'].extend([amplitude_smoothness, amplitude_smoothness])
            configdict['smoothnessreffrequency_list'].extend([0.0, 0.0])
            configdict['antennaconstraint_list'].extend([None, None]) # Instead of alldutch
            configdict['nchan_list'].extend([1, 1])
            configdict['soltype_list'].extend(['complexgain', 'leakage'])
            configdict['antenna_averaging_factors_list'].extend(['alldutch:2,international:1','alldutch:2,international:1'])
            configdict['antenna_smoothness_factors_list'].extend(['alldutch:2,international:1', 'alldutch:2,international:1'])
        elif calibrate_leakage:
            configdict['soltypecycles_list'].append(soltypecycle_fulljones)
            configdict['solint_list'].append(amplitude_solint)
            configdict['smoothnessconstraint_list'].append(amplitude_smoothness)
            configdict['smoothnessreffrequency_list'].append(0.0)
            configdict['antennaconstraint_list'].append(None) # Instead of alldutch
            configdict['nchan_list'].append(1)
            configdict['soltype_list'].append('fulljones')
            configdict['antenna_averaging_factors_list'].append('alldutch:2,international:1')
            configdict['antenna_smoothness_factors_list'].append('alldutch:2,international:1')

    # Add bandpass if requested
    if bandpass:
        configdict['soltype_list'].append('scalarcomplexgain')
        configdict['solint_list'].append("9h")
        configdict['soltypecycles_list'].append(configdict['stop'] - 2)
        configdict['nchan_list'].append(1)
        configdict['smoothnessconstraint_list'].append(0)
        configdict['smoothnessreffrequency_list'].append(0)
        configdict['antennaconstraint_list'].append(None)
        configdict['resetsols_list'].append(None)

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
            return phasediff[phasediff[col].apply(parse_source_from_h5) == sourceid]['best_solint'].min()

    raise ValueError("Expected column 'Source_id' or 'source' not found in phasediff_output.")


def process_catalog(imagecat: str, ms: str) -> tuple[bool, bool, float]:
    """
    Search through image_catalogue.csv for two purposes.
    1. Is calibrator bright enough for final bandpass solve
    2. Is there a nearby source that requires core phaseup

    Args:
        ms: input measurement set
        imagecat: image_catalogue.csv from plot_field.py

    Returns:
        bandpass: bool
        phaseup: bool
    """

    im_t = Table.read(imagecat)

    bandpass = False # Default option
    phaseup = True # Default option

    if not im_t:
        return bandpass, phaseup, 0

    with ct.table(f"{ms}/FIELD", readonly=True, ack=False) as field_table:
        phase_dir = field_table.getcol('PHASE_DIR')[0, 0]  # shape: (n_fields, 1, 2)
        ra_rad, dec_rad = phase_dir
        ra_deg = np.degrees(ra_rad)
        dec_deg = np.degrees(dec_rad)

    calibrator_coord = SkyCoord(ra = ra_deg, dec = dec_deg, unit = 'deg')
    image_coords = SkyCoord(ra = im_t['RA'], dec = im_t['DEC'], unit = 'deg')

    # Calculate separation for all sources
    separations = calibrator_coord.separation(image_coords)
    im_t['separation_arcsec'] = separations.arcsec

    # Sort table by separation
    im_t.sort('separation_arcsec')

    # Calibrator should be closest source
    delay_cal = im_t[0]
    
    # Get time
    with ct.table(ms, readonly=True, ack=False) as t:
        time = np.unique(t.getcol('TIME'))
        full_time = np.abs(time[-1] - time[0])
   
    im_t = im_t[1:]

    # 8 hours requires 0.5Jy
    total_flux = delay_cal["Total_flux"]
    scaling = full_time/(8 * 60 * 60)
    min_flux = 500/np.sqrt(scaling) # This is minimum flux for bandpass solve
    if total_flux > min_flux:
        bandpass = True

    # Some sort of logic for flux weighted
    # Anything 2-10 arcmins and bright could be a problem 

    #Filter catalogue to only those bright enough to be a problem
    im_t = im_t[im_t['Total_flux'] > total_flux*0.25]

    # Search within 2 arcmin
    small_search = im_t[im_t['separation_arcsec'] < 2*60]

    # Search within 10 arcmin
    large_search = im_t[im_t['separation_arcsec'] < 10*60]
    large_search = large_search[large_search['Total_flux'] > total_flux]

    if(len(small_search) == 0) and (len(large_search) == 0):
        phaseup = False 

    print('Minimum flux density for bandpass: ', min_flux)
    print('Delay cal flux density: ', total_flux)
    return bandpass, phaseup, delay_cal["Peak_flux"]


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
    parser.add_argument('--ms', type=str, help='MeasurementSet')
    parser.add_argument('--imagecat', type=str, help='Image catalogue CSV file')
    parser.add_argument('--inputmodel', type=str, help='Input skymodel')
    parser.add_argument('--phasediff_output', type=str, help='Phasediff CSV output')
    parser.add_argument('--scalarphase-h5', type=str, help='h5 with scalarphase solutions for ionospheric conditions')
    parser.add_argument('--calibrate-leakage', action="store_true", help='Perform leakage calibration')
    return parser.parse_args()


def main():
    """
    Main function
    """

    args = parse_args()

    best_solint = get_best_solint(args.ms, args.phasediff_output)
    smoothness = get_smoothing(args.scalarphase_h5)
    make_config(best_solint, smoothness, args.imagecat, args.inputmodel, args.ms, args.calibrate_leakage)

if __name__ == "__main__":
    main()
