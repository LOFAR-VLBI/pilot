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

    - id: flatten_solutions
      in:
        - id: nestedarray
          source: ddcal/solution_inspection_images
      out:
        - flattenedarray
      run: ../../steps/flatten.cwl

requirements:
  - class: ScatterFeatureRequirement
  - class: SubworkflowFeatureRequirement

outputs:
  - id: h5parms
    type: File[]
    outputSource: ddcal/merged_h5
    doc: Array of h5parms where each h5parm corresponds to the full cumulative calibration solutions for that calibrator

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
    outputSource: flatten_solutions/flattenedarray
    doc: LoSoTo solution inspection images

  - id: config_files
    type: File[]
    outputSource: ddcal/config_file
    doc: Automatically generated configuration files for facetselfcal
