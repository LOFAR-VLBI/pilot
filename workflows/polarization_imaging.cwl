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

    - id: stokes
      type: string[]
      default: ["Q","U"]

    - id: stokes_q_cube
      type: File
      doc: Stokes Q cube (per-channel) for RM synthesis.

    - id: stokes_u_cube
      type: File
      doc: Stokes U cube (per-channel) for RM synthesis.

    - id: freqs_hz
      type: File
      doc: Frequency list in Hz (one per channel) for RM synthesis.

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

    - id: apptainer_bin
      type: string?
      default: apptainer
      doc: Apptainer/Singularity executable name or path.

    - id: apptainer_image
      type: string?
      doc: Path to an Apptainer/Singularity image (.sif). If set, rmsynth3d runs inside this image.

    - id: apptainer_bind
      type: string[]?
      doc: Bind mount(s) for Apptainer/Singularity, e.g. /data:/mnt

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
        #add outputs for derotated cubes FDF_real/im_dirty.fits
      run: ../steps/rmsynthesis.cwl

    - id: run_rmtools
      label: RM synthesis
      in:
        - id: stokes_q
          source: stokes_q_cube
        - id: stokes_u
          source: stokes_u_cube
        - id: freqs_hz
          source: freqs_hz
        - id: max_lam2
          source: rmtools_max_lam2
        - id: dlam2
          source: rmtools_dlam2
        - id: output_prefix
          source: rmtools_output_prefix
        - id: extra_args
          source: rmtools_extra_args
        - id: apptainer_bin
          source: apptainer_bin
        - id: apptainer_image
          source: apptainer_image
        - id: apptainer_bind
          source: apptainer_bind
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
