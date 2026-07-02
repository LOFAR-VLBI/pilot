# Pipeline for the International LOFAR Telescope (PILOT)

The Pipeline for the International LOFAR Telscope (PILOT) is a calibration and imaging pipeline that includes all of LOFAR’s international stations to achieve sub-arcsecond resolution.
It is implemented in [Common Workflow Language](https://commonwl.org) and we recommend the use of [Toil](https://toil.readthedocs.io/en/latest/cwl/running.html) for running it.

Instructions on downloading data, setting up, configuration and usage of the pipeline in combination with high-performance computing clusters can be found in the [LOFAR-VLBI pipeline wiki](https://github.com/LOFAR-VLBI/lofar-vlbi-pipeline/wiki).

## Installing the pipeline

The simplest way to get set up is to install the package in a virtual environment, _e.g._ by running the following from the repository root directory:
```
python -m venv venv
. venv/bin/activate
pip install .
```

## Using the pipeline

It currently is strongly recommended to run PILoT through [FLoCs](https://tikk3r.github.io/flocs/).
In this case it is not necessary to install PILoT.
The most straightforward way to run PILoT through FLoCs requires the following steps:

1. Clone the PILoT repository.
2. Download the [latest FLoCs container](https://tikk3r.github.io/flocs/#latest-containers).
3. [Install the FloCs runners](https://tikk3r.github.io/flocs/docs/using-flocs.html#installing-flocs).
4. [Set up and run the FLoCs runners](https://github.com/LOFAR-VLBI/lofar-vlbi-pipeline/wiki/Running-the-pipeline).

### External dependencies
- Swarp: https://www.astromatic.net/software/swarp/ -- optional dependency that is required if mosaicing of facet images is enabled.


## Running the test suite

PILOT comes with a test suite, which is controlled through [tox](https://tox.wiki/en/latest/config.html).
Tox controls any dependencies, so running the tests is as simple as running `tox` from anywhere in the project directory after [installing PILOT](#installing-the-pipeline).

By default, tox tests against Python versions 3.11 through 3.13 (if available).
To test against a specific version, run tox with the `-e` flag.
For example, to test against Python 3.13, run
```
tox -e py313
```
The testing suite for the Python scripts can also be run using [`pytest`](pytest.org).
In this case, the variable `VLBI_ROOT_DIR` must be set to the project root directory and `PYTHONPATH` must include the project's `scripts` directory.
For example, if run from the project root directory:
```
VLBI_ROOT_DIR=$PWD PYTHONPATH=$PWD/scripts pytest
```

The CWL steps and workflows are validated using [cwltool](https://cwltool.readthedocs.io/en/latest/index.html).
Additional command line arguments which are relevant for cwltool's validation can be specified by separating them from tox' arguments with a `--`, _e.g._
```
tox -e py313 -- --singularity --strict
```
