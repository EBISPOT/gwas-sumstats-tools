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
    sumstats_file.filepath = "GCST1234567.tsv.gz"
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath)
    assert v._validate_file_ext() == (True, None)
    sumstats_file.filepath = "GCST1234567.other.tsv.gz"
    sumstats_file.to_file()
    v = Validator(sumstats_file=sumstats_file.filepath)
    assert v._validate_file_ext() == (True, None)


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
    v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=30)
    df = v.as_pd_df()
    assert v._minrow_check(df) == (False, f"The file has fewer than the minimum rows required: {len(df)} < 30.")
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

    def test_validate_p_value_field_missing(self, sumstats_file):
        sumstats_file.test_data.pop("p_value")
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
        sumstats_file.replace_values("p_value", [0, 0, 0, 0])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        # print(v.errors_table)
        assert v.primary_error_type == "p_val"
        assert v.errors_table.nrows() == 4
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4,
                      pval_zero=True)
        assert v.validate()[0] is True

    def test_neg_log_pvalue(self, sumstats_file):
        sumstats_file.replace_header_and_data(header_from="p_value",
                                              header_to="neg_log_10_p_value",
                                              data_to=[10, 2, 3, 4] + [i for i in range(1,23)])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is True

    def test_zero_neg_log_pvalue(self, sumstats_file):
        sumstats_file.replace_header_and_data(header_from="p_value",
                                              header_to="neg_log_10_p_value",
                                              data_to=[0, 0, 2, 3] + [i for i in range(1,23)])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4,
                      pval_zero=True)
        assert v.validate()[0] is True

    def test_validate_bad_rsid(self, sumstats_file):
        sumstats_file.replace_values("rsid", [0, 1, "daf", "adf"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 4

    def test_invalid_chromosome(self, sumstats_file):
        sumstats_file.replace_values("chromosome", [0, 26, "CHR1", None])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "missing_chromsomes"

    def test_invalid_position(self, sumstats_file):
        sumstats_file.replace_values("base_pair_location", [0, "pos", None, -2])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 5

    def test_invalid_effect_allele(self, sumstats_file):
        sumstats_file.replace_values("effect_allele", ["D", "I", "N", None])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 4

    def test_invalid_standard_error(self, sumstats_file):
        sumstats_file.replace_values("standard_error", ["str", None, "a", "b"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 5
    
    def test_invalid_effect_allele_frequency(self, sumstats_file):
        sumstats_file.replace_values("effect_allele_frequency", ["str", None, -1, 1.1])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 4

    def test_pvalue_scientific_notation(self, sumstats_file):
        sumstats_file.replace_values("p_value", ["1E-90000", "20e-2", "1e-90000", "200e-100"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is True

    def test_invalid_pvalue_data_invalid(self, sumstats_file):
        sumstats_file.replace_values("p_value", [5, 2, -1, None])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 6

    def test_invalid_pvalue_invalid(self, sumstats_file):
        sumstats_file.replace_values("p_value", ["1E+90000", 0, '0', 0.0])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "p_val"
        # print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 4

    def test_invalid_rsid(self, sumstats_file):
        sumstats_file.replace_values("rsid", ["str", None, 1, "123"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 3

    def test_invalid_ref(self, sumstats_file):
        sumstats_file.replace_values("ref_allele", ["str", None, 1, "A"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        assert v.errors_table.nrows() == 3

    def test_invalid_ci(self, sumstats_file):
        sumstats_file.replace_values("ci_upper", ["str", None, 1, "A"])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 3

    def test_invalid_info(self, sumstats_file):
        sumstats_file.replace_values("info", ["a", None, 1.1, -1])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 3
        
    def test_invalid_n(self, sumstats_file):
        sumstats_file.replace_values("n", ["a", None, 1.1, -1])
        sumstats_file.to_file()
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4)
        assert v.validate()[0] is False
        assert v.primary_error_type == "data"
        print(v.errors_table.look(limit=10))
        assert v.errors_table.nrows() == 5
# ---------------- p_value check ---------------------------------------------
    def test_pval_zero_true_1(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 0.2, 0])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # Validate the data
        assert status is True
        assert v.primary_error_type is None

    def test_pval_zero_true_2(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, -3, 0.2])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_true_3(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 5, 0.2])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_true_4(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 1, 0.2])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # Validate the data
        assert status is True
        assert v.primary_error_type is None

    def test_pval_zero_true_5(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 0, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_true_6(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, -3, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_true_7(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 5, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_true_8(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 1, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_true_9(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 0.1, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_true_10(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, "1E+90000", 0.2])
        # sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with pval_zero=True
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # print(v.errors_table)

        # Validate the data
        assert status is False
        assert v.primary_error_type == 'data'

    def test_pval_zero_true_11(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, '#NA', 0.2])
        # sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, pval_zero=True)
        status, message = v.validate()

        # print(v.errors_table)

        # Validate the data
        assert status is False
        assert v.primary_error_type == 'data'

    def test_pval_zero_false_1(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 0.2, 0])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type == 'p_val'

    def test_pval_zero_false_1_2(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 0.00, 0.4])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type == 'p_val'

    def test_pval_zero_false_2(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, -3, 0.2])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_false_3(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 5, 0.2])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_false_4(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 1, 0.2])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is True
        assert v.primary_error_type is None

    def test_pval_zero_false_5(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 0, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'p_val'

    def test_pval_zero_false_6(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, -3, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_false_7(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 5, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_false_8(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 1, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_false_9(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, 0.1, 0.2])
        sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # Validate the data
        assert status is False
        assert v.primary_error_type is 'data'

    def test_pval_zero_false_10(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, "1E+90000", 0.2])
        # sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # print(v.errors_table)

        # Validate the data
        assert status is False
        assert v.primary_error_type == 'data'

    def test_pval_zero_false_11(self, sumstats_file):
        # Set up the data with various p-values, including valid and invalid cases
        sumstats_file.replace_values("p_value", [0.3, 0.1, '#NA', 0.2])
        # sumstats_file.replace_values("rsid", ['rs185339560', 'rs11250701', '.', 'rs7085086'])
        sumstats_file.to_file()

        # Initialize the Validator with 
        v = Validator(sumstats_file=sumstats_file.filepath, minimum_rows=4, )
        status, message = v.validate()

        # print(v.errors_table)

        # Validate the data
        assert status is False
        assert v.primary_error_type == 'data'