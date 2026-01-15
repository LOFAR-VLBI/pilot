class: Workflow
cwlVersion: v1.2
id: facet_subtract_per_subband
doc: |
    This workflow:
    * Averages the input MeasurementSet to a lower time and frequency resolution
    * Predicts model data for each facet polygon separately
    * Makes a masks for subtraction by summing the corresponding polygon model data components
    * Upsamples the model data from low data resolution to the initial data resolution
    * Subtracts the upsampled data from the original data column
    * Reads the phase centre and averaging factors for each facet MeasurementSet from the polygon_info CSV file and applies them
    * Applies calibration solutions from the corresponding calibrator source
    * Applies the beam at the centre of the facet

inputs:
    - id: msin
      type: Directory
      doc: MeasurementSet
    - id: model_image_directory
      type: Directory
      doc: Directory with 1.2" model images
    - id: h5parm
      type: File
      doc: Merged h5parms
    - id: polygons
      type: File[]
      doc: Facet polygons
    - id: polygon_info
      type: File
      doc: Polygon CSV file
    - id: ncpu
      type: int?
      doc: Number of cores to use during predict and subtract
    - id: tmpdir
      type: string?
      doc: Temporary directory to run I/O heavy jobs

steps:

    - id: average_subband
      in:
         - id: msin
           source: msin
      out:
         - ms_avg
      run: ../../steps/prediction_avg.cwl

    - id: get_model_images_for_sb
      in:
         - id: msin
           source: msin
         - id: model_images
           source: model_image_directory
      out:
         - output_model_images
      run: ../../steps/get_model_images_for_sb.cwl

    - id: predict_facet_masks
      in:
         - id: msin
           source: average_subband/ms_avg
         - id: h5parm
           source: h5parm
         - id: polygons
           source: polygons
         - id: model_images
           source: get_model_images_for_sb/output_model_images
         - id: tmpdir
           source: tmpdir
      out:
         - model_data_npy
      run: ../../steps/predict_facets.cwl
      scatter: polygons

    - id: make_facet_masks
      in:
         - id: msin
           source: average_subband/ms_avg
         - id: facet_model_data
           source: predict_facet_masks/model_data_npy
         - id: ncpu
           source: ncpu
         - id: tmpdir
           source: tmpdir
      out:
         - ms_with_polygon_model
      run: ../../steps/make_facet_masks.cwl

    - id: make_facet_ms
      in:
         - id: avg_ms
           source: make_facet_masks/ms_with_polygon_model
         - id: full_ms
           source: msin
         - id: h5parm
           source: h5parm
         - id: polygon
           source: polygons
         - id: polygon_info
           source: polygon_info
         - id: ncpu
           source: ncpu
         - id: tmpdir
           source: tmpdir
      out:
         - facet_ms
      run: ../../steps/make_facet_ms.cwl
      scatter: polygon


requirements:
  - class: MultipleInputFeatureRequirement
  - class: ScatterFeatureRequirement

outputs:
    - id: subtracted_facet_ms
      type: Directory[]
      outputSource: make_facet_ms/facet_ms
