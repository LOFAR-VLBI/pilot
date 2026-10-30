"""Keep the native-channel LoTSS-HR example from silently averaging too far."""
import unittest
import numpy as np
from make_pol_imaging_config import output_channel_count


class PolarizationChannelCount(unittest.TestCase):
    def setUp(self):
        self.width = 12207.03125
        self.freq = 120e6 + np.arange(3680) * self.width
        self.widths = np.full(3680, self.width)

    def test_native_and_four_channel_averaging(self):
        self.assertEqual(output_channel_count(self.freq, self.widths, self.width), 3680)
        self.assertEqual(output_channel_count(self.freq, self.widths, self.width * 4), 920)

    def test_already_48khz_is_preserved(self):
        f = self.freq.reshape(-1, 4).mean(axis=1)
        self.assertEqual(output_channel_count(f, np.full(920, self.width * 4), self.width * 4), 920)

    def test_cannot_recover_fine_channels_from_averaged_ms(self):
        with self.assertRaisesRegex(ValueError, 'cannot be unaveraged'):
            output_channel_count(np.array([120e6, 120e6 + 390625]), np.full(2, 390625), self.width * 4)

    def test_missing_frequency_rejected(self):
        with self.assertRaisesRegex(ValueError, 'gaps'):
            output_channel_count(np.delete(self.freq, 1), self.widths[:-1], self.width)

    def test_uneven_groups_rejected(self):
        with self.assertRaisesRegex(ValueError, 'divisible'):
            output_channel_count(self.freq[:-1], self.widths[:-1], self.width * 4)


if __name__ == '__main__':
    unittest.main()
