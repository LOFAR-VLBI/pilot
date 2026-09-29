class: CommandLineTool
cwlVersion: v1.2
id: make_main_config
label: Generate DI configuration for main calibrators
doc: Generate a direction-independent facetselfcal configuration for main calibrators.

baseCommand:
  - make_config_dical.py

inputs:
  - id: ms
    type: Directory
    doc: Input MeasurementSet.
    inputBinding:
      prefix: --ms
      position: 0
      separate: true

  - id: phasediff_output
    type: File
    doc: Phasediff scores and solution intervals.
    inputBinding:
      prefix: --phasediff_output
      position: 1
      separate: true

  - id: imagecat
    type: File?
    doc: Optional image catalogue used for nearby-source detection.
    inputBinding:
      prefix: --imagecat
      position: 2
      separate: true

  - id: smoothness
    type: float
    default: 1.0
    doc: Fallback smoothness used when no scalarphase solution is available.
    inputBinding:
      prefix: --smoothness
      position: 3

outputs:
  - id: configfile
    type: File
    outputBinding:
      glob: '*.config.txt'
    doc: Generated direction-independent configuration file.

  - id: logfile
    type: File[]
    outputBinding:
      glob: make_config_dical*.log

requirements:
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.ms)

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: make_config_dical.log
stderr: make_config_dical_err.log
