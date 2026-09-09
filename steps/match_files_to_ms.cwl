cwlVersion: v1.2
class: CommandLineTool
label: Match files and MSes by name.
doc: |
  Filters the input files to retain only those for which a corresponding MS
  exists. This is checked by extracting the source name from both the file and
  the MS.

baseCommand: filter_files_to_mses.py

inputs:
  ms:
    type:
      - Directory[]
    doc: Input MeasurementSets to filter with
    inputBinding:
      prefix: "--ms"
      position: 1
      separate: true
  files:
    type:
      - File[]?
    doc: Files to filter into a set that matches the MSes.
    inputBinding:
      prefix: "--files"
      position: 2
      separate: true

outputs:
  filtered_files:
    type:
      - File[]?

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: match_files_to_ms.log
stderr: match_files_to_ms_err.log
