"""
In [90]: def v(df): 
    ...:     try: 
    ...:         schema.validate(df, lazy=True) 
    ...:     except pa.errors.SchemaErrors as err: 
    ...:         return err.failure_cases 
"""

import pandas as pd
import petl as etl
from pandera import DataFrameSchema, errors

from gwas_sumstats_tools.schema.data_table import SumStatsSchema
from gwas_sumstats_tools.sumstats.data_table import SumStatsTable


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

        valid = self._validate_df(sample_df)
        if len(sample_df) < self.minimum_rows:
            valid = False
            print(f"The file has fewer than {self.minimum_rows}, because of this alone, the file is invalid")
        if not valid:
            print((f"Validated the first {nrows} rows, "
                   "stopping there because errors were found"))
        else:
            full_df = self.as_pd_df()
            self._validate_df(full_df)
        return valid

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
        valid = False
        try:
            self.schema().validate(dataframe, lazy=True)
            valid = True
        except errors.SchemaErrors as err:
            self.errors_table = etl.fromdataframe(err.failure_cases) if len(err.failure_cases) > 0 else None
        return valid
