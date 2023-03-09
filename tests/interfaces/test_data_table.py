import pytest

from gwas_sumstats_tools.interfaces.data_table import SumStatsTable


@pytest.fixture()
def sumstats_file():
    sumstats = SSTestFile()
    yield sumstats
    sumstats.remove()


def test_get_field_label_from_index(mocker):
    headers = ("a", "b", "c", "d", "e", "f")
    mocker.patch("gwas_sumstats_tools.interfaces.data_table.SumStatsTable.header",
                 return_value=headers)
    assert SumStatsTable("test.tsv")._get_field_label_from_index(4) == headers[4]
    headers = ("a", "b", "c", "d")
    mocker.patch("gwas_sumstats_tools.interfaces.data_table.SumStatsTable.header",
                 return_value=headers)
    assert SumStatsTable("test.tsv")._get_field_label_from_index(4) is None


def test_effect_field(mocker):
    headers = ("a", "b", "c", "d", "e", "f")
    mocker.patch("gwas_sumstats_tools.interfaces.data_table.SumStatsTable.header",
                 return_value=headers)
    assert SumStatsTable("test.tsv").effect_field() == headers[4]


def test_p_value_field(mocker):
    headers = ("a", "b", "c", "d", "e", "f", "g", "h")
    mocker.patch("gwas_sumstats_tools.interfaces.data_table.SumStatsTable.header",
                 return_value=headers)
    assert SumStatsTable("test.tsv").p_value_field() == headers[7]