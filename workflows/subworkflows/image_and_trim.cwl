class: Workflow
cwlVersion: v1.2
id: image_facet 
label: Facet imaging
doc: |
  This subworkflow will image an MS at the specified angular resolution and trim it to the given region file.

requirements:
    - class: InlineJavascriptRequirement

inputs:
    - id: msin
      type: Directory
      doc: MeasurementSet that will be imaged.

    - id: ncpu
      type: int?
      default: 24
      doc: The number of cores that WSClean will use.

    - id: pixel_scale
      type: float
      doc: Pixel size in arcseconds.

    - id: resolution
      type: string
      default: 0.3asec
      doc: Angular resolution that will be passed to WSClean's taper argument. Its syntax follows that of WSClean.

    - id: briggs
      type: float?
      default: -1.4
      doc: Briggs weighting for WSClean.

    - id: facet_polygon
      type: File
      doc: DS9 region file that will be used to trim the facet.

    - id: restoring_beam
      type: float[]?
      doc: |
        Restoring beam to use for every facet following the WSClean order of major axis, minor axis, position angle.

    - id: tmpdir
      type: string?
      doc: Temporary directory to run I/O heavy jobs.

steps:
    - id: find_image_size
      label: image_size
      in:
        - id: region
          source: facet_polygon
        - id: pixel_size
          source: pixel_scale
        - id: resolution
          source: resolution
      out:
        - id: name
        - id: image_size
        - id: blavg
      run: ../../steps/estimate_image_size.cwl

    - id: make_facet_image
      label: make_facet_image
      in:
        - id: ncpu
          source: ncpu
        - id: msin
          source: msin
        - id: name
          source: find_image_size/name
        - id: size
          source: find_image_size/image_size
        - id: baseline_averaging
          source: find_image_size/blavg
        - id: taper-gaussian
          source: resolution
        - id: scale
          source: pixel_scale
          valueFrom: $(self.toString() + "asec")
        - id: beam-shape
          source: restoring_beam
        - id: briggs
          source: briggs
        - id: tmpdir
          source: tmpdir
        - id: apply-facet-beam
          default: false
        - id: apply-primary-beam
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
      run: ../../steps/wsclean.cwl

    - id: trim_image_pb
      label: Trim facet image-pb
      in:
        - id: image
          source:
           - make_facet_image/MFS_image_pb
        - id: region
          source: facet_polygon
        - id: output_name
          valueFrom: $('trimmed_'.concat(inputs.image.basename))
      out:
        - id: trimmed_image
      run: ../../steps/trim_facet.cwl

    - id: trim_image
      label: Trim facet image
      in:
        - id: image
          source:
           - make_facet_image/MFS_image
        - id: region
          source: facet_polygon
        - id: output_name
          valueFrom: $('trimmed_'.concat(inputs.image.basename))
      out:
        - id: trimmed_image
      run: ../../steps/trim_facet.cwl

    - id: trim_model_pb
      label: Trim model image-pb
      in:
        - id: image
          source:
           - make_facet_image/MFS_model_pb
        - id: region
          source: facet_polygon
        - id: output_name
          valueFrom: $('trimmed_'.concat(inputs.image.basename))
      out:
        - id: trimmed_image
      run: ../../steps/trim_facet.cwl

    - id: trim_model
      label: Trim model image
      in:
        - id: image
          source:
           - make_facet_image/MFS_model
        - id: region
          source: facet_polygon
        - id: output_name
          valueFrom: $('trimmed_'.concat(inputs.image.basename))
      out:
        - id: trimmed_image
      run: ../../steps/trim_facet.cwl

    - id: trim_residual_pb
      label: Trim residual image-pb
      in:
        - id: image
          source:
           - make_facet_image/MFS_residual_pb
        - id: region
          source: facet_polygon
        - id: output_name
          valueFrom: $('trimmed_'.concat(inputs.image.basename))
      out:
        - id: trimmed_image
      run: ../../steps/trim_facet.cwl

    - id: trim_residual
      label: Trim residual image
      in:
        - id: image
          source:
           - make_facet_image/MFS_residual
        - id: region
          source: facet_polygon
        - id: output_name
          valueFrom: $('trimmed_'.concat(inputs.image.basename))
      out:
        - id: trimmed_image
      run: ../../steps/trim_facet.cwl

outputs:
    - id: MFS_image_pb
      type: File
      outputSource: trim_image_pb/trimmed_image
    - id: MFS_image
      type: File
      outputSource:
        - trim_image/trimmed_image
      
    - id: MFS_model_pb
      type: File
      outputSource: trim_model_pb/trimmed_image
    - id: MFS_model
      type: File
      outputSource: trim_model/trimmed_image
      
    - id: MFS_residual_pb
      type: File
      outputSource: trim_residual_pb/trimmed_image
    - id: MFS_residual
      type: File
      outputSource: trim_residual/trimmed_image

    - id: MFS_psf
      type:
        - File?
        - File[]?
      outputSource: make_facet_image/MFS_psf
