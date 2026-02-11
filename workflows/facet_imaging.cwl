class: Workflow
cwlVersion: v1.2
id: image_facet 
label: Facet imaging
doc: |
  This workflow will image the provided MS(es) at the specified angular resolution
  and trim it using the provided DS9 region file(s).

requirements:
    - class: ScatterFeatureRequirement
    - class: SubworkflowFeatureRequirement

inputs:
    - id: msin
      type: Directory[]
      doc: MeasurementSets that will be imaged.

    - id: pixel_scale
      type: float
      doc: Pixel size in arcseconds.

    - id: resolution
      type: string
      doc: Angular resolution that will be passed to WSClean's taper argument. Its syntax follows that of WSClean.

    - id: facet_polygons
      type: File[]
      doc: |
        Optional DS9 region file(s) that will be used to trim the facet.
        Its length should match that of `msin`.

    - id: mosaic
      type: boolean
      doc: |
        Combine the individual facet images into a single mosaic using the specified SWarp configuration file.

    - id: restoring_beam
      type: float[]?
      doc: |
        Restoring beam to use for every facet following the WSClean order of major axis, minor axis, position angle.

    - id: swarp_config
      type: File?
      doc: |
        Optional configuration file to be passed to SWarp for mosaicing.
        If mosaic is true, a final mosaic will be made of the trimmed facet images
        using this configuration.


steps:
    - id: sort_mses
      label: Trim facets
      in:
        - id: input_entry
          source: msin
      out:
        - id: sorted_entries
      run: ../steps/sort_by_name.cwl

    - id: sort_facet_regions
      label: Trim facets
      in:
        - id: input_entry
          source: facet_polygons
      out:
        - id: sorted_entries
      run: ../steps/sort_by_name.cwl

    - id: image_and_trim
      label: image_size
      in:
        - id: msin
          source: sort_mses/sorted_entries
        - id: facet_polygon
          source: sort_facet_regions/sorted_entries
        - id: pixel_scale
          source: pixel_scale
        - id: resolution
          source: resolution
      out:
        - id: MFS_image_pb
        - id: MFS_image
        - id: MFS_residual_pb
        - id: MFS_residual
        - id: MFS_model_pb
        - id: MFS_model
        - id: MFS_psf
      scatter: [msin, facet_polygon]
      scatterMethod: dotproduct
      run: ./subworkflows/image_and_trim.cwl

    - id: mosaic_facets
      label: mosaic_facets
      in:
        - id: config
          source: swarp_config
          # This is to circumvent cwltool validation complaining about incompatible types.
          # This step won't run if the config is `null`, so it should always be compatible.
          valueFrom: $(self)
        - id: image_name
        - id: input_images
      out:
        - id: output_image
      run: ../steps/swarp.cwl
      when: $(inputs.mosaic)

outputs:
  - id: MFS_images_pb
    type: File[]
    outputSource: image_and_trim/MFS_image_pb
  - id: MFS_images
    type: File[]
    outputSource: image_and_trim/MFS_image

  - id: MFS_residuals_pb
    type: File[]
    outputSource: image_and_trim/MFS_residual_pb
  - id: MFS_residuals
    type: File[]
    outputSource: image_and_trim/MFS_residual

  - id: MFS_models_pb
    type: File[]
    outputSource: image_and_trim/MFS_model_pb
  - id: MFS_models
    type: File[]
    outputSource: image_and_trim/MFS_model

  - id: MFS_psfs
    type: File[]
    outputSource: image_and_trim/MFS_psf

  - id: MFS_mosaic
    type: File?
    outputSource: mosaic_facets/output_image
