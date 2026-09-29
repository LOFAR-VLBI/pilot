#!/usr/bin/env python
import json
from argparse import ArgumentParser

from make_config_international import parse_source_id


def filter_sources(
    main: list[str] = [],
    strong: list[str] = [],
    weak: list[str] = [],
    unreliable: list[str] = [],
):
    """Filter calibration products based on the final layer that they reached.

    They are kept in order of: unreliable, weak, strong, main.
    """
    unreliable_names: set[str] = {parse_source_id(source) for source in unreliable}
    retain_weak = [
        file for file in weak if parse_source_id(file) not in unreliable_names
    ]
    weak_names: set[str] = {parse_source_id(source) for source in retain_weak}

    reject_names: set[str] = unreliable_names | weak_names
    retain_strong = [
        file for file in strong if parse_source_id(file) not in reject_names
    ]
    strong_names: set[str] = {parse_source_id(source) for source in retain_strong}

    reject_names |= strong_names
    retain_main = [
        file for file in main if parse_source_id(file) not in reject_names
    ]

    return retain_weak, retain_strong, retain_main


def main():
    parser = ArgumentParser(
        "Filter only the final appropriate files from layered dd calibration."
    )
    parser.add_argument(
        "--files-main",
        nargs="*",
        default=[],
        help="Best cycle FITS files for main sources.",
    )
    parser.add_argument(
        "--files-strong",
        nargs="*",
        default=[],
        help="Best cycle FITS files for strong sources.",
    )
    parser.add_argument(
        "--files-weak",
        nargs="*",
        default=[],
        help="Best cycle FITS files for weak sources.",
    )
    parser.add_argument(
        "--files-unreliable",
        nargs="*",
        default=[],
        help="Best cycle FITS files for unreliable sources.",
    )

    args = parser.parse_args()
    final_weak, final_strong, final_main = filter_sources(
        args.files_main,
        args.files_strong,
        args.files_weak,
        args.files_unreliable,
    )

    if args.files_unreliable:
        cwl_files_unreliable = [
            {"class": "File", "path": f} for f in args.files_unreliable
        ]
    else:
        cwl_files_unreliable = None
    if final_weak:
        cwl_files_weak = [{"class": "File", "path": f} for f in final_weak]
    else:
        cwl_files_weak = None
    if final_strong:
        cwl_files_strong = [{"class": "File", "path": f} for f in final_strong]
    else:
        cwl_files_strong = None
    if final_main:
        cwl_files_main = [{"class": "File", "path": f} for f in final_main]
    else:
        cwl_files_main = None

    with open("cwl.output.json", "w") as f:
        json.dump(
            {
                "final_files_unreliable": cwl_files_unreliable,
                "final_files_weak": cwl_files_weak,
                "final_files_strong": cwl_files_strong,
                "final_files_main": cwl_files_main,
            },
            f,
        )


if __name__ == "__main__":
    main()
