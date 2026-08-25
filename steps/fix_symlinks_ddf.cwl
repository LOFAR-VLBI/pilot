class: CommandLineTool
cwlVersion: v1.2
id: fixsymlinks
doc: |-
  Deals with broken symlinks in the SOLSDIR directory
  by replacing them with the files they are supposed to
  link to.

baseCommand:
  - fix_symlinks_ddf.sh

inputs:
  - id: ddf_rundir
    type: Directory?
    doc: |
      Path to the directory of the DDF-pipeline run, where
      the output files for applying DI solutions and subtracting
      LoTSS can be found.
    inputBinding:
      position: 0
      valueFrom: $(self.path)
  - id: ddf_solsdir
    type: Directory?
    doc: |
      Path to the SOLSDIR directory of the ddf-pipeline run.
    inputBinding:
      position: 1

outputs:
  - id: solsdir
    type: Directory
    outputBinding:
      glob: SOLSDIR
    doc: |
      SOLSDIR with symlinks replaced by their corresponding files.
  - id: logfiles
    type: File[]
    outputBinding:
      glob: fixsymlinks*.log
    doc: |
        The files containing the stdout
        and stderr from the step.

requirements:
  - class: InplaceUpdateRequirement
    inplaceUpdate: true
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.ddf_solsdir)
        writable: true

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: fixsymlinks.log
stderr: fixsymlinks_err.log
