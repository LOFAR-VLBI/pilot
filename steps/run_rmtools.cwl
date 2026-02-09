class: CommandLineTool
cwlVersion: v1.2
id: run_rmtools
label: Run RM-Tools rmsynth3d
doc: |
  Run RM-Tools rmsynth3d on Stokes Q/U cubes and a frequency list.
  Can run locally or via Apptainer/Singularity when an image is provided.

baseCommand:
  - python3
  - run_rmtools.py

inputs:
  - id: rmtools_script
    type: File
    default:
      class: File
      path: scripts/run_rmtools.py
    doc: Internal helper script to run rmsynth3d.
  - id: stokes_q
    type: File
    doc: Stokes Q cube (per-channel).
    inputBinding:
      position: 1
      prefix: --stokes-q
  - id: stokes_u
    type: File
    doc: Stokes U cube (per-channel).
    inputBinding:
      position: 1
      prefix: --stokes-u
  - id: freqs_hz
    type: File
    doc: Frequency list in Hz (one per channel).
    inputBinding:
      position: 1
      prefix: --freqs
  - id: max_lam2
    type: float?
    default: 150
    doc: Maximum lambda-squared value for rmsynth3d (-l).
    inputBinding:
      position: 1
      prefix: --l
  - id: dlam2
    type: float?
    default: 0.3
    doc: Lambda-squared channel width for rmsynth3d (-d).
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
  - id: apptainer_bin
    type: string?
    default: apptainer
    doc: Apptainer/Singularity executable name or path.
    inputBinding:
      position: 1
      prefix: --apptainer-bin
  - id: apptainer_image
    type: string?
    doc: Path to an Apptainer/Singularity image (.sif). If set, rmsynth3d runs inside this image.
    inputBinding:
      position: 1
      prefix: --apptainer-image
  - id: apptainer_bind
    type: string[]?
    doc: Bind mount(s) for Apptainer/Singularity, e.g. /data:/mnt
    inputBinding:
      position: 1
      prefix: --apptainer-bind

outputs:
  - id: fdf_im_dirty
    type: File
    outputBinding:
      glob: $( (inputs.output_prefix && inputs.output_prefix.length > 0) ? inputs.output_prefix + "FDF_im_dirty.fits" : "FDF_im_dirty.fits" )
  - id: fdf_real_dirty
    type: File
    outputBinding:
      glob: $( (inputs.output_prefix && inputs.output_prefix.length > 0) ? inputs.output_prefix + "FDF_real_dirty.fits" : "FDF_real_dirty.fits" )
  - id: fdf_tot_dirty
    type: File
    outputBinding:
      glob: $( (inputs.output_prefix && inputs.output_prefix.length > 0) ? inputs.output_prefix + "FDF_tot_dirty.fits" : "FDF_tot_dirty.fits" )
  - id: fdf_maxpi
    type: File
    outputBinding:
      glob: $( (inputs.output_prefix && inputs.output_prefix.length > 0) ? inputs.output_prefix + "FDF_maxPI.fits" : "FDF_maxPI.fits" )
  - id: fdf_peakrm
    type: File
    outputBinding:
      glob: $( (inputs.output_prefix && inputs.output_prefix.length > 0) ? inputs.output_prefix + "FDF_peakRM.fits" : "FDF_peakRM.fits" )
  - id: rmsynth_stdout
    type: File
    outputBinding:
      glob: rmsynth3d_stdout.log
  - id: rmsynth_stderr
    type: File
    outputBinding:
      glob: rmsynth3d_stderr.log

stdout: rmsynth3d_stdout.log
stderr: rmsynth3d_stderr.log

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.rmtools_script)
