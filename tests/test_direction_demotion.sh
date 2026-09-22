#!/bin/sh

set -eu

work_dir=$(mktemp -d)
job_file=$(mktemp)
output_dir=$(mktemp -d)
trap 'rm -rf "$work_dir" "$job_file" "$output_dir"' EXIT

printf '%s\n' "mock solution" > "$work_dir/ILTJ103914.20+591425.8_L846954.concat.ms_weak.ms"

printf '%s\n' "{\"msin\":[{\"class\":\"Directory\",\"location\":\"$VLBI_ROOT_DIR/tests/data/ILTJ103914.20+591425.8_L846954.concat.ms_strong.ms\"}], \"validation_csv\":{\"class\":\"File\",\"location\":\"$VLBI_ROOT_DIR/tests/data/validate.csv\"}}" > "$job_file"

cat $job_file

PATH="$VLBI_ROOT_DIR/scripts:$PATH" cwltool --no-container \
    --outdir "$output_dir" \
    "$VLBI_ROOT_DIR/steps/demote_selection.cwl" \
    "$job_file" >/dev/null

fixed="$output_dir/ILTJ103914.20+591425.8_L846954.concat.ms_weak.ms"
[ -f "$fixed" ]
[ "$(cat "$fixed")" = "mock solution" ]
