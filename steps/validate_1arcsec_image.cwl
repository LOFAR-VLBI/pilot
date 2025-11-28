cwlVersion: v1.2
class: CommandLineTool
id: validate_1arcsec_image
doc: |
    Validate 1 arcsecond image quality. Current assumption is that
    the RMS background noise should be below 200 μJy/beam.

baseCommand: validate_1arcsec_image.py

inputs:
    - id: image
      type: File
      doc: FITS images
      inputBinding:
        position: 1
        separate: true

outputs:
    - id: validation_csv
      type: File
      doc: CSV with 1 arcsecond validation information
      outputBinding:
        glob: "validation_1arcsec_image.csv"
    - id: logfile
      type: File[]
      doc: Log files corresponding to this step
      outputBinding:
        glob: validate_1arcsec_image*.log

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: validate_1arcsec_image.log
stderr: validate_1arcsec_image_err.log