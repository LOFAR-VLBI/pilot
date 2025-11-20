#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 09:47:43 2025

@author: pwcc62
"""

import bdsf
import argparse
from astropy.table import Table
import os

def source_finder(input_image, detect_img, rmsbox, thresh_isl, thresh_pix):
    """
    Script to create source catalogue for an imput fits image
    """
    
    prefix = os.path.basename(input_image).replace('.fits','')
    print(input_image, detect_img, prefix)
    img = bdsf.process_image(input_image, thresh_isl=thresh_isl, thresh_pix=thresh_pix, rms_box=(int(rmsbox),int(rmsbox/8)), rms_box_bright=(int(rmsbox/3),int(rmsbox/12)), detection_image=detect_img, thresh=None)
    img.write_catalog(clobber=True, outfile='source_catalogue_{}.fits'.format(prefix), format='fits', catalog_type='srl') ###should be the none pb one
    img.write_catalog(clobber=True, outfile='gaussian_catalogue_{}.fits'.format(prefix), format='fits', catalog_type='gaul')
    img = Table.read('source_catalogue_{}.fits'.format(prefix))
    img2 = Table.read('gaussian_catalogue_{}.fits'.format(prefix))
    img2_ra = img2['RA']
    img2['RA'] = (img2_ra + 360) % 360
    img2['RA'].name = 'RA_bdsf'
    img2['DEC'].name = 'DEC_bdsf'
    img_ra = img['RA']
    img['RA'] = (img_ra + 360) % 360
    img['RA'].name = 'RA_bdsf'
    img['DEC'].name = 'DEC_bdsf'
    img.write('source_catalogue_{}.fits'.format(prefix), overwrite=True, format='fits')
    img2.write('gaussian_catalogue_{}.fits'.format(prefix), overwrite=True, format='fits')

    return img

def parse_args():
    
     parser = argparse.ArgumentParser(description='Source Finding with pyBDSF')
     parser.add_argument('--rmsbox', type=float, help='rms box pybdsf', default=120)
     parser.add_argument('--thresh_isl', type=float, help='sigma threshold for island detections with pybdsf', default=5)
     parser.add_argument('--thresh_pix', type=float, help='sigma threshold for pixel with pybdsf', default=5)
     parser.add_argument('--input_image', help='input image for source finding')
     parser.add_argument('--detect_img', help='detection image for source finding, nonpb')

     return parser.parse_args()
 

def main():
    """
    Main function
    """

    args = parse_args()
    source_finder(args.input_image, args.detect_img, args.rmsbox, args.thresh_isl, args.thresh_pix)


if __name__ == '__main__':
    main()

