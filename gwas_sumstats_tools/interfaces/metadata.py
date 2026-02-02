import yaml
import json
from typing import Optional, Union
from datetime import date
from pathlib import Path
import ruamel.yaml

from pydantic import ValidationError
from gwas_sumstats_tools.config import (REST_API_STUDIES_URL,
                                        REST_API_STUDY_MAPPINGS,
                                        REST_API_SAMPLE_MAPPINGS,
                                        INGEST_API_STUDIES_URL,
                                        INGEST_API_STUDY_MAPPINGS,
                                        INGEST_API_SAMPLE_MAPPINGS, 
                                        STUDY_FIELD_TO_SPLIT,
                                        SAMPLE_FIELD_TO_SPLIT,
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
    def __init__(
        self, 
        meta_dict: Optional[dict] = None, 
        in_file: Optional[Path] = None, 
        out_file: Optional[Path] = None
    ) -> None:
        """
        SumStats Metadata client

        Keyword Arguments:
            meta_dict -- Dict of metadata (default: None)
            in_file -- Input metadata YAML file (default: None)
            out_file -- Output metadata YAML file (default: None)
        """
        self.metadata = SumStatsMetadata.construct()
        self._meta_dict = meta_dict if meta_dict else {}
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
) -> dict:
    """Extract metadat from the GWAS Catalog API

    Arguments:
        accession_id(str): GWAS Catalog accession ID
        is_bypass_rest_api(bool, optional): A flag indicating whether the request comes from the sumstats
            service. If True, the function bypasses querying the REST API for additional study metadata.
            Defaults to False, which means the REST API response will be included in the metadata dict.

    Returns:
        Metadata dict
    """
    meta_dict = {}
    sample_list = []
    
    # Each step is not rest or ingest, but rest api first and ingest api provide more details it is available.
    # if sandbox, then update URL_API_INGEST in config
    ingest_study_url = INGEST_API_STUDIES_URL + accession_id
    ingest_sample_url = ingest_study_url + "/samples"
    rest_study_url = REST_API_STUDIES_URL + accession_id
    rest_ancestry_url =  rest_study_url + "/ancestries"

    # Old studies get 404 from Ingest API,
    # e.g. 
    # https://www.ebi.ac.uk/gwas/ingest/api/v2/studies/GCST008396, GCST90086118, GCST002047 - single ancestry

    # Try rest api firstly: evey study should have rest api entry
    # genotyping_technology, trait_description and ontology_mapping is available at here
    if not is_bypass_rest_api:
        rest_study_response = download_with_requests(url=rest_study_url)
        if rest_study_response:  # Add this check
            try:
                print(f"{rest_study_url} returned 200")
                rest_study_dict = _parse_gwas_rest_study_response(
                    rest_study_response,
                    replace_dict=REST_API_STUDY_MAPPINGS,
                    fields_to_split=STUDY_FIELD_TO_SPLIT,
                )
                meta_dict.update(rest_study_dict)
            except Exception as e:
                print(f"Error processing REST API response: {e}")
            pass
   
    ingest_study_response = download_with_requests(url=ingest_study_url)
    ingest_sample_response = download_with_requests(url=ingest_sample_url, params={"size": 100})
    # Ingest API as a internal API, will provide more detailed information if available. Overlapped fields will be overwrite by the ingest API info.
    if ingest_study_response:
        try:
            print(f"{ingest_study_url} returned 200")

            ingest_study_dict = _parse_ingest_study_response(
                ingest_study_response,
                replace_dict=INGEST_API_STUDY_MAPPINGS,
                fields_to_split=STUDY_FIELD_TO_SPLIT,
            )
            meta_dict.update(ingest_study_dict)
            
            # Update trait_description (both "trait" and "trait_description" fields exist in some studies)
            d = meta_dict.get("trait_description")
            t = meta_dict.get("trait")
            if not d and t:
                meta_dict.update({"trait_description": [t]})
        except Exception as e:
            print(f"Error processing REST API response: {e}")
            pass
    
    # Sample info is a list and here will be ingest api information firstly, if it does not exist, then fall back on the rest api.
    sample_list = []
    if ingest_sample_response:
        try:
            print(f"{ingest_sample_url} returned 200")
            ingest_samples_list = _parse_gwas_api_samples_response(
                ingest_sample_response,
                replace_dict=INGEST_API_SAMPLE_MAPPINGS,
                fields_to_split=SAMPLE_FIELD_TO_SPLIT,
            )
            sample_list = ingest_samples_list
        except Exception as e:
            print(f"Error processing Ingest Samples API response: {e}")
            pass
    
    # fallback to rest api samples info
    if not sample_list and not is_bypass_rest_api:
        print(f'Sample list from Ingest API: {sample_list}')
        print('Fall back on the REST API.')
        rest_sample_response = download_with_requests(url=rest_ancestry_url)
        if rest_sample_response:
            try:
                print(f"{rest_ancestry_url} returned 200")
                rest_samples_list = _parse_gwas_rest_samples_response(
                    rest_sample_response,
                    replace_dict=REST_API_SAMPLE_MAPPINGS,
                    fields_to_split=SAMPLE_FIELD_TO_SPLIT,
                )
                sample_list = rest_samples_list
            except Exception as e:
                print(
                    f"Sample info of {accession_id} is missing in the REST API and INGEST API: {e}"
                )

    meta_dict["samples"] = sample_list
    return meta_dict

