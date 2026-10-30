#!/usr/bin/env python3
"""Create Stokes Q and U cubes from WSClean channel images"""


import numpy as np
from astropy.io import fits
import os
import argparse
import json
import re
from pathlib import Path
from astropy import units as u

from validate_lofar_images import get_rms


def _channel_images(paths, stokes, nchan):
    """Index WSClean images by channel number, independent of staging paths."""
    channels = {}
    for path in paths:
        match = re.fullmatch(r"(.+)-(\d+)-([QU])-image\.fits", Path(path).name)
        if match is None or match[3] != stokes:
            raise ValueError(f"Expected a WSClean {stokes} channel image: {path}")
        index = int(match[2])
        if not 0 <= index < nchan or index in channels:
            raise ValueError(f"Invalid or duplicate {stokes} channel index {index}")
        channels[index] = (path, fits.getheader(path))
    return channels


def _frequency_hz(header):
    if header.get('CTYPE3') != 'FREQ':
        raise ValueError("Expected the third FITS axis to be FREQ")
    # WSClean channel images contain a single frequency plane.
    factor = u.Unit(header.get('CUNIT3', 'Hz')).to(u.Hz)
    return (header['CRVAL3'] + (1 - header['CRPIX3']) * header['CDELT3']) * factor


def cube_maker(q_images: list[str], u_images: list[str], nchan: int, imsize: list[int]) -> None:
    """Build regular Q/U cubes, keeping missing/rejected channels as NaN planes.

    Channel indices come from WSClean filenames. Available image frequencies
    must lie on one linear grid; irregular sampling is rejected rather than
    encoded with an inaccurate linear FITS axis. A pair is rejected if either
    image has non-finite pixels, its mean Q/U noise is undefined, or its mean
    noise exceeds five times the median across valid channel pairs.

    Output cubes and frequency/noise lists always retain all ``nchan`` entries.
    The frequency list is redundant with the FITS WCS. Undefined noise values
    are NaN; measured noise values are retained even for high-noise rejections.
    """
    if nchan < 1 or len(imsize) != 2 or min(imsize) < 1:
        raise ValueError("Positive channel count and image dimensions are required")
    q_channels = _channel_images(q_images, 'Q', nchan)
    u_channels = _channel_images(u_images, 'U', nchan)
    if not q_channels or not u_channels:
        raise ValueError("At least one Q image and one U image are required")

    samples = {}
    for channels in (q_channels, u_channels):
        for index, (_, header) in channels.items():
            frequency = _frequency_hz(header)
            if index in samples and not np.isclose(samples[index], frequency, rtol=0, atol=0.01):
                raise ValueError(f"Q/U frequency mismatch for channel pair {index}")
            samples[index] = frequency
    indices = np.array(sorted(samples))
    observed = np.array([samples[i] for i in indices])
    if len(indices) > 1:
        step = np.median(np.diff(observed) / np.diff(indices))
    else:
        header = next(iter(q_channels.values()))[1]
        step = header['CDELT3'] * u.Unit(header.get('CUNIT3', 'Hz')).to(u.Hz)
    origin = observed[0] - indices[0] * step
    if not np.isfinite(step) or step == 0 or not np.isfinite(observed).all():
        raise ValueError("Frequency grid must have a finite, nonzero channel step")
    if not np.allclose(observed, origin + indices * step, rtol=0, atol=0.01):
        raise ValueError("Image frequencies are not on a regular grid; cannot write a linear FITS axis")
    frequencies = origin + np.arange(nchan) * step

    cube_q = np.full((1, nchan, imsize[1], imsize[0]), np.nan, dtype=np.float32)
    cube_u = np.full_like(cube_q, np.nan)
    avgnoise = np.full(nchan, np.nan)
    for index in range(nchan):
        if index not in q_channels or index not in u_channels:
            print(f"Channel {index}: missing Q/U image, retaining NaN planes")
            continue
        qpath, _ = q_channels[index]
        upath, _ = u_channels[index]
        with fits.open(qpath) as qhdu, fits.open(upath) as uhdu:
            qdata, udata = qhdu[0].data, uhdu[0].data
            for data in (qdata, udata):
                if data.shape[-2:] != (imsize[1], imsize[0]) or data.size != imsize[0] * imsize[1]:
                    raise ValueError(f"Unexpected image dimensions for channel {index}")
            if not np.isfinite(qdata).all() or not np.isfinite(udata).all():
                print(f"Channel {index}: non-finite pixels, retaining NaN planes")
                continue
            noise = 0.5 * (get_rms(qpath) + get_rms(upath))
            if not np.isfinite(noise) or noise <= 0:
                print(f"Channel {index}: invalid noise estimate, retaining NaN planes")
                continue
            avgnoise[index] = noise
            cube_q[0, index] = qdata.reshape(imsize[1], imsize[0])
            cube_u[0, index] = udata.reshape(imsize[1], imsize[0])

    valid = np.isfinite(avgnoise)
    if not valid.any():
        raise ValueError("No valid Q/U channel pairs with finite noise estimates")
    limit = 5 * np.median(avgnoise[valid])
    noisy = valid & (avgnoise > limit)
    cube_q[:, noisy] = np.nan
    cube_u[:, noisy] = np.nan
    flagged = ~valid | noisy
    print(f"Noise threshold: {limit:g} Jy/beam; high-noise indices: {np.flatnonzero(noisy).tolist()}")
    print(f"Preserving {nchan} planes with {np.count_nonzero(flagged)} NaN channel pairs")

    firstq = Path(q_channels[min(q_channels)][0]).name
    imagename = re.fullmatch(r"(.+)-(\d+)-Q-image\.fits", firstq)[1]
    np.savetxt(f'{imagename}_frequency_list.dat', frequencies, fmt='%.17g')
    np.savetxt(f'{imagename}_avg_qunoise_list.dat', avgnoise, fmt='%.17g')
    channel_flags = {
        'nchan': nchan,
        'noise_threshold_Jy_beam': float(limit),
        'rule': 'mean(Q RMS,U RMS) > 5 * median; missing/nonfinite/zero-noise pairs also blanked',
        'blanked_channels': np.flatnonzero(flagged).tolist(),
        'high_noise_channels': np.flatnonzero(noisy).tolist(),
        'invalid_or_missing_channels': np.flatnonzero(~valid).tolist(),
    }
    Path(f'{imagename}_channel_flags.json').write_text(json.dumps(channel_flags, indent=2) + '\n')
    for stokes, channels, cube, code in [('Q', q_channels, cube_q, 2), ('U', u_channels, cube_u, 3)]:
        header = channels[min(channels)][1].copy()
        # These images use WSClean's separable, diagonal frequency WCS.
        # Reject spectral matrix terms rather than silently overriding them.
        if any(key.startswith('CD3_') or (key.startswith('PC3_') and header[key] != (1 if key == 'PC3_3' else 0))
               for key in header):
            raise ValueError("Unsupported spectral WCS matrix in channel images")
        header['CTYPE3'] = 'FREQ'
        header['CUNIT3'] = 'Hz'
        header['CRPIX3'] = 1.0
        header['CRVAL3'] = float(origin)
        header['CDELT3'] = float(step)
        header['CTYPE4'] = 'STOKES'
        header['CRPIX4'] = 1.0
        header['CRVAL4'] = float(code)
        header['CDELT4'] = 1.0
        header.add_history(f'Preserved {nchan} frequency channels; {int(flagged.sum())} paired NaN planes.')
        header.add_history(f'Noise flag: mean(Q RMS,U RMS) > 5 x median = {limit:.9g} Jy/beam.')
        fits.PrimaryHDU(cube, header).writeto(f'{imagename}-polcube-{stokes}.fits', overwrite=True, checksum=True)
        print(f'Stokes {stokes} cube written')


