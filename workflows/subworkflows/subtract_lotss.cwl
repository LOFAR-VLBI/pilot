class: Workflow
cwlVersion: v1.2
id: subtract_lotss
doc: |-
  Subtract a LoTSS model from the data using results from the DDF-pipeline.
  This prepares the data for widefield imaging by subtracting sources outside a given region,
  defaulting to the approximate FWHM of the international stations.

inputs:
  - id: msin
    type: Directory[]
    doc: Input data from which the LoTSS skymodel will be subtracted.
  - id: solsdir
    type: Directory
    doc: Path to the SOLSDIR directory of the DDF-pipeline run.
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

outputs:
  - id: regionbox
    type: File
    outputSource:
      - makebox/box
    doc: DS9 region file outside of which the LoTSS skymodel has been subtracted.
  - id: msout
    type: Directory[]
    outputSource:
      - upsample_subtract/subms
    doc: MS from which the LoTSS skymodel has been subtracted.

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
    doc: Make the box outside which the LoTSS skymodel will be subtracted.

  - id: gather_dds3
    in:
      - id: ddf_rundir
        source: ddf_rundir
    out:
      - id: dds3sols
      - id: fitsfiles
      - id: dicomodels
      - id: facet_layout
    run: ../../steps/gatherdds3.cwl
    doc: Gather the solutions and images required to subtract the LoTSS model.

  - id: fix_symlinks
    in:
      - id: ddf_rundir
        source: ddf_rundir
      - id: ddf_solsdir
        source: solsdir
    out:
      - id: logfiles
      - id: solsdir
    run: ../../steps/fix_symlinks_ddf.cwl

  - id: rename_solsdir_mses
    in:
      - id: msin
        source: msin
      - id: solsdir
        source: fix_symlinks/solsdir
    out:
      - id: fixed_solsdir
    run: ../../steps/rename_solsdir_entries.cwl

  - id: avg_ms_for_box_subtract
    in:
      - id: msin
        source: msin
    out:
      - id: avg_ms
    run: ../../steps/avg_ms_for_box_subtract.cwl
    scatter: msin

  - id: makemslist
    in:
      - id: ms
        source: avg_ms_for_box_subtract/avg_ms
    out:
      - id: mslist
    run: ../../steps/make_mslist.cwl
    scatter: ms
    doc: Make the list of MSes to subtract.

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
        source: rename_solsdir_mses/fixed_solsdir
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
