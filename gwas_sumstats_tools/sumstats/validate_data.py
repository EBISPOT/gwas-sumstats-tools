"""
In [90]: def v(df): 
    ...:     try: 
    ...:         schema.validate(df, lazy=True) 
    ...:     except pa.errors.SchemaErrors as err: 
    ...:         return err.failure_cases 
"""
from pathlib import Path
import pandas as pd
import petl as etl
from pandera import DataFrameSchema, errors

from gwas_sumstats_tools.schema.data_table import SumStatsSchema
from gwas_sumstats_tools.sumstats.data_table import SumStatsTable
from gwas_sumstats_tools.sumstats.metadata import init_metadata_from_file


class DataTableValidator(SumStatsTable):
    def __init__(self,
                 pval_zero: bool = False,
                 pval_neg_log: bool = False,
                 minimum_rows: int = 100_000,
                 sample_size: int = 100_000,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.pval_zero = pval_zero
        self.pval_neg_log = pval_neg_log
        self.errors_table = None
        self.minimum_rows = minimum_rows
        self.sample_size = sample_size
        self.error_types = {
            "file extension": False,
            "headers": False,
            "minrows": False,
            "data": False
        }
        self.valid = None

    def schema(self) -> DataFrameSchema:
        schema = SumStatsSchema(effect_field=self.effect_field(),
                                pval_zero=self.pval_zero,
                                pval_neg_log=self.pval_neg_log).schema()
        return schema

    def validate(self) -> bool:
        """Validate sumstats data.
        First validate a sample of 100,000 records,
        if this sample is valid, validate the rest of
        the data.

        Returns:
            Validation status
        """
        nrows = max(self.sample_size, self.minimum_rows)
        sample_df = self.as_pd_df(nrows=nrows)

        self.valid = self._validate_df(sample_df)
        if len(sample_df) < self.minimum_rows:
            self.valid = False
            self.error_types['minrows'] = True
            print(f"The file has fewer than {self.minimum_rows}, because of this alone, the file is invalid")
        if not self.valid:
            print((f"Validated the first {nrows} rows, "
                   "stopping there because errors were found"))
        else:
            full_df = self.as_pd_df()
            self._validate_df(full_df)
        return self.valid

    def write_errors_to_file(self) -> None:
        """Write the error df to a CSV file
        """
        errors_out = self.filename + ".err.csv.gz"
        self.errors_table.tocsv(errors_out)

    def _validate_df(self, dataframe: pd.DataFrame) -> bool:
        """Validate a pandas dataframe of specified size
        using Pandera.

        Keyword Arguments:
            sample_size -- Number of rows (default: {None})

        Returns:
            Validation status
        """
        try:
            self.schema().validate(dataframe, lazy=True)
            valid = True
        except errors.SchemaErrors as err:
            self.errors_table = etl.fromdataframe(err.failure_cases) if len(err.failure_cases) > 0 else None
            valid = False
        return valid
    
    def _evaluate_errors(self) -> dict:
        """Evaluate the error df and summarise in 
        the error_types dict

        Returns:
            Dict of error types
        """
        pass


def validate(filename: Path,
             errors_file: bool = False,
             pval_zero: bool = False,
             pval_neg_log: bool = False,
             minimum_rows: int = 100_000,
             infer_from_metadata: bool = False) -> bool:
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
        Valid status
    """
    if infer_from_metadata:
        ssm = init_metadata_from_file(filename=filename)
        if pval_zero is False:
            pval_zero = True if ssm.as_dict().get('analysisSoftware') is not None else False
        if pval_neg_log is False:
            pval_neg_log = ssm.as_dict().get('pvalueIsNegLog10') if True else False
    validator = DataTableValidator(pval_zero=pval_zero,
                                   pval_neg_log=pval_neg_log,
                                   minimum_rows=minimum_rows,
                                   sumstats_file=filename)
    valid = validator.validate()
    if valid:
        print("File is valid")
        return True
    else:
        print("File is not valid")
        if validator.errors_table is not None:
            print(validator.errors_table.head(10))
        if errors_file:
            print(f"[green]Writing errors --> {filename}.err.csv.gz[/green]")
            validator.write_errors_to_file()
        return False

