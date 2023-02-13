"""
Convert from old format to new standard
TODO:
1. reorder/rename columns
    - use petl
2. create metadata file from rest api 
    - import schema from standard repo
    - metadata client - take from harm pipeline

Input: 
    1. file labelled with GCST
    2. outfile name
steps:
    calc:
        GCST
        md5sum
        metadata
output:
    outfile + outfile-meta.yaml
"""


import typer
from pathlib import Path

from transformer import SumStatsTable


app = typer.Typer()


@app.command()
def main(filename: Path = typer.Argument(...,
                                         exists=True,
                                         readable=True),
         outfile: Path = typer.Option(None,
                                      "--outfile", "-o",
                                      writable=True,
                                      file_okay=True),
         metadata_only: bool = typer.Option(False,
                                            "--metadata-only", "-m")
         ):
    sst = SumStatsTable(filename)  
    print(sst.reformat_header())


if __name__ == "__main__":
    app()