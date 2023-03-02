from pathlib import Path
from typing import List, Optional, Union
import typer
import petl as etl
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from gwas_sumstats_tools.interfaces.data_table import (SumStatsTable,
                                                     header_dict_from_args)
from gwas_sumstats_tools.interfaces.metadata import (MetadataClient,
                                                   metadata_dict_from_args,
                                                   metadata_dict_from_gwas_cat,
                                                   get_file_metadata,
                                                   init_metadata_from_file)
from gwas_sumstats_tools.validate import validate
from gwas_sumstats_tools.utils import (set_data_outfile_name,
                                       set_metadata_outfile_name,
                                       parse_accession_id)


app = typer.Typer(add_completion=False,
                  no_args_is_help=True,
                  rich_markup_mode="rich",
                  context_settings={"help_option_names": ["-h", "--help"]})


def exit_if_no_data(table: Union[etl.Table, None]) -> None:
    if table is None:
        print("No data in table. Exiting.")
        raise typer.Exit()


def exit_status(status: bool) -> int:
    return 0 if status is True else 1


@app.command("validate",
             no_args_is_help=True,
             context_settings={"help_option_names": ["-h", "--help"],
                               "allow_extra_args": True,
                               "ignore_unknown_options": True})
def ss_validate(filename: Path = typer.Argument(...,
                                                exists=True,
                                                readable=True,
                                                help="Input sumstats file. Must be TSV or CSV and may be gzipped"),
                errors_file: bool = typer.Option(False,
                                                 "--errors-out", "-e",
                                                 help="Output erros to a csv file, <filename>.err.csv.gz"),
                pval_zero: bool = typer.Option(False,
                                               "--p-zero", "-z",
                                               help="Force p-values of zero to be allowable. Takes precedence over inferred value (-i)"),
                pval_neg_log: bool = typer.Option(False,
                                                  "--p-neg-log", "-n",
                                                  help="Force p-values to be validated as -log10. Takes precedence over inferred value (-i)"),
                minimum_rows: int = typer.Option(100_000,
                                                 "--min-rows", "-m",
                                                 help="Minimum rows acceptable for the file"),
                infer_from_metadata: bool = typer.Option(False,
                                                   "--infer-from-metadata", "-i",
                                                   help=("Infer validation options from the "
                                                         "metadata file <filename>-meta.yaml. "
                                                         "E.g. fields for analysis software and "
                                                         "negative log10 p-values affect the data "
                                                         "validation behaviour."))
                ):
    """
    [green]VALIDATE[/green] a GWAS summary statistics data file
    """
    print(f"Validating file: {filename}")
    with Progress(SpinnerColumn(),
                  TextColumn("[progress.description]{task.description}"),
                  transient=True
                  ) as progress:
        progress.add_task(description="Validating...", total=None)
        (valid,
         message,
         error_preview,
         error_type) = validate(filename=filename,
                                errors_file=errors_file,
                                pval_zero=pval_zero,
                                pval_neg_log=pval_neg_log,
                                minimum_rows=minimum_rows,
                                infer_from_metadata=infer_from_metadata)
    print(f"Validation status: {valid}")
    print(message)
    if error_type:
        print(("Primary reason for validation failure: "
               f"[red]{error_type}[/red]"))
    if error_preview:
        print(("See below for a preview of the errors. "
               "To get all the errors in a file run the "
               "[green][bold]validate[/bold][/green] command "
               "with the [green][bold]-e[/bold][/green] flag."))
        print(error_preview)
    raise typer.Exit(exit_status(valid))


@app.command("read",
             no_args_is_help=True,
             context_settings={"help_option_names": ["-h", "--help"],
                               "allow_extra_args": True,
                               "ignore_unknown_options": True})
def ss_read(filename: Path = typer.Argument(...,
                                            exists=True,
                                            readable=True,
                                            help="Input sumstats file. Must be TSV or CSV and may be gzipped"),
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
    [green]READ[/green] a sumstats file
    """
    sst = SumStatsTable(filename)
    exit_if_no_data(table=sst.sumstats)
    if get_header:
        print("[bold]\n-------- SUMSTATS HEADERS --------\n[/bold]")
        for h in sst.header():
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
                                              help="Input sumstats file. Must be TSV or CSV and may be gzipped"),
              data_outfile: Path = typer.Option(None,
                                                "--ss-out", "-o",
                                                writable=True,
                                                file_okay=True,
                                                help="Output sumstats file"),
              minimal_to_standard: bool = typer.Option(False,
                                                 "--minimal2standard", "-s",
                                                 help=("Try to convert a valid, minimally formatted file "
                                                       "to the standard format."
                                                       "This assumes the file at least has `p_value` "
                                                       " combined with rsid in `variant_id` field or "
                                                       "`chromosome` and `base_pair_location`. Validity "
                                                       "of the new file is not guaranteed because mandatory "
                                                       "data could be missing from the original file.")),
              generate_metadata: bool = typer.Option(False,
                                                     "--generate-metadata", "-m",
                                                     help="Create the metadata file"),
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
    [green]FORMAT[/green] a sumstats file by creating a new one from the existing one. Add/edit metadata.
    """
    # Set data outfile name
    ss_out = set_data_outfile_name(data_infile=filename,
                                   data_outfile=data_outfile)
    # Set metadata outfile name
    m_out = set_metadata_outfile_name(data_outfile=str(filename),
                                      metadata_outfile=metadata_outfile)
    if minimal_to_standard:
        m_out = set_metadata_outfile_name(data_outfile=ss_out,
                                          metadata_outfile=metadata_outfile)
        sst = SumStatsTable(filename)
        exit_if_no_data(table=sst.sumstats)
        print("[bold]\n-------- SUMSTATS DATA --------\n[/bold]")
        print(sst.sumstats)
        if custom_header_map:
            header_map = header_dict_from_args(args=extra_args.args)
            sst.reformat_header(header_map=header_map)
        else:
            sst.reformat_header()
        sst.normalise_missing_values()
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
    if not any([minimal_to_standard, generate_metadata]):
        print("Nothing to do.")


if __name__ == "__main__":
    app()
