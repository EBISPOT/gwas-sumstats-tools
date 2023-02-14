"""
Convert from old format to new standard
TODO:
[X] reorder/rename columns
    - use petl
[ ] create metadata file from rest api 
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

from pathlib import Path
import typer

from gwas_sumstats_formatter.sumstats_table import SumStatsTable
from gwas_sumstats_formatter.sumstats_metadata import (MetadataClient,
                                                       metadata_dict_from_args,
                                                       get_file_metadata)
from gwas_sumstats_formatter.utils import (set_data_outfile_name,
                                           set_metadata_outfile_name)


app = typer.Typer(add_completion=False,
                  context_settings={"allow_extra_args": True,
                                    "ignore_unknown_options": True}
                  )


@app.command()
def ss_format(filename: Path = typer.Argument(...,
                                              exists=True,
                                              readable=True,
                                              help="Input sumstats file"),
              data_outfile: str = typer.Option(None,
                                               "--ss-out", "-o",
                                               writable=True,
                                               file_okay=True,
                                               help="Output sumstats file"),
              metadata_only: bool = typer.Option(False,
                                                 "--metadata-only", "-m",
                                                 help="Only create the metadata file"),
              metadata_outfile: str = typer.Option(None,
                                                   "--meta-out",
                                                   writable=True,
                                                   file_okay=True,
                                                   help="Specify the metadata output file"),
              metadata_infile: str = typer.Option(None,
                                                  "--meta-in",
                                                  readable=True,
                                                  exists=True,
                                                  help="Specify a metadata file to read in"),
              metadata_edit_mode: bool = typer.Option(False,
                                                      "--meta-edit",
                                                      help=("Enable metadata edit mode. "
                                                            "Then provide params to edit in "
                                                            "the `--<KEY>=<VALUE>` format e.g. "
                                                            "`--GWASID=GCST123456` to edit/add "
                                                            "that value")),
              metadata_from_gwas_cat: bool = typer.Option(True,
                                                          "--meta-gwas",
                                                          help="Populate metadata from GWAS Catalog"),
              extra_args: typer.Context = typer.Option(None)
              ):
    # Set data outfile name
    ss_out = set_data_outfile_name(data_infile=filename,
                                   data_outfile=data_outfile)
    # Write metadata file
    m_out = set_metadata_outfile_name(data_outfile=ss_out,
                                      metadata_outfile=metadata_outfile)
    if not metadata_only:
        sst = SumStatsTable(filename)
        sst.reformat_header()
        sst.to_file(outfile=ss_out)
    # Get metadata
    meta_dict = {}
    if metadata_edit_mode:
        meta_dict.update(metadata_dict_from_args(args=extra_args.args))
    if metadata_from_gwas_cat:
        meta_dict = meta_dict
    ssm = MetadataClient(out_file=m_out,
                         in_file=metadata_infile)
    meta_dict.update(get_file_metadata(in_file=filename, out_file=ss_out))
    ssm.update_metadata(data_dict=meta_dict)
    ssm.to_file()



if __name__ == "__main__":
    app()
