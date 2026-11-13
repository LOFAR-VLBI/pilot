cwlVersion: v1.2
class: Workflow
id: correct_astrometry
label: Derive and apply astrometric corrections
doc: |
  Match validated calibrator measurements to an astrometric reference catalogue,
  fit source positions, derive per-MeasurementSet corrections, apply them, and
  update the headers of the self-calibration images.

requirements:
  - class: SubworkflowFeatureRequirement
  - class: ScatterFeatureRequirement
  - class: MultipleInputFeatureRequirement

inputs:
  - id: astrometric_references
    type: File?
    doc: Reference catalogue containing Source_id, RA, and DEC columns.

  - id: validation_csv
    type: File?
    doc: Validation results used to identify sources to cross-match.

  - id: msin
    type: Directory[]
    doc: MeasurementSets to receive the astrometric phase correction.

  - id: fits_images
    type: File[]
    doc: Self-calibration FITS images whose headers will be shifted.

  - id: h5parm
    type: File?
    doc: Existing calibration solutions to apply to the MeasurementSets.

steps:
  - id: derive_astrometric_corrections
    in:
      - id: astrometric_references
        source: astrometric_references
      - id: validation_csv
        source: validation_csv
      - id: fits_images
        source: fits_images
    out:
      - corrected_fits_images
      - delta_ra
      - delta_dec
      - logfiles
    run: ../../steps/derive_astrometric_corrections.cwl

  - id: create_astrometric_h5parm
    label: Derive an astrometric h5parm for each MeasurementSet
    in:
      - id: ms
        source: msin
      - id: delta_ra
        source: derive_astrometric_corrections/delta_ra
      - id: delta_dec
        source: derive_astrometric_corrections/delta_dec
    out:
      - h5parm
      - logfiles
    run: ../../steps/create_astrometric_h5parm.cwl
    scatter: [ms]

  - id: flatten_logs_h5parm
    in:
      - id: nestedarray
        source: create_astrometric_h5parm/logfiles
    out:
      - flattenedarray
    run: ../../steps/flatten.cwl

  - id: sort_mses
    in:
      - id: input_entry
        source: msin
    out:
      - id: sorted_entries
    run: ../../steps/sort_by_name.cwl

  - id: sort_h5parms
    in:
      - id: input_entry
        source: create_astrometric_h5parm/h5parm
    out:
      - id: sorted_entries
    run: ../../steps/sort_by_name.cwl

  - id: apply_astrometric_corrections
    label: Apply astrometric corrections to the MeasurementSets
    in:
      - id: ms
        source: sort_mses/sorted_entries
      - id: h5parm
        source: sort_h5parms/sorted_entries
      - id: infix
        default: ".astrometry"
    out:
      - ms_out
      - logfile
    run: ../../steps/applycal.cwl
    scatter: [ms, h5parm]
    scatterMethod: dotproduct

  - id: flatten_logs_apply_astrometry
    in:
      - id: nestedarray
        source: apply_astrometric_corrections/logfile
    out:
      - flattenedarray
    run: ../../steps/flatten.cwl

outputs:
  - id: msout
    type: Directory[]
    outputSource: apply_astrometric_corrections/ms_out
    doc: MeasurementSets with calibration and astrometric corrections applied.

  - id: corrected_fits_images
    type: File[]
    outputSource: derive_astrometric_corrections/corrected_fits_images

  - id: astrometric_h5parms
    type: File[]
    outputSource: create_astrometric_h5parm/h5parm
    doc: Per-MeasurementSet h5parms containing astrometric corrections.

  - id: logfile
    type: File[]
    outputSource:
      - derive_astrometric_corrections/logfiles
      - flatten_logs_h5parm/flattenedarray
      - flatten_logs_apply_astrometry/flattenedarray
    pickValue: all_non_null
    linkMerge: merge_flattened
    doc: Logs from the astrometric correction workflow.
