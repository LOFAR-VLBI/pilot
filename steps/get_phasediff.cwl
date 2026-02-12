class: CommandLineTool
cwlVersion: v1.2
id: get_phasediff_dd
label: Get scalarphasediff solutions
doc: This step makes scalarphasediff solution files, needed for collecting source selection scores.

baseCommand: facetselfcal

inputs:
    - id: phasediff_ms
      type: Directory
      doc: Input MeasurementSet
      inputBinding:
        position: 20

outputs:
    - id: phasediff_score_csv
      type: File
      doc: csv with phasediff scores
      outputBinding:
        glob: phasediff_output.csv
    - id: logfile
      type: File[]
      doc: log files from facetselfcal
      outputBinding:
        glob: phasediff*.log

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.phasediff_ms)

arguments:
  - --imagename=phasediff
  - --forwidefield
  - --phaseupstations=core
  - --skipbackup
  - --uvmin=20000
  - --soltype-list=['scalarphasediff']
  - --solint-list=["10min"]
  - --nchan-list=[6]
  - --docircular
  - --uvminscalarphasediff=0
  - --stop=1
  - --soltypecycles-list=[0]
  - --imsize=1600
  - --skymodelpointsource=1.0
  - --stopafterskysolve
  - --phasediff_only
  - --compute-phasediffstat
  - --avgfreqstep="390.56kHz"
  - --avgtimestep="60sec"

arguments:
  - --imagename=phasediff
  - --forwidefield
  - --phaseupstations=core
  - --skipbackup
  - --uvmin=20000
  - --soltype-list=['scalarphasediff','scalarphase']
  - --solint-list=["10min","32s"]
  - --nchan-list=[6,1]
  - --docircular
  - --uvminscalarphasediff=0
  - --stop=1
  - --soltypecycles-list=[0,0]
  - --imsize=1600
  - --skymodelpointsource=1.0
  - --stopafterskysolve
  - --phasediff_only
  - --compute-phasediffstat

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: ResourceRequirement
    coresMin: 2

stdout: phasediff.log
stderr: phasediff_err.log
