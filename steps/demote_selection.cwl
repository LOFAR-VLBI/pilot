class: CommandLineTool
cwlVersion: v1.2
id: demote_selection
label: Decreases calibrator strength qualifier
doc: This step uses reclassifies a calibrator source from e.g. strong to weak, such that the MSes can be used in another step.

baseCommand:
  - direction_selection.py

inputs:
    - id: msin
      type: Directory[]
      doc: All input MS directions
      inputBinding:
        prefix: "--ms"
        position: 1
        separate: true
    - id: validation_csv
      type: File?
      doc: CSV with validation results
      inputBinding:
        prefix: "--csv"
        position: 2
    - id: phasediff_score
      type: float
      default: 10.0
      doc: Phasediff score, see Section 3.3.1 from de Jong et al. (2024; https://arxiv.org/abs/2407.13247)
      inputBinding:
        prefix: "--best_score"
        position: 3
    - id: demote_from
      type: string
      default: "strong"
      doc: The current classification of the calibrators.
      inputBinding:
        prefix: "--reclassify_from"
        position: 4
    - id: demote_to
      type: string
      default: "weak"
      doc: The new classification of the calibrators.
      inputBinding:
        prefix: "--suffix"
        position: 5
    - id: validate
      type: boolean
      default: true

outputs:
    - id: msout
      type: Directory[]
      doc: Best directions
      outputBinding:
        glob: "ILTJ*$(inputs.demote_to).ms"

requirements:
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.msin)
        writable: true

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