def _parse_ingest_study_response(
    response: bytes,
    replace_dict: dict = None,
    fields_to_split: tuple = None
) -> dict:
    result_dict = {}

    if response:
        result_dict= json.loads(response.decode())

    # handling variable trait: trait_description, trait or diseaseTrait (diseaseTrait is high priority)
    trait_description = result_dict.get("diseaseTrait", {}).get("trait")
    if trait_description:
        result_dict.update({"trait_description": [trait_description]})

    # handling variable EFO mapping:
    efo_mapping =  "|".join(
        d.get("shortForm") 
        for d in result_dict.get("efoTraits", [])
    )
    if efo_mapping:
        result_dict.update({"ontology_mapping": efo_mapping})

    if replace_dict:
        result_dict= replace_dictionary_keys(
            data_dict=result_dict,
            replace_dict=replace_dict,
        )

    if fields_to_split:
        result_dict = split_fields_on_delimiter(
            data_dict=result_dict,
            fields=fields_to_split,
        )
    return result_dict


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
    result_dict["trait_description"]=response_dict['disease_trait']
    # multiple genotyping technology example: GCST005544
    result_dict["genotyping_technology"]="|".join(response_dict['genotyping_technologies'])
    
    # multiple efo trait example: GCST000854
    result_dict["ontology_mapping"]="|".join(d.get("efo_id") for d in response_dict['efo_traits'])

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

def _parse_gwas_rest_samples_response(ancestry_response: bytes = None,
                                      replace_dict: dict = None,
                                      fields_to_split: tuple = None
                                      ) -> list:
    """Parse the samples response from GWAS cat api

    Arguments:
        study_response -- response bytes from rest api v2 study endpoint
        ancestry_response -- response bytes from rest api v2 ancestry endpoint
    Keyword Arguments:
        replace_dict -- Header mappings (default: {None})
        fields_to_split -- fields to split (default: {None})

    Returns:
        List of samples dicts
    """
    formatted_list = []
    ancestry_list = []
    if ancestry_response:
        ancestry_dict = json.loads(ancestry_response.decode())
        ancestry_list = ancestry_dict.get("_embedded", {}).get("ancestries", [])

    sample_list = [x for x in ancestry_list if x.get("type") == "initial"] if ancestry_list else []
    
    if sample_list:
        for element in sample_list:
            element=dict((k,element[k]) for k in REST_API_SAMPLE_MAPPINGS.keys() if k in element)
            element['ancestral_groups']=[x.get('ancestral_group') for x in element['ancestral_groups']]
            
            if replace_dict:
                element=replace_dictionary_keys(data_dict=element,
                                                      replace_dict=replace_dict)
            if fields_to_split:
                element=split_fields_on_delimiter(data_dict=element,
                                                        fields=fields_to_split)
            formatted_list.append(element)

    return formatted_list

def get_file_metadata(in_file: Path, out_file: str, meta_dict: Optional[dict] = None) -> dict:
    """Get file related metadata

    Arguments:
        in_file -- sumstats in file
        outfile -- sumstats out file

    Returns:
        Metadata dict
    """
    meta_dict = meta_dict if meta_dict else {}

    inferred_meta_dict = {}
    inferred_meta_dict['gwas_id'] = parse_accession_id(filename=in_file)
    inferred_meta_dict['data_file_name'] = Path(out_file).name
    inferred_meta_dict['file_type'] = 'GWAS-SSF v1.0'
    inferred_meta_dict['genome_assembly'] = GENOME_ASSEMBLY_MAPPINGS.get(parse_genome_assembly(filename=in_file), 'unknown')
    inferred_meta_dict['data_file_md5sum'] = get_md5sum(out_file) if Path(out_file).exists() else None
    inferred_meta_dict['date_metadata_last_modified'] = date.today()
    inferred_meta_dict['gwas_catalog_api'] = REST_API_STUDIES_URL + parse_accession_id(filename=in_file)
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
