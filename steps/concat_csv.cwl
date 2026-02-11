class: CommandLineTool
cwlVersion: v1.2
id: concat_csv
doc: Concatenate CSV files with the same columns

baseCommand: concat_csv.py

inputs:
  - id: input_csvs
    type: File[]
    doc: Input CSVs
    inputBinding:
      prefix: --input
      separate: true
      position: 0
  - id: output_csv
    type: string?
    default: "concat.csv"
    doc: Output csv
    inputBinding:
      prefix: --output
      separate: true
      position: 1

outputs:
  - id: concat_csv
    type: File
    doc: Concatenated phasediff score concats CSV
    outputBinding:
      glob: $(inputs.output_csv)
  - id: logfile
    type: File[]
    outputBinding:
      glob: concat_csvs*.log
    doc: |
      The files containing the stdout
      and stderr from the step.

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: concat_csvs.log
stderr: concat_csvs_err.log