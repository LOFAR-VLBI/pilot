class: CommandLineTool
cwlVersion: v1.2
id: avg_ms_for_box_subtract
doc: Average MeasurementSet in time and frequency for faster prediction for box subtraction

baseCommand:
  - DP3

inputs:
  - id: msin
    type: Directory
    doc: Input MeasurementSet
    inputBinding:
      position: 0
      prefix: msin=
      separate: false

outputs:
  - id: ms_avg
    doc: MeasurementSet at lower time/freq resolution
    type: Directory
    outputBinding:
      glob: "$( inputs.msin.basename + '.avg6asec.ms')"

  - id: logfile
    type: File[]
    outputBinding:
      glob: 6asec_avg*.log
    doc: |
        The files containing the stdout
        and stderr from the step.

arguments:
  - steps=[avg]
  - avg.type=averager
  - avg.timeresolution=8
  - avg.freqresolution='97.68kHz'
  - msout.storagemanager='dysco'
  - msout=$( inputs.msin.basename + '.avg6asec.ms')
  - msout.antennacompression=false
  - msout.uvwcompression=false
  - msout.scalarflags=false

requirements:
  - class: ShellCommandRequirement
  - class: InlineJavascriptRequirement

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.msin)
        writable: false
  - class: ResourceRequirement
    coresMin: 4

stdout: 6asec_avg.log
stderr: 6asec_avg_err.log