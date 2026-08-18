class: CommandLineTool
cwlVersion: v1.2
id: rename_solsdirs
doc: Rename SOLSDIR entries while preserving complete SOLSDIR structure.

baseCommand: bash

arguments:
  - position: 1
    valueFrom: -c
  - position: 2
    valueFrom: |
      set -eu
      solsdir="$0"
      mapfile -t src < <(find "$solsdir" -mindepth 1 -maxdepth 1 -type d \( -name '*.ms' -o -name '*.dp3concat' \) -printf '%f\n' | sort)
      mapfile -t dst < <(printf '%s\n' "$@" | sort)
      if [ "${#src[@]}" -ne "${#dst[@]}" ]; then
        printf 'SOLSDIR/input MS count mismatch: %s != %s\n' "${#src[@]}" "${#dst[@]}" >&2
        exit 1
      fi
      for ((i = 0; i < ${#src[@]}; i++)); do
        [ "${src[i]}" = "${dst[i]}" ] || mv -- "$solsdir/${src[i]}" "$solsdir/${dst[i]}"
      done
inputs:
  - id: solsdir
    type: Directory
    doc: SOLSDIR to rename in place.
    inputBinding:
      position: 3
      valueFrom: $(self.basename)

  - id: msin
    type: Directory[]
    doc: MeasurementSets providing destination basenames.
    inputBinding:
      position: 4
      valueFrom: $(self.basename)

outputs:
  - id: fixed_solsdir
    type: Directory
    outputBinding:
      glob: $(inputs.solsdir.basename)

requirements:
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.solsdir)
        writable: true
