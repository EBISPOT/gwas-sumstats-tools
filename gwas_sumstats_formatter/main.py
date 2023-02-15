from pathlib import Path
from typing import List, Optional
import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from gwas_sumstats_formatter.sumstats_table import (SumStatsTable,
                                                    header_dict_from_args)
from gwas_sumstats_formatter.sumstats_metadata import (MetadataClient,
                                                       metadata_dict_from_args,
                                                       metadata_dict_from_gwas_cat,
                                                       get_file_metadata,
                                                       init_metadata_from_file)
from gwas_sumstats_formatter.utils import (set_data_outfile_name,
                                           set_metadata_outfile_name,
                                           parse_accession_id)


app = typer.Typer(add_completion=False,
                  rich_markup_mode="rich",
                  no_args_is_help=True,
                  context_settings={"help_option_names": ["-h", "--help"]})


"""
TODO: write, validate

@app.command("create")
def ss_write():
    pass

@app.command("validate")
def ss_validate():
    pass
"""


@app.command("read",
             no_args_is_help=True,
             context_settings={"help_option_names": ["-h", "--help"],
                               "allow_extra_args": True,
                               "ignore_unknown_options": True})
def ss_read(filename: Path = typer.Argument(...,
                                            exists=True,
                                            readable=True,
                                            help="Input sumstats file"),
            get_header: bool = typer.Option(False,
                                            "--get-header", "-h",
                                            help="Just return the headers of the file"),
            metadata_infile: Path = typer.Option(None,
                                                 "--meta-in",
                                                 readable=True,
                                                 exists=True,
                                                 help=("Specify a metadata file to read in, "
                                                       "defaulting to <filename>-meta.yaml"),
                                                 show_default=False),
            get_all_metadata: bool = typer.Option(False,
                                                  "--get-all-metadata", "-M",
                                                  help="Return all metadata"),
            get_metadata: Optional[List[str]] = typer.Option(None,
                                                             "--get-metadata", "-m",
                                                             help=("Get metadata for the "
                                                                   "specified fields e.g. "
                                                                   "`-m genomeAssembly -m isHarmonised"))
            ):
    """
    [green]Read[/green] a sumstats file
    """
    sst = SumStatsTable(filename)
    if get_header:
        print("[bold]\n-------- SUMSTATS HEADERS --------\n[/bold]")
        for h in sst.get_header():
            print(h)
    if get_all_metadata:
        ssm = init_metadata_from_file(filename=filename, metadata_infile=metadata_infile)
        print("[bold]\n-------- SUMSTATS METADATA --------\n[/bold]")
        print(ssm)
    if get_metadata:
        ssm = init_metadata_from_file(filename=filename, metadata_infile=metadata_infile)
        print("[bold]\n-------- SUMSTATS METADATA --------\n[/bold]")
        for f in get_metadata:
            print(f"{f}={ssm.as_dict().get(f)}")
    if not any([get_header, get_all_metadata, get_metadata]):
        # Just preview the file
        print("[bold]\n-------- SUMSTATS DATA --------\n[/bold]")
        print(sst.sumstats)
    



@app.command("format",
             no_args_is_help=True,
             context_settings={"help_option_names": ["-h", "--help"],
                               "allow_extra_args": True,
                               "ignore_unknown_options": True})
def ss_format(filename: Path = typer.Argument(...,
                                              exists=True,
                                              readable=True,
                                              help="Input sumstats file"),
              data_outfile: Path = typer.Option(None,
                                                "--ss-out", "-o",
                                                writable=True,
                                                file_okay=True,
                                                help="Output sumstats file"),
              generate_data: bool = typer.Option(True,
                                                 "--generate-data/--not-generate-data", "-d/-D",
                                                 help="Do/Don't create the data file"),
              generate_metadata: bool = typer.Option(True,
                                                     "--generate-metadata/--not-generate-metadata", "-m/-M",
                                                     help="Do/Don't create the metadata file"),
              metadata_outfile: Path = typer.Option(None,
                                                    "--meta-out",
                                                    writable=True,
                                                    file_okay=True,
                                                    help="Specify the metadata output file"),
              metadata_infile: Path = typer.Option(None,
                                                   "--meta-in",
                                                   readable=True,
                                                   exists=True,
                                                   help="Specify a metadata file to read in"),
              metadata_edit_mode: bool = typer.Option(False,
                                                      "--meta-edit", "-e",
                                                      help=("Enable metadata edit mode. "
                                                            "Then provide params to edit in "
                                                            "the `--<FIELD>=<VALUE>` format e.g. "
                                                            "`--GWASID=GCST123456` to edit/add "
                                                            "that value")),
              metadata_from_gwas_cat: bool = typer.Option(False,
                                                          "--meta-gwas", "-g",
                                                          help="Populate metadata from GWAS Catalog"),
              custom_header_map: bool = typer.Option(False,
                                                     "--custom-header-map", "-c",
                                                     help=("Provide a custom header mapping using "
                                                           "the `--<FROM>:<TO>` format e.g. "
                                                           "`--chr:chromosome`")),
              extra_args: typer.Context = typer.Option(None)
              ):
    """
    [green]Format[/green] a sumstats file and creating a new one. Add/edit metadata.
    """
    # Set data outfile name
    ss_out = set_data_outfile_name(data_infile=filename,
                                   data_outfile=data_outfile)
    # Set metadata outfile name
    m_out = set_metadata_outfile_name(data_outfile=ss_out,
                                      metadata_outfile=metadata_outfile)
    if generate_data:
        sst = SumStatsTable(filename)
        print("[bold]\n-------- SUMSTATS DATA --------\n[/bold]")
        print(sst.sumstats)
        if custom_header_map:
            header_map = header_dict_from_args(args=extra_args.args)
        sst.reformat_header(header_map=header_map)
        sst.reformat_table()
        print("[bold]\n-------- REFORMATTED DATA --------\n[/bold]")
        print(sst.sumstats)
        print(f"[green]Formatting and writing sumstats data --> {ss_out}[/green]")
        with Progress(SpinnerColumn(finished_text="Complete!"),
                      TextColumn("[progress.description]{task.description}"),
                      transient=True
                      ) as progress:
            progress.add_task(description="Processing...", total=None)
            sst.to_file(outfile=ss_out)
    # Get metadata
    if generate_metadata:
        print("[bold]\n---------- METADATA ----------\n[/bold]")
        meta_dict = get_file_metadata(in_file=filename, out_file=ss_out)
        if metadata_from_gwas_cat:
            meta_dict = metadata_dict_from_gwas_cat(accession_id=parse_accession_id(filename=filename))
        if metadata_edit_mode:
            meta_dict.update(metadata_dict_from_args(args=extra_args.args))
        ssm = MetadataClient(out_file=m_out,
                             in_file=metadata_infile)
        ssm.update_metadata(data_dict=meta_dict)
        print(ssm)
        print(f"[green]Writing metadata --> {m_out}[/green]")
        ssm.to_file()


if __name__ == "__main__":
    app()
