
GWAS_CAT_API_STUDIES_URL = "https://www.ebi.ac.uk/gwas/rest/api/studies/"

GWAS_CAT_API_INGEST_STUDIES_URL = "https://wwwdev.ebi.ac.uk/gwas/ingest/api/v2/studies/"

GWAS_CAT_STUDY_MAPPINGS = {
    'genotyping_technology': 'genotyping_technology',
    'traitDescription': 'trait_description',
    'effect_allele_frequency_lower_limit': 'minor_allele_freq_lower_limit',
    'minor_allele_frequency_lower_limit': 'minor_allele_freq_lower_limit',
    'summary_statistics_assembly': 'genome_assembly',
    'analysisSoftware': 'analysis_software',
    'imputationPanel': 'imputation_panel',
    'imputationSoftware': 'imputation_software',
    'adjustedCovariates': 'adjusted_covariates',
    'ontologyMapping': 'ontology_mapping',
    'readme_file': 'author_notes',
    'readme_text': 'author_notes',
    'coordinateSystem': 'coordinate_system',
    'sex': 'sex'
    }

GWAS_CAT_SAMPLE_MAPPINGS = {
    'size': 'sample_size',
    'ancestry': 'sample_ancestry',
    'ancestryMethod': 'ancestry_method',
    'caseControlStudy': 'case_control_study',
    'caseCount': 'case_count',
    'controlCount': 'control_count'
}

GENOME_ASSEMBLY_MAPPINGS = {
    '36': 'GRCh36',
    '37': 'GRCh37',
    '38': 'GRCh38'
    }

STUDY_FIELD_TO_SPLIT = ('genotyping_technology', 'trait_description', 'ontology_mapping', 'adjusted_covariates')

SAMPLE_FIELD_TO_SPLIT = ('ancestry_method', 'sample_ancestry')

