class: CommandLineTool
cwlVersion: v1.2
id: astrometry
doc: Script to determine astrometry offset between known positions e.g LoTSS and widefield VLBI image

baseCommand:
  - /cosma8/data/do011/dc-esco1/postprocessing/restored_post/correct_compact/astrometry.py

inputs:
  - id: crossmatch_fits
    type: File
    doc: Fits file containing positions of sources to crossmatch with new image
    inputBinding:
      position: 0
      prefix: '--crossmatch_fits'
  - id: source_fits
    type: File
    doc: Fits file containing positions of source from image created using widefield mode
    inputBinding:
      position: 1
      prefix: '--source_fits'
  - id: ra1
    type: string
    doc: Column name of RA from crossmatch catalogue
    inputBinding:
      position: 2
      prefix: '--ra1'
  - id: ra2
    type: string
    doc: Column name of RA from source catalogue
    inputBinding:
      position: 3
      prefix: '--ra2'
  - id: dec1       
    type: string
    doc: Column name of Dec from crossmatch catalogue
    inputBinding:
      position: 4
      prefix: '--dec1'
  - id: dec2       
    type: string
    doc: Column name of Dec from source catalogue
    inputBinding:
      position: 5
      prefix: '--dec2'
  - id: error
    type: float?
    doc: Error for crossmatching region
    default: 5
    inputBinding:
      position: 6
      prefix: '--error'

outputs:
   - id: astrometry_plot
     type: File
     doc: Plot to probe the astrometry offsets between crossmatch catalogue and image catalogue
     outputBinding:
       glob: astrometry_offset_*.png
   - id: ra_offset
     type: File
     doc: Table containing the RA offsets between the crossmatch catalogue and image catalogue
     outputBinding:
       glob: ra_offset_*.csv
   - id: dec_offset
     type: File
     doc: Table containing the Dec offsets between the crossmatch catalogue and image catalogue
     outputBinding:
       glob: dec_offset_*.csv
   - id: match_submission
     type: File
     doc: Bash script used to creat matched catalogue
     outputBinding:
       glob: match_*.sh
   - id: source_matches
     type: File
     doc: Table containing the crossmatched catalouge containing both crossmatch and source positions
     outputBinding:
       glob: source_matches_*.fits
   - id: SNR_sources
     type: File
     doc: Table containing the compact sources used for corrections
     outputBinding:
       glob: compact_sources_astrometry*.csv
