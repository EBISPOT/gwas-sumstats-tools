import pytest
from tests.prep_tests import SSTestFile

from gwas_sumstats_tools.validate import Validator


@pytest.fixture()
def sumstats_file():
    sumstats = SSTestFile()
    yield sumstats
    sumstats.remove()


class TestValidator():
    VALID_LABEL = "GCST1234567.tsv.gz"

    def test_validate_init(self, sumstats_file):
        sumstats_file.filepath = self.VALID_LABEL
        sumstats_file.to_file()
        v = Validator(sumstats_file=self.VALID_LABEL)
        assert v.filename == self.VALID_LABEL
        
    def test_validate_valid_data(self, sumstats_file):
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is True
        
    