from argparse import ArgumentParser, Namespace
from validate_lofar_images import get_rms
import csv
from pathlib import Path

class ValidationError(Exception):
    pass

def parse_args() -> Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """

    parser = ArgumentParser("Validation for 1 arcsec image, using the background RMS. "
                            "Current assumption is that the RMS background noise should be below 200 μJy/beam.")
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
    if rms > minimal_rms_value:
        raise ValidationError(f"RMS check failed: measured {rms} μJy/beam, but expected ≤ {minimal_rms_value} μJy/beam.")


if __name__ == '__main__':
    main()
