class: CommandLineTool
cwlVersion: v1.2
id: plot_field
doc: |
  Run plot_field on the phase centre from a given MeasurementSet.
  This requires internet access.

baseCommand: lofar-vlbi-plot

inputs:
  - id: msin
    type: Directory
    doc: MeasurementSet to take the phase centre from.
    inputBinding:
      prefix: --MS
      separate: true
      position: 0

outputs:
  - id: delay_calibrator_pf
    type: File
    doc: Delay Calibrator CSV
    outputBinding:
      glob: delay_calibrators.csv

arguments:
  - --continue_no_lotss

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
