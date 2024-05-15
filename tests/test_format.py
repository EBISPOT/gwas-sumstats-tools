import pytest
from pathlib import Path

from tests.prep_tests import (SSTestFile,
                              TEST_DATA,
                              MetaTestFile,
                              TEST_METADATA)
from gwas_sumstats_tools.format import Formatter


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

    def test_set_metadata_outfile_name(self, sumstats_file):
        f = Formatter(sumstats_file)
        assert isinstance(f.metadata_outfile, Path)
        assert str(f.metadata_outfile) == str((Path(f.data_outfile))) + "-meta.yaml"
        f = Formatter(sumstats_file, metadata_outfile="TEST_OUT")
        assert isinstance(f.metadata_outfile, Path)
        assert str(f.metadata_outfile) == "TEST_OUT"
        
