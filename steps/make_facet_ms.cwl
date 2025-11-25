class: CommandLineTool
cwlVersion: v1.2
id: make_facet_ms
doc: |
    Split out facet MeasurementSet after interpolating MODEL_DATA to DATA, subtraction, phase-shifting, averaging,
    applying of calibration solutions and the beam.

baseCommand:
  - make_facet_ms.py

inputs:
    - id: avg_ms
      type: Directory
      doc: Averaged MeasurementSet at lower time/freq resolution
      inputBinding:
        prefix: "--low_ms"
        position: 1
        separate: true
    - id: full_ms
      type: Directory
      doc: Full MeasurementSet without averaging
      inputBinding:
        prefix: "--high_ms"
        position: 2
    - id: h5parm
      type: File
      doc: Multi-directional h5parm
      inputBinding:
        prefix: "--h5"
        position: 3
        separate: true
    - id: polygon
      type: File
      doc: Facet polygon
      inputBinding:
        prefix: "--polygon"
        position: 4
        separate: true
    - id: polygon_info
      type: File
      doc: CSV with polygon information for averaging and names
      inputBinding:
        prefix: "--polygon_info"
        position: 5
        separate: true
    - id: tmpdir
      type: string?
      doc: Temporary directory to run I/O heavy jobs
      inputBinding:
        prefix: "--tmp"
        position: 5
        separate: true
    - id: ncpu
      type: int?
      doc: Number of cores to use during predict and subtract.
      default: 8


outputs:
    - id: facet_ms
      type: Directory
      doc: Predicted and subtracted MeasurementSet
      outputBinding:
        glob: "facet*.ms"

    - id: logfile
      type: File[]
      doc: Log files from model selection
      outputBinding:
        glob: make_facet_ms*.log

arguments:
    - --cleanup

hints:
    - class: DockerRequirement
      dockerPull: vlbi-cwl
    - class: ResourceRequirement
      coresMin: $(inputs.ncpu)

requirements:
    - class: InitialWorkDirRequirement
      listing:
        - entry: $(inputs.full_ms)
        - entry: $(inputs.avg_ms)
        - entry: $(inputs.h5parm)
        - entry: $(inputs.polygon)
        - entry: $(inputs.polygon_info)


stdout: make_facet_ms.log
stderr: make_facet_ms_err.log
