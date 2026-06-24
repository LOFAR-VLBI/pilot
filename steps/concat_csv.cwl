class: CommandLineTool
cwlVersion: v1.2
id: concat_csv
doc: Concatenate CSV files with identical columns

baseCommand: awk

arguments:
  - 'NR == 1 || FNR > 1'

inputs:
  - id: input_csvs
    type: File[]
    doc: Input CSVs
    inputBinding:
      position: 2
      prefix: ""
      separate: true

  - id: output_csv_name
    type: string?
    default: "concat.csv"
    doc: Output csv name

outputs:
  - id: concat_csv
    type: stdout
    doc: Concatenated phasediff score CSV

  - id: logfile
    type: File[]
    outputBinding:
      glob: concat_csvs*.log
    doc: |
      The file containing stderr from the step.
      Passed as an array for consistency with other steps.

requirements:
  - class: InlineJavascriptRequirement

stdout: $(inputs.output_csv_name)
stderr: concat_csvs_err.log
