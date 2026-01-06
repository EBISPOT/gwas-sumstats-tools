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
    "chromosome": ["1", "1", "2", "25"] + [str(i) for i in range (3,25)],
    "base_pair_location": [1118275, 1120431, 49129966, 48480252] + [135982+i for i in range(1,23)],
    "effect_allele": ["A", "CCG", "C", "T"] + ["A"]*22,
    "other_allele": ["G", "C", "T", "TTT"] + ["G"]*22,
    "beta": [0.92090, -1.01440, 0.97385, 0.99302] + [0.0242319]*22,
    "standard_error": [0.92090, 1.01440, 0.97385, 0.99302] + [0.022358]*22,
    "effect_allele_frequency": [3.926e-01, 4.900E-03, 0.0023, 7.000e-04] + [0.811015 ] *22,
    "p_value": [0.4865, 3.7899998e-15, 0.05986, 3.7899998E-15] + [0.05]*22,
    "variant_id": ["1_1118275_G_A", "1_1120431_C_CCG", "2_49129966_T_C", "25_48480252_TTT_T"] + [f"{chr}_{pos}_A_G" for chr, pos in zip(range(3, 25), range(135983, 135983 + 23))],
    "rsid": ["rs185339560", "rs11250701", "rs12345", "rs7085086"]+[f"rs{i}" for i in range(1,23)],
    "ref_allele": ["EA", "OA", "EA", "OA"] + ["OA"] *22,
    "ci_upper": [0.92090, 0.01440, 0.97385, 0.99302] + [0.9] * 22,
    "ci_lower": [0.92090, 0.01440, 0.97385, 0.99302] + [0.1] * 22,
    "info": [0.92090, 0.01440, 0.97385, 0.99302] + [0.5] * 22,
    "n": [123, 234, 345, 456] + [123] * 22
})

EFFECT_FIELDS = {"odds_ratio": [0.92090, 1.01440, 0.97385, 0.99302] + [0.99301] * 22,
                 "hazard_ratio": [0.92090, 1.01440, 0.97385, 0.99302] + [0.99301] * 22 }

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
    "date_metadata_last_modified": "2023-02-09",
    "genome_assembly": "GRCh37",
    "coordinate_system": "1-based",
    "sex": "combined"
}


class TestFileBase:
    """Test file base class
    """
    def remove(self) -> None:
        shutil.rmtree(TEST_DIR)

    def _setup_dir(self) -> None:
        os.makedirs(TEST_DIR, exist_ok=True)


class SSTestFile(TestFileBase):
    """Class for generating test sumstats data files
    """
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

    def replace_data(self,
                     header: str,
                     data_to: list) -> OrderedDict:

        self.test_data = OrderedDict((header, data_to)
                                     if k == header
                                     else (k, v)
                                     for k, v in self.test_data.items())
        return self.test_data
    
    def replace_value(self,
                      header: str,
                      index: int,
                      value: str) -> OrderedDict:
        if header not in self.test_data:
            raise KeyError(f"Header '{header}' not found in test_data.")

        if not (0 <= index < len(self.test_data[header])):
            raise IndexError(f"Index {index} is out of range for header '{header}'.")
        
        self.test_data[header][index] = value
        return self.test_data
    
    def replace_values(self,
                       header: str,
                       new_values: list) -> OrderedDict:
        
        if header not in self.test_data:
            raise KeyError(f"Header '{header}' not found in data.")
        
        n = len(new_values)  # Determine how many values to replace
        
        # Ensure n does not exceed the length of the original list
        if n > len(self.test_data[header]):
            raise ValueError(f"New values exceed the length of '{header}' list.")
        
        # Replace first n elements
        self.test_data[header] = new_values + self.test_data[header][n:]
        
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


class MetaTestFile(TestFileBase):
    """Class for generating test metadata files
    """
    def __init__(self,
                 filepath: Path = "test_file.tsv-meta.yaml"):
        self._setup_dir()
        self.filepath = os.path.join(TEST_DIR, filepath)
        self.test_data = TEST_METADATA

    def to_file(self) -> None:
        with open(self.filepath, "w") as f:
            yaml.dump(self.test_data, f)
