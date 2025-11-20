# Pipeline for the International LOFAR Telescope (PILOT)

The Pipeline for the International LOFAR Telscope (PILOT) is a calibration and imaging pipeline that includes all of LOFAR’s international stations to achieve sub-arcsecond resolution.
It is implemented in Common Workflow Language and we recommend the use of Toil for running it.

Instruction on setting up, configuration and usage of the pipeline can be found in the dedicated [wiki](https://git.astron.nl/RD/VLBI-cwl/-/wikis/home).

## Installing the pipeline

The simplest way to get set up is to install the package in a virtual environment, _e.g._ by running the following from the repository root directory:
```
python -m venv venv
. venv/bin/activate
pip install .
```


## Running the test suite

PILOT comes with a test suite, which is controlled through [tox](https://tox.wiki/en/latest/config.html).
Tox controls any dependencies, so running the tests is as simple as running `tox` after PILOT has been installed.

By default, tox tests against Python versions 3.10 through 3.13 (if available).
To test against a specific version, run tox with the `-e` flag.
For example, to test against Python 3.10, run
```
tox -e py310
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
