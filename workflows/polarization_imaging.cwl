class: Workflow
cwlVersion: v1.2
id: image_polarization 
label: Polarization imaging
doc: |
  This workflow will image the provided MS in Q and U, and perform Rotation Measure Synthesis to provide linear polarization images.

requirements:
    - class: SubworkflowFeatureRequirement

inputs:
    - id: msin
      type: Directory[]
      doc: MeasurementSets that will be imaged.

    - id: pixel_scale
      type: float
      doc: Pixel size in arcseconds.

    - id: resolution
      type: string
      doc: Angular resolution that will be passed to WSClean's taper argument. Its syntax follows that of WSClean.

    - id: image_size
      type: int
      doc: Size (in pixels) of image. Its syntax follows that of WSClean.

    - id: num_channels
      type: int
      doc: Number of channels to image in Q and U.

    - stokes:
      type: string[]
      default: ["Q","U"]

steps:
    - id: image_qu
      label: image_qu
      in:
        - id: msin
          source: msin
        - id: pixel_scale
          source: pixel_scale
        - id: resolution
          source: resolution
        - id: image_size
          source: image_size
        - id: num_channels
          source: num_channels
        - id: stokes
          source: stokes
      out:
        - id: MFS_image_pb
        - id: MFS_image
        - id: MFS_residual_pb
        - id: MFS_residual
        - id: MFS_model_pb
        - id: MFS_model
        - id: MFS_psf
      run: ../steps/wsclean_pol.cwl

    - id: make_cubes
      label: Make QU cubes
      in:
        - id: Q_images
          source: image_qu/Q_channel_images
        - id: U_images
          source: image_qu/U_channel_images
      out:
        - id: stokesQcube
        - id: stokesUcube
        - id: frequencies_list
      run: ../steps/concat_QU.cwl

    - id: rmsynth
      label: rmsynthesis
      in:
        - id: Qcube
          source: make_cubes/stokesQcube
        - id: Ucube
          source: make_cubes/stokesUcube
        - id: frequencies
          source: make_cubes/frequencies_list
      out:
        - id: FDF_maxPI
        - id: FDF_peakRM
        - id: FDF_clean_tot
      run: ../steps/rmsynthesis.cwl

outputs:
  - id: MFS_images_pb
    type: File[]
    outputSource: image_qu/MFS_image_pb
  - id: MFS_images
    type: File[]
    outputSource: image_qu/MFS_image

  - id: MFS_residuals_pb
    type: File[]
    outputSource: image_qu/MFS_residual_pb
  - id: MFS_residuals
    type: File[]
    outputSource: image_qu/MFS_residual

  - id: MFS_models_pb
    type: File[]
    outputSource: image_qu/MFS_model_pb
  - id: MFS_models
    type: File[]
    outputSource: image_qu/MFS_model

  - id: MFS_psfs
    type: File[]
    outputSource: image_qu/MFS_psf

  - id: stokesQcube
    type: File
    outputSource: make_cubes/stokesQcube

  - id: stokesUcube
    type: File
    outputSource: make_cubes/stokesUcube

  - id: FDF_maxPI
    type: File
    outputSource: rmsynth/FDF_maxPI

  - id: FDF_peakRM
    type: File
    outputSource: rmsynth/FDF_peakRM

  - id: FDF_clean_tot
    type: File
    outputSource: rmsynth/FDF_clean_tot




