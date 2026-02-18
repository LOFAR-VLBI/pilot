class: CommandLineTool
cwlVersion: v1.2
id: chunk_table
doc: Split source table into chunks

baseCommand:
  - chunk_table.sh

inputs:
  - id: table
    type: File
    doc: Input CSV or FITS table
    inputBinding:
      position: 1
  - id: chunk_size
    type: int?
    default: 10
    doc: Chunk size
    inputBinding:
      position: 2


outputs:
  - id: csv_chunked
    type: File[]
    doc: Chunked output CSVs
    outputBinding:
      glob: source_list_chunk*.csv
