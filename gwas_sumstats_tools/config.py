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


# These URLs are runtime-configurable to support sandbox/dev environments.
# All static field mappings live in constants.py instead.
REST_API_STUDIES_URL = _env_variable_else(
    "REST_API_STUDIES_URL", "https://www.ebi.ac.uk/gwas/rest/api/v2/studies/"
)

INGEST_API_STUDIES_URL = _env_variable_else(
    "INGEST_API_STUDIES_URL",
    "https://www.ebi.ac.uk/gwas/ingest/api/v2/studies/",
    # if sandbox, then use
    # "https://wwwdev.ebi.ac.uk/gwas/ingest/api/v2/studies/",
)