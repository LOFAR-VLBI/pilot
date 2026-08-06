class: CommandLineTool
cwlVersion: v1.2
id: plot_facet_layout
label: Plot facet layout
doc: Plot facet layout with facet numbers obtained from MeasurementSet phase centres.

baseCommand: plot_facet_layout.py

inputs:
  - id: msin
    type: Directory[]
    doc: MeasurementSets
    inputBinding:
      prefix: "--ms"
      position: 0
      separate: true

  - id: facet_layout
    type: File
    doc: DS9 polygon file
    inputBinding:
      prefix: "--facet_layout"
      position: 1
      separate: true

outputs:
  - id: facet_layout_png
    type: File
    doc: Facet layout PNG
    outputBinding:
      glob: "facet_layout*.png"

hints:
  - class: DockerRequirement
    dockerPull: vlbi-cwl
