from pathlib import Path
from typing import List, Optional
import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from gwas_sumstats_tools.gen_meta import gen_meta
from gwas_sumstats_tools.validate import validate
from gwas_sumstats_tools.read import read
from gwas_sumstats_tools.format import format
from gwas_sumstats_tools.utils import (header_dict_from_args,
                                       metadata_dict_from_args,
                                       get_version)


app = typer.Typer(add_completion=False,
                  no_args_is_help=True,
                  rich_markup_mode="rich",
                  context_settings={"help_option_names": ["-h", "--help"]})


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
                minimum_rows: int = typer.Option(100_000,
                                                 "--min-rows", "-m",
                                                 help="Minimum rows acceptable for the file"),
                chunkzize: int = typer.Option(1_000_000,
                                              "--chunksize", "-s",
                                              help=("Number of rows to store in memory at once. "
                                                    "Increase this number for more speed at the cost "
                                                    "of more memory. Decrease to save memory, at the "
                                                    "cost of speed.")),
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
                                minimum_rows=minimum_rows,
                                chunksize=chunkzize,
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
    result, message = read(filename=filename,
                           metadata_infile=metadata_infile,
                           get_header=get_header,
                           get_all_metadata=get_all_metadata,
                           get_metadata=get_metadata)
    print(message)
    print(result)


@app.command("format",
             no_args_is_help=True,
             context_settings={"help_option_names": ["-h", "--help"],
                               "allow_extra_args": True,
                               "ignore_unknown_options": True})
def ss_format(filename: Path = typer.Argument(...,
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
                                                          help="[italic]Internal use only[/italic]. Populate metadata from GWAS Catalog"),
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
    header_map = header_dict_from_args(args=extra_args.args) \
        if custom_header_map else {}
    meta_dict = metadata_dict_from_args(args=extra_args.args) \
        if metadata_edit_mode else {}
    format(filename=filename,
           data_outfile=data_outfile,
           minimal_to_standard=minimal_to_standard,
           generate_metadata=generate_metadata,
           metadata_outfile=metadata_outfile,
           metadata_infile=metadata_infile,
           metadata_from_gwas_cat=metadata_from_gwas_cat,
           header_map=header_map,
           metadata_dict=meta_dict)

@app.command("gen_meta",
             no_args_is_help=True,
             context_settings={"help_option_names": ["-h", "--help"],
                               "allow_extra_args": True,
                               "ignore_unknown_options": True})
def ss_gen_meta(filename: Path = typer.Argument(...,
                                              readable=True,
                                              help="Input sumstats file. Must be TSV or CSV and may be gzipped"),
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
                                                          help="[italic]Internal use only[/italic]. Populate metadata from GWAS Catalog"),
              extra_args: typer.Context = typer.Option(None)
              ):
    """
    [green]FORMAT[/green] a sumstats file by creating a new one from the existing one. Add/edit metadata.
    """
    meta_dict = metadata_dict_from_args(args=extra_args.args) \
        if metadata_edit_mode else {}
    gen_meta(filename=filename,
           generate_metadata=generate_metadata,
           metadata_outfile=metadata_outfile,
           metadata_infile=metadata_infile,
           metadata_from_gwas_cat=metadata_from_gwas_cat,
           metadata_dict=meta_dict)


@app.command("version")
def ss_version():
    """Print installed version and exit.
    """
    print(get_version())


if __name__ == "__main__":
    app()
