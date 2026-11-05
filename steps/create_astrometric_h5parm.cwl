cwlVersion: v1.2
class: CommandLineTool
id: create_astrometric_h5parm
label: Create astrometric correction h5parm
doc: |
  Derive the astrometric correction for a MeasurementSet using its phase centre.

baseCommand: create_astrometric_h5parm.py

inputs:
  - id: ms
    type: Directory
    doc: MeasurementSet used to read the phase centre and antenna positions.
    inputBinding:
      prefix: --ms
      position: 1

  - id: delta_ra
    type: float
    doc: Offset to shift towards the intended right ascension in degrees.
    inputBinding:
      prefix: --delta-ra
      position: 2

  - id: delta_dec
    type: float
    doc: Offset to shift toward the intended declination in degrees.
    inputBinding:
      prefix: --delta-dec
      position: 3

outputs:
  - id: h5parm
    type: File
    doc: H5parm containing the astrometric clock correction.
    outputBinding:
      glob: ILTJ*.astrometry.h5

  - id: logfiles
    type: File[]
    doc: Standard output and error logs from the script.
    outputBinding:
      glob:
        - create_astrometric_h5parm.log
        - create_astrometric_h5parm_err.log

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: create_astrometric_h5parm.log
stderr: create_astrometric_h5parm_err.log
