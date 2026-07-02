#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from argparse import ArgumentParser

from submods.source_selection.selfcal_selection import parse_source_from_h5


def main():
    parser = ArgumentParser(
        description="Filters a given set of files into one that matches the set of MSes. This is done by extracting the source name, so both MSes and files are expected to follow the ILTJ... naming convention."
    )
    parser.add_argument(
        "--ms",
        type=str,
        nargs="+",
        help="MSes to use as reference for filtering the files.",
    )
    parser.add_argument(
        "--files",
        type=str,
        nargs="*",
        help="Files to filter a set matching the MSes from.",
    )
    args = parser.parse_args()

    if not args.files:
        with open("cwl.output.json", "w") as f:
            json.dump({"filtered_files": None}, f)

    source_names_ms = {parse_source_from_h5(ms) for ms in args.ms}

    keep_files = [f for f in args.files if parse_source_from_h5(f) in source_names_ms]

    cwl_files = [{"type": "Directory", "path": f} for f in keep_files]

    with open("cwl.output.json", "w") as f:
        if cwl_files:
            json.dump({"filtered_files": cwl_files}, f)


if __name__ == "__main__":
    main()
