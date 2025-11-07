class: CommandLineTool
cwlVersion: v1.2
id: swarp
label: Swarp
doc: Runs Swarp to create a mosaic from the given images.

baseCommand: swarp

inputs:
  - id: config
    type: File
    inputBinding:
      position: 2
      itemSeparator: ' '
      prefix: '-c'
  - id: image_name
    type: string?
    default: "mosaic.fits"
    inputBinding:
      position: 3
      shellQuote: false
      itemSeparator: ' '
      prefix: '-imageout_name '
  - id: input_images
    type: File[]
    inputBinding:
      position: 4
      itemSeparator: ' '
  - id: cores
    type: int?
    default: 8

outputs:
  - id: output_image
    type: File
    doc: The final mosaic.
    outputBinding:
      glob: '$(inputs.image_name)'

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

requirements:
  - class: ShellCommandRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.input_images)
  - class: ResourceRequirement
    coresMin: $(inputs.cores)

stdout: swarp.log
stderr: swarp_err.log
