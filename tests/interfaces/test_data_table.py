import gzip
import os

import pytest

from gwas_sumstats_tools.interfaces.data_table import SumStatsTable
from tests.prep_tests import TEST_DIR, SSTestFile


@pytest.fixture()
def sumstats_file():
    sumstats = SSTestFile()
    yield sumstats
    sumstats.remove()


def test_from_file_raises_on_misnamed_gzip_content(sumstats_file):
    """A file whose content is gzip-compressed but whose name doesn't
    carry a .gz extension (or vice versa) should raise a clear error,
    not silently return None and crash later as a NoneType error.
    """
    sumstats_file.to_file()
    gzip_path = sumstats_file.filepath
    with open(sumstats_file.filepath, "rb") as f:
        raw_bytes = f.read()
    misnamed_path = os.path.join(TEST_DIR, "misnamed_gzip.tsv")
    with gzip.open(gzip_path + ".tmp.gz", "wb") as f:
        f.write(raw_bytes)
    os.replace(gzip_path + ".tmp.gz", misnamed_path)

    with pytest.raises(ValueError, match="Could not read"):
        SumStatsTable(misnamed_path)


def test_get_field_label_from_index(mocker):
    mocker.patch(
        "gwas_sumstats_tools.interfaces.data_table.SumStatsTable.from_file",
        return_value=None,
    )
    headers = ("a", "b", "c", "d", "e", "f")
    mocker.patch(
        "gwas_sumstats_tools.interfaces.data_table.SumStatsTable.header",
        return_value=headers,
    )
    assert SumStatsTable("test.tsv")._get_field_label_from_index(4) == headers[4]
    headers = ("a", "b", "c", "d")
    mocker.patch(
        "gwas_sumstats_tools.interfaces.data_table.SumStatsTable.header",
        return_value=headers,
    )
    assert SumStatsTable("test.tsv")._get_field_label_from_index(4) is None


def test_effect_field(mocker):
    mocker.patch(
        "gwas_sumstats_tools.interfaces.data_table.SumStatsTable.from_file",
        return_value=None,
    )
    headers = ("a", "b", "c", "d", "e", "f")
    mocker.patch(
        "gwas_sumstats_tools.interfaces.data_table.SumStatsTable.header",
        return_value=headers,
    )
    assert SumStatsTable("test.tsv").effect_field() == headers[4]


def test_p_value_field(mocker):
    mocker.patch(
        "gwas_sumstats_tools.interfaces.data_table.SumStatsTable.from_file",
        return_value=None,
    )
    headers = ("a", "b", "c", "d", "e", "f", "g", "p_value")
    mocker.patch(
        "gwas_sumstats_tools.interfaces.data_table.SumStatsTable.header",
        return_value=headers,
    )
    assert SumStatsTable("test.tsv").p_value_field() == "p_value"
    headers = ("a", "b", "c", "d", "e", "f", "neg_log_10_p_value")
    mocker.patch(
        "gwas_sumstats_tools.interfaces.data_table.SumStatsTable.header",
        return_value=headers,
    )
    assert SumStatsTable("test.tsv").p_value_field() == "neg_log_10_p_value"
