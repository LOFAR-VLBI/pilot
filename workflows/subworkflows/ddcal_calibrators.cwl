cwlVersion: v1.2
class: Workflow
id: ddcal_int
doc: Performing direction-dependent self-calibration for international LOFAR stations for multiple directions.

inputs:
  - id: msin
    type: Directory[]
    doc: Input MeasurementSets from individual calibrator directions.

  - id: dd_precorrections
    type: File?
    doc: Multi-directional h5parm with Dutch DD solutions.

  - id: freeze_dutch_solutions
    type: boolean
    doc: Leave the Dutch stations untouched during selfcal. Useful if pre-applying Dutch station corrections.

  - id: phasediff_score_csv
    type: File?
    doc: CSV with DD selection positions and phasediff scores.

  - id: model_cache
    type: string?
    doc: Neural network cache directory.

  - id: validate
    type: boolean
    default: true
    doc: If set to true the pipeline will perform validation of the direction-dependent calibrator selection.

  - id: max_rejected_fraction
    type: float?
    default: 0.3
    doc: |
       Maximum fraction of bad solutions when validating. Lower value is stricter.
       Workflow crashes if fraction is exceeded.

steps:
    - id: ddcal
      in:
        - id: msin
          source: msin
        - id: dd_precorrections
          source: dd_precorrections
        - id: freeze_dutch_solutions
          source: freeze_dutch_solutions
        - id: phasediff_score_csv
          source: phasediff_score_csv
        - id: model_cache
          source: model_cache
      out:
        - merged_h5
        - fits_images
        - selfcal_inspection_images
        - solution_inspection_images
        - config_file
      run: ./auto_selfcal.cwl
      scatter: msin

    - id: flatten_images
      in:
        - id: nestedarray
          source: ddcal/selfcal_inspection_images
      out:
        - flattenedarray
      run: ../../steps/flatten.cwl

    - id: flatten_solution_plots
      in:
        - id: nestedarray
          source: ddcal/solution_inspection_images
      out:
        - flattenedarray
      run: ../../steps/flatten.cwl

    - id: validation
      in:
        - id: images
          source: ddcal/fits_images
        - id: h5parm
          source: ddcal/merged_h5
        - id: model_cache
          source: model_cache
        - id: validate
          source: validate
        - id: max_rejected_fraction
          source: max_rejected_fraction
      out:
        - h5parm_selected
        - images_selected
        - validate_csv
      when: $(inputs.validate)
      run: ./ddcal_validation.cwl

requirements:
  - class: ScatterFeatureRequirement
  - class: SubworkflowFeatureRequirement

outputs:
  - id: h5parms
    type: File[]
    outputSource:
      - validation/h5parm_selected
      - ddcal/merged_h5
    pickValue: first_non_null
    linkMerge: merge_nested
    doc: Array of h5parms where each h5parm corresponds to the full cumulative calibration solutions for that calibrator

  - id: validation_csv
    type: File?
    outputSource: validation/validate_csv
    doc: Catalogue with validation results for all sources that were calibrated.

  - id: selfcal_images
    type: File[]
    outputSource: ddcal/fits_images
    doc: Self-calibration images in FITS format

  - id: selfcal_inspection_images
    type: File[]
    outputSource: flatten_images/flattenedarray
    doc: Self-calibration inspection images in PNG format

  - id: solution_inspection_images
    type: Directory[]
    outputSource: flatten_solution_plots/flattenedarray
    doc: LoSoTo solution inspection images

  - id: config_files
    type: File[]
    outputSource: ddcal/config_file
    doc: Automatically generated configuration files for facetselfcal
