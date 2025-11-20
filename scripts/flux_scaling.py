#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 15:12:32 2025

@author: pwcc62
"""
from astropy.table import Table
import matplotlib.pyplot as plt
from astropy.io import fits
import argparse
import numpy as np
import os

plt.rcParams['axes.labelsize'] = 19
plt.rc('font',family='Serif')
plt.rc('figure',figsize=(8,7)) ##8,6 previously
plt.rcParams['mathtext.fontset'] = 'dejavuserif'


def flux_scale(fitsfile, lotss_flux, image_flux):
    """
    Script to determine the flux scaling required between lotss and an input image
    """

    matches = Table.read(fitsfile)
    prefix = os.path.basename(fitsfile).replace('.fits','')
    #prefix = prefix_old.replace('source_matching_source_catalouge_','')
    #prefix = fitsfile.split('/')[-1].split('_')[2]
    comp = matches['Peak_flux_2']/matches['Total_flux_2'] ###making less extreme for facets, snr 15, compact 0.8, for whole image compact 0.9 snr 35, make this an opition for facets or whole image
    compact = matches[np.where((comp>=0.7))]
    SNR = compact['Peak_flux_2']/compact['Isl_rms_2']
    SNR_25 = compact[np.where(SNR>=10)]
    print(len(compact))
    print(len(SNR_25))
    SNR_25.write('compact_sources_fluxscaling_{}.csv'.format(prefix), format="csv", overwrite=True)

    flux_6 = SNR_25['{}'.format(lotss_flux)] ##Total_flux_1
    bdsf_flux = SNR_25['{}'.format(image_flux)] ##_2

    flux_scale = bdsf_flux/flux_6

    scale = Table()
    scale['flux_scale'] = flux_scale
    scale.write('flux_scale_{}.csv'.format(prefix), format='csv', overwrite=True)

    new_cmap = plt.cm.plasma(np.linspace(0,1,255))

    #fig = plt.figure(figsize=(12, 10))
    #grd = plt.GridSpec(4, 4, hspace=0.2, wspace=0.2)

    fig, ax = plt.subplots(1,1)
    #ax = fig.add_subplot(grd[1:, :-1]) #main plot
    #lax = fig.add_subplot(grd[1:, -1], sharey=ax) #left plot
    #bax = fig.add_subplot(grd[0, :-1], sharex=ax) #top plot

    mean_scale = np.mean(flux_scale)
    median_scale = np.median(flux_scale)

    line = np.linspace(min(bdsf_flux), max(bdsf_flux), num=len(bdsf_flux))
    predict_line_median = 1/(median_scale/line)
    predict_line_mean = 1/(mean_scale/line)
    ax.scatter(bdsf_flux, flux_6, color=new_cmap[50], alpha=0.4, marker='o', linewidth=0)
    #lax.hist(bdsf_flux, orientation='horizontal', color=new_cmap[50], alpha=0.4)
    #bax.hist(flux_6, color=new_cmap[50], alpha=0.4)
    ax.plot(line,line, color='k')
    ax.plot(line, predict_line_median, color='blue')
    ax.plot(line, predict_line_mean, color='pink')
    ax.set_xscale('log')
    ax.set_yscale('log')
    #lax.set_xscale('log')
    #bax.set_xscale('log')
    ax.set_xlabel('Log Flux at 1.2" [Jy]')
    ax.set_ylabel('Log Flux at 6" [Jy]')
    plt.savefig('flux_scaling_{}.png'.format(prefix))
    '''
    with fits.open('Bootes_ILT_mosaic-MFS-image_exact_boundaries_UPDATEDASTRO.fits') as hdu:
         flux = hdu[0].data
         new_flux = flux/median_scale
         print(flux[2], new_flux[2])
         hdu[0].data = new_flux
         print(hdu[0].data)
         hdu.writeto('Bootes_ILT_mosaic-MFS-image_exact_boundaries_UPDATEDFLUXANDASTRO.fits')
    '''

    return flux_scale

def parse_args():
    
     parser = argparse.ArgumentParser(description='Find flux scaling between 6" and pyBDSF image')
     parser.add_argument('--fitsfile', type=str, help='source_catalogue from pyBDSF with both image and 6" flux values')
     parser.add_argument('--lotss_flux', type=str, help='column name of total flux from 6" catalogue')
     parser.add_argument('--image_flux', type=str, help='column name of total flux from pyBDSF catalogue')
     return parser.parse_args()
 
def main():
    """
    Main function
    """

    args = parse_args()
    flux_scale(args.fitsfile, args.lotss_flux, args.image_flux)

if __name__ == '__main__':
    main()
 

