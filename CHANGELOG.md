# Changelog

## 1.1.0

### Fixed

* Several runtime errors in the facet imaging workflow were patched (#137)
* A shape check was added to the calibrator selection workflow (#142)

### Added

* A facet layout inspection plot is generated after facet subtraction (#130)

### Changed

* Imaging parameters in the facet imaging workflow were updated (#137)
* Inspection plots for delay calibrators are labelled by source name (#140)


## 1.0.0

### Fixed

* Resolved CWL warnings (#53, #72)
* Fixed various paths for pipeline failure (#59, #63, #58, #95, #98, #103, #116, #118)
* Fixed configuration issues (#107, #108, #111)
* Added various fixes in the 1 arcsecond resolution workflow (#99, #108, #110)

### Added

* Improvements to facet mosaicing using SWarp (#50, #90)
* lofar-vlbi-plot is used when no delay calibrator catalogue is provided (#70, #113)
* Improvements to phase-difference selection (#91, 95)
* Improved parallelisation in split directions (#97)
* Add option to set the acceptable fracton of bad DD calibration directions (#105)
* Additions to the delay calibrator selection (#113)
* Improvements to facet subtraction (#121, 122)

### Changed

* Updates to resource requirements (#55, #85, #87, #102)
* Intermediate ouputs delay calibration and dd-calibration outputs are stored (#101, #104)
* Various internal changes

### Removed

* Python 3.10 is no longer supported (#124)


## 0.9.1

### Fixed

* Fixed an issue where config file entries were written out before all the entries were known (6cca9662).

## 0.9.0

### Added

* New workflow `image_intermediate_resolution.cwl`: implements the 1–2" angular resolution imaging workflow (09f7723c, 48d3c07c).
* New workflow `facet_imaging.cwl`: implements the sub-arcsecond facet imaging (8acb6e71, a874f7f2).
* New subworkflow `ddcal_validation.cwl`: implements a routine to validate image and calibration solution quality for both direction-dependent and direction-independent effects (3c8d0052, 9c5c9a12).
* New subworkflow `find_best_calibrator.cwl`: implements a routine to perform delay calibration on several sources in parallel.
  These sources are chosen based on their ranking according to phasediff score (1f7bc410, 50e5a9b9).
* New subworkflow `delay_cal_run.cwl`: generates settings for delay calibration dynamically based on an initial phase difference calibration (74fa833).
* An explicit change log was added to the repository (ea55442c).

### Changed

* The VLBI pipeline has been renamed to `PILOT` (fdafca28, b40bb1fa).
* `skynet` is now able to construct an initial skymodel if the user supplies a FITS image of a source (36f5aad8, 90f70f67, deab17a9).
* LINC, lofar_helpers and lofar_facet_selfcal are now pipeline dependencies, and no longer need to be specified as workflow inputs (306360f3, a20bb37b, 0d54ad10).
* Delay calibration solutions are now automatically applied to the data (5f17d2b9).
* As a result of the addition of `delay_cal_run.cwl`: users are now required to supply `phaseup_config.txt` for the initial phase difference calibration.
* The CI runner can now be controlled more precisely via tox (cf4e26f7).
* The `facet_subtract` workflow has been sped up considerably (1c43ba0e). 
* The `subtract_lotss` workflow has been sped up considerably (f9ef10d7).

### Fixed

* Users can now specify the number of cores used by `facet_selfcal` (c8adbbe4)
* Patch names of A-team sources have been aligned with recent skymodels in LINC (42dda818).
* Target data preparation for A-team clipping now supports `spinifex` rotation measure tables (d704fefc).
* A duplicate entry in `concat_logfiles_phaseup` has been removed (d704fefc).
* Config files for facet_selfcal are now optional, circumventing toil issues (98bc5f78).
* The CI containers have been update after bitnami ceased support (238e9b42).

### Removed

* `generate_input.sh` (ef3a16cb).
* An unused import in `make_config_dical.py` (884f8c7d).
* The `finalise` CI workflow (373bc8a9).

## 0.8.0

### Added

* New subworkflow `auto_selfcal.cwl`: Performs direction-dependent self-calibration with full ILT calibrator data.
* New subworkflow `ddcal_calibrators.cwl`: Performs direction-dependent self-calibration for international LOFAR stations for multiple directions. Uses `auto_selfcal.cwl`.
* New workflow `dd-calibration.cwl`: Splits out directions with or without delay calibration solutions applied, performs automatic calibrator selection, and performs self-calibration on the best directions. Uses `split-directions.cwl` and `ddcal_calibrators.cwl`.

### Changed

* `split-directions.cwl`:
    * Step added to pre-select sources from catalogue based on their `peak_flux` value.
    * `delay_solset` is now an optional input parameter.

For more details see da86171f.


## 0.7.1

### Changed:

* Python logic was moved to dedicated script files (d8035a08, 45ce1906, 21927f89, 60970f2e, 89f5f290, c03da836, e5045d19, 61c7a300, abdaa6d3, 01ac6f1a, b6aded90).
* Replaced `pyrap` with `casacore` (a032eaea).

### Fixed:

* Fixed a bug where a A-team flags were written to a new MeasurementSet (c58abcdc).
* Fixed a typo in the README (83040d73).
* Fixed a mismatch between the A-team clipping workflow and the current LINC skymodel layout (32cab060).

### Removed

* Removed requirements.txt (3dafe748).


## 0.7.0

As of this release the pipeline is incompatible with flocs versions older than 5.5.

### Added

* Automatic CI has been added to the repository (1fc5e7af)

### Changed

* Moved to Semantic Versioning 2.0.0
* Local use of CI has been improved (5dc04989)
* Delay calibration:
    * The pipeline automatically processes the solutions generated by the DDF pipeline.
    * The workflow can subtract the LoTSS 6'' skymodel (required for wide-field imaging) (20b8472f).
    * The workflow has been optimised for LINC's high-resolution target workflow (aea458f0).
    * DDF pipeline workflows have been moved to a separate subworkflow of delay calibration (f33fe803).
    * The self-calibration of the delay calibrator now solves the phases for the remote and the international stations separately (f0006a95).
* Split directions:
    * Calibrator selection has been greatly improved based on scalar phase difference metrics (57603232).
    * A facet subtraction workflow has been added in preparation for wide-field imaging (63666fe1).
* Various improvements to the repository scripts and CWL files.


## v0.6

### Added

* Addition of the split directions workflow.

### Changed

* The A-team clipping workflow expects DP3's `clipper` step.
  Users of FLoCs should use v5.0.0 or more recent.
* LINC has been added as an explicit dependency.
  LINC scripts have been removed from the VLBI workflow files.
* The beam correction order for directions other than the delay calibrator has been updated (see e9710e87).
* The concatenation workflow now queries the computing infrastructure directly for available memory (see d208861a).
* Various minor optimisations and improvements to individual workflow files.


## v0.5

First working version. All pipeline components have been converted to CWL.
