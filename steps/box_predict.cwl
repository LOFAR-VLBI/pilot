class: CommandLineTool
cwlVersion: v1.2
id: subtract-LoTSS
label: Subtract a LoTSS model from the data.
doc: Predict a LoTSS model using the images and DD solutions derived by the DDF-pipeline. This requires DDFacet.

baseCommand:
  - sub_sources_outside_region

arguments:
  - --onlyuseweightspectrum
  - --noconcat
  - --keeplongbaselines
  - --nophaseshift
  - --nofixsym
  - --nosubtract
  - --stopafterpredict

inputs:
  - id: ms
    type: Directory
    doc: Input MeasurementSet to subtract the LoTSS model from.
  - id: solsdir
    type: Directory
    doc: Path to the SOLSDIR directory of the ddf-pipeline run.
  - id: boxfile
    type: File
    doc: DS9 region file outside which to subtract.
    inputBinding:
      position: 0
      prefix: --boxfile
  - id: mslist
    type: File
    doc: Text file with a list of MeasurementSets to subtract.
    inputBinding:
      position: 1
      prefix: --mslist
  - id: column
    type: string?
    doc: Column from which to subtract. Defaults to DATA_DI_CORRECTED.
    default: "DATA_DI_CORRECTED"
    inputBinding:
      position: 2
      prefix: --column
  - id: freqavg
    type: int?
    doc: Frequency averaging factor to average with after the subtract. Defaults to 1.
    default: 1
    inputBinding:
      position: 3
      prefix: --freqavg
  - id: timeavg
    type: int?
    doc: Time averaging factor to average with after the subtract. Defaults to 1.
    default: 1
    inputBinding:
      position: 4
      prefix: --timeavg
  - id: ncpu
    type: int?
    doc: Number of cores to use during the subtract. Defaults to 24.
    default: 6
    inputBinding:
      position: 5
      prefix: --ncpu
  - id: chunkhours
    type: float?
    doc: The range of time to predict the model for at once. Lowering this value reduces memory footprint, but can increase runtime.
    default: 0.5
    inputBinding:
      position: 6
      prefix: --chunkhours
  - id: dds3sols
    type: File[]
    doc: DDS3 solution files from the ddf-pipeline run.
  - id: fitsfiles
    type: File
    doc: The clean mask of the final image from the ddf-pipeline run.
  - id: dicomodels
    type: File
    doc: The clean component model of the final image from the ddf-pipeline run.
  - id: facet_layout
    type: File
    doc: The facet layout from the ddf-pipeline run.

outputs:
  - id: predictms
    type: Directory
    doc: MeasurementSet containing the predicted column.
    outputBinding:
      glob: $(inputs.ms.basename)
  - id: logfile
    type: File[]
    doc: log files corresponding to this step
    outputBinding:
      glob: box_predict*.log


requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.ms)
        writable: true
      - entry: $(inputs.solsdir)
      - entry: $(inputs.dds3sols)
      - entry: $(inputs.fitsfiles)
      - entry: $(inputs.dicomodels)
      - entry: $(inputs.facet_layout)
  - class: ResourceRequirement
    coresMax: $(inputs.ncpu)
    coresMin: $(inputs.ncpu)

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: box_predict.log
stderr: box_predict_err.log
