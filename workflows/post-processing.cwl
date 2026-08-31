cwlVersion: v1.2
class: Workflow
id: Post-Processing
label: Post Processing
doc: |
      This runs the post-processing step required to adjust wide-field images to comply with LoTSS fields. A catalogue will be generated using pyBDSF, astrometry offset will be analysed as well as the flux scaling require by comparing the image with 6".

inputs:
    - id: input_image
      type: File[]
      doc: The input image to produce catalogue
    - id: detection_image
      type: File[]
      doc: The detection image to locate sources (non-pb corrected)
    - id: rmsbox
      type: float?
      default: 120
      doc: rmsbox for pyBDSF
    - id: thresh_isl
      type: float?
      default: 3
      doc: Sigma threshold for island detections with pyBDSF
    - id: thresh_pix
      type: float?
      default: 5
      doc: Sigma threshold for pixels with pyBDSF
    - id: crossmatch_fits
      type: File
      doc: The catalogue to base astrometry of sources
    - id: ra1
      type: string
      doc: Column name of RA from crossmatch catalogue
    - id: ra2
      type: string
      doc: Column name of RA from pyBDSF catalogue which needs correcting
    - id: dec1
      type: string
      doc: Column name of Dec from crossmatch catalogue
    - id: dec2
      type: string
      doc: Column name of Dec from pyBDSF catalogue which needs correcting
    - id: error
      type: float?
      default: 5
      doc: Error for source location in pyBDSF
    - id: lotss_flux
      type: string
      doc: Column name of total flux from 6" catalogue
    - id: image_flux
      type: string
      doc: Column anme of total flux from image catalogue

steps:
        - id: source_finding
          label: Source Finder
          in:
            - id: input_image
              source: input_image
            - id: detection_image
              source: detection_image
            - id: rmsbox
              source: rmsbox
            - id: thresh_isl
              source: thresh_isl
            - id: thresh_pix
              source: thresh_pix
          out:
            - id: catalogue
            - id: gauss
          run: source_finding.cwl
          scatter: [input_image,detection_image]
          scatterMethod: dotproduct

        - id: astrometry
          label: astrometry
          in:
            - id: crossmatch_fits
              source: crossmatch_fits
            - id: source_fits
              source: source_finding/catalogue
            - id: ra1
              source: ra1
            - id: ra2
              source: ra2
            - id: dec1
              source: dec1
            - id: dec2
              source: dec2
            - id: error
              source: error
          out:
            - id: ra_offset
            - id: dec_offset
            - id: astrometry_plot
            - id: match_submission
            - id: source_matches
            - id: SNR_sources
          run: astrometry.cwl
          scatter: source_fits

        - id: flux_scaling
          label: Flux Scaling
          in:
             - id: fitsfile
               source: astrometry/source_matches
             - id: lotss_flux
               source: lotss_flux
             - id: image_flux
               source: image_flux
          out:
             - id: flux_scale
             - id: flux_scale_plot
             - id: flux_SNR_sources
          run: flux_scaling.cwl
          scatter: fitsfile
outputs:
        - id: source_finding_out
          type: File[]
          outputSource: source_finding/catalogue
        - id: source_finding_gauss
          type: File[]
          outputSource: source_finding/gauss       
        - id: astrometry_out_ra
          type: File[]
          outputSource:
            - astrometry/ra_offset
        - id: astrometry_out_dec
          type: File[]
          outputSource:
            - astrometry/dec_offset
        - id: astrometry_out_plot
          type: File[]
          outputSource:
            - astrometry/astrometry_plot
        - id: astrometry_out_sh
          type: File[]
          outputSource:
            - astrometry/match_submission
        - id: astrometry_out_match
          type: File[]
          outputSource:
            - astrometry/source_matches
        - id: astrometry_out_compact
          type: File[]
          outputSource:
            - astrometry/SNR_sources
        - id: flux_scaling_tab
          type: File[]
          outputSource:
            - flux_scaling/flux_scale
        - id: flux_scaling_plot
          type: File[]
          outputSource:
            - flux_scaling/flux_scale_plot
        - id: flux_scaling_compact
          type: File[]
          outputSource:
            - flux_scaling/flux_SNR_sources
requirements:
  - class: MultipleInputFeatureRequirement
  - class: ScatterFeatureRequirement
