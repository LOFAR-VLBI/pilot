# Polarization imaging examples

These configurations run **after** target extraction and application of the
required calibration solutions. They do not perform calibration or recover
spectral resolution from an averaged MS. The WSClean step reads `DATA`.

## LoTSS-HR starting point

`lotss-hr-0p3arcsec-48kHz.json` and `lotss-hr-0p3arcsec-12kHz.json` request:

- Q/U only; point CLEAN (`multiscale: false` for the tested WSClean 3.7 runtime).
- 0.075 arcsec pixels, 1600 x 1600 pixels: a 120 x 120 arcsec field.
- Briggs -1.4, a 0.25 arcsec Gaussian uv taper, and a **requested** common
  circular 0.3 arcsec restoring beam. The taper and restoring beam are distinct.
- +/-200 rad/m^2 in 0.3 rad/m^2 steps, with inverse-variance channel weights.
- Up to 100000 CLEAN iterations and 10 major cycles; eight imaging cores.

These are **adapted starting configurations**, not a new validated 0.3 arcsec
run of P160+55 or a demonstration on P112+32. Check the channel PSFs first:
a 0.3 arcsec restoring beam must encompass the channel PSFs, including the
low-frequency end. Use a larger common beam if necessary. For an ellipse,
set `beam_size` to null and `beam_shape` to `[major_arcsec, minor_arcsec, PA_deg]`.
Changing only FITS beam metadata does not homogenize resolution.

The checked-in channel counts (920 and 3680) describe an illustrative
3680-channel band. They are **not universal LoTSS counts**. Generate a target
configuration from its actual concatenated MS instead:

```sh
python scripts/make_pol_imaging_config.py \
  --ms /data/calibrated-target.ms --channel-width-khz 48 \
  --output target-pol.json
# Use --channel-width-khz 12 to retain native 12.20703125 kHz channels.
```

The generator uses 48.828125 kHz for the `48` shorthand, verifies uniform,
contiguous input channels, and derives `num_channels` from the MS. It accepts
one concatenated spectral window. An already 48.8 kHz MS is preserved when
48 is requested. Averaged 390 kHz data cannot be used for either option.

## Run the workflow

Use this checkout's scripts inside the FLOCS container, rather than older
container-bundled copies. With a FLOCS environment configured:

```sh
export VLBI_DATA_ROOT="$PWD"
# In addition to the normal FLOCS/LINC bindings:
export APPTAINER_BINDPATH="${APPTAINER_BINDPATH:+$APPTAINER_BINDPATH,}$PWD:/opt/lofar/VLBI-cwl"
export APPTAINERENV_PREPEND_PATH="/opt/lofar/VLBI-cwl/scripts${APPTAINERENV_PREPEND_PATH:+:$APPTAINERENV_PREPEND_PATH}"
cwltool --singularity --outdir target-pol-results \
  workflows/polarization-imaging.cwl target-pol.json
```

The existing `flocs-run vlbi polarization-imaging` command invokes the same
workflow. The runner version tested here (flocs-runners 1.1.0) does not expose
all beam/multiscale/iteration options in these JSON files; use the direct CWL
invocation above for an exact configuration. Its defaults also differ: do not
leave `stokes` or `num_channels` at their runner defaults unintentionally.
Fritz/Roland can expose these inputs when wiring this into autoPILOT.

## Products and checks

Q/U cubes retain the regular frequency grid in FITS WCS, including paired NaN
planes for missing, invalid, zero-noise or high-noise channels. The current
hard noise cut is mean(Q RMS, U RMS) >5 times the valid-channel median. It is
not a comprehensive artefact or RFI detector. A JSON sidecar records the
threshold and rejected channels; frequency/noise lists remain available.
RM synthesis receives the channel RMS array; blanked planes have zero weight.
Outputs include real/imaginary/absolute dirty FDF cubes, peak polarized
intensity, peak Faraday depth, and logs. There is no subsequent 1D RM-CLEAN or
polarized-intensity debiasing in this workflow. A peak map alone is not a
polarization detection catalogue.

Check channel beams, spectral WCS, surviving bandwidth, RMSF, residual noise,
CLEAN termination, and leakage around bright Stokes I emission. Validate the
calibration chain on known polarized and leakage-dominated targets. In
particular, a low-resolution polarized detection need not survive at 0.3 arcsec.

## Resource planning

A 2 arcmin field at 0.075 arcsec pixels has 2.56 million pixels. Two float32
Q/U cubes alone occupy about **18.8 GB for 920 channels** or **75.4 GB for
3680 channels** (decimal GB), before channel images, PSFs, CLEAN work arrays,
Faraday cubes, or CWL staging. The +/-200/0.3 Faraday grid has about 1335 planes;
one float32 Faraday cube alone is about 13.7 GB. Do not launch all targets
concurrently without measuring actual memory/disk requirements. Begin with
the two known polarized P112+32 targets, potentially at coarser angular
resolution first, and retain temporary fine-channel MSes as needed.

## Tested reference

`p160p55-reference.json` preserves the imaging settings used for our successful
P160+55 test, replacing only the local MS path with a placeholder:
120 channels of 390.625 kHz, 1.5 arcsec pixels, 256 x 256 pixels, Briggs -0.5,
no uv taper, and a common 10.7382 x 5.5881 arcsec beam (PA 96.9884 deg).
The field had known polarized emission around +5 to +10 rad/m^2 and an
ionospheric RM correction. The workflow recovered its strongest peak near
+6.9 rad/m^2 (~13.4 mJy/beam); empirical component noise was ~0.055 mJy/beam.
The actual 240 Q/U channel beam headers, frequency axes and noise-array
coverage were checked. This is a reference for the procedure, not a claim
that the adapted high-resolution configurations were run on that MS.

Runtime: FLOCS v6.2.3 container, WSClean 3.7, cwltool, with this checkout's
workflow/scripts mounted into the container. Record the container checksum,
PILOT commit and generated JSON in each production run. The changes also have
regression tests for channel alignment, NaN gaps, RMS weighting and channel
count generation. If upgrading WSClean (3.8 changes polarimetric multiscale
behaviour), validate the changed imaging mode separately.
