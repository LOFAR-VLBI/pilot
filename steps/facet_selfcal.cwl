cwlVersion: v1.2
class: CommandLineTool
id: facet_selfcal
label: Facet Selfcal
doc: Performs calibration with facetselfcal.

baseCommand: facetselfcal

arguments:
  - prefix: --auto
    valueFrom: $(inputs.configfile == null)
  - prefix: --early-stopping
    valueFrom: $(inputs.model_cache != null)
  - valueFrom: "&&"
    shellQuote: false
    position: 1000
  - valueFrom: |
      mv plots plots_$(inputs.msin.basename) &&
      mv fits_images fits_images_$(inputs.msin.basename); done
    shellQuote: false
    position: 1001

inputs:
    - id: msin
      type: Directory
      inputBinding:
        position: 1
      doc: |
        Input data phase-shifted to the
        delay calibrator in MeasurementSet format.

    - id: skymodel
      type: File?
      inputBinding:
        position: 0
        prefix: --skymodel
        separate: true
      doc: |
        The skymodel to be used in the first
        cycle in the self-calibration.

    - id: configfile
      type: File?
      inputBinding:
        position: 0
        prefix: --configpath
        separate: true
      doc: A plain-text file containing configuration options for self-calibration.

    - id: dde_directions
      type: File?
      doc: A text file with directions for DDE calibration
      inputBinding:
        prefix: "--facetdirection"
        position: 0
        separate: true

    - id: model_cache
      type: string?
      doc: Neural network cache directory.
      inputBinding:
        prefix: "--nn-model-cache"
        position: 0
        separate: true

    - id: number_cores
      type: int?
      default: 12
      doc: The number of cores that should be allocated for the self-calibration.

outputs:
    - id: h5parm
      type: File
      outputBinding:
        glob: [h5_solutions/merged_selfcalcycle*.h5, h5_solutions/merged_addCS_selfcalcycle*.h5]
        outputEval: $(self[self.length - 1])
      doc: |
        The calibration solution files generated
        by lofar_facet_selfcal in HDF5 format.

    - id: best_h5parm
      type: File
      outputBinding:
        glob: [h5_solutions/best_*solutions.h5, h5_solutions/merged_addCS_selfcalcycle*.h5]
        outputEval: |
          ${
            var best = self.filter(function(f) { return f.basename.indexOf("best_") === 0; });
            if (best.length > 0) { return best[0]; }
            function cycleNum(f) {
              var m = f.basename.match(/selfcalcycle(\d+)/);
              return m ? parseInt(m[1], 10) : -1;
            }
            var sorted = self.slice().sort(function(a, b) {
              return cycleNum(a) - cycleNum(b);
            });
            return sorted[sorted.length - 1];
          }
      doc: |
        The best output merged calibration solution file if early-stopping
        was used; otherwise falls back to the last regular selfcal-cycle
        h5parm, chosen by the highest cycle number.

    - id: inspection_plots
      type: Directory[]
      outputBinding:
        glob: $(["plots_" + inputs.msin.basename, "solution_plots*", "fits_images_" + inputs.msin.basename])
      doc: |
        Renamed directories (plots, fits_images, solution_plots*) containing
        delay calibrator images and LoSoTo solution plots, suffixed with an
        identifier extracted from the input MS name.

    - id: best_fits_image
      type: File
      outputBinding:
         glob: ['fits_images_$(inputs.msin.basename)/best_*MFS-image.fits', 'fits_images_$(inputs.msin.basename)/*MFS-*image.fits']
         outputEval: |
           ${
             var best = self.filter(function(f) { return f.basename.indexOf("best_") === 0; });
             if (best.length > 0) { return best[0]; }
             function cycleNum(f) {
               var m = f.basename.match(/selfcalcycle(\d+)/);
               return m ? parseInt(m[1], 10) : -1;
             }
             var sorted = self.slice().sort(function(a, b) {
               return cycleNum(a) - cycleNum(b);
             });
             return sorted[sorted.length - 1];
           }
      doc: |
        The best selfcal FITS image if early-stopping was used; otherwise
        falls back to the last regular selfcal-cycle FITS image, chosen by
        the highest cycle number.

    - id: logfile
      type: File[]
      outputBinding:
         glob: [facet_selfcal*.log, logs/selfcal.log]
      doc: |
        The files containing the stdout
        and stderr from the step.

requirements:
  - class: ShellCommandRequirement
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.msin)
      - entry: $(inputs.configfile)
      - entry: $(inputs.skymodel)
  - class: ResourceRequirement
    coresMin: $(inputs.number_cores)
    ramMin: 60000

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl

stdout: facet_selfcal.log
stderr: facet_selfcal_err.log
