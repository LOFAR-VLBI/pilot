class: CommandLineTool
cwlVersion: v1.2
id: wsclean_pol
label: WSClean
doc: Runs WSClean on the input data to produce an image.

baseCommand: wsclean
arguments: [-verbose, -log-time, -no-update-model-required]

inputs:
  - id: msin
    type:
      - Directory
      - Directory[]
    inputBinding:
      position: 2
      shellQuote: false
      itemSeparator: ' '
  - id: tempdir
    type: string
    default: '.'
    inputBinding:
      position: 1
      shellQuote: false
      itemSeparator: ' '
      prefix: '-temp-dir'
  - id: apply-primary-beam
    type: boolean?
    default: false
  - id: cores
    type: int?
    default: 12
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-j'
  - id: size
    type: int[]?
    default: [1024, 1024]
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-size'
  - id: baseline_averaging
    type: float?
    default: 7.74
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-baseline-averaging'
  - id: minuv-l
    type: float?
    default: 80.0
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-minuv-l'
  - id: weight
    type:
      - string?
    default: briggs 0.0
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-weight'
  - id: data-column
    type: string?
    default: CORRECTED_DATA
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-data-column'
  - id: auto-mask
    type: float?
    default: 5.0
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-auto-mask'
  - id: auto-threshold
    type: float?
    default: 3.0
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-auto-threshold'
  - id: pol
    type: string?
    default: I,Q,U,V
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-pol'
  - id: name
    type: string?
    default: "image"
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-name'
  - id: scale
    type: string?
    default: "0.1asec"
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-scale'
  - id: beam-size
    type: string?
    default: "0.5asec"
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-beam-size'
  - id: channels-out
    type: int?
    default: 44
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-channels-out'

outputs:
  - id: Q_channel_images
    type: File[]
    doc: Per-channel Stokes Q images.
    outputBinding:
      glob: '$(inputs.name)-????-Q-image.fits'
  - id: U_channel_images
    type: File[]
    doc: Per-channel Stokes U images.
    outputBinding:
      glob: '$(inputs.name)-????-U-image.fits'

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

requirements:
  - class: ShellCommandRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.msin)
  - class: ResourceRequirement
    coresMin: $(inputs.cores)

stdout: wsclean_qu.log
stderr: wsclean_qu_err.log
