from pathlib import Path
from typing import Union
import yaml
import petl as etl

from gwas_sumstats_tools.interfaces.data_table import SumStatsTable
from gwas_sumstats_tools.interfaces.metadata import (MetadataClient,
                                                     SumStatsMetadata)
from gwas_sumstats_tools.utils import exit_if_no_data


class Reader():
    """Class for reading summary statistics data tables
    and associated metadata
    """
    def __init__(self,
                 sumstats_file: Path = None,
                 metadata_file: Path = None) -> None:
        if not metadata_file and isinstance(sumstats_file, Path):
            metadata_file = sumstats_file.with_suffix(sumstats_file.suffix + "-meta.yaml")
        self.data = SumStatsTable(sumstats_file=sumstats_file) \
            if sumstats_file else None
        self.meta = MetadataClient(in_file=metadata_file) \
            if metadata_file else None

    def file_header(self) -> Union[SumStatsTable.header, None]:
        """Get the file header

        Returns:
            Sumstats data file header
        """
        if self.data:
            return self.data.header()
        else:
            return None

    def metadata_model(self, **kwargs) -> Union[SumStatsMetadata, None]:
        """Get the metadata model

        Keyword Arguments:
            **kwargs to pydantic model.dict

        Returns:
            Metadata model
        """
        if self.meta:
            self.meta.from_file()
            return self.meta.metadata
        else:
            return None

    def metadata_dict(self, include: list = None, **kwargs) -> dict:
        """Get the metadata as a dict

        Keyword Arguments:
            include -- Optional list of fields to include (default: include all)
            **kwargs to pydantic model.dict()

        Returns:
            Dict of metadata
        """
        metadata_dict = {}
        if self.meta:
            self.meta.from_file()
            if include:
                metadata_dict = {field: self.meta.metadata.dict(**kwargs).get(field)
                                 for field in include}
            else:
                return self.meta.metadata.dict(**kwargs)
        return metadata_dict

    def head(self, **kwargs) -> Union[etl.Table, None]:
        """Head of data file

        Returns:
            etl.Table
        """
        if self.data:
            return self.data.head_table(**kwargs)
        else:
            return None


def read(filename: Path,
         metadata_infile: Path = None,
         get_header: bool = False,
         get_all_metadata: bool = False,
         get_metadata: list = None):
    """Driver function for the Reader class

    Arguments:
        filename -- sumstats filename

    Keyword Arguments:
        metadata_infile -- metadata filename (default: {None})
        get_header -- return the header (default: {False})
        get_all_metadata -- return all the metadata  (default: {False})
        get_metadata -- return the metadata fields specified in this list (default: {None})

    Returns:
        _description_
    """
    reader = Reader(sumstats_file=filename,
                    metadata_file=metadata_infile)
    exit_if_no_data(reader.data.sumstats)
    if get_header:
        message = "[bold]\n#-------- SUMSTATS HEADERS --------#\n[/bold]"
        return (reader.file_header(), message)
    if get_all_metadata:
        message = "[bold]\n#-------- SUMSTATS METADATA --------#\n[/bold]"
        return (yaml.dump(reader.metadata_dict()), message)
    if get_metadata:
        message = "[bold]\n#-------- SUMSTATS METADATA --------#\n[/bold]"
        return (yaml.dump(reader.metadata_dict(include=get_metadata)), message)
    if not any([get_header, get_all_metadata, get_metadata]):
        message = "[bold]\n#-------- SUMSTATS DATA PREVIEW --------#\n[/bold]"
        return (reader.head(), message)
