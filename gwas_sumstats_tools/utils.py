import re
import hashlib
import requests
import logging
from typing import Union
from pathlib import Path

from requests.adapters import HTTPAdapter, Retry


logging.basicConfig(level=logging.ERROR, format='(%(levelname)s): %(message)s')
logger = logging.getLogger(__name__)


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
    gcst_search = re.search(r"([Build|[GRCh]*)([0-9]+)\.", filename.stem, re.IGNORECASE)
    return gcst_search.group(2) if gcst_search else None


def download_with_requests(url, params=None, headers=None) \
    -> Union[bytes, None]:
    """Download content from URL

    Arguments:
        url -- request url
        params -- requests parameters
        headers -- request headers

    Return:
        Content from URL if status code is 200 or None
    """
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


def set_data_outfile_name(data_infile: Path, data_outfile: str) -> str:
    if data_outfile is None:
        accession_id = parse_accession_id(filename=data_infile)
        if accession_id:
            data_outfile = accession_id + ".tsv.gz"
        else:
            data_outfile = data_infile.stem + "-REFORMED.tsv.gz"
    return data_outfile


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
