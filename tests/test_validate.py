import pytest
import pathlib
import petl as etl
from tests.prep_tests import SSTestFile, EFFECT_FIELDS
from pandera import DataFrameSchema

from gwas_sumstats_tools.validate import Validator


@pytest.fixture()
def sumstats_file():
    sumstats = SSTestFile()
    yield sumstats
    sumstats.remove()


VALID_LABEL = "GCST1234567.tsv.gz"


def test_validate_init(sumstats_file):
    sumstats_file.filepath = VALID_LABEL
    sumstats_file.to_file()
    v = Validator(sumstats_file=VALID_LABEL)
    assert v.filename == VALID_LABEL


def test_schema(mocker):
    v = Validator(sumstats_file=VALID_LABEL)
    mocker.patch("gwas_sumstats_tools.validate.Validator.effect_field",
                 return_value="beta")
    schema = v.schema().schema()
    assert isinstance(schema, DataFrameSchema)
    assert schema.columns.get('beta')
    assert not schema.columns.get('odds_ratio')


def test_validate(sumstats_file):
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
    assert v.validate() == (True, "Data table is valid.")


def test_write_errors_to_file(sumstats_file):
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
    v.errors_table = etl.fromcolumns([["test"]])
    v.write_errors_to_file()
    assert pathlib.Path(v.filename + ".err.csv.gz").exists()


def test_validate_file_ext(sumstats_file):
    sumstats_file.filepath = "GCST1234567.tsv"
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath)
    assert v._validate_file_ext() == (True, None)
    sumstats_file.filepath = "GCST1234567.txt"
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath)
    assert v._validate_file_ext()[0] is False
    assert isinstance(v._validate_file_ext()[1], str)
    assert v.primary_error_type == "file_ext"
    sumstats_file.filepath = "GCST1234567.csv"
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath)
    assert v._validate_file_ext()[0] is False
    assert isinstance(v._validate_file_ext()[1], str)
    assert v.primary_error_type == "file_ext"


def test_validate_field_order(sumstats_file):
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath)
    assert v._validate_field_order() == (True, None)
    sumstats_file.test_data.move_to_end("variant_id")
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath)
    assert v._validate_field_order() == (True, None)
    sumstats_file.test_data.move_to_end("chromosome")
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath)
    assert v._validate_field_order()[0] is False
    assert isinstance(v._validate_field_order()[1], str)
    assert v.primary_error_type == "field order"


def test_validate_df(sumstats_file):
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath)
    df = v.as_pd_df()
    assert v._validate_df(df) == (True, "Data table is valid.")


def test_minrow_check(sumstats_file):
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=5)
    df = v.as_pd_df()
    assert v._minrow_check(df) == (False, f"The file has fewer than the minimum rows required: {len(df)} < 5.")
    v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
    assert v._minrow_check(df) == (True, None)


def test_evaluate_errors():
    v = Validator(sumstats_file=VALID_LABEL)
    v.errors_table = etl.fromcolumns([["DataFrameSchema"]], header=['schema_context'])
    v._evaluate_errors()
    assert v.primary_error_type == 'headers'


@pytest.mark.filterwarnings("ignore: overflow")
class TestValidator:
    """
    Test the validator with dummy data
    """
    def test_validate_valid_data(self, sumstats_file):
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is True

    def test_validate_good_file_extension(self, sumstats_file):
        sumstats_file.filepath = "GCST1234567.tsv"
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is True

    def test_validate_bad_file_extension(self, sumstats_file):
        sumstats_file.filepath = "GCST1234567.txt"
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "file_ext"
        sumstats_file.filepath = "GCST1234567.csv"
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "file_ext"

    def test_validate_good_field_order(self, sumstats_file):
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is True

    def test_validate_bad_field_order(self, sumstats_file):
        sumstats_file.test_data.move_to_end("chromosome")
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "field order"

    def test_validate_optional_field_order(self, sumstats_file):
        sumstats_file.test_data.move_to_end("variant_id")
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
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
        assert v.errors_table.nrows() == 4
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4,
                      pval_zero=True)
        assert v.validate()[0] is True

    def test_neg_log_pvalue(self, sumstats_file):
        sumstats_file.replace_data("p_value", [10, 2, 3, 4])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 4
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4,
                      pval_neg_log=True)
        assert v.validate()[0] is True

    def test_zero_neg_log_pvalue(self, sumstats_file):
        sumstats_file.replace_data("p_value", [0, 0, 2, 3])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 4
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4,
                      pval_zero=True, pval_neg_log=True)
        assert v.validate()[0] is True

    def test_validate_bad_rsid(self, sumstats_file):
        sumstats_file.replace_data("rsid", [0, 1, "daf", "adf"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 4

    def test_invalid_chromosome(self, sumstats_file):
        sumstats_file.replace_data("chromosome", [0, 26, "CHR1", None])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 5

    def test_invalid_position(self, sumstats_file):
        sumstats_file.replace_data("base_pair_location", [0, "pos", None, -2])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 5

    def test_invalid_effect_allele(self, sumstats_file):
        sumstats_file.replace_data("effect_allele", ["D", "I", "N", None])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 4

    def test_invalid_standard_error(self, sumstats_file):
        sumstats_file.replace_data("standard_error", ["str", None, "a", "b"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 5
    
    def test_invalid_effect_allele_frequency(self, sumstats_file):
        sumstats_file.replace_data("effect_allele_frequency", ["str", None, -1, 1.1])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 4

    def test_pvalue_scientific_notation(self, sumstats_file):
        sumstats_file.replace_data("p_value", ["1E-90000", "20e-2", "1e-90000", "200e-100"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is True

    def test_invalid_pvalue(self, sumstats_file):
        sumstats_file.replace_data("p_value", ["1E+90000", 2, -1, None])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 6

    def test_invalid_rsid(self, sumstats_file):
        sumstats_file.replace_data("rsid", ["str", None, 1, "123"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 3

    def test_invalid_ref(self, sumstats_file):
        sumstats_file.replace_data("ref_allele", ["str", None, 1, "A"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 3

    def test_invalid_ci(self, sumstats_file):
        sumstats_file.replace_data("ci_upper", ["str", None, 1, "A"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 3

    def test_invalid_info(self, sumstats_file):
        sumstats_file.replace_data("info", ["a", None, 1.1, -1])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 3
        
    def test_invalid_n(self, sumstats_file):
        sumstats_file.replace_data("n", ["a", None, 1.1, -1])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 5
