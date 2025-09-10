---
title: An automated pipeline for LOFAR very-long baseline interferometry
authors:
  - name: Matthijs van der Wild
    orcid: 0000-0002-3949-3063
    corresponding: true
    affiliation: 1
affiliations:
  - index: 1
    name: |
        Centre for Extragalactic Astronomy,
        Deparment of Physics,
        Durham University,
        South Road,
        Durham DH1 3LE, UK
    index: 1
---

# Summary

The Low-Frequency ARray Very-Long BaseLine Interferometry (LOFAR-VLBI) pipeline is an automated data reduction pipeline that produces calibrated radio data suitable for sub-second resolution imaging.
It is a tool that facilitates calibrator and source selection, self-calibration of data, and both postage-stamp and widefield imaging.
While a diverse ecosystem of processing and imaging tools already exist for the LOFAR telescope, none of these have been designed with high-resolution imaging in mind.
As a result, data reduction with the ILT is a manual and error-prone process.
Furthermore, owing to the distributed nature of software development in the LOFAR community, all of these tools have been developed with different input and output conventions.

The LOFAR-VLBI pipeline aims to incorporate these diverse software tools into a unified framework.
Special care has been placed on ensuring that all of its software components are controlled through a consistent framework and that intermediate steps of the pipeline can be consistently safely resumed in the event of intermediate failure.
Because of the large volumes of data required to do VLBI with the international LOFAR telescope, the pipeline has been designed to use job schedulers common in High-Performance Computing (HPC) clusters.
This minimises manual intervention and optimises the use of available computing resources.

# Statement of need

It is necessary for journal submissions to be compilable.
Hence, this is an attempt to provide a working foundation to build the paper off.

# Acknowledgements

Matthijs van der Wild is supported by the Science and Technology Facilities Council via LOFAR-U.K. [ST/V002406/1] and UKSRC [ST/T000244/1].
