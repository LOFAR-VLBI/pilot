#!/usr/bin/env python3

import numpy as np
from astropy.io import fits
import os
import argparse
import re


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



def cube_maker(q_images, u_images, nchan, imsize):
    # Extract the name for the frequency and rms noise files
    firstq = os.path.basename(q_images[0])
    imagename = firstq.split("-")[0]
    # If you later want the regex version, uncomment:
    # m = re.match(r"(.+)-\\d{4}-Q-image\\.fits$", firstq)
    # if not m:
    #     raise ValueError(f"Unexpected Q filename format: {firstq}")
    # imagename = m.group(1)

    cube_q = np.zeros((1, nchan, imsize, imsize))
    cube_u = np.zeros((1, nchan, imsize, imsize))

    print(f"PWD: {os.getcwd()}")
    print(f"Writing frequency list to: {imagename}_frequency_list.dat")
    print(f"Writing noise list to: {imagename}_avg_qunoise_list.dat")

    with open(f"{imagename}_frequency_list.dat", "w") as lfr:
        with open(f"{imagename}_avg_qunoise_list.dat", "w") as avgqunoise:
            for i in range(nchan):
                with fits.open(q_images[i]) as hdu_q, fits.open(u_images[i]) as hdu_u:
                    data_q = np.squeeze(hdu_q[0].data)
                    data_u = np.squeeze(hdu_u[0].data)
                    if np.isnan(data_q).any() or np.isnan(data_u).any():
                        print(f"Channel {i} is NaN, move to the next one...")
                        continue
                    if i == 0:
                        header_q = hdu_q[0].header
                        header_u = hdu_u[0].header

                    avgnoise = 0.5 * (findrms(data_q) + findrms(data_u))
                    frequ = hdu_q[0].header["CRVAL3"]

                lfr.write(f"{frequ}\n")
                avgqunoise.write(f"{avgnoise}\n")
                cube_q[0, i, :, :] = data_q
                cube_u[0, i, :, :] = data_u

            lfr.flush()
            avgqunoise.flush()

    # Check the average QU noise for each channel.
    with open(f"{imagename}_avg_qunoise_list.dat", "r") as avgqunoise:
        avgqunoise_values = np.array([float(line.strip()) for line in avgqunoise])

    with open(f"{imagename}_frequency_list.dat", "r") as lfr:
        frequencies = np.array([float(line.strip()) for line in lfr])

    if avgqunoise_values.size == 0 or frequencies.size == 0:
        raise RuntimeError("Frequency/noise lists are empty after writing.")

    mask = avgqunoise_values <= 5.0 * np.median(avgqunoise_values)

    correct_frequencies = frequencies[mask]
    correct_avgqunoise = avgqunoise_values[mask]
    correct_cube_q = cube_q[:, mask, :, :]
    correct_cube_u = cube_u[:, mask, :, :]

    with open(f"{imagename}_frequency_list.dat", "w") as lfr:
        for freq in correct_frequencies:
            lfr.write(str(freq) + "\n")

    with open(f"{imagename}_avg_qunoise_list.dat", "w") as avgqunoise:
        for noise in correct_avgqunoise:
            avgqunoise.write(str(noise) + "\n")

    # Writing the cubes
    hdu_cube_q = fits.PrimaryHDU(correct_cube_q, header_q)
    hdu_cube_q.writeto(f"{imagename}-polcube-Q.fits", overwrite=True)
    print("Stokes Q cube written")

    hdu_cube_u = fits.PrimaryHDU(correct_cube_u, header_u)
    hdu_cube_u.writeto(f"{imagename}-polcube-U.fits", overwrite=True)
    print("Stokes U cube written")


def main():
    parser = argparse.ArgumentParser(description='Cubes maker from WSClean images for RM-synthesis with RMtools')
    parser.add_argument('--qimages', help='List of input Stokes Q channel images', type=str, required=True)
    parser.add_argument('--uimages', help='List of input Stokes U channel images', type=str, required=True)
    parser.add_argument('--nchan', help='Channels out as in WSClean', default=480, type=int)
    parser.add_argument('--imsize', help='Image size in pixels as in WSClean (x y)', type=int, nargs=2, required=True)
    args = parser.parse_args()

    q_images = args.qimages.split(',')
    u_images = args.uimages.split(',')

    q_images = sorted(q_images)
    u_images = sorted(u_images)
    
    if len(q_images) < args.nchan or len(u_images) < args.nchan:
        raise ValueError(
            f"Not enough channel images: Q={len(q_images)}, U={len(u_images)}, nchan={args.nchan}"
        )

    imsize_x, imsize_y = args.imsize
    if imsize_x != imsize_y:
      raise ValueError(f"Only square images are supported, got {imsize_x}x{imsize_y}")
    cube_maker(q_images, u_images, args.nchan, imsize_x)


if __name__ == '__main__':
    main()
