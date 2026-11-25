cwlVersion: v1.2
class: Workflow
id: peel_calibrators
label: Build a peeling model and peel one MeasurementSet

requirements:
  - class: InlineJavascriptRequirement
  - class: MultipleInputFeatureRequirement
  - class: SubworkflowFeatureRequirement

inputs:
  - id: msin
    type: Directory
    doc: Input MeasurementSet.

  - id: peeling_model
    type: File[]
    doc: Sky models to combine and filter for peeling.

steps:
  - id: make_model
    in:
      - id: msin
        source: msin
      - id: skymodels
        source: peeling_model
      - id: peel_radius
        default: 15
    out:
      - skymodel
    run: ../../steps/make_peeling_model.cwl

  - id: peel
    in:
      - id: msin
        source: msin
      - id: skymodel
        source: make_model/skymodel
    out:
      - msout
    run: ./dp3_peel.cwl
    when: $(inputs.skymodel != null)

outputs:
  - id: msout
    type: Directory
    outputSource:
      - peel/msout
      - msin
    pickValue: first_non_null
    doc: Peeled MeasurementSet, or the original when no peeling model was supplied.