def main():
    parser = argparse.ArgumentParser(description='Cubes maker from WSClean images for RM-synthesis with RMtools')
    parser.add_argument('--qimages', help='Comma-separated input Stokes Q images (legacy interface)', type=str)
    parser.add_argument('--uimages', help='Comma-separated input Stokes U images (legacy interface)', type=str)
    parser.add_argument('--image-manifest', help='JSON file with Q_images and U_images path lists; preferred for many channels')
    parser.add_argument('--nchan', help='Channels out as in WSClean', default=480, type=int)
    parser.add_argument('--imsize', help='Image size in pixels as in WSClean (width,height or single value)', default='1024,1024', type=str)
    args = parser.parse_args()

    if args.image_manifest:
        if args.qimages or args.uimages:
            parser.error('Use --image-manifest or --qimages/--uimages, not both')
        manifest = json.loads(Path(args.image_manifest).read_text())
        if manifest.get('image_directory'):
            directory = Path(manifest['image_directory'])
            q_images = [str(p) for p in directory.iterdir()
                        if re.fullmatch(r'.+-\d+-Q-image\.fits', p.name)]
            u_images = [str(p) for p in directory.iterdir()
                        if re.fullmatch(r'.+-\d+-U-image\.fits', p.name)]
        else:
            q_images = manifest['Q_images']
            u_images = manifest['U_images']
        if not all(isinstance(paths, list) and all(isinstance(p, str) for p in paths)
                   for paths in (q_images, u_images)):
            parser.error('Manifest Q_images and U_images must be lists of paths')
    else:
        if not args.qimages or not args.uimages:
            parser.error('Provide --image-manifest or both --qimages and --uimages')
        q_images = args.qimages.split(',')
        u_images = args.uimages.split(',')

    # CWL stages each file in a different random directory; sort by image name.
    q_images = sorted(q_images, key=os.path.basename)
    u_images = sorted(u_images, key=os.path.basename)

    imsize_parts = args.imsize.split(',')
    if len(imsize_parts) == 2:
        imsize = [int(imsize_parts[0]), int(imsize_parts[1])]
    else:
        single_size = int(imsize_parts[0])
        imsize = [single_size, single_size]

    cube_maker(q_images, u_images, args.nchan, imsize)


if __name__ == '__main__':
    main()
