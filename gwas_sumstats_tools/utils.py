import re
import hashlib
import requests
import logging
from typing import Union
from pathlib import Path
import typer
import petl as etl
from rich import print
from requests.adapters import HTTPAdapter, Retry
import importlib.metadata


logging.basicConfig(level=logging.ERROR, format='(%(levelname)s): %(message)s')
logger = logging.getLogger(__name__)


def get_version() -> str:
    return importlib.metadata.version('gwas-sumstats-tools')


def exit_if_no_data(table: Union[etl.Table, None]) -> None:
    if table is None:
        print("No data in table. Exiting.")
        raise typer.Exit()


def parse_accession_id(filename: Path) -> Union[str, None]:
    """Get accession ID from file path

    Arguments:
        filename -- Input file path 

    Returns:
        GCST or None
    """
    gcst_search = re.search(r"GCST[0-9]+", filename.stem)
    return gcst_search.group() if gcst_search else None


def parse_genome_assembly(filename: Path) -> Union[str, None]:
    """Get genome assembly from file path

    Arguments:
        filename -- Input file path 

    Returns:
        Genome assembly or None
    """
    gcst_search = re.search(r"(build|grch)([0-9]+)", filename.stem, re.IGNORECASE)
    return gcst_search.group(2) if gcst_search else None


def download_with_requests(url,
                           params: dict = None,
                           headers: dict = None) -> Union[bytes, None]:
    """Download content from URL

    Arguments:
        url -- request url
        params -- requests parameters
        headers -- request headers, modified to include cache-control

    Return:
        Content from URL if status code is 200 or None
    """
    if headers is None:
        headers = {}

    headers.update({'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})

    s = requests.Session()
    retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    s.mount(url, HTTPAdapter(max_retries=retries))
    try:
        r = s.get(url, params=params, headers=headers)
        status_code = r.status_code
        if status_code == 200:
            return r.content
        else:
            logger.error(f"{url} returned {status_code} status code")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(e)
        return None


def append_to_path(path: Path, to_add: str) -> Path:
    return path.parent / (path.name + to_add)


def set_metadata_outfile_name(data_outfile: str, metadata_outfile: str) -> str:
    if metadata_outfile is None:
        metadata_outfile = data_outfile + "-meta.yaml"
    return metadata_outfile


def get_md5sum(file: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def header_dict_from_args(args: list) -> dict:
    """Generate a dict from cli args split on ":"

    Arguments:
        args -- cli args list

    Returns:
        Dict of key, values
    """
    header_dict = {}
    for arg in args:
        if ":" not in arg:
            # skip because it's not a metadata mapping
            pass
        else:
            key, value = arg.replace("--", "").split(":")
            header_dict[key] = value
    return header_dict


def metadata_dict_from_args(args: list) -> dict:
    """Generate a dict from cli args split on "="

    Arguments:
        args -- cli args list

    Returns:
        Dict of key, values
    """
    meta_dict = {}
    for arg in args:
        if "=" not in arg:
            # skip because it's not a metadata mapping
            pass
        else:
            key, value = arg.replace("--", "").split("=")
            meta_dict[key] = value
    return meta_dict


def replace_dictionary_keys(data_dict: dict, replace_dict: dict) -> dict:
    """Replace data_dict keys with values from replace_dict

    Arguments:
        data_dict -- dict to replace keys in
        replace_dict -- dict mapping 'find' to 'replace' keys

    Returns:
        dict with keys replaced
    """
    return {replace_dict.get(k, k): v for k, v in data_dict.items()}


def update_dict_if_not_set(data_dict: dict, field: str, value: any) -> dict:
    if data_dict.get(field) is None:
        data_dict[field] = value
    return data_dict


def split_fields_on_delimiter(data_dict: dict,
                              fields: tuple,
                              delimiter: str = "|") -> dict:
    """Split specified fields in dict on delimiter

    Arguments:
        data_dict -- dict to split fields in
        fields -- fields to split

    Keyword Arguments:
        delimiter -- delimiter (default: {"|"})

    Returns:
        data_dict with fields split
    """
    return dict((k, v.split(delimiter))
                if k in fields
                else (k, v)
                for k, v
                in data_dict.items())
