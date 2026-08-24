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
    - class: InlineJavascriptRequirement
    - class: MultipleInputFeatureRequirement

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

    - id: averaging_factor
      type: int?
      default: 1
      doc: Additional factor to average the data with in both time and frequency before imaging.

    - id: facet_polygons
      type: File[]
      doc: |
        Optional DS9 region file(s) that will be used to trim the facet.
        Its length should match that of `msin`.

    - id: restoring_beam
      type: float[]?
      doc: |
        Restoring beam to use for every facet following the WSClean order of major axis, minor axis, position angle.

    - id: briggs
      type: float?
      default: -1.4
      doc: Briggs weighting for WSClean.

    - id: swarp_config
      type: File?
      doc: |
        Optional configuration file to be passed to SWarp for mosaicing.
        If mosaic is true, a final mosaic will be made of the trimmed facet images
        using this configuration.

    - id: tmpdir
      type: string?
      doc: Temporary directory to run I/O heavy jobs.

    - id: ncpu
      type: int?
      doc: |
        The number of cores that WSClean will use.
        Default is to calculate it internally based on image size

steps:
    - id: average_ms
      label: Apply extra averaging of MS
      in:
        - id: msin
          source: msin
        - id: freq_step
          source: averaging_factor
        - id: time_step
          source: averaging_factor
        - id: ncpu
          default: 8
        - id: dysco_databitrate
          default: 8
      out:
        - dp3_avg_ms
      run: ../steps/dp3_avg.cwl
      scatter: msin
      when: $(inputs.time_step > 1)

    - id: sort_mses
      label: Sort MS based on name
      in:
        - id: input_entry
          source:
            - average_ms/dp3_avg_ms
            - msin
          linkMerge: merge_nested
          pickValue: all_non_null
          valueFrom: |
            ${
              var avg = self[0];
              if (avg === null || avg === undefined) { return self[1]; }
              var kept = [];
              for (var i = 0; i < avg.length; i++) {
                if (avg[i] !== null && avg[i] !== undefined) { kept.push(avg[i]); }
              }
              return kept.length === 0 ? self[1] : kept;
            }
      out:
        - id: sorted_entries
      run: ../steps/sort_by_name.cwl

    - id: sort_facet_regions
      label: Sort facets based on name
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
        - id: briggs
          source: briggs
        - id: tmpdir
          source: tmpdir
        - id: ncpu
          source: ncpu
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
      when: $(inputs.config != null)

    - id: flatten_psf_images
      in:
         - id: nestedarray
           source: image_and_trim/MFS_psf
      out:
         - flattenedarray
      run: ../steps/flatten.cwl

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
    outputSource: flatten_psf_images/flattenedarray

  - id: MFS_mosaic
    type: File?
    outputSource: mosaic_facets/output_image
