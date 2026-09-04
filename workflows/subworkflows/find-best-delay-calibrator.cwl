class: Workflow
cwlVersion: v1.2
id: delay-calibration
label: VLBI delay calibration
doc: |
    Selects the best delay calibrator candidate.

requirements:
  - class: SubworkflowFeatureRequirement
  - class: MultipleInputFeatureRequirement
  - class: StepInputExpressionRequirement
  - class: InlineJavascriptRequirement
  - class: ScatterFeatureRequirement

inputs:
    - id: msin
      type: Directory[]
      doc: The raw data in a MeasurementSet version 2.0 format.
    - id: delay_calibrator
      type: File
      doc: A delay calibrator catalogue in CSV format.
    - id: image_catalogue
      type: File
      doc: A catalogue with other sources in the field (e.g. a LoTSS catalogue).
    - id: starting_skymodel
      type:
        - File[]?
      doc: |
        Optional starting models in FITS format used to kickstart the delay calibration. If given, the number of skymodels must be equal to `select_best_n_delay_calibrators`. Additionally, they should be named in such a way that when sorted by name, the delay calibrator MSes and skymodels end up in the same order.
    - id: select_best_n_delay_calibrators
      type: int?
      default: 1
      doc: Select this number of top-scoring delay calibrator candidates to attempt to calibrate.
    - id: frequency_resolution
      type: string?
      default: '390.56kHz'
      doc: |
        Frequency resolution to average the split off delay calibrators to.
    - id: time_resolution
      type: string?
      default: '32.'
      doc: |
        Time resolution to average the split off delay calibrators to.

steps:
    - id: select_best_delay_cal
      in:
        - id: msin
          source: msin
        - id: dd_selection
          default: true
        - id: do_selfcal
          default: false
        - id: image_cat
          source: delay_calibrator
        - id: select_best_n
          source: select_best_n_delay_calibrators
        - id: frequency_resolution
          source: frequency_resolution
        - id: time_resolution
          source: time_resolution
      out:
        - id: msout_concat_strong
        - id: msout_concat_weak
        - id: msout_concat_unreliable
        - id: phasediff_score_csv
      run: ../split-directions.cwl
      label: select_best_delay_cal
    
    - id: filter_skymodels
      in:
        - id: ms
          source:
            - select_best_delay_cal/msout_concat_strong
            - select_best_delay_cal/msout_concat_weak
            - select_best_delay_cal/msout_concat_unreliable
          linkMerge: merge_flattened
          pickValue: all_non_null
        - id: files
          source: starting_skymodel
      out:
        - id: filtered_files
      run: ../../steps/match_files_to_ms.cwl
      when: $(inputs.files != null)

    - id: sort_skymodels
      in:
        - id: input_entry
          source:
            - filter_skymodels/filtered_files
          pickValue: all_non_null
          linkMerge: merge_flattened
      out:
        - id: sorted_entries
      run: ../../steps/sort_by_name.cwl

    - id: sort_ms
      in:
        - id: input_entry
          source:
            - select_best_delay_cal/msout_concat_strong
            - select_best_delay_cal/msout_concat_weak
            - select_best_delay_cal/msout_concat_unreliable
          linkMerge: merge_flattened
          pickValue: all_non_null
      out:
        - id: sorted_entries
      run: ../../steps/sort_by_name.cwl

    - id: delay_selfcal
      label: Delay Selfcal
      in:
        - id: msin
          source: sort_ms/sorted_entries
        - id: delay_calibrator
          source: delay_calibrator
        - id: image_catalogue
          source: image_catalogue
        - id: model_image
          source: sort_skymodels/sorted_entries
      out:
        - id: solutions
        - id: starting_skymodel
        - id: config
        - id: pictures
        - id: logfile
      run: ./delay_cal_run.cwl
      scatter: [msin, model_image]
      scatterMethod: dotproduct

    - id: flatten_delay_images
      in:
        - id: nestedarray
          source: delay_selfcal/pictures
      out:
        - id: flattenedarray
      run: ../../steps/flatten.cwl
      label: flatten_delay_images

    - id: flatten_delay_models
      in:
        - id: nestedarray
          source: delay_selfcal/starting_skymodel
      out:
        - id: flattenedarray
      run: ../../steps/flatten.cwl
      label: flatten_delay_models

outputs:
  - id: msout
    outputSource:
      - select_best_delay_cal/msout_concat_strong
      - select_best_delay_cal/msout_concat_weak
      - select_best_delay_cal/msout_concat_unreliable
    linkMerge: merge_flattened
    pickValue: all_non_null
    type: Directory[]
    doc: |
        The fully concatenated data in MeasurementSet
        format, phase-shifted to the delay calibrator.

  - id: starting_skymodels
    outputSource: 
      - flatten_delay_models/flattenedarray
    type: File[]
    doc: Starting skymodels that were used to kickstart the delay calibration.

  - id: pictures
    outputSource: 
      - flatten_delay_images/flattenedarray
    type: File[]
    pickValue: all_non_null
    linkMerge: merge_flattened
    doc: Inspection plots generated by lofar_facet_selfcal.

  - id: configs
    outputSource: 
      - delay_selfcal/config
    type: File[]
    pickValue: all_non_null
    linkMerge: merge_flattened
    doc: Facetselfcal config files used for the calibration.

  - id: phasediff_score_csv
    outputSource: select_best_delay_cal/phasediff_score_csv
    type: 
      - File?
    doc: |
      A CSV file containing the phasediff scores for each of the calibrators that were split out.

  - id: solutions
    outputSource: delay_selfcal/solutions
    type:
      - File
      - File[]
    doc: |
      Delay calibration solutions for each source.


