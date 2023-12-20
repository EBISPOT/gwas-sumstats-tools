from pathlib import Path
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

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

class Gen_meta:
    def __init__(
        self,
        data_infile: Path,
        metadata_infile: Path = None,
        metadata_outfile: Path = None,
        format_data: bool = False,
    ) -> None:
        self.format_data = format_data
        self.data_infile = Path(data_infile)
        self.metadata_outfile = Path(
            self._set_metadata_outfile_name()
            if not metadata_outfile
            else metadata_outfile
        )
        self.meta = MetadataClient(
            in_file=metadata_infile, out_file=self.metadata_outfile
        )

    def _set_metadata_outfile_name(self) -> str:
        #return append_to_path(self.data_outfile, "-meta.yaml")
        return append_to_path(self.data_infile, "-meta.yaml")

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

        meta_dict = get_file_metadata(
            in_file=self.data_infile,
            out_file=self.data_infile,
            meta_dict=self.meta.as_dict(),
        )
        if from_gwas_cat:
            accession_id = parse_accession_id(filename=self.data_infile)
            meta_dict.update(metadata_dict_from_gwas_cat(accession_id=accession_id))
        if custom_metadata:
            meta_dict.update(custom_metadata)
        self.meta.update_metadata(meta_dict)
        return self.meta


def gen_meta(
    filename: Path,
    generate_metadata: bool = False,
    metadata_outfile: Path = None,
    metadata_infile: Path = None,
    metadata_from_gwas_cat: bool = False,
    metadata_dict: dict = None,
) -> None:
    gen_meta = Gen_meta(
        data_infile=filename,
        metadata_infile=metadata_infile,
        metadata_outfile=metadata_outfile,
    )
    # Get metadata
    
    print("[bold]\n---------- METADATA ----------\n[/bold]")
    metadata = gen_meta.set_metadata(
        from_gwas_cat=metadata_from_gwas_cat, custom_metadata=metadata_dict
        )
    print(metadata)
    print(f"[green]Writing metadata --> {str(metadata_outfile)}[/green]")
    metadata.to_file()