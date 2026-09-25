class: CommandLineTool
cwlVersion: v1.2
id: dp3_phaseup
label: DP3 phaseup
doc: |
    Phaseshifts data to the delay calibrator,
    averages the data, combines the core
    stations into one superstation.

baseCommand: DP3

arguments:
    - 'steps=[shift, average1, applybeam, average2]'
    - shift.type=phaseshift
    - average1.type=averager
    - applybeam.type=applybeam
    - applybeam.updateweights=true
    - average2.type=averager
    - msout.overwrite=True

inputs:
    - id: msin
      type: Directory
      doc: Input data in MeasurementSet format.
      inputBinding:
        position: 0
        prefix: msin=
        separate: false
        shellQuote: false

    - id: msout_name
      type: string?
      default: "dp3-phaseup-"
      inputBinding:
        position: 0
        prefix: msout=
        separate: false
        valueFrom: |
          $(self + "_" + inputs.msin.basename)
      doc: |
        Filename prefix for the output MeasurementSet
        to be prepended to the name of the msin input.

    - id: storagemanager
      type: string?
      default: 'dysco'
      inputBinding:
        position: 1
        prefix: msout.storagemanager=
        separate: false
        shellQuote: false
      doc: |
        String that specifies what storage manager
        to use. By default uses dysco compression.

    - id: datacolumn_in
      type: string?
      default: 'DATA'
      doc: |
        Name of the data column from which
        input data is read.
      inputBinding:
        position: 1
        prefix: msin.datacolumn=
        separate: false
        shellQuote: false

    - id: datacolumn_out
      type: string?
      default: 'DATA'
      doc: |
        Name of the data column into which
        output data is written.
      inputBinding:
        position: 1
        prefix: msout.datacolumn=
        separate: false
        shellQuote: false

    - id: phase_center
      type: string
      doc: |
        Source coordinates (right ascension, declination)
        to shift the phase centre to.
      inputBinding:
        position: 1
        separate: false
        prefix: shift.phasecenter=

    - id: freqresolution
      type: string?
      default: '48.82kHz'
      inputBinding:
        position: 1
        separate: false
        prefix: average1.freqresolution=
      doc: |
        Target frequency resolution for
        the first averaging.

    - id: timeresolution
      type: float?
      default: 4.0
      inputBinding:
        position: 1
        separate: false
        prefix: average1.timeresolution=
      doc: |
        Target time resolution in seconds
        for the first averaging.

    - id: beam_direction
      type: string
      doc: |
        Source coordinates (right ascension, declination)
        to apply beam corrections.
      inputBinding:
        position: 1
        separate: false
        prefix: applybeam.direction=

    - id: max_dp3_threads
      type: int?
      default: 4
      inputBinding:
        position: 1
        separate: false
        prefix: numthreads=
      doc: |
        The number of CPU threads to use.

    - id: beam_mode
      type: string?
      default: full
      doc: Applied beam mode. 'Full' applies both element beam and array factor.
      inputBinding:
        position: 1
        separate: false
        prefix: applybeam.beammode=

    - id: frequency_resolution
      type: string?
      default: 390.56kHz
      inputBinding:
        position: 1
        separate: false
        prefix: average2.freqresolution=
      doc: |
        Target frequency resolution for
        the second averaging.

    - id: time_resolution
      type: string?
      default: '32.0'
      inputBinding:
        position: 1
        separate: false
        prefix: average2.timeresolution=
      doc: |
        Target time resolution in seconds
        for the second averaging.

outputs:
    - id: msout
      type: Directory
      outputBinding:
        glob: $(inputs.msout_name + "_" + inputs.msin.basename)
      doc: |
        The phase-shifted output data in MeasurementSet format.

    - id: logfile
      type: File
      outputBinding:
        glob: dp3_phaseup.log
      doc: The file containing the stdout from the step.

    - id: errorfile
      type: File
      outputBinding:
        glob: dp3_phaseup_err.log
      doc: The file containing the stderr from the step.

requirements:
  - class: InlineJavascriptRequirement
  - class: ResourceRequirement
    coresMin: $(inputs.max_dp3_threads)

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: dp3_phaseup.log
stderr: dp3_phaseup_err.log
