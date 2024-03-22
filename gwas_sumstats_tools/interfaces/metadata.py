import yaml
import json
from typing import Union
from datetime import date
from pathlib import Path
import ruamel.yaml

from pydantic import ValidationError
from gwas_sumstats_tools.config import (GWAS_CAT_API_STUDIES_URL,
                                        GWAS_CAT_API_INGEST_STUDIES_URL,
                                        GWAS_CAT_API_INGEST_STUDIES_URL_SANDBOX,
                                        GWAS_CAT_STUDY_MAPPINGS,
                                        REST_GWAS_CAT_STUDY_MAPPINGS,
                                        STUDY_FIELD_TO_SPLIT,
                                        SAMPLE_FIELD_TO_SPLIT,
                                        GWAS_CAT_SAMPLE_MAPPINGS,
                                        REST_GWAS_CAT_SAMPLE_MAPPINGS,
                                        GENOME_ASSEMBLY_MAPPINGS)
from gwas_sumstats_tools.utils import (download_with_requests,
                                       parse_accession_id,
                                       parse_genome_assembly,
                                       get_md5sum,
                                       replace_dictionary_keys,
                                       split_fields_on_delimiter,
                                       update_dict_if_not_set)
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
        if self._in_file is None:
            return None
        with open(self._in_file, "r") as fh:
            self._meta_dict = yaml.safe_load(fh)
            self.update_metadata(self._meta_dict)

    def to_file(self) -> None:
        """Write metadata to YAML file
        """
        yaml_data =yaml.dump(self.metadata.dict(exclude_none=True), default_flow_style=False,sort_keys=False)
        yaml_yaml=ruamel.yaml.YAML().load(str(yaml_data))
        yaml_yaml.yaml_set_start_comment("Study meta-data")
        yaml_yaml.yaml_set_comment_before_after_key('trait_description','\nTrait Information')
        yaml_yaml.yaml_set_comment_before_after_key('genome_assembly','\nGenotyping Information')
        yaml_yaml.yaml_set_comment_before_after_key('samples','\nSample Information')
        yaml_yaml.yaml_set_comment_before_after_key('data_file_name','\nSummary Statistic information')
        yaml_yaml.yaml_set_comment_before_after_key('is_harmonised','\nHarmonization status')

        with open(self._out_file, "w") as fh:
            yml = ruamel.yaml.YAML()
            yml.indent(mapping=2, sequence=4, offset=2)
            yml.dump(yaml_yaml,
                      fh)

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
        return yaml.dump(self.metadata.dict(**kwargs),sort_keys=False,default_flow_style=False)
    
    def yscbak(self, key, before=None, indent=0, after=None, after_indent=None):
        """
        expects comment (before/after) to be without `#` and possible have multiple lines
        """
        from ruamel.yaml.error import Mark
        from ruamel.yaml.tokens import CommentToken
        
        def comment_token(s, mark):
            # handle empty lines as having no comment
            return CommentToken(('# ' if s else '') + s + '\n', mark, None)
        
        if after_indent is None:
            after_indent = indent + 2
        if before and before[-1] == '\n':
            before = before[:-1]  # strip final newline if there
        if after and after[-1] == '\n':
            after = after[:-1]  # strip final newline if there
        start_mark = Mark(None, None, None, indent, None, None)
        c = self.ca.items.setdefault(key, [None, [], None, None])
        if before:
            for com in before.split('\n'):
                c[1].append(comment_token(com, start_mark))
        if after:
            start_mark = Mark(None, None, None, after_indent, None, None)
            if c[3] is None:
                c[3] = []
            for com in after.split('\n'):
                c[3].append(comment_token(com, start_mark))
    if not hasattr(ruamel.yaml.comments.CommentedMap,'yaml_set_comment_before_after_key'):
        ruamel.yaml.comments.CommentedMap.yaml_set_comment_before_after_key = yscbak

