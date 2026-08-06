class: CommandLineTool
cwlVersion: v1.2
id: dp3_avg_step
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

  - id: avgstep
    type: int?
    doc: Averaging factor

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
  - valueFrom: $("avg.timestep=" + inputs.avgstep)
  - valueFrom: $("avg.freqstep=" + inputs.avgstep)
  - msout.storagemanager='dysco'
  - msout.storagemanager.databitrate=6
  - msout=$( inputs.msin.basename + '.avg.ms')

requirements:
  - class: InlineJavascriptRequirement

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: ResourceRequirement
    coresMin: 8

stdout: dp3_avg_step.log
stderr: dp3_avg_step_err.log

