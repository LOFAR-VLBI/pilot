from argparse import ArgumentParser, Namespace
from validate_lofar_images import get_rms
from sys import exit
import csv
from pathlib import Path


def parse_args() -> Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """

    parser = ArgumentParser("Validation for 1 arcsec image, using the background RMS.")
    parser.add_argument('widefield_image', help='FITS image', default=None)

    return parser.parse_args()


def main():
    minimal_rms_value = 200
    args = parse_args()
    rms = get_rms(args.widefield_image) * 10**6

    # Write RMS to CSV
    csv_path = Path("validation_1arcsec_image.csv")
    with csv_path.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "rms_uJy"])
        writer.writerow([args.widefield_image, f"{rms:.3f}"])

    # Validation
    if rms>minimal_rms_value:
        exit(f"ERROR: We report an RMS value of {rms} μJy/beam, while we expect a minimal RMS value of {minimal_rms_value} μJy/beam")


if __name__ == '__main__':
    main()
