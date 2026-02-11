class: CommandLineTool
cwlVersion: v1.2
id: get_phasediff
label: Polarization Phase Difference
doc: This step makes scalarphasediff solution files, needed for collecting source selection scores

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
      doc: h5parm solution with simple scalarphase solutions
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
  - imagename='phasediff'
  - forwidefield=True
  - phaseupstations='core'
  - skipbackup=True
  - uvmin=20000
  - soltype_list=['scalarphasediff','scalarphase']
  - solint_list=['10min',1]
  - nchan_list=[6,1]
  - docircular=True
  - uvminscalarphasediff=0
  - stop=1
  - soltypecycles_list=[0,0]
  - imsize=1600
  - skymodelpointsource=1.0
  - stopafterskysolve=True
  - phasediff_only=True
  - compute_phasediffstat=True

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: ResourceRequirement
    coresMin: 2

stdout: phasediff.log
stderr: phasediff_err.log
