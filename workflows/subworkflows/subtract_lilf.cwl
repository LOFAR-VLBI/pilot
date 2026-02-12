class: Workflow
cwlVersion: v1.2
id: subtract_lilf
doc: |-
  Subtract a lilf model from the data using results from the LiLF pipeline.
  This prepares the data for widefield imaging by subtracting sources outside a given region.

inputs:
  - id: msin
    type: Directory[]
    doc: Input data from which the LoTSS skymodel will be subtracted.
  - id: h5_dd
    type: File
    doc: H5parm file containing the DD solutions
  - id: ddf_rundir
    type: Directory
    doc: Directory containing the output from DDF-pipeline.
  - id: box_size
    type: float?
    doc: |-
      Side length of a square box in degrees. The LoTSS skymodel is subtracted outside of this box.
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
    default: 6
  - id: chunkhours
    type: float?
    doc: The range of time to predict the model for at once. Lowering this value reduces memory footprint, but can increase runtime.

# h5_dd

outputs:
  - id: regionbox
    type: File
    outputSource:
      - makebox/box
    doc: DS9 region file outside of which the LiLF skymodel has been subtracted.
  - id: msout
    type: Directory[]
    outputSource:
      - upsample_subtract/subms
    doc: MS from which the LiLF skymodel has been subtracted.

steps:
  - id: makebox
    in:
      - id: ms
        source: msin
        valueFrom: $(self[0])
      - id: box_size
        source: box_size
    out:
      - id: box
    run: ../../steps/makebox.cwl
    doc: Make the box outside which the LiLF skymodel will be subtracted.

  - id: avg_ms_for_box_subtract
    in:
      - id: msin
        source: msin
    out:
      - id: avg_ms
    run: ../../steps/avg_ms_for_box_subtract.cwl
    scatter: msin

  - id: prepare_lilf_ddsol
    in:
      - id: avg_ms
        source: avg_ms_for_box_subtract/avg_ms
      - id: h5_dd
        source: h5_dd
    out:
      - id: h5_dd_addIS
    run: ../../steps/prepare_lilf_ddsol.cwl
    doc: Prepare ddsols of LiLF.

  - id: subtract
    in:
      - id: ms
        source: avg_ms_for_box_subtract/avg_ms
      - id: boxfile
        source: makebox/box
      - id: mslist
        source: makemslist/mslist
      - id: column
        default: "DATA"
      - id: solsdir
        source: fix_symlinks/solsdir
      - id: dds3sols
        source: gather_dds3/dds3sols
      - id: fitsfiles
        source: gather_dds3/fitsfiles
      - id: dicomodels
        source: gather_dds3/dicomodels
      - id: facet_layout
        source: gather_dds3/facet_layout
      - id: freqavg
        source: freqavg
      - id: timeavg
        source: timeavg
      - id: ncpu
        source: ncpu
      - id: chunkhours
        source: chunkhours
    out:
      - id: predictms
    run: ../../steps/box_predict.cwl
    scatter:
      - ms
      - mslist
    scatterMethod: dotproduct
    doc: Subtract the LoTSS model from the data.

  - id: upsample_subtract
    in:
      - id: msin_lowres
        source: subtract/predictms
      - id: msin_highres
        source: msin
    out:
      - id: subms
    run: ../../steps/upsample_subtract.cwl
    scatter:
      - msin_lowres
      - msin_highres
    scatterMethod: dotproduct

requirements:
  - class: ScatterFeatureRequirement
  - class: StepInputExpressionRequirement
