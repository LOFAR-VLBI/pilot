#!/bin/bash

# Convert Table to CSV (also works for CSV inputs)
if [[ "${1,,}" != *.csv ]]; then
    stilts tcopy "$1" temp_csv.csv ofmt=csv
    input_file="tmp_csv.csv"
else
    input_file="$1"
fi

chunk_size=$2

output_prefix="source_list_chunk"
chunk_counter=1
line_counter=0
header=$(head -n 1 "$input_file")

output_file="${output_prefix}_${chunk_counter}.csv"
echo "$header" > "$output_file"

awk 'NR > 1 { print }' "$input_file" | while read -r line; do
  ((line_counter++))
  if ((line_counter > chunk_size)); then
    line_counter=1
    ((chunk_counter++))
    output_file="${output_prefix}_${chunk_counter}.csv"
    echo "$header" > "$output_file"
  fi
  echo "$line" >> "$output_file"
done
