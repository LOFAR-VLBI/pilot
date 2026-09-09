class: Workflow
cwlVersion: v1.2
id: phasediff_selection
label: Source selection based on phasediff score
doc: |
   This workflow does the following:
        * DP3 prep to average measurement to the same freq/time resolution
        * Get h5parm solutions with scalarphasediff corrections from facetselfcal
        * Get solution scores using the circular standard deviation
        * Select MS with scores below 2.3
   This selection metric is described in Section 3.3.1 from de Jong et al. (2024; https://arxiv.org/pdf/2407.13247)
   And the score's relation to S/N is demonstrated in Appendix A from de Jong et al. (2025; https://arxiv.org/pdf/2508.12115)

requirements:
  - class: ScatterFeatureRequirement
  - class: SubworkflowFeatureRequirement

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
    - id: dp3_prep_phasediff
      in:
        - id: msin
          source: msin
        - id: freq_resolution
          default: 1953.6kHz
        - id: time_resolution
          default: 120
      out:
        - id: dp3_avg_ms
      run: ../../steps/dp3_avg.cwl
      scatter: msin

    - id: calc_phasediff
      in:
        - id: phasediff_ms
          source: dp3_prep_phasediff/dp3_avg_ms
      out:
        - id: phasediff_score_csv
      run: ../../steps/get_phasediff.cwl
      scatter: phasediff_ms

    - id: concat_phasediff_csvs
      in:
        - id: input_csvs
          source: calc_phasediff/phasediff_score_csv
        - id: output_csv_name
          default: "phasediff_concat.csv"
      out:
        - id: concat_csv
      run: ../../steps/concat_csv.cwl

    - id: select_best_directions
      label: Select best directions
      in:
        - id: phasediff_csv
          source: concat_phasediff_csvs/concat_csv
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
      outputSource: concat_phasediff_csvs/concat_csv
      doc: csv with scores
    - id: best_ms
      type: Directory[]
      outputSource: select_best_directions/best_ms
      doc: Final MS selection
