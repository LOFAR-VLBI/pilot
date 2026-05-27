class: CommandLineTool
cwlVersion: v1.2
id: prediction_avg
label: DP3 averaging for prediction
doc: Average MeasurementSet in time and frequency for faster prediction.

baseCommand: DP3

inputs:
  - id: msin
    type: Directory
    doc: Input MeasurementSet
    inputBinding:
      position: 0
      prefix: msin=
      separate: false
  - id: ncpu
    type: int?
    doc: Number of cores to use.
    default: 4
    inputBinding:
      position: 0
      prefix: numthreads=
      separate: false


outputs:
  - id: ms_avg
    doc: MeasurementSet at lower time/freq resolution
    type: Directory
    outputBinding:
      glob: "$( inputs.msin.basename + '.avg.ms')"

  - id: logfile
    type: File[]
    outputBinding:
      glob: predict_avg*.log
    doc: |
        The files containing the stdout
        and stderr from the step.

arguments:
  - steps=[avg]
  - avg.type=averager
  - avg.timeresolution=4
  - avg.freqresolution='48.84kHz'
  - msout.storagemanager='dysco'
  - msout=$( inputs.msin.basename + '.avg.ms')
  - msout.antennacompression=false
  - msout.uvwcompression=false
  - msout.scalarflags=false

requirements:
  - class: InlineJavascriptRequirement

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.msin)
        writable: false
  - class: ResourceRequirement
    coresMin: $(inputs.ncpu)

stdout: predict_avg.log
stderr: predict_avg.log

