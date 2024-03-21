import os


def _env_variable_else(env_var_name: str, default: str) -> str:
    """Get an environment variable

    Arguments:
        env_var_name -- variable name
        default -- default value

    Returns:
        value of environment variable
    """
    value = os.environ.get(env_var_name)
    return value if value else default


GWAS_CAT_API_STUDIES_URL = _env_variable_else(
    "GWAS_CAT_API_STUDIES_URL", "https://www.ebi.ac.uk/gwas/rest/api/studies/"
)

GWAS_CAT_API_INGEST_STUDIES_URL = _env_variable_else(
    "GWAS_CAT_API_INGEST_STUDIES_URL",
    "https://www.ebi.ac.uk/gwas/ingest/api/v2/studies/",
)

GWAS_CAT_API_INGEST_STUDIES_URL_SANDBOX = _env_variable_else(
    "GWAS_CAT_API_INGEST_STUDIES_URL_SANDBOX",
    "https://wwwdev.ebi.ac.uk/gwas/ingest/api/v2/studies/",
)

GWAS_CAT_STUDY_MAPPINGS = {
    "genotyping_technology": "genotyping_technology",
    "traitDescription": "trait_description",
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

REST_GWAS_CAT_STUDY_MAPPINGS = {
    "genotypingTechnologies": "genotyping_technology",
    "diseaseTrait": "trait_description",
    "shortForm": "ontology_mapping",
    "initialSampleSize": "case_control_study",
}

GWAS_CAT_SAMPLE_MAPPINGS = {
    "size": "sample_size",
    "ancestry_category": "sample_ancestry_category",
    "ancestry": "sample_ancestry", 
    "ancestryMethod": "ancestry_method",
    "caseControlStudy": "case_control_study",
    "caseCount": "case_count",
    "controlCount": "control_count",
}

REST_GWAS_CAT_SAMPLE_MAPPINGS = {
    "numberOfIndividuals": "sample_size",
    "ancestralGroups": "sample_ancestry_category",
}

GENOME_ASSEMBLY_MAPPINGS = {"36": "GRCh36", "37": "GRCh37", "38": "GRCh38"}


STUDY_FIELD_TO_SPLIT = (
    "genotyping_technology",
    "trait_description",
    "ontology_mapping",
    "adjusted_covariates",
)


SAMPLE_FIELD_TO_SPLIT = ("ancestry_method", "sample_ancestry_category","sample_ancestry")