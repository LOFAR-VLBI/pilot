class: CommandLineTool
cwlVersion: v1.2
id: make_cubes
doc: Concatenate Q and U images into cubes for RM-synthesis

baseCommand:
  - make_pol_cubes.py

arguments: [--image-manifest, channel-images.json]

inputs:
  - id: image_directory
    type: Directory?
    doc: Directory containing WSClean channel images; preferred for large channel counts.
  - id: Q_images
    type: File[]?
    doc: List of Stokes Q images.
  - id: U_images
    type: File[]?
    doc: List of Stokes U images.
  - id: image_size
    type: int[]?
    doc: Image size in pixels as [x, y], matching WSClean -size.
    inputBinding:
      position: 0
      prefix: '--imsize'
      itemSeparator: ','
  - id: nchannels
    type: int
    doc: Number of channels as provided to WSClean.
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
    type: File
    doc: List of channels frequencies.
    outputBinding:
      glob: "*frequency_list.dat"
  - id: channel_flags
    type: File
    doc: JSON summary of channel rejection and noise threshold.
    outputBinding:
      glob: '*channel_flags.json'
  - id: rms_list
    type: File
    doc: List of average Q and U rms noise per channel.
    outputBinding:
      glob: "*avg_qunoise_list.dat"

requirements:
    - class: InlineJavascriptRequirement
    - class: DockerRequirement
      dockerPull: vlbi-cwl
    - class: LoadListingRequirement
      loadListing: no_listing
    - class: InitialWorkDirRequirement
      listing:
        - entryname: channel-images.json
          entry: >-
            $(JSON.stringify({image_directory: inputs.image_directory ? inputs.image_directory.path : null,
                             Q_images: (inputs.Q_images || []).map(function(f) { return f.path; }),
                             U_images: (inputs.U_images || []).map(function(f) { return f.path; })}))
