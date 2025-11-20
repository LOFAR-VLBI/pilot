#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 11:15:16 2025

@author: pwcc62
"""

from astropy.table import Table
from astropy import units as u
import matplotlib.pyplot as plt
from astropy.io import fits
import numpy as np
import argparse
import os

##example input below
##python3 astrometry.py --crossmatch_fits "/home/pwcc62/AGN_outflows/Bootes_nonAGN/bootes_final_cross_match_catalogue-v1.0.fits" 
#--source_fits "test_source_catalouge.fits" --ra1 "optRA" --ra2 "RA_bdsf" --dec1 "optDec" --dec2 "DEC_bdsf" --error 5

#DR1 = Table.read('/home/pwcc62/AGN_outflows/Bootes_FITS/bootes_optIR_catalogue_full.fits')
#source_cat = Table.read('/home/pwcc62/Bootes/test_source_catalog.fits')

plt.rcParams['axes.labelsize'] = 19
plt.rc('font',family='Serif')
plt.rc('figure',figsize=(8,7)) ##8,6 previously
plt.rcParams['mathtext.fontset'] = 'dejavuserif'

def astrometry(crossmatch_fits, source_fits, ra1, ra2, dec1, dec2, error):
    
    """
    Script to determine the astrometry off set between e.g lotss and another image
    
    """
    #prefix_old = source_fits.split('/')[-1].split('_')[2]
    prefix = os.path.basename('{}'.format(source_fits)).replace('.fits','')
    cmd1 = 'java -jar /cosma8/data/do011/dc-esco1/postprocessing/stilts.jar tskymatch2 in1="{}" in2="{}" out=source_matches_{}.fits ra1={} dec1={} ra2={} dec2={} error={} join=1and2'.format(crossmatch_fits, source_fits, prefix, ra1, dec1, ra2, dec2, error)
    #cmd1 = 'stilts tskymatch2 in1=\"/home/pwcc62/AGN_outflows/Bootes_nonAGN/bootes_final_cross_match_catalogue-v1.0.fits\" in2="test_source_catalouge.fits" out=source_matches.fits ra1=optRA dec1=optDEC ra2=RA_bdsf dec2=DEC_bdsf error=1 join=1and2'
    print(cmd1)
    with open('match_{}.sh'.format(prefix),'w') as f:
        f.write(cmd1)
        f.write('\n')

    os.system('bash match_{}.sh'.format(prefix))

    matches = Table.read("source_matches_{}.fits".format(prefix)) ## want RA_bdsf as this is from source_catalouge

    print(matches)
    comp = matches['Peak_flux_2']/matches['Total_flux_2'] ##changed for facets previous 35 and 0.9
    compact = matches[np.where((comp>=0.6))]
    SNR = compact['Peak_flux_2']/compact['Isl_rms_2']
    SNR_25 = compact[np.where(SNR>=7)]
    print(len(compact))
    print(len(SNR_25))
    print(SNR_25)
    SNR_25.write('compact_sources_astrometry_{}.csv'.format(prefix), format="csv", overwrite=True)

    bdsf_ra = SNR_25['{}'.format(ra2)]
    bdsf_dec = SNR_25['{}'.format(dec2)]
    opt_ra = SNR_25['{}'.format(ra1)]
    opt_dec = SNR_25['{}'.format(dec1)]

    ra_offset = (opt_ra - bdsf_ra) * u.deg
    dec_offset = (opt_dec - bdsf_dec) * u.deg

    ra_off_arcsec = ra_offset.to(u.arcsec)
    dec_off_arcsec = dec_offset.to(u.arcsec)
    ra_off = Table()
    ra_off['ra_offset'] = ra_off_arcsec
    dec_off = Table()
    dec_off['dec_offset'] = dec_off_arcsec
    ra_off.write('ra_offset_{}.csv'.format(prefix), format='csv', overwrite=True)
    dec_off.write('dec_offset_{}.csv'.format(prefix), format='csv', overwrite=True)

    new_cmap = plt.cm.plasma(np.linspace(0,1,255))

    mean_ra = np.mean(ra_off_arcsec)/u.arcsec
    mean_dec = np.mean(dec_off_arcsec)/u.arcsec
    median_ra = np.median(ra_off_arcsec)/u.arcsec
    median_dec = np.median(dec_off_arcsec)/u.arcsec
    print(mean_dec)
    fig = plt.figure(figsize=(12, 10))
    grd = plt.GridSpec(4, 4, hspace=0.2, wspace=0.2)

    ax = fig.add_subplot(grd[1:, :-1]) #main plot
    lax = fig.add_subplot(grd[1:, -1], sharey=ax) #left plot
    bax = fig.add_subplot(grd[0, :-1], sharex=ax) #top plot
    #fig = plt.figure()
    
    ax.scatter(ra_off_arcsec, dec_off_arcsec, color=new_cmap[50], alpha=0.4, marker='o', linewidth=0)
    ax.axvline(mean_ra, color='k')
    ax.axhline(mean_dec, color='k')
    ax.axvline(median_ra, color='blue')
    ax.axhline(median_dec, color='blue')
    bax.axvline(mean_ra, color='k')
    bax.axvline(median_ra, color='blue')
    lax.axhline(mean_dec, color='k')
    lax.axhline(median_dec, color='blue')
    lax.hist(dec_off_arcsec, bins=100, orientation='horizontal', color=new_cmap[50], alpha=0.4)
    bax.hist(ra_off_arcsec, bins=100, color=new_cmap[50], alpha=0.4)
    
    ax.set_xlabel('RA offset')
    ax.set_ylabel('Dec offset')
    plt.savefig('astrometry_offset_{}.png'.format(prefix))
    '''
    with fits.open('Bootes_ILT_mosaic-MFS-image_exact_boundaries_posttest.fits') as hdu: ##### make this an input
        ra_im = hdu[0].header['CRVAL1']
        dec_im = hdu[0].header['CRVAL2']
        if median_ra>=0:
           ra_new = ra_im-median_ra
        if median_dec>=0:
           dec_new = dec_im-median_dec
        hdr = hdu[0].header
        hdu[0].header['CRVAL1']=float(ra_new)
        hdu[0].header['CRVAL2']=float(dec_new)
        print(hdu[0].header['CRVAL1'])
        hdu.writeto('Bootes_ILT_mosaic-MFS-image_exact_boundaries_UPDATEDASTRO.fits')
    '''

    return ra_off, dec_off


def parse_args():
    
     parser = argparse.ArgumentParser(description='Find Astrometry offset to 6" image')
     parser.add_argument('--crossmatch_fits', type=str, help='6" catalogue with flux values')
     parser.add_argument('--source_fits', type=str, help='source_catalogue from pyBDSF')
     parser.add_argument('--ra1', type=str, help='column name of ra from crossmatch catalogue')
     parser.add_argument('--ra2', type=str, help='column name of ra from pyBDSF catalogue')
     parser.add_argument('--dec1', type=str, help='column name of dec from crossmatch catalogue')
     parser.add_argument('--dec2', type=str, help='column name of dec from pyBDSF catalogue')
     parser.add_argument('--error', type=str, help='Error for source location for crossmatching', default=5)

     return parser.parse_args()
 
def main():
    """
    Main function
    """

    args = parse_args()
    astrometry(args.crossmatch_fits, args.source_fits, args.ra1, args.ra2, args.dec1, args.dec2, args.error)


if __name__ == '__main__':
    main()
