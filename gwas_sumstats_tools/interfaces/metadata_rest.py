import yaml
import json
from typing import Union
from datetime import date
from pathlib import Path
from collections import OrderedDict


import sys
sys.path.insert(0, '..')

from pydantic import ValidationError
from config import (GWAS_CAT_API_STUDIES_URL,
                                        GWAS_CAT_API_INGEST_STUDIES_URL,
                                        GWAS_CAT_STUDY_MAPPINGS,
                                        REST_GWAS_CAT_STUDY_MAPPINGS,
                                        STUDY_FIELD_TO_SPLIT,
                                        SAMPLE_FIELD_TO_SPLIT,
                                        GWAS_CAT_SAMPLE_MAPPINGS,
                                        REST_GWAS_CAT_SAMPLE_MAPPINGS,
                                        GENOME_ASSEMBLY_MAPPINGS)
from utils import (download_with_requests,
                                       parse_accession_id,
                                       parse_genome_assembly,
                                       get_md5sum,
                                       replace_dictionary_keys,
                                       split_fields_on_delimiter,
                                       update_dict_if_not_set)
from schema.metadata import SumStatsMetadata

from metadata import *

def metadata_dict_from_gwas_cat_rest(accession_id: str) -> dict:
    '''Extract metadat from the GWAS Catalog REST API

    Arguments:
        accession_id -- GWAS Catalog accession ID

    Returns:
        Metadata dict
    '''
    meta_dict={}
    url = GWAS_CAT_API_STUDIES_URL + accession_id
    response = download_with_requests(url=url)
    if response:
        response_dict = json.loads(response.decode())
        # study
        meta_dict["trait_description"]=response_dict['diseaseTrait'].get('trait')
        meta_dict["genotypingTechnologies"]=[d.get("genotypingTechnology") for d in response_dict['genotypingTechnologies']]
        #case_control
        if ("case" in response_dict['initialSampleSize'] ) and ("control" in response_dict['initialSampleSize']):
            meta_dict["case_control_study"]="true"
        # extract EFO
        efo_url=response_dict['_links']['efoTraits']['href']
        efo_response =download_with_requests(url=efo_url)
        if efo_response:
            efo_info=json.loads(efo_response.decode())['_embedded']['efoTraits']
            meta_dict["ontology_mapping"]=[d.get("shortForm") for d in efo_info]
        
        # samples
        formatted_list = []
        ancestry=response_dict['ancestries']
        sample_list=[x for x in ancestry if x.get('type') == 'initial']
        for element in sample_list:
            element=dict((k,element[k]) for k in REST_GWAS_CAT_SAMPLE_MAPPINGS.keys() if k in element)
            element['ancestralGroups']=[x.get('ancestralGroup') for x in element['ancestralGroups']]
            element=replace_dictionary_keys(element,REST_GWAS_CAT_SAMPLE_MAPPINGS)
            element=split_fields_on_delimiter(element,REST_GWAS_CAT_SAMPLE_MAPPINGS)
            formatted_list.append(element)
    
    meta_dict['samples'] = formatted_list
    return meta_dict
