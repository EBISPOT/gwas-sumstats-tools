from pathlib import Path
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from gwas_sumstats_tools.interfaces.data_table import SumStatsTable
from gwas_sumstats_tools.interfaces.generate_config import Config
from gwas_sumstats_tools.interfaces.apply_config import Applyconfig
from gwas_sumstats_tools.utils import (
    parse_accession_id,
    append_to_path,
    exit_if_no_data,
)


class Formatter:
    def __init__(
        self,
        data_infile: Path,
        data_outfile: Path = None,
        format_data: bool = False,
    ) -> None:
        self.format_data = format_data
        self.data_infile = Path(data_infile)
        self.data_outfile = Path(
            self._set_data_outfile_name() if not data_outfile else data_outfile
        )
    
        self.data = (
            SumStatsTable(sumstats_file=self.data_infile) if self.data_infile else None
        )

    def _set_data_outfile_name(self) -> str:
        """Set the data outfile name.
        This method only runs if the data outfile is not
        set. Then if the data is not to be reformatted, the
        outfile is the same as the infile. If the data is
        to be formatted, the outfile name is configured based
        on infile name accession ID parsing.

        Returns:
            data outfile name string
        """
        if self.format_data:
            accession_id = parse_accession_id(filename=self.data_infile)
            if accession_id:
                self.data_outfile = accession_id + ".tsv.gz"
            else:
                self.data_outfile = append_to_path(
                    self.data_infile, "-FORMATTED.tsv.gz"
                )
        else:
            self.data_outfile = self.data_infile
        return self.data_outfile

format(filename=filename,
           data_outfile=data_outfile,
           minimal_to_standard=minimal_to_standard,
           config_outfile=config_outfile,
           config_infile=config_infile,
           generate_config=generate_config,
           test_config=test_config,
           apply_config=apply_config)


def format(
    filename: Path,
    data_outfile: Path = None,
    minimal_to_standard: bool = False,
    generate_config: bool = False,
    config_outfile: Path = None,
    config_infile: Path = None,
    test_config: bool = False,
    apply_config: bool = False,
) -> None:
    formatter = Formatter(
        data_infile=filename,
        data_outfile=data_outfile,
        config_infile=config_infile,
        config_outfile=config_outfile,
        format_data=minimal_to_standard,

    )
    if minimal_to_standard:
        exit_if_no_data(table=formatter.data.sumstats)
        print("[bold]\n-------- SUMSTATS DATA --------\n[/bold]")
        print(formatter.data.sumstats)
        if header_map:
            formatter.data.reformat_header(header_map=header_map)
        else:
            formatter.data.reformat_header()
        formatter.data.normalise_missing_values()
        print("[bold]\n-------- REFORMATTED DATA --------\n[/bold]")
        print(formatter.data.sumstats)
        print(
            f"[green]Formatting and writing sumstats data --> {str(formatter.data_outfile)}[/green]"
        )
        with Progress(
            SpinnerColumn(finished_text="Complete!"),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Processing...", total=None)
            formatter.data.to_file(outfile=formatter.data_outfile)
    
    if generate_config:
        if data_outfile:
            formatter.to_file()
        else:
            formatter.generate_config.to_file()
    if test_config:
        config = Config()
        config.test_config()
    elif apply_config:
        config = Config()
        config.apply_config()
    if not any([minimal_to_standard, generate_config, apply_config,test_config ]):
        print("Nothing to do.")

format(filename=filename,
           data_outfile=data_outfile,
           minimal_to_standard=minimal_to_standard,
           config_outfile=config_outfile,
           config_infile=config_infile,
           generate_config=generate_config,
           test_config=test_config,
           apply_config=apply_config)