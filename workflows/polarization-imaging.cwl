class: Workflow
cwlVersion: v1.2
id: image_polarization 
label: Polarization imaging
doc: |
  This workflow will image the provided MS in Q and U, and perform Rotation Measure
  Synthesis to provide linear polarization images. The intended use is for datasets
  of science targets that have been fully calibrated, including leakage calibration.
  Choose time/frequency averaging for the field size and Faraday-depth range.
  Fine-channel inputs (e.g. 12.207 or 48.828 kHz) must not be averaged further
  unintentionally by channels-out. The input must already contain the required
  polarization-preserving calibration corrections.

requirements:
    - class: InlineJavascriptRequirement

inputs:
    - id: msin
      type: Directory[]
      doc: MeasurementSets that will be imaged.

    - id: pixel_scale
      type: string
      doc: Pixel size (WSClean scale), e.g. "0.075asec".

    - id: taper
      type: string?
      doc: Angular resolution that will be passed to WSClean's taper argument. Its syntax follows that of WSClean.

    - id: beam_size
      type: string?
      default: "0.3asec"
      doc: Common circular restoring beam; set null when using beam_shape.

    - id: beam_shape
      type: float[]?
      doc: Common elliptical restoring beam [major arcsec, minor arcsec, PA degrees].

    - id: min_uv_lambda
      type: float?
      default: 80.0
      doc: Minimum baseline in wavelengths.

    - id: niter
      type: int
      default: 5000
      doc: Maximum CLEAN iterations.

    - id: max_major_cycles
      type: int
      default: 5
      doc: Maximum WSClean major iterations.

    - id: image_size
      type: int[]?
      default: [1024, 1024]
      doc: Size (in pixels) of image, [x, y]. Its syntax follows that of WSClean.

    - id: briggs
      type: float?
      default: -1.4
      doc: Briggs weighting for WSClean.

    - id: num_channels
      type: int
      doc: Number of output Q/U channels. Set to the input channel count to preserve its channel width.

    - id: stokes
      type: string
      default: "QU"

    - id: multiscale
      type: boolean
      default: false
      doc: Enable multiscale Q/U deconvolution; leave false for WSClean before 3.8.

    - id: rmtools_max_lam2
      type: float?
      default: 150
      doc: Maximum absolute Faraday depth in rad/m^2 (rmsynth3d -l).

    - id: rmtools_dlam2
      type: float?
      default: 0.3
      doc: Faraday-depth sampling interval in rad/m^2 (rmsynth3d -d).

    - id: rmtools_output_prefix
      type: string?
      doc: Prefix for RM-Tools output products. Defaults to Stokes Q basename.

    - id: rmtools_extra_args
      type: string?
      doc: Extra arguments passed to rmsynth3d.

    - id: ncpu
      type: int?
      default: 12
      doc: Number of cores to use during WSClean imaging.

steps:
    - id: image_qu
      label: Image Stokes Q and U
      when: $(inputs.pol == "QU")
      in:
        - id: msin
          source: msin
        - id: scale
          source: pixel_scale
        - id: taper-gaussian
          source: taper
        - id: size
          source: image_size
        - id: channels-out
          source: num_channels
        - id: pol
          source: stokes
        - id: multiscale
          source: multiscale
        - id: briggs
          source: briggs
        - id: ncpu
          source: ncpu
        - id: beam-size
          source: beam_size
        - id: beam-shape
          source: beam_shape
        - id: minuv-l
          source: min_uv_lambda
        - id: niter
          source: niter
        - id: nmiter
          source: max_major_cycles
      out:
        - id: Q_channel_images
        - id: U_channel_images
        - id: MFS_images
        - id: channel_images
      run: ../steps/wsclean_pol.cwl

    - id: image_iv
      label: Image Stokes I and V
      when: $(inputs.pol == "IV")
      in:
        - id: msin
          source: msin
        - id: scale
          source: pixel_scale
        - id: taper-gaussian
          source: taper
        - id: size
          source: image_size
        - id: channels-out
          source: num_channels
        - id: pol
          source: stokes
        - id: briggs
          source: briggs
        - id: fitrm
          default: false
        - id: squared-channel-joining
          default: false
        - id: join-polarizations
          default: false
        - id: multiscale-max-scales
          default: 8
        - id: multiscale-scale-bias
          default: 0.7
        - id: ncpu
          source: ncpu
        - id: beam-size
          source: beam_size
        - id: beam-shape
          source: beam_shape
        - id: minuv-l
          source: min_uv_lambda
        - id: niter
          source: niter
        - id: nmiter
          source: max_major_cycles
      out:
        - id: I_channel_images
        - id: V_channel_images
        - id: MFS_images
      run: ../steps/wsclean_pol.cwl

    - id: make_qu_cubes
      label: Make QU cubes
      when: $(inputs.stokes == "QU")
      in:
        - id: image_directory
          source: image_qu/channel_images
        - id: image_size
          source: image_size
        - id: nchannels
          source: num_channels
        - id: stokes
          source: stokes
      out:
        - id: stokesQcube
        - id: stokesUcube
        - id: frequencies_list
        - id: rms_list
        - id: channel_flags
      run: ../steps/concat_pol.cwl

    - id: run_rmtools
      label: Run RM synthesis
      when: $(inputs.stokes == "QU")
      in:
        - id: stokes_q
          source: make_qu_cubes/stokesQcube
        - id: stokes_u
          source: make_qu_cubes/stokesUcube
        - id: rms_noise
          source: make_qu_cubes/rms_list
        - id: max_lam2
          source: rmtools_max_lam2
        - id: dlam2
          source: rmtools_dlam2
        - id: output_prefix
          source: rmtools_output_prefix
        - id: extra_args
          source: rmtools_extra_args
        - id: stokes
          source: stokes
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
  - id: channel_flags
    type: File?
    outputSource: make_qu_cubes/channel_flags

  - id: frequencies_list
    type: File?
    outputSource: make_qu_cubes/frequencies_list

  - id: rms_list
    type: File?
    outputSource: make_qu_cubes/rms_list

  - id: stokesI
    type: File[]?
    outputSource: image_iv/I_channel_images

  - id: stokesV
    type: File[]?
    outputSource: image_iv/V_channel_images

  - id: IV_MFS_images
    type: File[]?
    outputSource: image_iv/MFS_images

  - id: stokesQcube
    type: File?
    outputSource: make_qu_cubes/stokesQcube

  - id: stokesUcube
    type: File?
    outputSource: make_qu_cubes/stokesUcube

  - id: fdf_im_dirty
    type: File?
    outputSource: run_rmtools/fdf_im_dirty

  - id: fdf_real_dirty
    type: File?
    outputSource: run_rmtools/fdf_real_dirty

  - id: fdf_tot_dirty
    type: File?
    outputSource: run_rmtools/fdf_tot_dirty

  - id: fdf_maxpi
    type: File?
    outputSource: run_rmtools/fdf_maxpi

  - id: fdf_peakrm
    type: File?
    outputSource: run_rmtools/fdf_peakrm

  - id: rmtools_stdout
    type: File?
    outputSource: run_rmtools/rmsynth_stdout

  - id: rmtools_stderr
    type: File?
    outputSource: run_rmtools/rmsynth_stderr
