#!/usr/bin/env python3
"""Adapt the LoTSS-HR polarization example to one calibrated target MS."""
import argparse
import json
from pathlib import Path

import numpy as np


def output_channel_count(frequencies, widths, requested_width_hz):
    """Reject upsampling, gaps, and uneven channel groups before imaging."""
    frequencies = np.asarray(frequencies, dtype=float)
    widths = np.abs(np.asarray(widths, dtype=float))
    if frequencies.ndim != 1 or not len(frequencies) or widths.shape != frequencies.shape:
        raise ValueError('Expected one non-empty spectral window with one width per channel')
    if not np.isfinite(frequencies).all() or not np.isfinite(widths).all() or np.any(widths <= 0):
        raise ValueError('Invalid channel frequencies or widths')
    width = float(widths[0])
    if not np.allclose(widths, width, rtol=0, atol=.01):
        raise ValueError('Channel widths are not uniform')
    if len(frequencies) > 1 and not np.allclose(np.diff(frequencies), width, rtol=0, atol=.01):
        raise ValueError('Expected ascending contiguous channels; check gaps and spectral windows')
    factor = int(round(requested_width_hz / width))
    if factor < 1 or not np.isclose(factor * width, requested_width_hz, rtol=0, atol=.01):
        raise ValueError('Requested width must be an integer multiple of the input width; averaged data cannot be unaveraged')
    if len(frequencies) % factor:
        raise ValueError('Channel count is not divisible by the averaging factor')
    return len(frequencies) // factor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ms', required=True, type=Path, help='One concatenated, calibrated target MS with DATA')
    parser.add_argument('--channel-width-khz', type=int, choices=[12, 48], default=48,
                        help='Shorthand for 12.20703125 or 48.828125 kHz (default: 48)')
    parser.add_argument('--template', type=Path, default=Path(__file__).resolve().parents[1] /
                        'pipeline_config_files/polarization/lotss-hr-0p3arcsec-48kHz.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from casacore.tables import table
    with table(str(args.ms), readonly=True, ack=False) as ms:
        if 'DATA' not in ms.colnames():
            raise ValueError('WSClean step reads DATA; supply the calibrated target data in DATA')
        used_spws = np.unique(ms.getcol('DATA_DESC_ID'))
    with table(str(args.ms / 'DATA_DESCRIPTION'), readonly=True, ack=False) as desc:
        used_spws = np.unique([desc.getcell('SPECTRAL_WINDOW_ID', int(i)) for i in used_spws])
    if len(used_spws) != 1:
        raise ValueError('This example requires one concatenated spectral window per target')
    with table(str(args.ms / 'SPECTRAL_WINDOW'), readonly=True, ack=False) as spw:
        freq = spw.getcell('CHAN_FREQ', int(used_spws[0]))
        widths = spw.getcell('CHAN_WIDTH', int(used_spws[0]))
    requested = 12207.03125 * (4 if args.channel_width_khz == 48 else 1)
    count = output_channel_count(freq, widths, requested)
    config = json.loads(args.template.read_text())
    config['msin'] = [{'class': 'Directory', 'path': str(args.ms.resolve())}]
    config['num_channels'] = count
    args.output.write_text(json.dumps(config, indent=2) + '\n')
    print(f'Wrote {args.output}: {count} output channels, {requested / 1000:.8f} kHz each')


if __name__ == '__main__':
    main()
