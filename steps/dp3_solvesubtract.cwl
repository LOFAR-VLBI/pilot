class: CommandLineTool
cwlVersion: v1.2
id: dp3_peel
label: DP3 peeling
doc: |
    This step peels a MODEL_DATA column from the provided MeasurementSet.
    Intended for use on DD calibrators or similar datasets.

baseCommand: DP3

arguments:
  - steps=[ddecal]
  - msout.storagemanager=dysco
  - ddecal.h5parm=peel.h5
  - ddecal.modelddatacolumns=[MODEL_DATA]
  - ddecal.mode=scalarcomplexgain
  - ddecal.solint=40
  - ddecal.nchan=1
  - ddecal.subtract=True
  - ddecal.smoothnessreffrequency=120000000
  - ddecal.smoothnessconstraint=5000000
  - ddecal.propagatesolutions=true
  - msout=${
      var base = inputs.msin.basename;
      var i = base.lastIndexOf(".");
      return base.slice(0, i) + "peeled" + base.slice(i);
    }

inputs:
    - id: msin
      type: Directory
      doc: Input measurement set
      inputBinding:
        prefix: msin=
        separate: false
    - id: ncpu
      type: int?
      doc: Number of cores to use
      default: 8
      inputBinding:
        prefix: numthreads=
        separate: false

outputs:
    - id: msout
      type: Directory
      doc: Output MeasurementSet
      outputBinding:
        glob: "*peeled*"
    - id: logfile
      type: File[]
      doc: DP3 log files
      outputBinding:
        glob: dp3_peel*.log

requirements:
  - class: InlineJavascriptRequirement

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
  - class: ResourceRequirement
    coresMin: $(inputs.ncpu)

stdout: dp3_peel.log
stderr: dp3_peel_err.log
