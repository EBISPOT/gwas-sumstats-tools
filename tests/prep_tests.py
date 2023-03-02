import os
import shutil
from pathlib import Path
from typing import Union
from collections import OrderedDict
import pandas as pd


class SSTestFile:
    TEST_DIR = "./tests/data"
    TEST_DATA = OrderedDict({
        "chromosome": ["1", "1", "2", "25"],
        "base_pair_location": [1118275, 1120431, 49129966, 48480252],
        "effect_allele": ["A", "CCG", "C", "T"],
        "other_allele": ["G", "C", "T", "TTT"],
        "beta": [0.92090, 1.01440, 0.97385, 0.99302],
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

    def __init__(self,
                 filepath: Path = "test_file.tsv",
                 sep: str = "\t",
                 test_data: Union[OrderedDict, None] = None) -> None:
        self._setup_dir()
        self.filepath = os.path.join(self.TEST_DIR, filepath)
        self.sep = sep
        self.test_data = test_data if test_data else self.TEST_DATA

    def to_file(self) -> None:
        df = pd.DataFrame.from_dict(self.test_data)
        df.to_csv(self.filepath, sep=self.sep, index=False, mode='w')
        
    def remove(self) -> None:
        shutil.rmtree(self.TEST_DIR)
        
    def _setup_dir(self) -> None:
        os.makedirs(self.TEST_DIR, exist_ok=True)
