class: CommandLineTool
cwlVersion: v1.2
id: concat_csv
doc: Concatenate CSV files with identical columns

baseCommand: [bash, concat.sh]

inputs:
  - id: input_csvs
    type: File[]
    doc: Input CSVs
    inputBinding:
      position: 2
      prefix: ""
      separate: true

  - id: output_csv
    type: string?
    default: "concat.csv"
    doc: Output csv
    inputBinding:
      position: 1

outputs:
  - id: concat_csv
    type: File
    doc: Concatenated phasediff score CSV
    outputBinding:
      glob: $(inputs.output_csv)

  - id: logfile
    type: File[]
    outputBinding:
      glob: concat_csvs*.log
    doc: |
      The files containing stdout and stderr from the step.

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entryname: concat.sh
        entry: |
          #!/bin/bash
          set -euo pipefail
          awk 'NR == 1 || FNR > 1' "$@" > "$1"

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: concat_csvs.log
stderr: concat_csvs_err.log
