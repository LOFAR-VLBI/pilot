#!/usr/bin/env bash
# Find all the DIS2 solutions from a ddf-pipeline run,
# convert them to H5parm format and merge them into a
# single H5parm, then flag outlying diagonal solutions.
set -euo pipefail

if [[ $# -ne 3 ]]; then
    printf 'Usage: %s SOLSDIR MSNAME FLAGGING_PARSET\n' "$0" >&2
    exit 2
fi
SOLSDIR=$1
MSNAME=$2
FLAGGING_PARSET=$3

if [[ ! -f "$FLAGGING_PARSET" ]]; then
    printf 'DIS2 flagging parset does not exist: %s\n' "$FLAGGING_PARSET" >&2
    exit 1
fi

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
losoto -v DIS2_full.h5 "$FLAGGING_PARSET" 2>&1 | tee losoto-dis2.log

# LoSoTo can exit successfully after an operation reports failure. Require
# both fixed parset steps to complete, as well as a successful process exit.
for flag_step in flagamp flagphase; do
    if ! grep -Fq "Step '$flag_step' completed successfully." losoto-dis2.log; then
        printf 'LoSoTo DIS2 flagging did not complete %s; see losoto-dis2.log\n' "$flag_step" >&2
        exit 1
    fi
done
if grep -Eq '(^|[[:space:]])(ERROR|CRITICAL)(:|[[:space:]])|Traceback \(most recent call last\):|Step .+ incomplete' losoto-dis2.log; then
    printf 'LoSoTo DIS2 flagging reported an error; see losoto-dis2.log\n' >&2
    exit 1
fi