def metadata_dict_from_gwas_cat(
    accession_id: str, 
    is_bypass_rest_api: bool = False, 
    is_sandbox: bool = False,
) -> dict:
    """Extract metadat from the GWAS Catalog API

    Arguments:
        accession_id(str): GWAS Catalog accession ID
        is_bypass_rest_api(bool, optional): A flag indicating whether the request comes from the sumstats
            service. If True, the function bypasses querying the REST API for additional study metadata.
            Defaults to False, which means the REST API response will be included in the metadata dict.
        is_sandbox(bool, optional): A A flag indicating whether the request comes from the sandbox sumstats
            service.

    Returns:
        Metadata dict
    """
    meta_dict = {}
    sample_list = []
    study_url = GWAS_CAT_API_INGEST_STUDIES_URL + accession_id
    if is_sandbox:
        study_url = GWAS_CAT_API_INGEST_STUDIES_URL_SANDBOX + accession_id
    sample_url = study_url + "/samples"
    rest_url = GWAS_CAT_API_STUDIES_URL + accession_id

    study_response = download_with_requests(url=study_url)
    sample_response = download_with_requests(url=sample_url, params={"size": 100})

    if not is_bypass_rest_api:
        rest_response = download_with_requests(url=rest_url)

        try:
            if rest_response:
                print(f"{rest_url} returned 200")
            rest_dict = _parse_gwas_rest_study_response(
                rest_response,
                replace_dict=GWAS_CAT_STUDY_MAPPINGS,
                fields_to_split=STUDY_FIELD_TO_SPLIT,
            )
            meta_dict.update(rest_dict)
        except Exception as e:
            print(f"Error processing REST API response: {e}")
            pass
    else:
        try:
            rest_dict = _parse_ingest_study_response(
                study_response,
                replace_dict=GWAS_CAT_STUDY_MAPPINGS,
                fields_to_split=STUDY_FIELD_TO_SPLIT,
            )
            print(f"Ingest Study Response ::: {rest_dict=}")
            meta_dict.update(rest_dict)
        except Exception as e:
            print(f"Error processing REST API response: {e}")
            pass

    try:
        ingest_dict = _parse_gwas_api_study_response(
            study_response,
            replace_dict=GWAS_CAT_STUDY_MAPPINGS,
            fields_to_split=STUDY_FIELD_TO_SPLIT,
        )
        meta_dict.update(ingest_dict)

        # Update trait_description
        d = meta_dict.get("trait_description")
        t = meta_dict.get("trait")
        if not d and t:
            meta_dict.update({"trait_description": t})
    except Exception as e:
        print(f"Error processing Ingest API response: {e}")
        pass

    try:
        ingest_samples_list = _parse_gwas_api_samples_response(
            sample_response,
            replace_dict=GWAS_CAT_SAMPLE_MAPPINGS,
            fields_to_split=SAMPLE_FIELD_TO_SPLIT,
        )
        sample_list = ingest_samples_list
    except Exception as e:
        print(f"Error processing Ingest Samples API response: {e}")
        pass

    if not sample_list:
        try:
            rest_samples_list = _parse_gwas_rest_samples_response(
                rest_response,
                replace_dict=GWAS_CAT_SAMPLE_MAPPINGS,
                fields_to_split=SAMPLE_FIELD_TO_SPLIT,
            )
            sample_list = rest_samples_list
        except Exception as e:
            print(
                f"Ample info of {accession_id} is missing in the REST API and INGEST API: {e}"
            )

    meta_dict["samples"] = sample_list
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


def _parse_ingest_study_response(
    response: bytes,
    replace_dict: dict = None,
    fields_to_split: tuple = None
) -> dict:
    response_parsed = {}
    response = json.loads(response.decode())

    # study
    trait_description = response.get("diseaseTrait", {}).get("trait")
    if trait_description:
        response_parsed["trait_description"] = [trait_description]

    # # extract EFO
    # efo_url=response['_links']['efoTraits']['href']
    # efo_response =download_with_requests(url=efo_url)
    # if efo_response:
    #     efo_info=json.loads(efo_response.decode())['_embedded']['efoTraits']
    #     response_parsed["ontology_mapping"]="|".join(d.get("shortForm") for d in efo_info)
    # if replace_dict:
    #     response_parsed = replace_dictionary_keys(data_dict=response_parsed,
    #                                               replace_dict=replace_dict)
    # if fields_to_split:
    #     response_parsed = split_fields_on_delimiter(data_dict=response_parsed,
    #                                                 fields=fields_to_split)
    return response_parsed


