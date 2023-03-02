from typing import Union
from pathlib import Path
import pandas as pd
import petl as etl
from pandera import DataFrameSchema, errors

from gwas_sumstats_tools.schema.data_table import SumStatsSchema
from gwas_sumstats_tools.interfaces.data_table import SumStatsTable
from gwas_sumstats_tools.interfaces.metadata import init_metadata_from_file


class Validator(SumStatsTable):
    def __init__(self,
                 sumstats_file: Path,
                 pval_zero: bool = False,
                 pval_neg_log: bool = False,
                 minimum_rows: int = 100_000,
                 sample_size: int = 100_000,
                 **kwargs) -> None:
        super().__init__(sumstats_file=sumstats_file)
        self.pval_zero = pval_zero
        self.pval_neg_log = pval_neg_log
        self.errors_table = None
        self.minimum_rows = minimum_rows
        self.sample_size = sample_size
        self.primary_error_type = None
        self.valid = None

    def schema(self) -> DataFrameSchema:
        effect_field = self.effect_field() if self.effect_field() is not None else 'beta'
        schema = SumStatsSchema(effect_field=effect_field,
                                pval_zero=self.pval_zero,
                                pval_neg_log=self.pval_neg_log).schema()
        return schema

    def validate(self) -> tuple[bool, str]:
        """Validate sumstats data.
        First validate a sample of 100,000 records,
        if this sample is valid, validate the rest of
        the data.

        Returns:
            Validation status, message
        """
        self.valid, message = self._validate_file_ext()
        if self.valid:
            nrows = max(self.sample_size, self.minimum_rows)
            sample_df = self.as_pd_df(nrows=nrows)
            self.valid, message = self._minrow_check(df=sample_df)
        if self.valid:
            self.valid, message = self._validate_df(sample_df,
                                                    message=f"Validated the first {nrows} rows.")
        if self.valid:
            full_df = self.as_pd_df()
            self.valid, message = self._validate_df(full_df)
        self._evaluate_errors()
        return self.valid, message

    def write_errors_to_file(self) -> None:
        """Write the error df to a CSV file
        """
        errors_out = self.filename + ".err.csv.gz"
        self.errors_table.tocsv(errors_out)

    def _validate_file_ext(self) -> tuple[bool, Union[str, None]]:
        file_ext = "".join(Path(self.filename).suffixes)
        valid = file_ext in SumStatsSchema.FILE_EXTENSIONS
        if not valid:
            self.primary_error_type = "file_ext"
            return valid, (f"Extension, '{file_ext}', "
                           f"not in valid set: {SumStatsSchema.FILE_EXTENSIONS}.")
        return valid, None

    def _validate_df(self,
                     dataframe: pd.DataFrame,
                     message: str = "Data table is invalid") -> tuple[bool, str]:
        """Validate a pandas dataframe of specified size
        using Pandera.

        Keyword Arguments:
            sample_size -- Number of rows (default: {None})
            message -- Custom error message (default: {"Errors were found in data"})

        Returns:
            Validation status, message
        """
        try:
            self.schema().validate(dataframe, lazy=True)
            valid = True
            message = "Data table is valid."
            self.errors_table = None
            self.primary_error_type = None
        except errors.SchemaErrors as err:
            self.errors_table = etl.fromdataframe(err.failure_cases) if len(err.failure_cases) > 0 else None
            valid = False
        return valid, message

    def _minrow_check(self, df: pd.DataFrame) -> tuple[bool, Union[str, None]]:
        """Min row check

        Arguments:
            df -- dataframe

        Returns:
            Valid status, message
        """
        if len(df) < self.minimum_rows:
            message = ("The file has fewer than the minimum rows required: "
                       f"{len(df)} < {self.minimum_rows}.")
            self.primary_error_type = "minrows"
            return False, message
        return True, None

    def _evaluate_errors(self) -> None:
        """Evaluate the error df and summarise in 
        the primary_error_types dict

        Returns:
            Update error types dict
        """

        if self.errors_table:
            if 'DataFrameSchema' in self.errors_table['schema_context']:
                self.primary_error_type = 'headers' 
            elif 'Column' in self.errors_table['schema_context']:
                self.primary_error_type = 'data'


def validate(filename: Path,
             errors_file: bool = False,
             pval_zero: bool = False,
             pval_neg_log: bool = False,
             minimum_rows: int = 100_000,
             infer_from_metadata: bool = False) -> tuple[bool,
                                                         str,
                                                         Union[etl.Table, None],
                                                         Union[str, None]
                                                         ]:
    """Validate driver function

    Arguments:
        filename -- Sumstats file path

    Keyword Arguments:
        errors_file -- create error file csv (default: {False})
        pval_zero -- allow pvalues of zero (default: {False})
        pval_neg_log -- pvalues validated as -log10 (default: {False})
        minimum_rows -- set minimum rows allowable (default: {100_000})
        infer_from_metadata -- infer validation options from metadata (default: {False})

    Returns:
        Valid status: bool, message: str, error preview: etl.Table|none, error type: str|None
    """
    error_preview = None
    primary_error_type = None
    if infer_from_metadata:
        ssm = init_metadata_from_file(filename=filename)
        if ssm:
            if pval_zero is False:
                pval_zero = True if ssm.as_dict().get('analysisSoftware') is not None else False
            if pval_neg_log is False:
                pval_neg_log = ssm.as_dict().get('pvalueIsNegLog10') if True else False
        else:
            print("Cannot infer options from metadata file, because metadata file cannot be found.")
    validator = Validator(pval_zero=pval_zero,
                          pval_neg_log=pval_neg_log,
                          minimum_rows=minimum_rows,
                          sumstats_file=filename)
    valid, message = validator.validate()
    if not valid:
        if validator.errors_table:
            error_preview = validator.errors_table.head(10)
        if errors_file and validator.errors_table:
            message += f"\n[green]Writing errors --> {filename}.err.csv.gz[/green]"
            validator.write_errors_to_file()
        primary_error_type = validator.primary_error_type
    return valid, message, error_preview, primary_error_type
