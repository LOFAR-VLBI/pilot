class: CommandLineTool
cwlVersion: v1.2
id: make_cubes
doc: Concatenate Q and U images into cubes for RM-synthesis

baseCommand:
  - make_pol_cubes.py

inputs:
  - id: imagename
    type: string
    doc: Image name as provided in WSClean.
    inputBinding:
      position: 0
      prefix: '--imagename'
  - id: image_size
    type: int
    doc: Image size in pixels as provided in WSClean.
    inputBinding:
      position: 0
      prefix: '--imsize'
  - id: nchannels
    type: int
    doc: Number of channels as provided in WSClean as -channels-out.
    default: 480
    inputBinding:
      position: 0
      prefix: '--nchan'

outputs:
  - id: stokesQcube
    type: string
    doc: Name of the Stokes Q that will be created.
  - id: stokesUcube
    type: string
    doc: Name of the Stokes U that will be created.
  - id: freqlist
    type: string
    doc: List of channels frequencies.
  - id: rmslist
    type: string
    doc: List of average Q and U rms noise per channel.

requirements:
    - class: InlineJavascriptRequirement
