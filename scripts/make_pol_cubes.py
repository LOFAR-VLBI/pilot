#!/usr/bin/env python3

import numpy as np
from astropy.io import fits
import os
import argparse


def findrms(mIn, maskSup=1e-7):
    """
    find the rms of an array, from Cyril Tasse/kMS
    """
    m = mIn[np.abs(mIn) > maskSup]
    rmsold = np.std(m)
    diff = 1e-1
    cut = 3.
    med = np.median(m)
    for i in range(10):
        ind = np.where(np.abs(m - med) < rmsold * cut)[0]
        rms = np.std(m[ind])
        if np.abs((rms - rmsold) / rmsold) < diff: break
        rmsold = rms
    return rms



def cube_maker(imagename, nchan, imsize):

    # To check whether we can get nchan and imsize from the WSClean command through CWL, otherwise we have to look
    # for the imsize from an already produced image
    '''
    hdu = fits.open('' + str(imagename) + '-0000-I-image.fits')
    data = hdu[0].data[:,:,:,:]
    nx = data.shape[2]
    ny = data.shape[3]
    hdu.close()
    '''

    cube_q = np.zeros((1,nchan,imsize,imsize))
    cube_u = np.zeros((1,nchan,imsize,imsize))
    
    with open('' + str(imagename) + '_frequency_list.dat','w') as lfr:
        with open('' + str(imagename) + '_avg_qunoise_list.dat','w') as avgqunoise:
            for i in range(0,nchan):
                hdu_q = fits.open('' + str(imagename) + str("-{:04d}".format(i))+'-Q-image.fits')
                hdu_u = fits.open('' + str(imagename) + str("-{:04d}".format(i))+'-U-image.fits')
                data_q = hdu_q[0].data[:,:]
                data_u = hdu_u[0].data[:,:]
                if np.isnan(data_q).any() or np.isnan(data_u).any():
                    print("Channel " + str(i) + "is NaN, move to the next one...")
                    continue
                header_q = hdu_q[0].header
                header_u = hdu_u[0].header
                avgnoise = 0.5 * ( findrms(data_q) + findrms(data_u) )
                frequ = hdu_q[0].header['CRVAL3']
                lfr.write(str(frequ)+'\n')
                avgqunoise.write(str(avgnoise)+'\n')
                cube_q[0,i,:,:] = data_q
                cube_u[0,i,:,:] = data_u

    # Writing the cubes
    hdu_cube_q = fits.PrimaryHDU(cube_q,header_q)
    hdu_cube_q.writeto('' + str(imagename) + 'polcube_Q.fits', overwrite=True)
    print("Q cube written")

    hdu_cube_u = fits.PrimaryHDU(cube_u,header_u)
    hdu_cube_u.writeto('' + str(imagename) + 'polcube_U.fits', overwrite=True)
    print("U cube written")

    # To implement: check on the average QU noise for each channel. If it is more than 5 times the
    # median noise, then it is required to exclude that channel.


def main():
    parser = argparse.ArgumentParser(description='Cubes maker from WSClean images for RM-synthesis with RMtools')
    parser.add_argument('--imagename', help='Image name used in WSClean', default='image', type=str)
    parser.add_argument('--nchan', help='Channels out as in WSClean', default=500, type=int)
    parser.add_argument('--imsize', help='Image size in pixels as in WSClean', default=1024, type=int)
    args = parser.parse_args()

    cube_maker(args.imagename, args.nchan, args.imsize)


if __name__ == '__main__':
    main()
