"""
A helper class for creating summary statistics
data files for the tests.
"""

import os
import shutil
from pathlib import Path
from typing import Union
import yaml
from collections import OrderedDict
import pandas as pd


TEST_DIR = "./tests/data"
TEST_DATA = OrderedDict({
    "chromosome": ["1", "1", "2", "25"],
    "base_pair_location": [1118275, 1120431, 49129966, 48480252],
    "effect_allele": ["A", "CCG", "C", "T"],
    "other_allele": ["G", "C", "T", "TTT"],
    "beta": [0.92090, -1.01440, 0.97385, 0.99302],
    "standard_error": [0.92090, 1.01440, 0.97385, 0.99302],
    "effect_allele_frequency": [3.926e-01, 4.900E-03, 0.0023, 7.000e-04],
    "p_value": [0.4865, 3.7899998e-15, 0.05986, 3.7899998E-15],
    "variant_id": ["1_1118275_G_A", "1_1120431_C_CCG", "2_49129966_T_C", "25_48480252_TTT_T"],
    "rsid": ["rs185339560", "rs11250701", "rs12345", "rs7085086"],
    "ref_allele": ["EA", "OA", "EA", "OA"],
    "ci_upper": [0.92090, 0.01440, 0.97385, 0.99302],
    "ci_lower": [0.92090, 0.01440, 0.97385, 0.99302],
    "info": [0.92090, 0.01440, 0.97385, 0.99302],
    "n": [123, 234, 345, 456]
})

EFFECT_FIELDS = {"odds_ratio": [0.92090, 1.01440, 0.97385, 0.99302],
                 "hazard_ratio": [0.92090, 1.01440, 0.97385, 0.99302]}

TEST_METADATA = {
    "genotyping_technology": ["Genome-wide genotyping array"],
    "gwas_id": "GCST90000123",
    "samples": [
        {
            "sample_size": 12345,
            "sample_ancestry": ["European"],
            "ancestry_method": [
                "self-reported",
                "genetically determined"
            ]
            }
    ],
    "trait_description": [
        "breast carcinoma"
    ],
    "minor_allele_freq_lower_limit": 0.001,
    "data_file_name": "0000123.tsv",
    "file_type": "GWAS-SSF v1.0",
    "data_file_md5sum": "32ce41c3dca4cd9f463a0ce7351966fd",
    "is_harmonised": False,
    "is_sorted": False,
    "date_last_modified": "2023-02-09",
    "genome_assembly": "GRCh37",
    "coordinate_system": "1-based",
    "sex": "combined"
}

class SSTestFile:
    def __init__(self,
                 filepath: Path = "test_file.tsv",
                 sep: str = "\t",
                 test_data: Union[OrderedDict, None] = None) -> None:
        self._setup_dir()
        self.filepath = os.path.join(TEST_DIR, filepath)
        self.sep = sep
        self.test_data = OrderedDict(test_data) if test_data else OrderedDict({k:v for k,v in TEST_DATA.items()})

    def to_file(self) -> None:
        df = pd.DataFrame.from_dict(self.test_data)
        df.to_csv(self.filepath, sep=self.sep, index=False, mode='w')

    def remove(self) -> None:
        shutil.rmtree(TEST_DIR)

    def _setup_dir(self) -> None:
        os.makedirs(TEST_DIR, exist_ok=True)

    def replace_data(self,
                     header: str,
                     data_to: list) -> OrderedDict:

        self.test_data = OrderedDict((header, data_to)
                                     if k == header
                                     else (k, v)
                                     for k, v in self.test_data.items())
        return self.test_data

    def replace_header_and_data(self,
                                data_to: list,
                                header_from: str,
                                header_to: str) -> OrderedDict:
        self.test_data = OrderedDict((header_to, data_to)
                                     if k == header_from
                                     else (k, v)
                                     for k, v in self.test_data.items())
        return self.test_data

    def replace_header(self,
                       header_from: str,
                       header_to: str) -> OrderedDict:
        self.test_data = OrderedDict((header_to if k == header_from else k, v)
                                     for k, v in self.test_data.items())
        return self.test_data


class MetaTestFile:
    def __init__(self,
                 filepath: Path = "test_file.tsv-meta.yaml"):
        self._setup_dir()
        self.filepath = os.path.join(TEST_DIR, filepath)
        self.test_data = TEST_METADATA

    def to_file(self) -> None:
        with open(self.filepath, "w") as f:
            yaml.dump(self.test_data, f)

    def remove(self) -> None:
        shutil.rmtree(TEST_DIR)

    def _setup_dir(self) -> None:
        os.makedirs(TEST_DIR, exist_ok=True)
