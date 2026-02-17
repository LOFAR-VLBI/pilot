class: CommandLineTool
cwlVersion: v1.2
id: chunk_table
doc: Split CSV or FITS table into smaller chunks

baseCommand:
  - chunk_table.sh

inputs:
  - id: csv
    type: File
    doc: Input CSV or FITS table
    inputBinding:
      position: 1

outputs:
  - id: csv_chunked
    type: File[]
    doc: Chunked output CSVs
    outputBinding:
      glob: source_list_chunk*.csv
