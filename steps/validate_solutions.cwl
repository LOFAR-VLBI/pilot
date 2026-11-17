cwlVersion: v1.2
class: CommandLineTool
id: validate_solutions
doc: Validate calibration solution quality

baseCommand: validate_lofar_solutions.py

arguments:
    - prefix: --output-dir
      valueFrom: '$((inputs.weighting_mses != null || inputs.flag_solutions) ? "validated_solutions" : null)'

inputs:
    - id: solutions
      type:
        - File
        - File[]
      doc: Calibration solutions
      inputBinding:
        position: 2
        separate: true

    - id: weighting_mses
      type:
        - "null"
        - type: array
          items: Directory
          inputBinding:
            prefix: --weight-ms
            separate: true
      default: null
      doc: Matching calibrator MSes, read-only, for weighting and flagging limits.
      inputBinding:
        position: 3

    - id: weight_uvmin
      type: float
      default: 40000.0
      doc: Minimum baseline length in wavelengths for MS phase weighting.
      inputBinding:
        position: 4
        prefix: --weight-uvmin

    - id: use_ms_weighting
      type: boolean
      default: true
      doc: Use MS sensitivity weighting when matching MSes are supplied.
      inputBinding:
        position: 5
        prefix: --no-ms-weighting
        valueFrom: $(!self)

    - id: flag_solutions
      type: boolean
      default: false
      doc: Flag phase outliers within the limits and recalculate validation scores.
      inputBinding:
        position: 6
        prefix: --flag-solutions

outputs:
    - id: validation_csv
      type: File
      doc: CSV with calibration solution validation information
      outputBinding:
        glob: "validation_solutions.csv"
    - id: selected_h5
      type: File[]
      doc: The solution copies corresponding to the reported validation scores.
      outputBinding:
        glob: "validated_solutions/*.h5"
        outputEval: "$(self.length ? self : [].concat(inputs.solutions))"
    - id: logfile
      type: File[]
      doc: Log files corresponding to this step
      outputBinding:
        glob: validate_solutions*.log

requirements:
  - class: InlineJavascriptRequirement

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: validate_solutions.log
stderr: validate_solutions_err.log
