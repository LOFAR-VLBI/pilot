class: CommandLineTool
cwlVersion: v1.2
id: make_cubes
doc: Concatenate Q and U images into cubes for RM-synthesis

baseCommand:
  - python3
  - /home/shane/LOFAR_VLBI/pilot/scripts/make_pol_cubes.py

inputs:
  - id: Q_images
    type: File[]
    doc: List of Stokes Q images from /steps/wsclean_pol.cwl.
    inputBinding:
      position: 0
      prefix: '--qimages'
      itemSeparator: ','
  - id: U_images
    type: File[]
    doc: List of Stokes U images from /steps/wsclean_pol.cwl.
    inputBinding:
      position: 0
      prefix: '--uimages'
      itemSeparator: ','
  - id: image_size
    type: int[]
    doc: Image size in pixels as [x, y], matching WSClean -size.
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
    type: File
    doc: Name of the Stokes Q that will be created.
    outputBinding:
      glob: "*-polcube-Q.fits"
  - id: stokesUcube
    type: File
    doc: Name of the Stokes U that will be created.
    outputBinding:
      glob: "*-polcube-U.fits"
  - id: frequencies_list
    type: File?
    doc: List of channels frequencies.
    outputBinding:
      glob: "image_frequency_list.dat"
  - id: rms_list
    type: File?
    doc: List of average Q and U rms noise per channel.
    outputBinding:
      glob: "image_avg_qunoise_list.dat"

requirements:
  - class: InlineJavascriptRequirement

stdout: make_cubes_stdout.log
stderr: make_cubes_stderr.log