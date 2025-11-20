class: CommandLineTool
cwlVersion: v1.2
id: source_finding
doc: Generates a source catalogue of input image using pyBDSF

baseCommand:
  - /cosma8/data/do011/dc-esco1/postprocessing/restored_post/source_finding.py

inputs:
  - id: input_image
    type: File
    doc: fits image to create catalogue from (pb corrected)
    inputBinding:
      position: 0
      prefix: '--input_image'
  - id: detection_image
    type: File
    doc: fits image to use as a detection image (non-pb)
    inputBinding:
      position: 1
      prefix: '--detect_img'
  - id: rmsbox
    type: float?
    doc: Size in pixels of noise area for pyBDSF
    default: 120
    inputBinding:
      position: 2
      prefix: '--rmsbox'
  - id: thresh_isl
    type: float?
    doc: Sigma threshold for island detections with pyBDSF                
    default: 5
    inputBinding:
      position: 3
      prefix: '--thresh_isl'
  - id: thresh_pix
    type: float?
    doc: Sigma threshold for pixel detections with pyBDSF                
    default: 5
    inputBinding:
      position: 4
      prefix: '--thresh_pix'

outputs:
   - id: catalogue
     type: File
     doc: source catalogue
     outputBinding:
       glob: source_catalogue_*.fits
   - id: gauss
     type: File
     doc: gaussian catalogue
     outputBinding:
       glob: gaussian_catalogue_*.fits
