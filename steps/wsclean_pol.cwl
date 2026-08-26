class: CommandLineTool
cwlVersion: v1.2
id: wsclean_pol_qu
label: WSClean
doc: Runs WSClean on the input data to produce Q and U channel images.

baseCommand: wsclean
arguments: [-verbose, -log-time, -no-update-model-required]

inputs:
  - id: msin
    type: Directory[]
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
  - id: size
    type: int[]?
    default: [1024, 1024]
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-size'
  - id: minuv-l
    type: float?
    default: 80.0
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-minuv-l'
  - id: briggs
    type: float?
    default: -1.4
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-weight briggs'
  - id: parallel-reordering
    type: int?
    default: 6
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-parallel-reordering'
  - id: mgain
    type: float?
    default: 0.6
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-mgain'
  - id: auto-mask
    type: float?
    default: 3.0
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-auto-mask'
  - id: auto-threshold
    type: float?
    default: 0.5
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-auto-threshold'
  - id: pol
    type: string?
    default: q,u
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
    default: "0.075asec"
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-scale'
  - id: beam-size
    type: string?
    default: "0.3asec"
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-beam-size'
  - id: taper-gaussian
    type: string?
    default: 0.25asec
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-taper-gaussian'
  - id: niter
    type: int
    default: 5000
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-niter'
  - id: multiscale-scale-bias
    type: float?
    default: 0.85
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-multiscale-scale-bias'
  - id: parallel-deconvolution
    type: int?
    default: 2600
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-parallel-deconvolution'
  - id: parallel-gridding
    type: int?
    default: 6
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-parallel-gridding'
  - id: multiscale
    type: boolean?
    default: true
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-multiscale'
  - id: multiscale-max-scales
    type: int?
    default: 3
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-multiscale-max-scales'
  - id: nmiter
    type: int?
    default: 5
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-nmiter'
  - id: channels-out
    type: int?
    default: 480
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-channels-out'
  - id: join-channels
    type: boolean?
    default: true
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-join-channels'
  - id: join-polarizations
    type: boolean?
    default: true
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-join-polarizations'
  - id: squared-channel-joining
    type: boolean?
    default: true
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-squared-channel-joining'
  - id: fit-spectral-pol
    type: int?
    default: 3
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-fit-spectral-pol'
  - id: gridder
    type: string?
    default: wgridder
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-gridder'
  - id: fitrm
    type: boolean?
    default: true
    inputBinding:
      position: 1
      shellQuote: false
      prefix: '-fit-rm'

outputs:
  - id: Q_channel_images
    type: File[]?
    doc: Per-channel Stokes Q images.
    outputBinding:
      glob: '$(inputs.name)-????-Q-image.fits'
  - id: U_channel_images
    type: File[]?
    doc: Per-channel Stokes U images.
    outputBinding:
      glob: '$(inputs.name)-????-U-image.fits'
  - id: I_channel_images
    type: File[]?
    doc: Per-channel Stokes I images.
    outputBinding:
      glob: '$(inputs.name)-????-I-image.fits'
  - id: V_channel_images
    type: File[]?
    doc: Per-channel Stokes V images.
    outputBinding:
      glob: '$(inputs.name)-????-V-image.fits'
  - id: MFS_images
    type: File[]?
    doc: MFS images.
    outputBinding:
      glob: '*MFS*image.fits'

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

requirements:
  - class: ShellCommandRequirement
  - class: InlineJavascriptRequirement
    expressionLib:
      - |
        function wsclean_cores(size) {
          var imsize = Math.max(size[0], size[1]);
          var raw = imsize / 512.0;
          var cores = Math.round(raw / 4.0) * 4;   // nearest multiple of 4
          return Math.max(4, Math.min(64, cores));
        }
  - class: ResourceRequirement
    coresMin: |
      ${ return inputs.ncpu !== null ? inputs.ncpu : wsclean_cores(inputs.size); }
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.msin)

stdout: wsclean_qu.log
stderr: wsclean_qu_err.log
