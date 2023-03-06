import pytest
from tests.prep_tests import SSTestFile, EFFECT_FIELDS

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

    def test_validate_good_file_extension(self, sumstats_file):
        sumstats_file.filepath = "GCST1234567.tsv"
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v._validate_file_ext()[0] is True
        assert v.validate()[0] is True

    def test_validate_bad_file_extension(self, sumstats_file):
        sumstats_file.filepath = "GCST1234567.txt"
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v._validate_file_ext()[0] is False
        assert v.validate()[0] is False
        assert v.primary_error_type == "file_ext"
        sumstats_file.filepath = "GCST1234567.csv"
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v._validate_file_ext()[0] is False
        assert v.validate()[0] is False
        assert v.primary_error_type == "file_ext"

    def test_validate_good_field_order(self, sumstats_file):
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v._validate_field_order()[0] is True
        assert v.validate()[0] is True

    def test_validate_bad_field_order(self, sumstats_file):
        sumstats_file.test_data.move_to_end("chromosome")
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v._validate_field_order()[0] is False
        assert v.validate()[0] is False
        assert v.primary_error_type == "field order"

    def test_validate_optional_field_order(self, sumstats_file):
        sumstats_file.test_data.move_to_end("variant_id")
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v._validate_field_order()[0] is True
        assert v.validate()[0] is True

    def test_validate_odds_ratio_instead_of_beta(self, sumstats_file):
        sumstats_file.replace_header_and_data(EFFECT_FIELDS["odds_ratio"],
                                              "beta",
                                              "odds_ratio")
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v._validate_field_order()[0] is True
        assert v.validate()[0] is True

    def test_validate_hazard_ratio_instead_of_beta(self, sumstats_file):
        sumstats_file.replace_header_and_data(EFFECT_FIELDS["hazard_ratio"],
                                              "beta",
                                              "hazard_ratio")
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v._validate_field_order()[0] is True
        assert v.validate()[0] is True

    def test_validate_mandatory_field_missing(self, sumstats_file):
        sumstats_file.test_data.pop("chromosome")
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "field order"

    def test_validate_optional_field_missing(self, sumstats_file):
        sumstats_file.test_data.pop("rsid")
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is True

    def test_validate_mandatory_field_wrong_name(self, sumstats_file):
        sumstats_file.replace_header("beta", "WRONG_NAME")
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "field order"

    def test_zero_pvalue(self, sumstats_file):
        sumstats_file.replace_data("p_value", [0, 0, 0, 0])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4,
                      pval_zero=True)
        assert v.validate()[0] is True

    def test_neg_log_pvalue(self, sumstats_file):
        sumstats_file.replace_data("p_value", [1, 2, 3, 4])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4,
                      pval_neg_log=True)
        assert v.validate()[0] is True

    def test_zero_neg_log_pvalue(self, sumstats_file):
        sumstats_file.replace_data("p_value", [0, 1, 2, 3])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        v = Validator(sumstats_file=sumstats_file.filepath,minimum_rows=4,
                      pval_zero=True, pval_neg_log=True)
        assert v.validate()[0] is True


#    def test_validate_bad_snp_file_data(self):

#    def test_validate_bad_snp_and_no_pos_file_data(self):

#    def test_validate_bad_chr_file_data(self):

#    def test_validate_bad_chr_and_no_snp_file_data(self):

#
#    def test_validate_bad_bp_file_data(self):

#
#    def test_validate_bad_bp_and_no_snp_file_data(self):
#
#    def test_validate_bad_optional_odds_ratio_file_data(self):

#
#    def test_validate_bad_optional_effect_allele_file_data(self):
#
#    def test_validate_empty_snp_file_data(self):
#
#    def test_validate_empty_snp_no_pos_file_data(self):
#
#    def test_validate_ref_allele_ok(self):
#
#    def test_validate_ref_allele_not_ok(self):
#
#    def test_validate_small_pvalue_file_data(self):
#
#    def test_validate_pvalue_can_be_one(self):
#
#    def test_drop_bad_rows_does_not_drop_good_lines(self):
#
#    def test_drop_bad_rows_drops_bad_lines(self):
#
#    def test_drop_bad_rows_drops_bad_rows_even_with_linelimit(self):