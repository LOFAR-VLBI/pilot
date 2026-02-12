#!/usr/bin/env python3

import pandas as pd
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description="Concatenate multiple CSV files with the same columns into one."
    )
    parser.add_argument(
        "--input",
        nargs="+",
        help="Input folder containing CSV files OR a glob pattern (e.g. data/*.csv)"
    )
    parser.add_argument(
        "--output",
        default="concat.csv",
        help="Output CSV filename (default: combined.csv)"
    )

    args = parser.parse_args()

    files = args.input

    if not files:
        print("No CSV files found.")
        sys.exit(1)

    print(f"Found {len(files)} CSV files. Concatenating...")

    # Concatenate all CSVs
    combined = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)

    # Save output
    combined.to_csv(args.output, index=False)
    print(f"Saved combined CSV to: {args.output}")

if __name__ == "__main__":
    main()
