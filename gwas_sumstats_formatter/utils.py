from pathlib import Path
import re


def parse_accession_id(filename: Path) -> str:
    gcst_search = re.search(r"GCST[0-9]+", filename.stem)
    return gcst_search.group()