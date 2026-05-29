cwlVersion: v1.2
class: CommandLineTool
id: generate_parset_split_directions
label: Generate DP3 parset for split directions
doc: |
    Generates a DP3 parameterset to split off
    directions from a given MeasurementSet.

baseCommand: [cat, input.parset]

stdout: dp3_explode.parset

inputs:

    - id: phase_centers
      type: string
      doc: |
        A string of pairs of right ascension and declination
        coordinates, one for each direction to image.

    - id: frequency_resolution
      type: string?
      default: '390.56kHz'
      doc: |
        Frequency resolution for the third averaging.

    - id: time_resolution
      type: string?
      default: '32.'
      doc: |
        Time resolution in seconds for the third averaging.

    - id: beamdir_delay_cal
      type: string?
      doc: |
        Direction in which the primary beam correction for
        the delay calibration has been done.

outputs:
  - id: parset
    type: stdout
    doc: A DP3 parameterset file.

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entryname: input.parset
        entry: |+
            steps                       = [split]

            split.replaceparms          = [phaseshift.phasecenter, applytargetbeam.direction, msout.name]
            split.steps                 = [phaseshift, averager1, applydelaybeam, applycal, applytargetbeam, averager2, msout]

            phaseshift.type             = phaseshift
            phaseshift.phasecenter      = $(inputs.phase_centers)

            averager1.type              = averager
            averager1.freqresolution    = 48.82kHz
            averager1.timeresolution    = 4.

            # Beam and solutions are fulljones, so they don't commute.
            applydelaybeam.type              = applybeam
            applydelaybeam.direction         = $(inputs.beamdir_delay_cal)
            applydelaybeam.beammode          = full
            applydelaybeam.updateweights     = True

            # Apply delay calibrator solutions now.
            applycal.type               = applycal
            applycal.correction         = fulljones
            applycal.soltab             = [amplitude000, phase000]
            
            # Only now can we properly apply the primary beam of the target.
            # DP3 understands the previous applybeam. No explicit undo needed.
            applytargetbeam.type              = applybeam
            applytargetbeam.direction         = $(inputs.phase_centers)
            applytargetbeam.beammode          = full
            applytargetbeam.updateweights     = True

            averager2.type              = averager
            averager2.freqresolution    = $(inputs.frequency_resolution)
            averager2.timeresolution    = $(inputs.time_resolution)

            msout.storagemanager        = dysco
            msout.overwrite             = True
