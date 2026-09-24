cwlVersion: v1.2
class: CommandLineTool
id: make_dd_config
doc: Creates a configuration file as input for direction-dependant calibration with data from the full ILT.

baseCommand:
    - make_config_international.py

inputs:
  - id: ms
    type: Directory
    doc: Input MeasurementSet
    inputBinding:
      position: 2
      prefix: "--ms"
      separate: true

  - id: phasediff_output
    type: File?
    doc: Phasediff scoring output csv
    inputBinding:
      prefix: "--phasediff_output"
      position: 3
      separate: true

  - id: reset_dutch_solutions
    type: boolean
    doc: Reset Dutch station solutions during calibration such that pre-applied NL corrections are kept as-is.
    inputBinding:
      prefix: "--reset_dutch_solutions"
      position: 4

outputs:
    - id: dd_config
      type: File
      doc: A plain-text file containing configuration options for self-calibration
      outputBinding:
        glob: "*.config.txt"
    - id: logfile
      type: File[]
      doc: Log files corresponding to this step
      outputBinding:
        glob: make_dd_config*.log

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entry: $( inputs.ms )

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: make_dd_config.log
stderr: make_dd_config_err.log
