cwlVersion: v1.2
class: Workflow
id: dical_val
doc: |
    Performing validation on direction-independent calibration solutions.
    Validation is based on phase and amplitude noise statistics.

inputs:
  - id: h5parm
    type:
      - File
      - File[]
    doc: h5parm calibration solution files

  - id: weighting_mses
    type: Directory[]?
    default: null
    doc: Matching calibrator MSes, read-only, for weighting and flagging limits.

  - id: use_ms_weighting
    type: boolean
    default: true

  - id: weight_uvmin
    type: float
    default: 40000.0

  - id: flag_solutions
    type: boolean
    default: false

steps:

  - id: validate_solutions
    in:
       - id: solutions
         source: h5parm
       - id: weighting_mses
         source: weighting_mses
       - id: use_ms_weighting
         source: use_ms_weighting
       - id: weight_uvmin
         source: weight_uvmin
       - id: flag_solutions
         source: flag_solutions
    out:
       - validation_csv
       - selected_h5
    run: ../../steps/validate_solutions.cwl

  - id: final_validation
    in:
       - id: validation_solutions_csv
         source: validate_solutions/validation_csv
       - id: solutions
         source: validate_solutions/selected_h5
    out:
       - logfile
    run: ../../steps/inspect_di_validated_sols.cwl

outputs:

  - id: validate_csv
    type: File
    outputSource: validate_solutions/validation_csv
    doc: Validation CSV file

  - id: selected_h5
    type: File[]
    outputSource: validate_solutions/selected_h5
    doc: The solution copies corresponding to the reported validation scores.
