#!/usr/bin/env bash
# Find all the DIS2 solutions from a ddf-pipeline run,
# convert them to H5parm format and merge them into a
# single H5parm, then flag outlying diagonal solutions.
set -euo pipefail

if [[ $# -ne 2 ]]; then
    printf 'Usage: %s SOLSDIR MSNAME\n' "$0" >&2
    exit 2
fi
SOLSDIR=$1
MSNAME=$2

shopt -s nullglob
solution_files=("$SOLSDIR"/L*/*DIS2*.sols.npz)
if [[ ${#solution_files[@]} -eq 0 ]]; then
    printf 'No DIS2 solution files found under %s\n' "$SOLSDIR" >&2
    exit 1
fi

converted_files=()
for solution_index in "${!solution_files[@]}"; do
    printf -v converted_file 'DIS2_%02d.h5' "$solution_index"
    killMS2H5parm.py --solset sol000 --verbose "$converted_file" "${solution_files[$solution_index]}"
    converted_files+=("$converted_file")
done

h5_merger --h5_tables "${converted_files[@]}" --h5_out DIS2_full.h5 --merge_diff_freq --add_ms_stations --ms "$MSNAME" --h5_time_freq True

# Flag on the final merged grid, before any MS consumes these solutions.
flag_DIS2_solutions.py DIS2_full.h5 2>&1 | tee losoto-dis2.log
