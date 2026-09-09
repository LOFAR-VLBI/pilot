from argparse import ArgumentParser
import json
import os


def filter_sources(strong: list[str], weak: list[str], unreliable: list[str]):
    retain_weak = []
    if unreliable:
        for source in unreliable:
            if source.endswith(".png"):
                # PNG file naming follows e.g. ILTJ*_003.png
                name = os.path.basename(source).split("_")[0]
            elif source.endswith(".fits"):
                # FITS file naming follows e.g. best_ILTJ*_003-MFS-image.fits
                name = os.path.basename(source).split("_")[1]
            else:
                raise RuntimeError("Unknown file type encountered.")
            retain_weak = list(filter(lambda x: name in x, weak))

    retain_strong = []
    if not retain_weak:
        retain_weak = weak
    if retain_weak:
        for source in retain_weak:
            if source.endswith(".png"):
                # PNG file naming follows e.g. ILTJ*_003.png
                name = os.path.basename(source).split("_")[0]
            elif source.endswith(".fits"):
                # FITS file naming follows e.g. best_ILTJ*_003-MFS-image.fits
                name = os.path.basename(source).split("_")[1]
            else:
                raise RuntimeError("Unknown file type encountered.")
            retain_strong = list(filter(lambda x: name in x, strong))

    return retain_weak, retain_strong


if __name__ == "__main__":
    parser = ArgumentParser(
        "Filter only the final appropriate images from layered dd calibration."
    )
    parser.add_argument(
        "--images-strong",
        nargs="*",
        help="Best cycle FITS images for strong sources.",
    )
    parser.add_argument(
        "--images-weak",
        nargs="*",
        help="Best cycle FITS images for weak sources.",
    )
    parser.add_argument(
        "--images-unreliable",
        nargs="*",
        help="Best cycle FITS images for unreliable sources.",
    )

    args = parser.parse_args()
    final_weak, final_strong = filter_sources(
        args.images_strong, args.images_weak, args.images_unreliable
    )

    if final_weak:
        cwl_files_weak = [{"class": "File", "path": f} for f in final_weak]
    else:
        cwl_files_weak = None
    if final_strong:
        cwl_files_strong = [{"class": "File", "path": f} for f in final_strong]
    else:
        cwl_files_strong = None

    with open("cwl.output.json", "w") as f:
        json.dump({"final_weak": cwl_files_weak, "final_strong": cwl_files_strong}, f)
