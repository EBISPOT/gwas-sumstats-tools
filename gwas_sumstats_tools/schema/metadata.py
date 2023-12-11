"""
A pydantic (https://docs.pydantic.dev/) schema that can be 
used by python projects for defining the metadata model.
"""

from pydantic import (BaseModel,
                      constr)
from datetime import date
from typing import List, Optional
from enum import Enum
"""
Enums
"""


class SexEnum(str, Enum):
    male = 'M'
    female = 'F'
    combined = 'combined'
    unknown='NR'


class CoordinateSystemEnum(str, Enum):
    zero = '0-based'
    one = '1-based'


"""
Models
"""


class SampleMetadata(BaseModel):
    sample_ancestry_category: List[str] = None
    sample_ancestry: List[str] = None
    sample_size: int = None
    ancestry_method: Optional[List[str]] = None
    case_control_study: Optional[bool] = None
    case_count: Optional[int] = None
    control_count: Optional[int] = None


class SumStatsMetadata(BaseModel):
    # Study meta-data
    gwas_id: Optional[constr(regex=r'^GCST\d+$')] = None
    author_notes: Optional[str] = None
    gwas_catalog_api: Optional[str] = None
    date_metadata_last_modified: date = None
    # Trait Information
    trait_description: List[str] = None
    ontology_mapping: Optional[List[str]] = None
    # Genotyping Information
    genome_assembly: str = None
    coordinate_system: CoordinateSystemEnum = None
    genotyping_technology: List[str] = None
    imputation_panel: Optional[str] = None
    imputation_software: Optional[str] = None
    # Sample Information
    samples: List[SampleMetadata] = None
    sex: Optional[SexEnum] = None
    # Summary Statistic information:
    data_file_name: str = None
    file_type: str = None
    data_file_md5sum: str = None
    analysis_software: Optional[str] = None
    adjusted_covariates: Optional[List[str]] = None
    minor_allele_freq_lower_limit: Optional[float] = None
    # Harmonization status
    is_harmonised: Optional[bool] = False
    is_sorted: Optional[bool] = False
    harmonisation_reference: Optional[str] = None
    
    class Config:
        title = 'GWAS Summary Statistics metadata schema'
        use_enum_values = True