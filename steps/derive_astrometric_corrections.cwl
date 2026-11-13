cwlVersion: v1.2
class: CommandLineTool
id: derive-astrometric-offset
doc: |
  Derives a global astrometric correction for the field.

baseCommand: derive_astrometric_offset.py

inputs:
  - id: astrometric_references
    type: File?
    doc: Reference catalogue with Source_id, RA, and DEC columns.
    inputBinding:
      prefix: --astrometric-references
      position: 1

  - id: validation_csv
    type: File?
    doc: Validation results to cross-match against the reference catalogue.
    inputBinding:
      prefix: --validation-csv
      position: 2

  - id: fits_images
    type: File[]
    doc: Self-calibration FITS images associated with the validated sources.
    inputBinding:
      prefix: --fits-images
      position: 4

outputs:
  - id: corrected_fits_images
    type: File[]
    outputBinding:
      glob: "*.astrometry.fits"
  - id: delta_ra
    type: float
    doc: Astrometric correction for the right ascension.
    outputBinding:
      loadContents: true
      glob: astrometry.json
      outputEval: $(JSON.parse(self[0].contents).delta_ra)
  - id: delta_dec
    type: float
    doc: Astrometric correction for the declination.
    outputBinding:
      loadContents: true
      glob: astrometry.json
      outputEval: $(JSON.parse(self[0].contents).delta_dec)
  - id: logfiles
    type: File[]
    doc: Standard output and error logs from the cross-match.
    outputBinding:
      glob:
        - derive_astrometric_corrections.log
        - derive_astrometric_corrections_err.log

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: derive_astrometric_corrections.log
stderr: derive_astrometric_corrections_err.log
