class: Workflow
cwlVersion: v1.2
id: facet_subtract
label: Facet subtraction
doc: |
    This workflow:
    * Gets the facet layout using the merged h5parm
    * Gathers the essential model images from the 1.2" imaging output data
    * Splits the multi-facet region file into separate facets (polygons)
    * Averages all input MeasurementSets to a lower time and frequency resolution
    * Predicts model data for each facet polygon separately
    * Makes a masks for subtraction by summing the corresponding polygon model data components
    * Upsamples the model data from low data resolution to the initial data resolution
    * Subtracts the upsampled data from the original data column
    * Reads the phase centre and averaging factors for each facet MeasurementSet from the polygon_info CSV file and applies them
    * Applies calibration solutions from the corresponding calibrator source
    * Applies the beam at the centre of the facet
    * Concatenates the subtracted phase-shifted MeasurementSets per polygon

inputs:
    - id: msin
      type: Directory[]
      doc: MeasurementSets with coverage of the target directions.
    - id: model_image_directory
      type: Directory
      doc: Directory with 1.2" model images.
    - id: h5parm
      type: File
      doc: Merged h5parm with calibration solutions for multiple directions.
    - id: tmpdir
      type: string?
      doc: Temporary directory to run I/O heavy jobs.
    - id: ncpu
      type: int?
      doc: Number of cores to use during predict and subtract.
    - id: dysco_bitrate
      type: int?
      doc: Number of bits per float used for columns containing visibilities.
      default: 8

steps:
    - id: get_facet_layout
      in:
        - id: msin
          source: msin
          valueFrom: $(self[0])
        - id: h5parm
          source: h5parm
        - id: imsize
          default: 22500
      out:
        - id: facet_regions
      run: ../steps/get_facet_layout.cwl

    - id: gather_all_model_images
      in:
        - id: model_image_directory
          source: model_image_directory
      out:
        - id: filtered_model_image_directory
      run: ../steps/gather_model_images.cwl

    - id: split_polygons
      in:
         - id: facet_regions
           source: get_facet_layout/facet_regions
         - id: h5parm
           source: h5parm
      out:
         - id: polygon_info
         - id: polygon_regions
      run: ../steps/split_polygons.cwl

    - id: predict_facets
      in:
         - id: msin
           source: msin
         - id: model_image_directory
           source: gather_all_model_images/filtered_model_image_directory
         - id: h5parm
           source: h5parm
         - id: polygons
           source: split_polygons/polygon_regions
         - id: polygon_info
           source: split_polygons/polygon_info
         - id: ncpu
           source: ncpu
         - id: tmpdir
           source: tmpdir
      out:
         - subtracted_facet_ms
      run: subworkflows/predict_subtract_facets.cwl
      scatter: msin

    - id: flatten_subtracte_ms
      in:
         - id: nestedarray
           source: predict_facets/subtracted_facet_ms
      out:
         - flattenedarray
      run: ../steps/flatten.cwl

    - id: make_concat_parset
      in:
         - id: msin
           source: flatten_subtracte_ms/flattenedarray
         - id: dysco_bitrate
           source: dysco_bitrate
      out:
         - id: concat_parsets
      run: ../steps/make_concat_parsets.cwl

    - id: concat_facets
      in:
        - id: msin
          source: flatten_subtracte_ms/flattenedarray
        - id: parset
          source: make_concat_parset/concat_parsets
        - id: ncpu
          default: 8
      out:
        - id: msout
      run: ../steps/dp3_parset.cwl
      scatter: parset

requirements:
  - class: MultipleInputFeatureRequirement
  - class: ScatterFeatureRequirement
  - class: SubworkflowFeatureRequirement

outputs:
    - id: facet_ms
      type: Directory[]
      outputSource: concat_facets/msout
    - id: polygon_info
      type: File
      outputSource: split_polygons/polygon_info
    - id: polygon_regions
      type: File[]
      outputSource: split_polygons/polygon_regions
