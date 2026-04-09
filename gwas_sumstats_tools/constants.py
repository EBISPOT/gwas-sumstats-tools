from typing import Final, Literal

# Field name mappings from Ingest API JSON keys -> internal metadata field names
INGEST_API_STUDY_MAPPINGS: Final[dict[str, str]] = {
    "genotyping_technology": "genotyping_technology",
    "traitDescription": "trait_description",
    "trait": "trait_description",
    "effect_allele_frequency_lower_limit": "minor_allele_freq_lower_limit",
    "minor_allele_frequency_lower_limit": "minor_allele_freq_lower_limit",
    "summary_statistics_assembly": "genome_assembly",
    "analysisSoftware": "analysis_software",
    "imputationPanel": "imputation_panel",
    "imputationSoftware": "imputation_software",
    "adjustedCovariates": "adjusted_covariates",
    "ontologyMapping": "efo_trait",
    "readme_file": "author_notes",
    "readme_text": "author_notes",
    "coordinateSystem": "coordinate_system",
    "sex": "sex",
}

INGEST_API_SAMPLE_MAPPINGS: Final[dict[str, str]] = {
    "size": "sample_size",
    "ancestry_category": "sample_ancestry_category",
    "ancestry": "sample_ancestry",
    "ancestryMethod": "ancestry_method",
    "caseControlStudy": "case_control_study",
    "caseCount": "case_count",
    "controlCount": "control_count",
}

# Field name mappings from REST API JSON keys -> internal metadata field names
REST_API_STUDY_MAPPINGS: Final[dict[str, str]] = {
    "genotyping_technologies": "genotyping_technology",
    "disease_trait": "trait_description",
    "efo_traits": "ontology_mapping",
}

REST_API_SAMPLE_MAPPINGS: Final[dict[str, str]] = {
    "number_of_individuals": "sample_size",
    "ancestral_groups": "sample_ancestry_category",
}

# Genome assembly build number -> GRC assembly name
GenomeAssembly = Literal["GRCh36", "GRCh37", "GRCh38"]
GENOME_ASSEMBLY_MAPPINGS: Final[dict[str, GenomeAssembly]] = {
    "36": "GRCh36",
    "37": "GRCh37",
    "38": "GRCh38",
}

# Fields that may contain pipe-delimited values and should be split into lists
STUDY_FIELD_TO_SPLIT: Final[tuple[str, ...]] = (
    "genotyping_technology",
    "trait_description",
    "ontology_mapping",
    "adjusted_covariates",
    "sample_ancestry_category",
)

SAMPLE_FIELD_TO_SPLIT: Final[tuple[str, ...]] = (
    "ancestry_method",
    "sample_ancestry_category",
    "sample_ancestry",
)
