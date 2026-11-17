class: Workflow
cwlVersion: v1.2
id: dp3_peel
label: Predict and peel a sky model with DP3
doc: |
  Predict the supplied sky model into a MeasurementSet, then solve and subtract
  the predicted model with DP3.

requirements:
  - class: MultipleInputFeatureRequirement

inputs:
  - id: msin
    type: Directory
    doc: Input MeasurementSet.

  - id: skymodel
    type: File
    doc: Sky model in BBS format to predict and peel.

steps:
  - id: predict
    in:
      - id: msin
        source: msin
      - id: skymodel
        source: skymodel
    out:
      - msout
      - logfile
    run: ../../steps/dp3_predict.cwl

  - id: solvesubtract
    in:
      - id: msin
        source: predict/msout
    out:
      - msout
      - logfile
    run: ../../steps/dp3_solvesubtract.cwl

outputs:
  - id: msout
    type: Directory
    outputSource: solvesubtract/msout
    doc: MeasurementSet with the predicted sky model peeled.

  - id: logfile
    type: File[]
    outputSource:
      - predict/logfile
      - solvesubtract/logfile
    linkMerge: merge_flattened
    pickValue: all_non_null
    doc: Log files from prediction and solve-subtract.
