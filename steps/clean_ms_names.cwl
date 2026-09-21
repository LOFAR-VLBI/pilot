cwlVersion: v1.2
class: CommandLineTool
id: clean_ms_names
label: Cleans up MeasurementSet directory names after dd calibration.
doc: Rename MeasurementSets using their extracted ILTJ source names.

baseCommand: /bin/true

inputs:
  - id: msin
    type: Directory[]
    doc: MeasurementSet directories to rename.

outputs:
  - id: msout
    type: Directory[]
    outputBinding:
      glob: "*"

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing: |
      ${
        var sourceRegex = /ILTJ\d{6}\.\d{2}[+-]\d{6}\.\d{1}/;

        return inputs.msin.map(function (directory) {
          var match = directory.basename.match(sourceRegex);
          var observation = directory.basename.match(/L\d+/);
          var extension = directory.basename.match(/(\.[^.]+)$/);

          return {
            entry: directory,
            entryname: match
              ? match[0]
                + (observation ? "_" + observation[0] : "")
                + (extension ? extension[1] : "")
              : directory.basename
          };
        });
      }
