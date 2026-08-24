class: CommandLineTool
cwlVersion: v1.2
id: dp3_averaging
label: DP3 averaging
doc: This step averages a MeasurementSet with DP3

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
    - id: freq_resolution
      type: string?
      doc: Target frequency resolution, in Hz (or append MHz or kHz to specify it in those units)
      inputBinding:
        prefix: avg.freqresolution=
        shellQuote: false
        separate: false
    - id: time_resolution
      type: int?
      doc: Time resolution in seconds
      inputBinding:
        prefix: avg.timeresolution=
        separate: false
    - id: freq_step
      type: int?
      doc: Number of channels to average
      inputBinding:
        prefix: avg.freqstep=
        separate: false
    - id: time_step
      type: int?
      doc: Number of time slots to average
      inputBinding:
        prefix: avg.timestep=
        separate: false
    - id: ncpu
      type: int?
      doc: Number of cores to use
      default: 2
      inputBinding:
        prefix: numthreads=
        separate: false

outputs:
    - id: phasediff_ms
      type: Directory
      doc: Output measurement sets
      outputBinding:
        glob: $(inputs.msin.basename+".avg.ms")
    - id: logfile
      type: File[]
      doc: DP3 log files
      outputBinding:
        glob: dp3_averager*.log

arguments:
  - steps=[avg]
  - msout.storagemanager=dysco
  - avg.type=averager
  - msout=$(inputs.msin.basename+".avg.ms")

requirements:
  - class: InlineJavascriptRequirement

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: ResourceRequirement
    coresMin: $(inputs.ncpu)

stdout: dp3_averager.log
stderr: dp3_averager_err.log
