---
title: An automated pipeline for LOFAR very-long baseline interferometry
tags:
  - AGN
  - astronomy
  - Common Workflow Language
  - high-resolution imaging
  - LOFAR
  - Python
authors:
  - name: Matthijs van der Wild
    orcid: 0000-0002-3949-3063
    corresponding: true
    affiliation: 1
  - name: Frits Sweijen
    orcid: 0000-0002-6470-7967
    affiliation: 1
  - name: Jurjen de Jong
    orcid: 0000-0001-6876-8719
    affiliation: "2, 3"
  - name: Alexander Drabent
    orcid: 0000-0003-2792-1793
    affiliation: 4
  - name: Emmy Escott
    orcid: 0009-0009-5108-4324
    affiliation: 1
  - name: Neal Jackson
    orcid: 0000-0002-7782-4847
    affiliation: 5
  - name: Marcel Loose
    orcid: 0000-0003-4721-747X
    affiliation: 3
  - name: Vijay Mahatma
    orcid: 0000-0001-5221-2636
    affiliation: "6, 7"
  - name: Leah K. Morabito
    orcid: 0000-0003-0487-6651
    affiliation: "1, 8"
  - name: James Petley
    orcid: 0000-0002-4496-0754
    affiliation: 2
affiliations:
  - index: 1
    name: |
        Centre for Extragalactic Astronomy,
        Deparment of Physics,
        Durham University,
        South Road,
        Durham DH1 3LE, UK
  - index: 2
    name: |
        Leiden Observatory,
        Leiden University,
        PO Box 9513,
        2300 RA Leiden,
        The Netherlands
  - index: 3
    name: |
        ASTRON,
        Oude Hoogeveensedijk 4,
        7991 PD Dwingeloo,
        The Netherlands
  - index: 4
    name: |
        Thüringer Landessternwarte,
        Sternwarte 5,
        07778 Tautenburg,
        Germany
  - index: 5
    name: |
        University of Manchester,
        Jodrell Bank Centre for Astrophysics,
        Department of Physics and Astronomy,
        Oxford Rd, Manchester M13 9PL,
        United Kingdom
  - index: 6
    name: |
        Cavendish Laboratory - Astrophysics Group,
        University of Cambridge,
        19 JJ Thomson Avenue, Cambridge CB3 0HE,
        United Kingdom
  - index: 7
    name: |
        Kavli Institute for Cosmology,
        University of Cambridge,
        Madingley Road, Cambridge CB3 0HA,
        United Kingdom
  - index: 8
    name: |
        Institute for Computational Cosmology,
        Department of Physics,
        Durham University,
        South Road, Durham DH1 3LE,
        United Kingdom
bibliography: paper.bib
---

# Summary

The Very-Long Baseline Interferometry (VLBI) Pipeline for the International Low-Frequency ARray Telescope (PILoT) is an automated data reduction pipeline that produces calibrated radio data suitable for sub-second resolution imaging.
It is a tool that facilitates calibrator and source selection, self-calibration of data, and both postage-stamp and widefield imaging.

While a diverse ecosystem of processing and imaging tools exists for the LOFAR telescope, none of those tools have been designed with high-resolution imaging in mind.
As a result, data reduction with the International LOFAR Telescope is a manual and error-prone process.
Furthermore, owing to the distributed nature of software development in the LOFAR community, all of these tools have been developed with different input and output conventions.

PILoT aims to incorporate these diverse software tools into a simple and unified framework, making VLBI imaging with LOFAR accessible to a larger group of astronomers.
Special care has been placed on ensuring that all of its software components are controlled through a consistent framework and that intermediate steps of the pipeline can be consistently and safely resumed in the event of intermediate failure.
Because of the large volumes of data required to do VLBI with the International LOFAR Telescope, the pipeline has been designed to use job schedulers common in High-Performance Computing (HPC) clusters.
This minimises manual intervention and optimises the use of available computing resources.

# Statement of need

The International Low-Frequency ARray Telescope (ILT) [@LOFAR] comprises 38 Dutch stations and 15 international stations located in partner countries across the European Union.
It is a radio telescope operating at low radio frequencies with a sensitivity of up to 3 orders of magnitude better than previous telescopes operating at comparable frequencies.
By combining data from all stations, the ILT is effectively a continent-sized telescope which is able to image astronomical radio sources at sub-arcsecond resolution [@Morabito-2025].

The VLBI Pipeline for the International LOFAR Telescope (PILoT) is an implementation of a data reduction pipeline which was designed to exploit the full imaging power of the ILT [@Morabito-2022].
PILoT addresses several critical issues the original reference implementation had to face:

