import pytest

from tests.prep_tests import (SSTestFile,
                              TEST_DATA,
                              MetaTestFile,
                              TEST_METADATA)
from gwas_sumstats_tools.read import Reader, read


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


class TestReader:
    def test_file_header(self, sumstats_file):
        r = Reader()
        assert r.file_header() is None
        r = Reader(sumstats_file=sumstats_file)
        assert r.file_header() == tuple(k for k in TEST_DATA.keys())

    def test_metadata_all(self, meta_file):
        r = Reader()
        assert r.metadata_model() is None
        r = Reader(metadata_file=meta_file)
        metadata = r.metadata_model()
        assert metadata is not None
        assert metadata.gwas_id == TEST_METADATA.get('gwas_id')

    def test_metadata_by_field(self, meta_file):
        r = Reader(metadata_file=meta_file)
        assert r.metadata_dict().get('gwas_id') == TEST_METADATA.get('gwas_id')
        assert r.metadata_dict(include=['gwas_id']) == {'gwas_id': TEST_METADATA.get('gwas_id')}
