class: CommandLineTool
cwlVersion: v1.2
id: gather_model_images
doc: |
    Gather the correct WSClean model images from a given directory
    with WSClean output products from a previous imaging run

baseCommand:
  - gather_model_images.sh

inputs:
  - id: model_image_directory
    type: Directory
    doc: Directory with model images
    inputBinding:
      position: 1

outputs:
  - id: filtered_model_image_directory
    type: Directory
    doc: Directory with filtered WSClean model images
    outputBinding:
      glob: output_images

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
