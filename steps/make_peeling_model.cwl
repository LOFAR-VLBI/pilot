class: CommandLineTool
cwlVersion: v1.2
id: make_peeling_model
doc: |
    Combines multiple skymodels and filters sources to keep for peeling.

baseCommand: make_peeling_model.py

inputs:
    - id: msin
      type: Directory
      doc: Input data in MeasurementSet format.
      inputBinding:
        position: 0
        prefix: --ms
        separate: true

    - id: skymodels
      type: File[]
      doc: Input sky models to merge and filter.
      inputBinding:
        prefix: --skymodels
        separate: true

    - id: peel_radius
      type: float
      doc: Radius in arcminutes within which sources are included for peeling.
      inputBinding:
        prefix: "--peel-radius"
        position: 4

outputs:
    - id: skymodel
      type: File
      outputBinding:
        glob: '*.peeling_skymodel.txt'
      doc: The merged and filtered sky model.

    - id: logfile
      type: File[]
      outputBinding:
        glob: make_peeling_model*.log
      doc: |
        The files containing the stdout
        and stderr from the step.

hints:
    - class: DockerRequirement
      dockerPull: vlbi-cwl

stdout: make_peeling_model.log
stderr: make_peeling_model_err.log
