class: Workflow
cwlVersion: v1.2
id: post-subtract-ddcal
label: Automated direction-dependent calibration for wide-field imaging after facet subtraction
doc: |
  This is a workflow for the LOFAR-VLBI pipeline that follows on the delay-calibration and:
    * Splits a LOFAR MeasurementSet into various target directions with split-directions.cwl
    * Performs self-calibration on the target facet at 6" resolution with facetselfcal
    * Performs self-calibration on the target direction at 0.3" resolution with facetselfcal

requirements:
  - class: SubworkflowFeatureRequirement
  - class: MultipleInputFeatureRequirement

inputs:
    - id: msin
      type: Directory[]
      doc: The input MeasurementSets of the entire field-of-view with or without delay-calibration solutions applied.

    - id: polygon_info
      type: File
      doc: Polygon CSV file with information about polygon centre and selfcal direction (output from facet_subtract.cwl)

    - id: phasediff_scores
      type: File
      doc: CSV with DD selection positions and phasediff scores (from dd-calibration.cwl)

    - id: max_dp3_threads
      type: int?
      default: 4
      doc: Number of cores to use per job for tasks with high I/O or memory.

    - id: model_cache
      type: string?
      doc: Neural network cache directory.

    - id: multi_observation
      type: boolean?
      default: false
      doc: If multiple observations are combined, this requires additional steps.

steps:
    - id: split_facet_directions #TODO: Read polygon_info to get selfcal direction from facet and split out
      label: Split out calibrator sources corresponding to facet directions
      in:
        - id: msin
          source: msin
        - id: polygon_info
          source: polygon_info
      out:
        - selfcal_ms
      run: ./...
      scatter: msin

    - id: combine_selfcal_directions #TODO: Combine selfcal groups from same target directions
      label: Combine self-calibration directions
      in:
        - id: msin
          source: split_facet_directions/selfcal_ms
        - id: multi_observations
          source: multi_observations
      out:
        - ms_groups
      run: ./...
      when: $(inputs.multi_observations)

    - id: dd_calibration #TODO: 0.3" calibration with auto_selfcal.cwl, make 6" image to inspect artefacts, extra averaging for 6" facet-calibration (for facets with artefacts), then merge solutions together
      label: ...
      in:
        - id: msin
          source:
            - combine_selfcal_directions/ms_groups
            - split_facet_directions/selfcal_ms
          pickValue: first_non_null
        - id: polygon_info
          source: polygon_info
        - id: phasediff_scores
          source: phasediff_scores
      out:
        - h5parms
        - selfcal_images
        - selfcal_inspection_images
        - solution_inspection_images
      scatter: msin #TODO: Can be both array and non-array?

outputs:

    - id: FITS_images
      type: File[]
      outputSource: dd_calibration/selfcal_images
      doc: Self-calibration image in FITS format

    - id: calibration_solutions
      type: File[]
      outputSource: dd_calibration/h5parms
      doc: Self-calibration solutions in h5parm format

    - id: solution_inspection_images
      type: Directory[]
      outputSource: dd_calibration/solution_inspection_images
      doc: LoSoTo solution inspection images

    - id: selfcal_PNG_images
      type: File[]
      outputSource: dd_calibration/selfcal_inspection_images
      doc: Self-calibration images in PNG format

    - id: msout
      type: Directory[]
      outputSource: split_facet_directions/msout_concat
      doc: MeasurementSets of all directions
