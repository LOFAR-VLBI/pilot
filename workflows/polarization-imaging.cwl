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
      type: string
      doc: Pixel size (WSClean scale), e.g. "0.075asec".

    - id: resolution
      type: string
      doc: Angular resolution that will be passed to WSClean taper argument. Syntax follows that of WSClean.

    - id: image_size
      type: int[]
      doc: Size (in pixels) of image, [x, y]. Syntax follows that of WSClean.

    - id: num_channels
      type: int
      doc: Number of channels to image in Q and U.

    - id: stokes
      type: string
      default: "IQUV"

    - id: rmtools_max_lam2
      type: float?
      default: 150
      doc: Maximum lambda-squared value for rmsynth3d (-l).

    - id: rmtools_dlam2
      type: float?
      default: 0.3
      doc: Lambda-squared channel width for rmsynth3d (-d).

    - id: rmtools_output_prefix
      type: string?
      doc: Prefix for RM-Tools output products. Defaults to Stokes Q basename.

    - id: rmtools_extra_args
      type: string?
      doc: Extra arguments passed to rmsynth3d.

steps:
    - id: image_qu
      label: image_qu
      in:
        - id: msin
          source: msin
        - id: scale
          source: pixel_scale
        - id: taper-gaussian
          source: resolution
        - id: size
          source: image_size
        - id: channels-out
          source: num_channels
        - id: pol
          source: stokes
      out:
        - id: Q_channel_images
        - id: U_channel_images
      run: ../steps/wsclean_pol.cwl

    - id: make_cubes
      label: Make QU cubes
      in:
        - id: Q_images
          source: image_qu/Q_channel_images
        - id: U_images
          source: image_qu/U_channel_images
        - id: image_size
          source: image_size
        - id: nchannels
          source: num_channels
      out:
        - id: stokesQcube
        - id: stokesUcube
        - id: frequencies_list
        - id: rms_list
      run: ../steps/concat_pol.cwl

    - id: run_rmtools
      label: RM synthesis
      in:
        - id: stokes_q
          source: make_cubes/stokesQcube
        - id: stokes_u
          source: make_cubes/stokesUcube
        - id: freqs_hz
          source: make_cubes/frequencies_list
        - id: max_lam2
          source: rmtools_max_lam2
        - id: dlam2
          source: rmtools_dlam2
        - id: output_prefix
          source: rmtools_output_prefix
        - id: extra_args
          source: rmtools_extra_args
      out:
        - id: fdf_im_dirty
        - id: fdf_real_dirty
        - id: fdf_tot_dirty
        - id: fdf_maxpi
        - id: fdf_peakrm
        - id: rmsynth_stdout
        - id: rmsynth_stderr
      run: ../steps/run_rmtools.cwl

outputs:
  - id: stokesQcube
    type: File
    outputSource: make_cubes/stokesQcube

  - id: stokesUcube
    type: File
    outputSource: make_cubes/stokesUcube

  - id: fdf_im_dirty
    type: File
    outputSource: run_rmtools/fdf_im_dirty

  - id: fdf_real_dirty
    type: File
    outputSource: run_rmtools/fdf_real_dirty

  - id: fdf_tot_dirty
    type: File
    outputSource: run_rmtools/fdf_tot_dirty

  - id: fdf_maxpi
    type: File
    outputSource: run_rmtools/fdf_maxpi

  - id: fdf_peakrm
    type: File
    outputSource: run_rmtools/fdf_peakrm

  - id: rmtools_stdout
    type: File
    outputSource: run_rmtools/rmsynth_stdout

  - id: rmtools_stderr
    type: File
    outputSource: run_rmtools/rmsynth_stderr
