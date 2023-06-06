from pathlib import Path
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from gwas_sumstats_tools.interfaces.data_table import SumStatsTable
from gwas_sumstats_tools.interfaces.metadata import (
    MetadataClient,
    metadata_dict_from_gwas_cat,
    get_file_metadata,
)
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
        metadata_infile: Path = None,
        metadata_outfile: Path = None,
        format_data: bool = False,
    ) -> None:
        self.format_data = format_data
        self.data_infile = Path(data_infile)
        self.data_outfile = Path(
            self._set_data_outfile_name() if not data_outfile else data_outfile
        )
        self.metadata_outfile = Path(
            self._set_metadata_outfile_name()
            if not metadata_outfile
            else metadata_outfile
        )
        self.data = (
            SumStatsTable(sumstats_file=self.data_infile) if self.data_infile else None
        )
        self.meta = MetadataClient(
            in_file=metadata_infile, out_file=self.metadata_outfile
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

    def _set_metadata_outfile_name(self) -> str:
        return append_to_path(self.data_outfile, "-meta.yaml")

    def set_metadata(
        self, from_gwas_cat: bool = False, custom_metadata: dict = None
    ) -> MetadataClient:
        """Set metadata.
        The hierarchy of where metadata is set is as follows:
        1. custom_metadata map (overwrites anything below)
        2. metadata from the GWAS Catalog
        3. metadata from the original input file
        4. metadata inferred from the datafile

        Keyword Arguments:
            from_gwas_cat -- update with data from GWAS catalog (default: {False})
            custom_metadata -- Update with this map (default: {None})

        Returns:
            metadata object
        """
        self.meta.from_file()
        meta_dict = get_file_metadata(
            in_file=self.data_infile,
            out_file=self.data_outfile,
            meta_dict=self.meta.as_dict(),
        )
        if from_gwas_cat:
            accession_id = parse_accession_id(filename=self.data_infile)
            meta_dict.update(metadata_dict_from_gwas_cat(accession_id=accession_id))
        if custom_metadata:
            meta_dict.update(custom_metadata)
        self.meta.update_metadata(meta_dict)
        return self.meta


def format(
    filename: Path,
    data_outfile: Path = None,
    minimal_to_standard: bool = False,
    generate_metadata: bool = False,
    metadata_outfile: Path = None,
    metadata_infile: Path = None,
    metadata_from_gwas_cat: bool = False,
    header_map: dict = None,
    metadata_dict: dict = None,
) -> None:
    formatter = Formatter(
        data_infile=filename,
        data_outfile=data_outfile,
        metadata_infile=metadata_infile,
        metadata_outfile=metadata_outfile,
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
    # Get metadata
    if generate_metadata:
        print("[bold]\n---------- METADATA ----------\n[/bold]")
        metadata = formatter.set_metadata(
            from_gwas_cat=metadata_from_gwas_cat, custom_metadata=metadata_dict
        )
        print(metadata)
        print(f"[green]Writing metadata --> {str(metadata._out_file)}[/green]")
        metadata.to_file()
    if not any([minimal_to_standard, generate_metadata]):
        print("Nothing to do.")
