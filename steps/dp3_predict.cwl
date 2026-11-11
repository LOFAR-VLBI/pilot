class: CommandLineTool
cwlVersion: v1.2
id: dp3_predict
label: DP3 prediction
doc: |
    This step predicts a skymodel into a given MeasurementSet using DP3.

baseCommand: DP3

arguments:
  - steps=[predict]
  - msout.storagemanager=sisco
  - msout.datacolumn=MODEL_DATA
  - predict.usefastpredict=False
  - predict.operation=replace
  - predict.usebeammodel=True
  - predict.usechannelfreq=True
  - predict.beam_interval=240
  - predict.correcttimesmearing=true
  - predict.correctfreqsmearing=true

inputs:
    - id: msin
      type: Directory
      doc: Input measurement set
      inputBinding:
        prefix: msin=
        separate: false
    - id: skymodel
      type: File
      doc: Sky model in BBS format to predict.
      inputBinding:
        prefix: predict.sourcedb=
        separate: false
    - id: ncpu
      type: int?
      doc: Number of cores to use
      default: 8
      inputBinding:
        prefix: numthreads=
        separate: false

outputs:
    - id: msout
      type: Directory
      doc: Output MeasurementSet
      outputBinding:
        glob: $(inputs.msin.basename)
    - id: logfile
      type: File[]
      doc: DP3 log files
      outputBinding:
        glob: dp3_averager*.log

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.msin)
        writable: true

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: ResourceRequirement
    coresMin: $(inputs.ncpu)

stdout: dp3_predict.log
stderr: dp3_predict_err.log
