class: CommandLineTool
cwlVersion: v1.2
id: summary
label: VLBI summary
doc: |
    This step creates a JSON formatted file
    containing pipeline run summary statistics.

baseCommand:
  - make_summary_pilot.py

inputs:
  - id: flagFiles
    type:
      - File[]
      - File
    inputBinding:
      position: 1
    doc: List of files with flag information in JSON format.

  - id: pipeline
    type: string?
    default: 'VLBI'
    inputBinding:
      position: 0
      prefix: --pipeline
    doc: Name of the pipeline.

  - id: run_type
    default: 'calibrator'
    type: string?
    inputBinding:
      position: 0
      prefix: --run_type
    doc: The type of the pipeline.

  - id: filter
    default: '*&'
    type: string?
    inputBinding:
      position: 0
      prefix: --filtered_antennas
    doc: A pattern of antenna names to filter from the processing.

  - id: bad_antennas
    default: '*&'
    type: string?
    inputBinding:
      position: 0
      prefix: --bad_antennas
    doc: A pattern of names of antennas with bad data.

  - id: Ateam_separation_file
    default: false
    type:
      - boolean?
      - File?
    inputBinding:
      position: 0
      prefix: --Ateam_separation_file

  - id: solutions
    default: false
    type:
      - boolean?
      - File?
    inputBinding:
      position: 0
      prefix: --solutions

  - id: clip_sources
    default: false
    type:
      - string?
      - boolean?
    inputBinding:
      position: 0
      prefix: --clip_sources
      separate: true
      itemSeparator: ','
      valueFrom: '$(self)'

  - id: removed_bands
    default: false
    type:
      - string?
      - boolean?
    inputBinding:
      position: 0
      prefix: --removed_bands
      separate: true
      itemSeparator: ','
      valueFrom: '$(self)'

  - id: min_unflagged_fraction
    default: 0.5
    type: float?
    inputBinding:
      position: 0
      prefix: --min_unflagged
    doc: The minimum required fraction of unflagged data per band.

  - id: refant
    default: ''
    type: string?
    inputBinding:
      position: 0
      prefix: --refant
    doc: The reference antenna used.

outputs:
  - id: summary_file
    doc: Summary File in JSON format.
    type: File
    outputBinding:
      glob: '*.json'

  - id: logfile
    type: File[]
    outputBinding:
      glob: summary*.log
    doc: |
        The files containing the stdout
        and stderr from the step.

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: summary.log
stderr: summary_err.log
