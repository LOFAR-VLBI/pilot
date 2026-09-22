class: CommandLineTool
cwlVersion: v1.2
id: select_final_files
label: Select final selfcal files.
doc: Selects the final selfcal files from overlapping sets of sources

baseCommand: select_final_files.py

inputs:
  - id: files_strong
    type: File[]?
    inputBinding:
      position: 1
      prefix: --files-strong
      separate: true
    doc: |
        A string that determines which
        MeasurementSets should be combined.

  - id: files_weak
    type: File[]?
    inputBinding:
      position: 1
      prefix: --files-weak
      separate: true
    doc: |
        A string that determines which
        MeasurementSets should be combined.

  - id: files_unreliable
    type: File[]?
    inputBinding:
      position: 1
      prefix: --files-unreliable
      separate: true
    doc: |
        A string that determines which
        MeasurementSets should be combined.

outputs:
  - id: final_files_strong
    type: File[]?
    doc: The final files of strong calibrators.
  - id: final_files_weak
    type: File[]?
    doc: The final files of weak calibrators.
  - id: final_files_unreliable
    type: File[]?
    doc: The final files of unreliable calibrators.

requirements:
  - class: InlineJavascriptRequirement
hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: select_final_files.log
stderr: select_final_files_err.log
