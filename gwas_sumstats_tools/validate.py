from typing import Union
from pathlib import Path
import pandas as pd
import petl as etl
from pandera import errors
from rich import print

from gwas_sumstats_tools.schema.data_table import SumStatsSchema
from gwas_sumstats_tools.interfaces.data_table import SumStatsTable
from gwas_sumstats_tools.interfaces.metadata import init_metadata_from_file


class Validator(SumStatsTable):
    def __init__(self,
                 sumstats_file: Path,
                 pval_zero: bool = False,
                 minimum_rows: int = 100_000,
                 sample_size: int = 100_000,
                 chunksize: int = 1_000_000,
                 **kwargs) -> None:
        super().__init__(sumstats_file=sumstats_file)
        self.pval_zero = pval_zero
        self.errors_table = None
        self.minimum_rows = minimum_rows
        self.sample_size = sample_size
        self.chunksize = chunksize
        self.primary_error_type = None
        self.valid = None

    def schema(self) -> SumStatsSchema:
        effect_field = self.effect_field() if self.effect_field() in \
            SumStatsSchema().EFFECT_FIELD_DEFINITIONS else 'beta'
        p_value_field = self.p_value_field() if self.p_value_field() in \
            SumStatsSchema().PVALUE_FIELD_DEFINITIONS else 'p_value'
        schema = SumStatsSchema(effect_field=effect_field,
                                pval_field=p_value_field,
                                pval_zero=self.pval_zero)
        return schema

    def validate(self) -> tuple[bool, str]:
        """Validate sumstats data.
        First validate a sample of 100,000 records,
        if this sample is valid, validate the rest of
        the data.

        Returns:
            Validation status, message
        """
        print("Validating extension...")
        self.valid, message = self._validate_file_ext()

        if self.valid:
            print("--> [green]Ok[/green]")
            print("Validating column order...")
            self.valid, message = self._validate_field_order()

        if self.valid:
            print("--> [green]Ok[/green]")
            print(f"Validating the chromosomes...")
            self.valid, message = self._validate_chromosomes()
            print(f"    [dim][grey](note: {message})[/grey][/dim]") 
        if self.valid:
            print("--> [green]Ok[/green]")
            nrows = max(self.sample_size, self.minimum_rows)
            print("Validating minimum row count...")
            sample_df = self.as_pd_df(nrows=nrows)
            self.valid, message = self._minrow_check(df=sample_df)
        if self.valid:
            print("--> [green]Ok[/green]")
            print(f"Validating the first {nrows} rows...")
            self.valid, message = self._validate_df(sample_df)
        if self.valid:
            print("--> [green]Ok[/green]")
            print("Validating the rest of the file...")
            try:
                df_iter = self.as_pd_df(chunksize=self.chunksize,
                                        skiprows=nrows)
                for df in df_iter:
                    self.valid, message = self._validate_df(df)
                    if self.valid is False:
                        break
            except pd.errors.EmptyDataError:
                print("Nothing left to validate")
        self._evaluate_errors()
        return self.valid, message

    def write_errors_to_file(self) -> None:
        """Write the error df to a CSV file
        """
        errors_out = self.filename + ".err.csv.gz"
        self.errors_table.tocsv(errors_out)

    def _validate_file_ext(self) -> tuple[bool, Union[str, None]]:
        message = None
        file_ext = "".join(Path(self.filename).suffixes)
        valid = file_ext.endswith(tuple(SumStatsSchema.FILE_EXTENSIONS))
        if not valid:
            self.primary_error_type = "file_ext"
            message = (f"Extension, '{file_ext}', "
                       f"not in valid set: {SumStatsSchema.FILE_EXTENSIONS}.")
        return valid, message

    def _validate_field_order(self) -> tuple[bool, Union[str, None]]:
        message = None
        required_order = self.schema().field_order()
        actual_order = self.header()[:len(required_order)]
        valid = actual_order == required_order
        if not valid:
            self.primary_error_type = "field order"
            message = ("Fields not in the required order:\n"
                       f"Headers given:    {actual_order}\n"
                       f"Headers required: {required_order}")
        return valid, message

    def _validate_chromosomes(self) -> tuple[bool, str]:
        """Check if the chromosome column contains only integers 1-22.
        
        Args:
        sself.sumstats: petl read input sumstat files
        
        Returns:
        tuple[bool, str]: Validation status and error message.
          """
    
        if "chromosome" not in self.header():
            return False, "Chromosome column is missing from the input file."
        else:
            table=etl.convert(self.sumstats,'chromosome', str)
            chr_column=etl.values(table,'chromosome')
            
            unique_chr = set(chr_column)
            autosomes_chromosomes=set(map(str, range(1, 23)))
            optional_chromosomes = set(map(str, range(23, 26)))
            
            missing_autosomes = sorted(autosomes_chromosomes - unique_chr, key=int)
            missing_optional = sorted(optional_chromosomes - unique_chr, key=int)
            
            if unique_chr == {"23"}:
                return True, "This file only contains chromosome X."
            if missing_autosomes:
                self.primary_error_type = "missing_chromsomes"
                return False, f"Chromosome column missing values: {missing_autosomes}"
            if missing_optional:
                return True, f"All autosomes exist. Optional chromosomes {missing_optional} do not exist."
            
            return True, "All chromosomes, including X, Y, and MT, exist."
    
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
            dataframe = self.pval_to_mantissa_and_exponent(dataframe)
            self.schema().schema().validate(dataframe, lazy=True)
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
            # print(self.errors_table)            
            if 'DataFrameSchema' in self.errors_table['schema_context']:
                self.primary_error_type = 'headers' 
            elif 'Column' in self.errors_table['schema_context']:
                self.primary_error_type = 'data'

                # Sample self.errors_table
                # (
                #     # Header
                #     ('schema_context', 'column', 'check', 'check_number', 'failure_case', 'index'),
                #     # Data
                #     ('Column', '_p_value_mantissa', 'Must be greater than 0', 0, 0.0, 0),
                #     ('Column', '_p_value_mantissa', 'Must be greater than 0', 0, 0.0, 1),
                #     ('Column', '_p_value_mantissa', 'not_nullable', None, nan, 2), 
                # )

                # Unless specific error with p-val appears in errors table,
                # return 'data' error.
                if any(
                    row[0] == 'Column' and
                    row[1] == '_p_value_mantissa' and
                    row[2] == 'Must be greater than 0' and
                    row[4] == 0
                    for row in self.errors_table[1:]  # Skip the header row
                ):
                    self.primary_error_type = 'p_val'


def validate(filename: Path,
             errors_file: bool = False,
             pval_zero: bool = False,
             minimum_rows: int = 100_000,
             chunksize: int = 1_000_000,
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
        else:
            print("Cannot infer options from metadata file, because metadata file cannot be found.")

    validator = Validator(pval_zero=pval_zero,
                          minimum_rows=minimum_rows,
                          sumstats_file=filename,
                          chunksize=chunksize)
    valid, message = validator.validate()
    if not valid:
        if validator.errors_table:
            error_preview = validator.errors_table.head(10)
        if errors_file and validator.errors_table:
            message += f"\n[green]Writing errors --> {filename}.err.csv.gz[/green]"
            validator.write_errors_to_file()
        primary_error_type = validator.primary_error_type
    return valid, message, error_preview, primary_error_type