def _parse_gwas_rest_study_response(response: bytes,
                                   replace_dict: dict = None,
                                   fields_to_split: tuple = None
                                   ) -> dict:
    """Parse study repsonse from GWAS cat rest api

    Arguments:
        response -- response bytes

    Keyword Arguments:
        replace_dict -- Header mappings (default: {None})
        fields_to_split -- fields to split (default: {None})

    Returns:
        Dict of metadata
    """
    result_dict={}
    response_dict = json.loads(response.decode())
    # study
    result_dict["trait_description"]=response_dict['diseaseTrait'].get('trait')
    result_dict["genotyping_technology"]="|".join(d.get("genotypingTechnology") for d in response_dict['genotypingTechnologies'])
    
    # extract EFO
    efo_url=response_dict['_links']['efoTraits']['href']
    efo_response =download_with_requests(url=efo_url)
    if efo_response:
        efo_info=json.loads(efo_response.decode())['_embedded']['efoTraits']
        result_dict["ontology_mapping"]="|".join(d.get("shortForm") for d in efo_info)
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
        sample = result_dict["_embedded"].get('samples')
        sample_list=[x for x in sample if x.get('stage') == 'discovery']
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

def _parse_gwas_rest_samples_response(response: bytes,
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
    response_dict = json.loads(response.decode())
    #case_control
    sample_dict={}
    if ("case" in response_dict['initialSampleSize'] ) and ("control" in response_dict['initialSampleSize']):
        sample_dict["case_control_study"]="true"
    formatted_list = []
    ancestry=response_dict['ancestries']
    sample_list=[x for x in ancestry if x.get('type') == 'initial']
    if sample_list:
        for element in sample_list:
            element=dict((k,element[k]) for k in REST_GWAS_CAT_SAMPLE_MAPPINGS.keys() if k in element)
            element['ancestralGroups']=[x.get('ancestralGroup') for x in element['ancestralGroups']]
            element.update(sample_dict)
            
            if replace_dict:
                element=replace_dictionary_keys(element,REST_GWAS_CAT_SAMPLE_MAPPINGS)
            if fields_to_split:
                element=split_fields_on_delimiter(element,REST_GWAS_CAT_SAMPLE_MAPPINGS)
            formatted_list.append(element)

    return formatted_list

def get_file_metadata(in_file: Path, out_file: str, meta_dict: dict = {}) -> dict:
    """Get file related metadata

    Arguments:
        in_file -- sumstats in file
        outfile -- sumstats out file

    Returns:
        Metadata dict
    """
    inferred_meta_dict = {}
    inferred_meta_dict['gwas_id'] = parse_accession_id(filename=in_file)
    inferred_meta_dict['data_file_name'] = Path(out_file).name
    inferred_meta_dict['file_type'] = 'GWAS-SSF v1.0'
    inferred_meta_dict['genome_assembly'] = GENOME_ASSEMBLY_MAPPINGS.get(parse_genome_assembly(filename=in_file), 'unknown')
    inferred_meta_dict['data_file_md5sum'] = get_md5sum(out_file) if Path(out_file).exists() else None
    inferred_meta_dict['date_metadata_last_modified'] = date.today()
    inferred_meta_dict['gwas_catalog_api'] = GWAS_CAT_API_STUDIES_URL + parse_accession_id(filename=in_file)
    for field, value in inferred_meta_dict.items():
        update_dict_if_not_set(meta_dict, field, value)
    return meta_dict


def init_metadata_from_file(filename: Path, metadata_infile: Path = None) -> Union[SumStatsMetadata, None]:
    m_in = metadata_infile if metadata_infile else filename.with_suffix(filename.suffix + "-meta.yaml")
    if m_in.exists():
        ssm = MetadataClient(in_file=m_in)
        ssm.from_file()
        return ssm
    else:
        return None
