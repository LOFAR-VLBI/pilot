class: CommandLineTool
cwlVersion: v1.2
id: upsample_subtract
doc: |
    Upsample the model visibilities in time and frequency from the low-resolution MeasurementSet
    to the full high-resolution data resolution and subtract these predicted model visibilities
    from the original high-resolution data.

baseCommand: DP3

inputs:
  - id: msin_highres
    type: Directory
    doc: Input MeasurementSet with high data resolution
    inputBinding:
      position: 0
      prefix: msin=
      separate: false
  - id: msin_lowres
    type: Directory
    doc: Input MeasurementSet with low data resolution
    inputBinding:
      position: 1
      prefix: transfer.source_ms=
      separate: false
  - id: ncpu
    type: int?
    doc: Number of cores to use.
    default: 4

outputs:
  - id: subms
    doc: Subtracted MeasurementSet
    type: Directory
    outputBinding:
      glob: $( inputs.msin_highres.basename + '.sub.ms')

  - id: logfile
    type: File[]
    outputBinding:
      glob: 6asec_avg*.log
    doc: |
        The files containing the stdout
        and stderr from the step.

arguments:
  - steps=[transfer,combine]
  - transfer.type=transfer
  - transfer.data=True
  - transfer.outputbuffername=PREDICT_SUB_BUFFER
  - transfer.datacolumn=PREDICT_SUB
  - combine.type=combine
  - combine.operation=subtract
  - combine.buffername=PREDICT_SUB_BUFFER
  - msout.storagemanager='dysco'
  - msout=$( inputs.msin_highres.basename + '.sub.ms')
  - msout.antennacompression=false
  - msout.uvwcompression=false
  - msout.scalarflags=false
  - msin.datacolumn=DATA_DI_CORRECTED
  - numthreads=$(inputs.ncpu)

requirements:
  - class: InlineJavascriptRequirement

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.msin_lowres)
        writable: false
  - class: ResourceRequirement
    coresMin: $(inputs.ncpu)

stdout: upsample_subtract.log
stderr: upsample_subtract_err.log
