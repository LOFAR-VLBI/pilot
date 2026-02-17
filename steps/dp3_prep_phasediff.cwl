class: CommandLineTool
cwlVersion: v1.2
id: pre_averaging_dp3
label: DP3 Pre-averaging
doc: This step pre-averages measurement set for pulling phasediff scores from facetselfcal

baseCommand: DP3

inputs:
    - id: msin
      type: Directory
      doc: Input measurement set
      inputBinding:
        prefix: msin=
        position: 0
        shellQuote: false
        separate: false

outputs:
    - id: phasediff_ms
      type: Directory
      doc: Output measurement sets
      outputBinding:
        glob: $(inputs.msin.basename+".phasediff.ms")
    - id: logfile
      type: File[]
      doc: DP3 log files
      outputBinding:
        glob: dp3_prephasediff*.log

arguments:
  - steps=[avg]
  - msin.datacolumn=DATA
  - msout.storagemanager=dysco
  - avg.type=averager
  - avg.freqresolution=1562.24kHz
  - avg.timeresolution=120
  - msout=$(inputs.msin.basename+".phasediff.ms")

requirements:
  - class: InlineJavascriptRequirement

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: ResourceRequirement
    coresMin: 6


stdout: dp3_prephasediff.log
stderr: dp3_prephasediff_err.log
