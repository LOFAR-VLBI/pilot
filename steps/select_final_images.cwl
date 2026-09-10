class: CommandLineTool
cwlVersion: v1.2
id: select_final_images
label: Select final selfcal images.
doc: Selects the final selfcal images from overlapping sets of sources

baseCommand: select_final_images.py

inputs:
  - id: fits_strong
    type: File[]?
    inputBinding:
      position: 1
      prefix: --images-strong
      separate: true
    doc: |
        A string that determines which
        MeasurementSets should be combined.

  - id: fits_weak
    type: File[]?
    inputBinding:
      position: 1
      prefix: --images-weak
      separate: true
    doc: |
        A string that determines which
        MeasurementSets should be combined.

  - id: fits_unreliable
    type: File[]?
    inputBinding:
      position: 1
      prefix: --images-unreliable
      separate: true
    doc: |
        A string that determines which
        MeasurementSets should be combined.

outputs:
  - id: final_fits_strong
    type: File[]?
    doc: The final images of strong calibrators.
  - id: final_fits_weak
    type: File[]?
    doc: The final images of weak calibrators.
  - id: final_fits_unreliable
    type: File[]?
    doc: The final images of unreliable calibrators.

requirements:
  - class: InlineJavascriptRequirement
hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: select_final_images.log
stderr: select_final_images_err.log
