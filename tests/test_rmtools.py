"""Verify channel-noise validation and actual forwarding to RM-Tools."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits
import run_rmtools as rm


class RMNoiseWeights(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.old = Path.cwd()
        os.chdir(self.directory.name)
        self.q = np.ones((1, 3, 2, 2))
        self.u = np.ones_like(self.q) * .25
        self.q[:, 1] = np.nan
        self.u[:, 1] = np.nan
        self.addCleanup(self.cleanup_directory)

    def cleanup_directory(self):
        os.chdir(self.old)
        self.directory.cleanup()

    def noise(self, values):
        np.savetxt('noise.dat', values)
        return 'noise.dat'

    def cubes(self):
        header = fits.Header({'CTYPE1': 'RA---SIN', 'CTYPE2': 'DEC--SIN',
            'CRPIX1': 1., 'CRPIX2': 1., 'CRVAL1': 0., 'CRVAL2': 0.,
            'CDELT1': -.001, 'CDELT2': .001, 'CTYPE3': 'FREQ', 'CUNIT3': 'Hz',
            'CRPIX3': 1., 'CRVAL3': 120e6, 'CDELT3': 1e6,
            'CTYPE4': 'STOKES', 'CRPIX4': 1., 'CRVAL4': 2., 'CDELT4': 1.})
        fits.writeto('q.fits', self.q, header)
        header['CRVAL4'] = 3.
        fits.writeto('u.fits', self.u, header)

    def test_blank_nan_noise_becomes_zero_weight(self):
        result = rm.load_channel_rms(self.noise([1., np.nan, 2.]), self.q, self.u)
        np.testing.assert_array_equal(1 / result**2, [1., 0., .25])

    def test_invalid_unblanked_noise_fails(self):
        for bad in [0., -1., np.nan, np.inf]:
            with self.subTest(noise=bad), self.assertRaisesRegex(ValueError, 'strictly positive'):
                rm.load_channel_rms(self.noise([bad, np.nan, 2.]), self.q, self.u)

    def test_wrong_length_or_multicolumn_noise_fails(self):
        for values in [[1., 2.], [[1., 2.], [2., 3.], [3., 4.]]]:
            with self.subTest(values=values), self.assertRaisesRegex(ValueError, 'one value'):
                rm.load_channel_rms(self.noise(values), self.q, self.u)

    def test_mismatched_blank_pairs_fail(self):
        self.u[:, 1] = 1.
        with self.assertRaisesRegex(ValueError, 'same blanked'):
            rm.load_channel_rms(self.noise([1., np.nan, 2.]), self.q, self.u)

    def test_variance_forwards_channel_rms_and_header_frequencies(self):
        self.cubes()
        with patch.object(rm, 'run_rmsynth', return_value=[] ) as synth, patch.object(rm, 'writefits'):
            rm.do_rmsynth('q.fits', 'u.fits', None, 80., .3,
                          noise_file=self.noise([1., np.nan, 2.]))
        self.assertEqual(synth.call_args.kwargs['weightType'], 'variance')
        np.testing.assert_array_equal(synth.call_args.kwargs['rmsArr'], [1., np.inf, 2.])
        np.testing.assert_array_equal(synth.call_args.args[2], [120e6, 121e6, 122e6])

    def test_missing_noise_cannot_silently_fall_back_to_uniform(self):
        self.cubes()
        with self.assertRaisesRegex(ValueError, 'requires --rms'), patch.object(rm, 'run_rmsynth') as synth:
            rm.do_rmsynth('q.fits', 'u.fits', None, 80., .3)
        synth.assert_not_called()

    def test_real_synthesis_handles_blank_channel_and_recovers_rm(self):
        freq = 120e6 + np.arange(64) * .75e6
        rm_value = 7.3
        phase = 2 * rm_value * (299792458.0 / freq)**2
        q = np.broadcast_to(np.cos(phase)[None, :, None, None], (1, 64, 2, 2)).copy()
        u = np.broadcast_to(np.sin(phase)[None, :, None, None], q.shape).copy()
        q[:, 12] = np.nan
        u[:, 12] = np.nan
        self.cubes()
        header = fits.getheader('q.fits')
        header['CDELT3'] = .75e6
        fits.writeto('q.fits', q, header, overwrite=True)
        header['CRVAL4'] = 3.
        fits.writeto('u.fits', u, header, overwrite=True)
        noise = np.ones(64)
        noise[12] = np.nan
        rm.do_rmsynth('q.fits', 'u.fits', None, 20., .1, output_prefix='test', noise_file=self.noise(noise))
        np.testing.assert_allclose(fits.getdata('testFDF_peakRM.fits'), rm_value, atol=.001)
        np.testing.assert_allclose(fits.getdata('testFDF_maxPI.fits'), 1., atol=1e-4)

    def test_uniform_is_explicit(self):
        self.cubes()
        with patch.object(rm, 'run_rmsynth', return_value=[]) as synth, patch.object(rm, 'writefits'):
            rm.do_rmsynth('q.fits', 'u.fits', None, 80., .3, weighting='uniform')
        self.assertEqual(synth.call_args.kwargs['weightType'], 'uniform')
        self.assertIsNone(synth.call_args.kwargs['rmsArr'])


if __name__ == '__main__':
    unittest.main()
