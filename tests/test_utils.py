from pathlib import Path
from gwas_sumstats_tools.utils import (append_to_path)


def test_append_to_path():
    test_path = Path("./tests/utils_test/test.ext1")
    assert append_to_path(path=test_path, to_add="-ext2.ext3") == Path("./tests/utils_test/test.ext1-ext2.ext3")