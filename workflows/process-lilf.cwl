class: Workflow
cwlVersion: v1.2
id: process_lilf
doc: |-
  Uses the results from the LiLF pipeline to the data to effect the following:

  * Correct the data from the Dutch stations for direction-independent effects.
  * Correct the data from the Dutch stations for direction-dependent effects towards the direction of the infield cal.
  * [Optionally] subtract the LiLF Dutch-baseline model from the data.

  Subtracting the LoTSS skymodel prepares the data for widefield imaging by subtracting sources outside a given region,
  defaulting to the approximate FWHM of the international stations.

inputs:
  - id: msin
    type: Directory[]
    doc: Input data from which the LiLF skymodel will be subtracted.
  - id: h5_rm
    type: File
    doc: Path to the LiLF h5parm containing the rotationmeasure000 solutions.
  - id: h5_phase
    type: File
    doc: Path to the LiLF h5parm containing the phase000 solutions.
  - id: h5_amp
    type: File
    doc: Path to the LiLF h5parm containing the amplitudeSmooth solutions.
  - id: box_size
    type: float?
    doc: |-
      Side length of a square box in degrees. The LiLF skymodel is subtracted outside of this box.
      Defaults to 2.5 degrees.
    default: 2.5
  - id: freqavg
    type: int?
    doc: Number of frequency channels to average after the subtract has been performed. Defaults to 1 (no averaging).
    default: 1
  - id: timeavg
    type: int?
    doc: Number of time slots to average after the subtract has been performed. Defaults to 1 (no averaging).
    default: 1
  - id: ncpu
    type: int?
    doc: Number of cores to use during the subtract. Defaults to 24.
    default: 24
  - id: chunkhours
    type: float?
    doc: The range of time to predict the model for at once. Lowering this value reduces memory footprint, but can increase runtime.
  - id: do_subtraction
    type: boolean?
    default: false
    doc: When set to true, the LiLF model will be subtracted from the LiLF corrected data.
  - id: solsdir
    type: Directory
    doc: aaaaa
  - id: ddf_rundir
    type: Directory
    doc: aaaaa

outputs:
  - id: regionbox
    type: File?
    outputSource:
      - subtract_lilf/regionbox
    pickValue: all_non_null
    doc: DS9 region file outside of which the LiLF skymodel has been subtracted.
  - id: msout
    type: Directory[]
    outputSource:
      - subtract_lilf/msout
      - dp3_applycal_lilf/output_data
    pickValue: first_non_null
    doc: MSs from which the LiLF skymodel has been subtracted.

steps:
  - id: dp3_applycal_lilf
    in:
      - id: msin
        source: msin
      - id: h5_rm
        source: h5_rm
      - id: h5_phase
        source: h5_phase
      - id: h5_amp
        source: h5_amp
    out:
      - id: output_data
      - id: logfile
    run: ../steps/dp3_applycal_lilf.cwl
    label: dp3_applycal_lilf
    scatter: msin


  - id: subtract_lilf
    in:
      - id: msin
        source: dp3_applycal_lilf/output_data
      - id: box_size
        source: box_size
      - id: freqavg
        source: freqavg
      - id: timeavg
        source: timeavg
      - id: ncpu
        source: ncpu
      - id: chunkhours
        source: chunkhours
      - id: do_subtraction
        source: do_subtraction
      - id: solsdir
        source: solsdir
      - id: ddf_rundir
        source: ddf_rundir
    out:
      - id: regionbox
      - id: msout
    label: subtract_lilf
    when: $(inputs.do_subtraction)
    run: ./subworkflows/subtract_lotss.cwl

requirements:
  - class: ScatterFeatureRequirement
  - class: StepInputExpressionRequirement
  - class: SubworkflowFeatureRequirement
  - class: MultipleInputFeatureRequirement
  - class: InlineJavascriptRequirement