- The original pipeline was implemented in an obsolete framework, which makes it difficult to impossible to ensure that it would be functional on modern computing infrastructure.
  In contrast, PILoT is implemented in the Common Workflow Language [@CWL].
  This ensures that the pipeline will be logically consistent and maintainable in the long term.
- The original pipeline did not support modern scheduling systems such as SLURM or TOIL.
  The implementation in CWL allowed for optimisation of PILoT for the workflow runner toil [@toil], providing native support for these schedulers.
  This reduces the runtimes of the pipeline by orders of magnitudes as individual processing jobs can automatically be distributed to available nodes.

In addition, PILoT includes expanded functionality featuring implementations of state-of-the-art advances in imaging techniques such as improvements in imaging resolution [@Ye-2024; @Sweijen-2022], source selection [@Sweijen-2022; @DeJong-2024], and wide-field imaging techniques [@Sweijen-2022; @DeJong-2025b].

PILoT forms a natural part of the LOFAR software landscape and is designed to be used on data that has been corrected for various instrumental and ionospheric effects [@deGasperin-2019] and calibrated for directional effects using the data obtained by the Dutch stations using pipelines such as DDF-pipeline [@DDF-calibration; @DDF-pipeline] or Rapthor [@rapthor].
It uses DP3 [@DP3], WSclean [@WSclean], AOflagger [@AOflagger], and the LOFAR Initial Calibration (LINC) pipeline [@LINC], which are developed by the ILT host institute ASTRON, as well as various codebases developed by researchers in the LOFAR community such as the DDF-pipeline [@DDF-calibration] for direction-dependent calibration, LOFAR facet-selfcal [@VanWeeren-2021;@lofar-facet-selfcal] for self-calibration, and the LOFAR Helpers [@lofar-helpers] auxiliary library.
Finally, it has been adapted and integrated into the FLoCs LOFAR containers [@flocs] to ensure portability across computing facilities.

PILoT embeds the software tools above into a single cohesive framework and provides several complementary modes with the aim of being a modular and fully automated imaging pipeline.
It is able to determine when intermediate results are no longer needed, and disposes of intermediate results once they are no longer required.
Furthermore, since the pipeline is optimised to work with toil, processing steps can easily be resumed should the execution of a mode be interrupted for any reason.

The pipeline provides the following main modes of operation:

## Postage stamp imaging
The pipeline supports single-source imaging, in which the calibration is performed on an in-field calibrator to correct for direction-independent phases and delays from the international stations.
Following this, multiple imaging targets can be specified at once; the pipeline performs self-calibration and imaging on each target (for a small field-of-view around the target) in parallel.
The data products are the calibrated data and images and the phase solutions in a H5parm format[^1].

## Source subtraction from catalogue
The pipeline is able to remove radio sources from observation data beyond a square field of view of 6.25 degrees² centred on the imaging target, if given a 6 arcsecond image generated by the DDF-pipeline.
The dataproduct is the data with the sources removed in a MeasurementSet format[^2].

## Automatic calibrator selection and validation of the calibrator solutions
This module selects the best calibrator sources out of a single catalogue, based on the images and solutions from all performed self-calibration cycles.
The data product is a single H5parm, which contains the phase and amplitude solutions from the selected calibrators.

## Wide-field imaging
The pipeline is capable of intermediate (1–2 arcseconds) and high-resolution (sub-arcsecond) imaging.
High-resolution imaging supports a resolution of 0.6 or 0.3 arcseconds, of which the former reduces the imaging time by a factor of 2 compared to the latter.
Intermediate resolution imaging speeds up the imaging time by a factor of 4 compared to the 0.3 arcsecond imaging.
The data products are FITS formatted images of the stated resolution.

A list of ongoing research projects where PILoT is a central tool is provided in section 4 of reference [@Morabito-2025].

# Acknowledgements

Matthijs van der Wild is supported by the Science and Technology Facilities Council via LOFAR-U.K. [ST/V002406/1] and UKSRC [ST/T000244/1].
FS appreciates the support of STFC [ST/Y004159/1].
LKM is grateful for support from a UKRI FLF [MR/Y020405/1] and LOFAR-UK via STFC [ST/V002406/1].
AD acknowledges support by the BMBF Verbundforschung under the grant 05A23STA.
This research made use of the University of Hertfordshire high-performance computing facility and the LOFAR-UK computing facility located at the University of Hertfordshire and supported by STFC [ST/P000096/1].

The scripts developed for PILoT make use of the ASTROPY [@astropy], casacore [@casacore], LoSoTo [@losoto], numpy [@numpy], pandas [@pandas], and PyBDSF [@pybdsf] libraries.

# References

[^1]: The H5parm format is described in appendix C of [@deGasperin-2019].
[^2]: The MeasurementSet format currently in use is version 2, described in [@MeasurementSet].
