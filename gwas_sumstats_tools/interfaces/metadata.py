import yaml
import json
from typing import Union
from datetime import date
from pathlib import Path
from pydantic import ValidationError
from gwas_sumstats_tools.config import (GWAS_CAT_API_STUDIES_URL,
                                        GWAS_CAT_API_INGEST_STUDIES_URL,
                                        GWAS_CAT_STUDY_MAPPINGS,
                                        STUDY_FIELD_TO_SPLIT,
                                        SAMPLE_FIELD_TO_SPLIT,
                                        GWAS_CAT_SAMPLE_MAPPINGS,
                                        GENOME_ASSEMBLY_MAPPINGS)
from gwas_sumstats_tools.utils import (download_with_requests,
                                       parse_accession_id,
                                       parse_genome_assembly,
                                       get_md5sum,
                                       replace_dictionary_keys,
                                       split_fields_on_delimiter)
from gwas_sumstats_tools.schema.metadata import SumStatsMetadata


class MetadataClient:
    def __init__(self, meta_dict: dict = {},
                 in_file: Path = None,
                 out_file: Path = None) -> None:
        """SumStats Metadata client

        Keyword Arguments:
            meta_dict -- Dict of metadata (default: {None})
            in_file -- Input metadata YAML file (default: {None})
            out_file -- Output metadata YAML file (default: {None})
        """
        self.metadata = SumStatsMetadata.construct()
        self._meta_dict = meta_dict
        self._in_file = in_file
        self._out_file = out_file

    def from_file(self) -> None:
        """Create metadata from YAML file
        """
        with open(self._in_file, "r") as fh:
            self._meta_dict = yaml.safe_load(fh)
            self.update_metadata(self._meta_dict)

    def to_file(self) -> None:
        """Write metadata to YAML file
        """
        with open(self._out_file, "w") as fh:
            yaml.dump(self.metadata.dict(exclude_none=True),
                      fh,
                      encoding='utf-8')

    def update_metadata(self, data_dict: dict) -> None:
        """Create a copy of the model and update (no validation occurs)

        Arguments:
            data_dict -- Dict of data to populate model
        """
        self._meta_dict.update(data_dict)
        try:
            self.metadata = self.metadata.parse_obj(self._meta_dict)
        except ValidationError as e:
            print(f"Metadata not updated due to the following error:\n {e}\n")

    def __repr__(self) -> str:
        """Representation of metadata.
        """
        return self.as_yaml()

    def as_dict(self) -> dict:
        """Dict repr of metadata

        Returns:
            Dict of metadata
        """
        return self.metadata.dict()

    def as_yaml(self, **kwargs) -> str:
        return yaml.dump(self.metadata.dict(**kwargs))


def metadata_dict_from_gwas_cat(accession_id: str) -> dict:
    """Extract metadat from the GWAS Catalog API

    Arguments:
        accession_id -- GWAS Catalog accession ID

    Returns:
        Metadata dict
    """
    study_url = GWAS_CAT_API_INGEST_STUDIES_URL + accession_id
    study_response = download_with_requests(url=study_url)
    meta_dict = _parse_gwas_api_study_response(study_response,
                                         replace_dict=GWAS_CAT_STUDY_MAPPINGS,
                                         fields_to_split=STUDY_FIELD_TO_SPLIT)
    sample_url = study_url + "/samples"
    sample_response = download_with_requests(url=sample_url, params={"size": 100})
    samples_list = _parse_gwas_api_samples_response(sample_response,
                                                    replace_dict=GWAS_CAT_SAMPLE_MAPPINGS,
                                                    fields_to_split=SAMPLE_FIELD_TO_SPLIT)
    meta_dict['samples'] = samples_list
    return meta_dict


def _parse_gwas_api_study_response(response: bytes,
                                   replace_dict: dict = None,
                                   fields_to_split: tuple = None
                                   ) -> dict:
    """Parse study repsonse from GWAS cat api

    Arguments:
        response -- response bytes

    Keyword Arguments:
        replace_dict -- Header mappings (default: {None})
        fields_to_split -- fields to split (default: {None})

    Returns:
        Dict of metadata
    """
    result_dict = {}
    if response:
        result_dict = json.loads(response.decode())
        if replace_dict:
            result_dict = replace_dictionary_keys(data_dict=result_dict,
                                                  replace_dict=replace_dict)
        if fields_to_split:
            result_dict = split_fields_on_delimiter(data_dict=result_dict,
                                                    fields=fields_to_split)
    return result_dict


def _parse_gwas_api_samples_response(response: bytes,
                                     replace_dict: dict = None,
                                     fields_to_split: tuple = None
                                     ) -> list:
    """Parse the samples response from GWAS cat api

    Arguments:
        response -- responce bytes

    Keyword Arguments:
        replace_dict -- Header mappings (default: {None})
        fields_to_split -- fields to split (default: {None})

    Returns:
        List of samples dicts
    """
    formatted_list = []
    if response:
        result_dict = json.loads(response.decode())
        sample_list = result_dict["_embedded"].get('samples')
        if sample_list:
            for element in sample_list:
                if replace_dict:
                    element = replace_dictionary_keys(data_dict=element,
                                                      replace_dict=replace_dict)
                if fields_to_split:
                    element = split_fields_on_delimiter(data_dict=element,
                                                        fields=fields_to_split)
                formatted_list.append(element)
    return formatted_list


def get_file_metadata(in_file: Path, out_file: str) -> dict:
    """Get file related metadata

    Arguments:
        in_file -- sumstats in file
        outfile -- sumstats out file

    Returns:
        Metadata dict
    """
    meta_dict = {}
    accession_id = parse_accession_id(filename=in_file) 
    meta_dict['gwas_id'] = accession_id
    meta_dict['data_file_name'] = Path(out_file).name
    meta_dict['file_type'] = 'GWAS-SFF v1.0'
    meta_dict['genome_assembly'] = GENOME_ASSEMBLY_MAPPINGS.get(parse_genome_assembly(filename=in_file), 'unknown')
    meta_dict['data_file_md5sum'] = get_md5sum(out_file) if Path(out_file).exists() else None
    meta_dict['date_last_modified'] = date.today()
    meta_dict['gwas_catalog_api'] = GWAS_CAT_API_STUDIES_URL + accession_id
    return meta_dict


def init_metadata_from_file(filename: Path, metadata_infile: Path = None) -> Union[SumStatsMetadata, None]:
    m_in = metadata_infile if metadata_infile else filename.with_suffix(filename.suffix + "-meta.yaml")
    if m_in.exists():
        ssm = MetadataClient(in_file=m_in)
        ssm.from_file()
        return ssm
    else:
        return None