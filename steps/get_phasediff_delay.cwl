class: CommandLineTool
cwlVersion: v1.2
id: get_phasediff
label: Get scalarphasediff and scalarphase solutions
doc: |
    This step makes scalarphasediff and scalarphase solution files,
    needed for collecting source selection scores and setting parameters for delay calibration.

baseCommand: facetselfcal

inputs:
    - id: phasediff_ms
      type: Directory
      doc: Input MeasurementSet
      inputBinding:
        position: 20

outputs:
    - id: scalarphase_h5out
      type: File
      doc: h5parm with simple scalarphase solutions.
      outputBinding:
        glob: "scalarphase1*.h5"
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
        writable: true

arguments:
  - --imagename=phasediff
  - --forwidefield
  - --phaseupstations=core
  - --skipbackup
  - --uvmin=20000
  - --soltype-list=['scalarphasediff','scalarphase']
  - --solint-list=['10min','32s']
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
  - --ncpu_max_DP3solve=2

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: ResourceRequirement
    coresMin: 2

stdout: phasediff.log
stderr: phasediff_err.log
