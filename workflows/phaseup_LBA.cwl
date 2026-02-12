class: Workflow
cwlVersion: v1.2
id: phaseup_LBA
label: VLBI phaseup
doc: |
    Phase shifts data to the in-field calibrator.

inputs:
  - id: msin
    type: Directory[]
    doc: Input data in MeasurementSet format.

  - id: delay_calibrator
    type: File
    doc: Catalogue file with information on in-field calibrator.

  - id: phaseup_config
    type: File
    doc: phaseup_config.txt for phaseup scores - ideally from root.

  - id: max_dp3_threads
    type: int?
    default: 5
    doc: The maximum number of threads DP3 should use per process.

  - id: number_cores
    type: int?
    default: 12
    doc: |
      Number of cores to use per job for tasks with
      high I/O or memory.

steps:
  - id: prep_delay
    in:
      - id: delay_calibrator
        source: delay_calibrator
      - id: mode
        default: "delay_calibration"
    out:
      - id: source_id
      - id: coordinates
      - id: logfile
    run: ../steps/prep_delay.cwl
    label: prep_delay

  - id: dp3_phaseup
    in:
      - id: msin
        source: msin
      - id: phase_center
        source: prep_delay/coordinates
      - id: beam_direction
        source: prep_delay/coordinates
      - id: msout_name
        source: prep_delay/source_id
      - id: max_dp3_threads
        source: max_dp3_threads
    out:
      - id: msout
      - id: logfile
      - id: errorfile
    run: ../steps/dp3_phaseup.cwl
    scatter: msin
    label: dp3_phaseup

  - id: summary
    in:
      - id: flagFiles
        source: phaseup_flags_join/flagged_fraction_antenna
      - id: pipeline
        default: VLBI
      - id: run_type
        default: phaseup-concat
      - id: solutions
        source: delay_cal_run/solutions
      - id: min_unflagged_fraction
        default: 0.5
      - id: refant
        default: CS001HBA0
    out:
      - id: summary_file
      - id: logfile
    run: ../steps/summary.cwl
    label: summary

  - id: save_logfiles
    in:
      - id: files
        linkMerge: merge_flattened
        source:
          - prep_delay/logfile
          - summary/logfile
      - id: sub_directory_name
        default: phaseup
    out:
      - id: dir
    run: ../steps/collectfiles.cwl
    label: save_logfiles

outputs:
  - id: msout
    type: Directory[]
    outputSource: phaseup_concatenate/msout
    doc: |
        The data in MeasurementSet format after
        phase-shifting to the delay calibrator.

  - id: logdir
    outputSource: save_logfiles/dir
    type: Directory
    doc: |
        The directory containing all the stdin
        and stderr files from the workflow.

  - id: summary_file
    type: File
    outputSource: summary/summary_file
    doc: |
        Pipeline summary statistics
        in JSON format.

requirements:
  - class: SubworkflowFeatureRequirement
  - class: ScatterFeatureRequirement
  - class: StepInputExpressionRequirement
  - class: MultipleInputFeatureRequirement
  - class: InlineJavascriptRequirement
