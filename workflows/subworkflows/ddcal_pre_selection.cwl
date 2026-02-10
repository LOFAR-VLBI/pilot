class: Workflow
cwlVersion: v1.2
id: ddcal_pre_selection
label: DD direction selection
doc: |
   This workflow does the following:
        * DP3 prep to average measurement to the same freq/time resolution
        * Get h5parm solutions with scalarphasediff corrections from facetselfcal
        * Get solution scores using the circular standard deviation
        * Select MS with scores below 2.3
   This selection metric is described in Section 3.3.1 from de Jong et al. (2024; https://arxiv.org/pdf/2407.13247)

requirements:
  - class: ScatterFeatureRequirement

inputs:
    - id: msin
      type: Directory[]
      doc: The input concatenated MS.
    - id: phasediff_score
      type: float
      default: 2.3
      doc: Phasediff-score for calibrator selection <2.3 good for DD-calibrators and <0.7 good for DI-calibrators.
    - id: select_best_n
      type: int?
      default: 1
      doc: Return this number of best sources according to the selection metric.

steps:
    - id: calc_phasediff
      in:
        - id: phasediff_ms
          source: msin
      out:
        - id: phasediff_score_csv
      run: ../../steps/get_phasediff.cwl
      scatter: msin

#TODO concat CSVs!

    - id: select_best_directions
      in:
        - id: phasediff_csv
          source: calc_phasediff/phasediff_score_csv
        - id: msin
          source: msin
        - id: phasediff_score
          source: phasediff_score
        - id: select_best_n
          source: select_best_n
      out:
        - best_ms
      run: ../../steps/select_best_directions.cwl

outputs:
    - id: phasediff_score_csv
      type: File
      outputSource: calc_phasediff/phasediff_score_csv
      doc: csv with scores
    - id: best_ms
      type: Directory[]
      outputSource: select_best_directions/best_ms
      doc: Final MS selection
