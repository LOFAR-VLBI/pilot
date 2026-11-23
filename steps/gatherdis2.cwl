class: CommandLineTool
cwlVersion: v1.2
id: gatherdis2
doc: |-
  Converts and merges the DDF-pipeline DIS2 solutions, then flags outlying
  diagonal amplitudes and phases before the full-Jones solutions are applied.

baseCommand:
  - convert_DIS2_to_h5parm.sh

inputs:
  - id: msin
    type: Directory
    doc: |
      MeasurementSet to extract a reference station list from
      for adding dummy international stations to the final h5parm.
    inputBinding:
      position: 2
  - id: ddf_solsdir
    type: Directory
    doc: |-
      Path to the SOLSIDR directory of the DDF-pipeline containing the
      folders with DIS2 solutions.
    inputBinding:
      position: 1
  - id: flagging_parset
    type: File
    default:
      class: File
      location: ../pipeline_config_files/losoto_dis2_flagging.parset
    doc: LoSoTo configuration for flagging the merged DIS2 solutions.
    inputBinding:
      position: 3

outputs:
  - id: dis2_h5parm
    type: File
    doc: Full-Jones DIS2 solutions with outlier flags stored in the H5 weights.
    outputBinding:
      glob: DIS2_full.h5
  - id: solsdir
    type: Directory
    outputBinding:
      outputEval: $(inputs.ddf_solsdir)
  - id: logfile
    type: File[]
    doc: Conversion, merging and LoSoTo flagging logs.
    outputBinding:
      glob: [gatherdis2.log, gatherdis2_err.log, losoto-dis2.log]

requirements:
  - class: ResourceRequirement
    coresMin: 4
    coresMax: 4
    ramMin: 120000

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: gatherdis2.log
stderr: gatherdis2_err.log
