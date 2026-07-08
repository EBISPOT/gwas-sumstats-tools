from pathlib import Path

import pytest

from gwas_sumstats_tools.format import Formatter
from tests.prep_tests import MetaTestFile, SSTestFile


@pytest.fixture()
def sumstats_file():
    sumstats = SSTestFile()
    sumstats.to_file()
    yield sumstats.filepath
    sumstats.remove()


@pytest.fixture()
def meta_file():
    metafile = MetaTestFile()
    metafile.to_file()
    yield metafile.filepath
    metafile.remove()


class TestFormatter:
    def test_set_data_outfile_name_when_formatting(self, sumstats_file):
        f = Formatter(sumstats_file, format_data=True)
        assert isinstance(f.data_infile, Path)
        assert isinstance(f.data_outfile, Path)
        assert str(f.data_outfile) == str((Path(sumstats_file))) + "-FORMATTED.tsv.gz"

    def test_set_data_outfile_name_when_not_formatting(self, sumstats_file):
        f = Formatter(sumstats_file, format_data=False)
        assert isinstance(f.data_infile, Path)
        assert isinstance(f.data_outfile, Path)

    def test_set_data_outfile_name_when_given_custom_outfile_name(self, sumstats_file):
        f = Formatter(sumstats_file, data_outfile="TEST_OUT", format_data=True)
        assert isinstance(f.data_outfile, Path)
        assert str(f.data_outfile) == "TEST_OUT"
        f = Formatter(sumstats_file, data_outfile="TEST_OUT", format_data=False)
        assert isinstance(f.data_outfile, Path)
        assert str(f.data_outfile) == "TEST_OUT"

    def test_suggest_header_mapping_z_score_alias(self):
        sumstats = SSTestFile()
        try:
            sumstats.replace_header("beta", "zscore")
            sumstats.test_data.pop("standard_error")
            sumstats.to_file()
            f = Formatter(sumstats.filepath)
            assert f.suggest_header_mapping()["zscore"] == "z-score"
        finally:
            sumstats.remove()

    def test_map_header_orders_z_score_without_beta(self):
        sumstats = SSTestFile()
        try:
            sumstats.replace_header("beta", "zscore")
            sumstats.test_data.pop("standard_error")
            sumstats.to_file()
            f = Formatter(sumstats.filepath)
            f.data.rename_headers({"zscore": "z-score"})
            f.data.map_header()
            assert f.data.header()[:7] == (
                "chromosome",
                "base_pair_location",
                "effect_allele",
                "other_allele",
                "z-score",
                "standard_error",
                "effect_allele_frequency",
            )
            assert f.data.header()[7] == "p_value"
            standard_error_index = f.data.header().index("standard_error")
            assert {row[standard_error_index] for row in list(f.data.sumstats)[1:]} == {
                "#NA"
            }
            assert "beta" not in f.data.header()
        finally:
            sumstats.remove()

    def test_map_header_overwrites_z_score_standard_error(self):
        sumstats = SSTestFile()
        try:
            sumstats.replace_header("beta", "zscore")
            sumstats.to_file()
            f = Formatter(sumstats.filepath)
            f.data.rename_headers({"zscore": "z-score"})
            f.data.map_header()
            standard_error_index = f.data.header().index("standard_error")
            assert {row[standard_error_index] for row in list(f.data.sumstats)[1:]} == {
                "#NA"
            }
        finally:
            sumstats.remove()

    def test_map_header_keeps_standard_error_when_beta_present(self):
        # When a real effect field (beta) is present, z-score is just an extra
        # column and the genuine standard_error must be preserved, not blanked.
        sumstats = SSTestFile()
        try:
            n_rows = len(sumstats.test_data["beta"])
            sumstats.test_data["zscore"] = [str(i % 3) for i in range(n_rows)]
            sumstats.to_file()
            f = Formatter(sumstats.filepath)
            f.data.rename_headers({"zscore": "z-score"})
            f.data.map_header()
            header = f.data.header()
            # beta remains the effect field at index 4; z-score appended after.
            assert header[4] == "beta"
            assert "z-score" in header
            assert header.index("z-score") > header.index("standard_error")
            standard_error_index = header.index("standard_error")
            se_values = {row[standard_error_index] for row in list(f.data.sumstats)[1:]}
            assert se_values != {"#NA"}
            assert "#NA" not in se_values
        finally:
            sumstats.remove()

    def test_configured_z_score_format_prints_fallback_warning(self, capsys):
        sumstats = SSTestFile()
        try:
            sumstats.replace_header("beta", "zscore")
            sumstats.test_data.pop("standard_error")
            sumstats.to_file()
            config = {
                "fileConfig": {
                    "outFilePrefix": None,
                    "fieldSeparator": "\t",
                    "naValue": None,
                    "convertNegLog10Pvalue": False,
                    "removeComments": None,
                },
                "columnConfig": {
                    "split": [],
                    "edit": [
                        {
                            "field": "zscore",
                            "rename": "z-score",
                            "find": None,
                            "replace": None,
                            "extract": None,
                        }
                    ],
                },
            }
            f = Formatter(sumstats.filepath, config_dict=config)
            f.test_config()
            captured = capsys.readouterr().out
            assert (
                "WARNING: z-score is accepted only as a fallback effect size"
                in captured
            )
            assert "beta" in captured
            assert "odds ratio (OR)" in captured
            assert "hazard ratio" in captured
        finally:
            sumstats.remove()

    def test_pandas_column_order_keeps_z_score_standard_error_in_standard_position(
        self,
    ):
        ordered = Formatter._pd_column_order(
            [
                "chromosome",
                "base_pair_location",
                "effect_allele",
                "other_allele",
                "z-score",
                "standard_error",
                "effect_allele_frequency",
                "p_value",
            ]
        )
        assert ordered[:7] == [
            "chromosome",
            "base_pair_location",
            "effect_allele",
            "other_allele",
            "z-score",
            "standard_error",
            "effect_allele_frequency",
        ]
        assert ordered[7] == "p_value"
