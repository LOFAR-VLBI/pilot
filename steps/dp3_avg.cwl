class: CommandLineTool
cwlVersion: v1.2
id: dp3_averaging
label: DP3 averaging
doc: |
    This step averages a MeasurementSet with DP3.
    Note that freq_resolution and freq_step are mutually
    exclusive (likewise for time_resolution and time_step)

baseCommand: DP3

arguments:
  - steps=[avg]
  - msout.storagemanager=dysco
  - avg.type=averager
  - msout=$(inputs.msin.basename+".avg.ms")

inputs:
    - id: msin
      type: Directory
      doc: Input measurement set
      inputBinding:
        prefix: msin=
        position: 0
        separate: false
    - id: freq_resolution
      type: string?
      doc: Target frequency resolution, in Hz (or append MHz or kHz to specify it in those units)
      inputBinding:
        prefix: avg.freqresolution=
        separate: false
    - id: time_resolution
      type: float?
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
      default: 1
      inputBinding:
        prefix: numthreads=
        separate: false

outputs:
    - id: dp3_avg_ms
      type: Directory
      doc: Output MeasurementSet
      outputBinding:
        glob: $(inputs.msin.basename+".avg.ms")
    - id: logfile
      type: File[]
      doc: DP3 log files
      outputBinding:
        glob: dp3_averager*.log

requirements:
  - class: InlineJavascriptRequirement

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: ResourceRequirement
    coresMin: $(inputs.ncpu)

stdout: dp3_averager.log
stderr: dp3_averager_err.log
