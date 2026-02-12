class: CommandLineTool
cwlVersion: v1.2
id: prepare-lilf-ddsol
label: Prepare lilf dd solutions
doc: Order LiLF dd solutions dir axis, average and add IS

baseCommand:
  - prepare_lilf_ddsol.py

arguments:
  - --mss
  - --h5_dd

inputs:
  - id: avg_ms
    type: Directory[]
    doc: Input MeasurementSets to add the stations from
    inputBinding:
      position: 0
      prefix: --mss
  - id: h5_dd
    type: File
    doc: Input dutch DD sols from LiLF
    inputBinding:
      position: 1
      prefix: --h5_dd

outputs:
  - id: h5_dd_addIS
    type: File
    doc: dd h5parm with IS added
    outputBinding:
      glob: $(inputs.ms.basename)
  - id: logfile
    type: File[]
    doc: log files corresponding to this step
    outputBinding:
      glob: prepare_lilf_ddsols*.log


requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
  - class: ResourceRequirement
    coresMax: $(inputs.ncpu)
    coresMin: $(inputs.ncpu)

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: prepare_lilf_ddsol.log
stderr: prepare_lilf_ddsol-err.log
