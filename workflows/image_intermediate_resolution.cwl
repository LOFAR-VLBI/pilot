class: Workflow
cwlVersion: v1.2
id: image_intermediate_resolution
label: Intermediate resolution imaging
doc: |
    This workflow will make an intermediate resolution image.

requirements:
    - class: InlineJavascriptRequirement
    - class: StepInputExpressionRequirement
    - class: ScatterFeatureRequirement

inputs:
    - id: msin
      type: Directory[]
      doc: MeasurementSets that will be imaged.

    - id: number_cores
      type: int?
      default: 24
      doc: The minimum number of cores that should be available for steps that require high I/O.

    - id: dd_solutions
      type: File
      doc: Direction-dependent calibration solutions in the form of a multi-direction H5parm.
      
    - id: image_size
      type: int[]?
      default: [22500, 22500]
      doc: Size of the image to make in pixels.

    - id: pixel_scale
      type: float?
      default: 0.4
      doc: Pixel size in arcseconds.

    - id: facet_region_file
      type: File?
      doc: Optional user-provided facet layout file

    - id: tmpdir_wsclean
      type: string?
      default: '.'
      doc: |
         Path to the directory where wsclean will perform the data reordering
         required for imaging. Can be absolute or relative to the working directory.
         Intended for fast scratch space local to the compute node. By default
         this the step's working directory. See wsclean documentation for more
         details.

steps:
    - id: average_data
      label: average
      in:
        - id: msin
          source: msin
        - id: ncpu
          source: number_cores
      out:
        - id: ms_avg
      run: ../steps/average_intermediate_resolution.cwl

    - id: make_facet_layout
      label: facet_layout
      in:
        - id: msin
          source: msin
          valueFrom: $(self[0])
        - id: h5parm
          source: dd_solutions
        - id: imsize
          source: image_size
          valueFrom: $(Math.round(self[0] * 1.1))
        - id: pixelscale
          source: pixel_scale
        - id: output_region_file
          valueFrom: "facets_1p5asec.reg"
        - id: facet_region_file
          source: facet_region_file
      out:
        - id: facet_regions
      run: ../steps/get_facet_layout.cwl
      when: $(inputs.facet_region_file == null)

    - id: make_intermediate_resolution_image
      label: intermediate_resolution_image
      in:
        - id: msin
          source: average_data/ms_avg
        - id: ncpu
          source: number_cores
        - id: tmpdir
          source: tmpdir_wsclean
        - id: size
          source: image_size
        - id: scale
          source: pixel_scale
          valueFrom: $(self.toString() + "asec")
        - id: taper-gaussian
          valueFrom: $(1.5.toString() + "asec")
        - id: facet-regions
          source:
            - make_facet_layout/facet_regions
            - facet_region_file
          pickValue: first_non_null
          valueFrom: $(self)
        - id: dd_solutions
          source: dd_solutions
        - id: facet-options
          valueFrom: |
            $({
              "facet-solutions": inputs.dd_solutions,
              "soltabs": ["amplitude000", "phase000"]
            })
        - id: scalar-visibilities
          default: true
      out:
        - id: MFS_image_pb
        - id: MFS_image
        - id: MFS_residual_pb
        - id: MFS_residual
        - id: MFS_model_pb
        - id: MFS_model
        - id: MFS_psf
        - id: channel_model_images
      run: ../steps/wsclean.cwl

    - id: validate_image
      label: validation
      in:
        - id: image
          source: make_intermediate_resolution_image/MFS_image_pb
      out:
        - id: validation_csv
      run: ../steps/validate_1arcsec_image.cwl

outputs:
    - id: facet_region
      type: File?
      outputSource:
        - make_facet_layout/facet_regions
        - facet_region_file
      pickValue: first_non_null
      doc: |
        DS9 region file containing the facet layout.

    - id: MFS_image_pb
      outputSource: make_intermediate_resolution_image/MFS_image_pb
      type: File
      doc: |
        Final primary-beam corrected MFS FITS image at intermediate resolution.
    - id: MFS_image
      outputSource: make_intermediate_resolution_image/MFS_image
      type: File
      doc: |
        Final apparent corrected MFS FITS image at intermediate resolution.

    - id: MFS_residual_pb
      outputSource: make_intermediate_resolution_image/MFS_residual_pb
      type: File
      doc: |
        Final primary-beam corrected MFS FITS image at intermediate resolution.
    - id: MFS_residual
      outputSource: make_intermediate_resolution_image/MFS_residual
      type: File
      doc: |
        Final apparent corrected MFS FITS image at intermediate resolution.

    - id: MFS_model_pb
      outputSource: make_intermediate_resolution_image/MFS_model_pb
      type: File
      doc: |
        Final primary-beam corrected MFS FITS image at intermediate resolution.
    - id: MFS_model
      outputSource: make_intermediate_resolution_image/MFS_model
      type: File
      doc: |
        Final apparent corrected MFS FITS image at intermediate resolution.

    - id: MFS_psf
      outputSource: make_intermediate_resolution_image/MFS_psf
      type: File[]
      doc: |
        Final MFS psf FITS image at intermediate resolution.
    - id: channel_model_images
      outputSource: make_intermediate_resolution_image/channel_model_images
      type: File[]
      doc: |
        Final channel model FITS images of the intermediate resolution image.

    - id: validation_csv
      outputSource: validate_image/validation_csv
      type: File
      doc: 1 arcsecond validation output
