class: CommandLineTool
cwlVersion: v1.2
id: run_rmtools
label: Run RM-Tools rmsynth3d
doc: |
  Run RM-Tools rmsynth3d on Stokes Q/U cubes. By default frequencies are
  reconstructed from the FITS spectral WCS; an explicit list is optional.

baseCommand: run_rmtools.py

inputs:
  - id: stokes_q
    type: File?
    doc: Stokes Q cube (per-channel).
    inputBinding:
      position: 1
      prefix: --stokes-q
  - id: stokes_u
    type: File?
    doc: Stokes U cube (per-channel).
    inputBinding:
      position: 1
      prefix: --stokes-u
  - id: freqs_hz
    type: File?
    doc: Optional frequency list in Hz; otherwise use the FITS spectral WCS.
    inputBinding:
      position: 1
      prefix: --freqs
  - id: max_lam2
    type: float?
    default: 150
    doc: Maximum absolute Faraday depth in rad/m^2 (rmsynth3d -l).
    inputBinding:
      position: 1
      prefix: --l
  - id: rms_noise
    type: File?
    doc: Channel RMS in Jy/beam, one entry per cube plane. Required for variance weighting.
    inputBinding:
      position: 1
      prefix: --rms
  - id: weighting
    type: string
    default: variance
    doc: Channel weighting, variance or uniform. Variance requires rms_noise.
    inputBinding:
      position: 1
      prefix: --weighting
  - id: dlam2
    type: float?
    default: 0.3
    doc: Faraday-depth sampling interval in rad/m^2 (rmsynth3d -d).
    inputBinding:
      position: 1
      prefix: --d
  - id: output_prefix
    type: string?
    doc: Prefix for output products passed to rmsynth3d (-o). Defaults to Stokes Q basename if not provided.
    inputBinding:
      position: 1
      prefix: --output-prefix
  - id: extra_args
    type: string?
    doc: Extra arguments passed to rmsynth3d.
    inputBinding:
      position: 1
      prefix: --extra-args

outputs:
  - id: fdf_im_dirty
    type: File
    outputBinding:
      glob: '*FDF_im_dirty.fits'
  - id: fdf_real_dirty
    type: File
    outputBinding:
      glob: '*FDF_real_dirty.fits'
  - id: fdf_tot_dirty
    type: File
    outputBinding:
      glob: '*FDF_tot_dirty.fits'
  - id: fdf_maxpi
    type: File
    outputBinding:
      glob: '*FDF_maxPI.fits'
  - id: fdf_peakrm
    type: File
    outputBinding:
      glob: '*FDF_peakRM.fits'
  - id: rmsynth_stdout
    type: File
    outputBinding:
      glob: rmsynth3d_stdout.log
  - id: rmsynth_stderr
    type: File
    outputBinding:
      glob: rmsynth3d_stderr.log

requirements:
  - class: InlineJavascriptRequirement
hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: rmsynth3d_stdout.log
stderr: rmsynth3d_stderr.log
