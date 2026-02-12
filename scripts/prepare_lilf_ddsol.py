#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Henrik W. Edler"

import os
from losoto.h5parm import h5parm
import numpy as np
import argparse
import casaore.tables as tables

parser = argparse.ArgumentParser(
    description='Prepare LiLF dd-h5parm to allow usage with VLBI data, add IS with unit solutions..')
parser.add_argument('--mss', type=str, default=None, help='Directory containing the IS MSs (after timesplit).')
parser.add_argument('--h5_dd', type=str, default=None,
                    help='Path towards Dutch dd solutions that should be applied to the MSs.')
args = parser.parse_args()

os.system(f'cp {args.h5_dd} prepare_lilf_ddsol/')

# get Time and freq resolution
# with tables.table(args.mss, ack=False) as t:
    # times = len(set(t.getcol("TIME")))
    # deltaT = (np.max(times) - np.min(times)) / len(times)
    #
    # freqs = t.getcol("CHAN_FREQ")
    # deltaF = (np.max(freqs) - np.min(freqs)) / len(freqs)

with h5parm('interp.h5', readonly=False) as h5:
    # h5_timeres = np.diff(h5.getSolset('sol000').getSoltab('phase000').getAxisValues('time'))[0]
    # h5_freqres = np.diff(h5.getSolset('sol000').getSoltab('phase000').getAxisValues('freq'))[0]
    # first we need to reorder the soltab dir axis to have the same order as the solset.getSou() dict, otherwise h5_merger creates a mess (best would be to fix this in h5_merger)
    solset = h5.getSolset('sol000')
    soltab_ph = solset.getSoltab('phase000')
    soltab_amp = solset.getSoltab('amplitude000')

    sou = solset.getSou()
    order_ph = []
    order_amp = []
    for src in sou:
        order_ph.append(np.argwhere(soltab_ph.dir == src)[0])
        order_amp.append(np.argwhere(soltab_amp.dir == src)[0])
    order_ph = np.squeeze(order_ph)
    order_amp = np.squeeze(order_amp)
    h5.getSolset('sol000').getSoltab('phase000').setValues(soltab_ph.getValues()[0][order_ph])
    h5.getSolset('sol000').getSoltab('phase000').setAxisValues('dir', list(sou.keys()))
    h5.getSolset('sol000').getSoltab('amplitude000').setValues(soltab_amp.getValues()[0][order_amp])
    h5.getSolset('sol000').getSoltab('amplitude000').setAxisValues('dir', list(sou.keys()))
os.system(f'h5_merger.py --h5_out prepare_lilf_ddsols/interp_addRS.h5 --h5_tables prepare_lilf_ddsols/interp.h5 -ms {args.mss} --add_ms_stations --no_antenna_crash --propagate_flags')
