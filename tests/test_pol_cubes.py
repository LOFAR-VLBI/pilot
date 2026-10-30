"""Regression checks for regular FITS cubes and paired NaN channel flags."""
import os
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import make_pol_cubes as pol


class CubeChannelAlignment(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.old_dir = Path.cwd()
        os.chdir(self.directory.name)
        self.addCleanup(self.cleanup_directory)

    def cleanup_directory(self):
        os.chdir(self.old_dir)
        self.directory.cleanup()

    def images(self, nchan=3, invalid=None, missing=(), frequencies=None):
        paths = {'Q': [], 'U': []}
        for i in range(nchan):
            if i in missing:
                continue
            frequency = frequencies[i] if frequencies is not None else 120e6 + i * 1e6
            for stokes, code in [('Q', 2), ('U', 3)]:
                header = fits.Header({'CTYPE1': 'RA---SIN', 'CTYPE2': 'DEC--SIN',
                    'CRPIX1': 2., 'CRPIX2': 2., 'CRVAL1': 0., 'CRVAL2': 0.,
                    'CDELT1': -.001, 'CDELT2': .001, 'CUNIT1': 'deg', 'CUNIT2': 'deg',
                    'CTYPE3': 'FREQ', 'CUNIT3': 'Hz', 'CRPIX3': 1.,
                    'CRVAL3': frequency, 'CDELT3': 1e6,
                    'CTYPE4': 'STOKES', 'CRPIX4': 1., 'CRVAL4': float(code), 'CDELT4': 1.})
                data = np.full((1, 1, 4, 4), float(i + 1))
                if invalid == (i, stokes):
                    data[:] = np.nan
                name = f'image-{i:04d}-{stokes}-image.fits'
                fits.writeto(name, data, header, overwrite=True)
                paths[stokes].append(name)
        return paths['Q'], paths['U']

    def test_zero_rms_pair_is_blanked(self):
        q, u = self.images()
        noise = lambda path: 0.0 if '-0001-' in path else 1.0
        with patch.object(pol, 'get_rms', side_effect=noise):
            pol.cube_maker(q, u, 3, [4, 4])
        self.assertTrue(np.isnan(fits.getdata('image-polcube-Q.fits')[:, 1]).all())
        self.assertTrue(np.isnan(fits.getdata('image-polcube-U.fits')[:, 1]).all())
        self.assertEqual(fits.getheader('image-polcube-Q.fits')['BITPIX'], -32)

    def test_staged_paths_are_sorted_by_channel(self):
        q = ['/z/image-0000-Q-image.fits', '/a/image-0001-Q-image.fits']
        u = ['/a/image-0000-U-image.fits', '/z/image-0001-U-image.fits']
        args = SimpleNamespace(qimages=','.join(q[::-1]), uimages=','.join(u[::-1]), image_manifest=None, nchan=2, imsize='4,4')
        with patch.object(pol.argparse.ArgumentParser, 'parse_args', return_value=args), \
             patch.object(pol, 'cube_maker') as maker:
            pol.main()
        maker.assert_called_once_with(q, u, 2, [4, 4])

    def test_large_manifest_avoids_long_path_list_arguments(self):
        q = [f'/very/long/{"directory/" * 20}/image-{i:04d}-Q-image.fits' for i in range(920)]
        u = [path.replace('-Q-', '-U-') for path in q]
        self.assertGreater(len(','.join(q)), 131072)
        Path('channels.json').write_text(json.dumps({'Q_images': q[::-1], 'U_images': u[::-1]}))
        args = SimpleNamespace(image_manifest='channels.json', qimages=None, uimages=None, nchan=920, imsize='4,4')
        with patch.object(pol.argparse.ArgumentParser, 'parse_args', return_value=args), \
             patch.object(pol, 'cube_maker') as maker:
            pol.main()
        maker.assert_called_once_with(q, u, 920, [4, 4])

    def test_directory_manifest_selects_only_numbered_channel_images(self):
        directory = Path('channel-images')
        directory.mkdir()
        for name in ['image-0001-Q-image.fits', 'image-0000-Q-image.fits',
                     'image-0000-U-image.fits', 'image-0001-U-image.fits',
                     'image-MFS-Q-image.fits', 'image-0000-Q-residual.fits']:
            (directory / name).touch()
        Path('channels.json').write_text(json.dumps({'image_directory': str(directory)}))
        args = SimpleNamespace(image_manifest='channels.json', qimages=None, uimages=None, nchan=2, imsize='4,4')
        with patch.object(pol.argparse.ArgumentParser, 'parse_args', return_value=args), \
             patch.object(pol, 'cube_maker') as maker:
            pol.main()
        maker.assert_called_once_with(
            [str(directory / f'image-{i:04d}-Q-image.fits') for i in range(2)],
            [str(directory / f'image-{i:04d}-U-image.fits') for i in range(2)], 2, [4, 4])

    def check_output(self, flagged):
        frequencies = 120e6 + np.arange(3) * 1e6
        for stokes, code in [('Q', 2), ('U', 3)]:
            with fits.open(f'image-polcube-{stokes}.fits', checksum=True) as hdul:
                hdul.verify('exception')
                cube = hdul[0].data
                self.assertEqual(cube.shape, (1, 3, 4, 4))
                np.testing.assert_array_equal(np.isnan(cube).all(axis=(0, 2, 3)), flagged)
                good = np.flatnonzero(~np.asarray(flagged))
                np.testing.assert_array_equal(cube[0, good, 0, 0], good + 1)
                np.testing.assert_allclose(WCS(hdul[0].header).spectral.pixel_to_world_values(np.arange(3)), frequencies)
                self.assertEqual(hdul[0].header['CRVAL4'], code)
        np.testing.assert_array_equal(np.loadtxt('image_frequency_list.dat'), frequencies)

    def test_nonfinite_first_middle_last_channels_preserve_grid(self):
        for invalid in range(3):
            with self.subTest(invalid=invalid):
                q, u = self.images(invalid=(invalid, 'Q' if invalid % 2 else 'U'))
                with patch.object(pol, 'get_rms', return_value=1.):
                    pol.cube_maker(q, u, 3, [4, 4])
                flags = np.arange(3) == invalid
                self.check_output(flags)
                noise = np.loadtxt('image_avg_qunoise_list.dat')
                np.testing.assert_array_equal(np.isnan(noise), flags)

    def test_missing_first_or_middle_image_keeps_original_channel_index(self):
        for missing in [0, 1]:
            with self.subTest(missing=missing):
                q, u = self.images(missing=[missing])
                with patch.object(pol, 'get_rms', return_value=1.):
                    pol.cube_maker(q, u, 3, [4, 4])
                self.check_output(np.arange(3) == missing)

    def test_noise_threshold_is_strictly_greater_than_five_median(self):
        q, u = self.images()
        for value in [5., 6.]:
            with self.subTest(noise=value):
                def noise(path):
                    return value if '-0002-' in path else 1.
                with patch.object(pol, 'get_rms', side_effect=noise):
                    pol.cube_maker(q, u, 3, [4, 4])
                self.check_output([False, False, value > 5])
                np.testing.assert_array_equal(np.loadtxt('image_avg_qunoise_list.dat'), [1., 1., value])

    def test_irregular_frequency_grid_is_rejected(self):
        q, u = self.images(frequencies=[120e6, 121e6, 123e6])
        with self.assertRaisesRegex(ValueError, 'not on a regular grid'):
            pol.cube_maker(q, u, 3, [4, 4])

    def test_mismatched_qu_frequencies_are_rejected(self):
        q, u = self.images()
        fits.setval(u[1], 'CRVAL3', value=121.5e6)
        with self.assertRaisesRegex(ValueError, 'Q/U frequency mismatch'):
            pol.cube_maker(q, u, 3, [4, 4])


if __name__ == '__main__':
    unittest.main()
