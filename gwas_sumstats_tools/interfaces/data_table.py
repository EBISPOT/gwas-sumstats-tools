from pathlib import Path
from typing import Union
import pandas as pd
from pandas.io.parsers import TextFileReader
import numpy as np
import petl as etl
import pandas as pd


"""formatters

rename_headers(chromosome=...,)

order_headers(custome_order=False)

replace_values(all=False, field, from, to)
    petl.transform.conversions.replaceall()
    petl.transform.conversions.replace()

coerce_chromosome()

normalise_missing_values()

"""


class SumStatsTable:
    FIELD_MAP = {"variant_id": "rsid"}
    FIELDS_REQUIRED = ("chromosome", "base_pair_location", "effect_allele",
                       "other_allele", "standard_error",
                       "effect_allele_frequency", "p_value")
    FIELDS_EFFECT = ("beta", "odds_ratio", "hazard_ratio")
    FIELDS_OPTIONAL = ("variant_id", "rsid", "info", "ci_upper", "ci_lower", "ref_allele")

    def __init__(self, sumstats_file: Path, delimiter: str = None, removecomments: str = None) -> None:
        self.filename = str(sumstats_file)
        self.delimiter = delimiter if delimiter else self._get_delimiter(sumstats_file)
        self.removecomments = removecomments if removecomments else None
        self.sumstats = self.from_file()
        

    def reformat_header(self, header_map: dict = FIELD_MAP) -> etl.Table:
        """Reformats the headers according to the standard

        Returns:
            etl.Table
        """
        self.rename_headers(header_map=header_map)
        missing_headers = self._get_missing_headers()
        if missing_headers:
            self._add_missing_headers(missing_headers)
        header_order = self._set_header_order()
        self.sumstats = etl.cut(self.sumstats, *header_order)
        return self.sumstats
    
    def map_header(self) -> etl.Table:
        """Reformats the headers according to the standard

        Returns:
            etl.Table
        """
        missing_headers = self._get_missing_headers()
        if missing_headers:
            self._add_missing_headers(missing_headers)
        header_order = self._set_header_order()
        self.sumstats = etl.cut(self.sumstats, *header_order)
        return self

    def from_file(self) -> Union[etl.Table, None]:
        """Try to read the file in to a Table.
        Files can be TAB seperated and optionally compressed
        with (B)GZIP. There could be cases where an input file 
        has been renamed but the data is something different 
        to that suggested by the name and extension. Most 
        cases should be covered by the exception clause.

        Arguments:
            infile -- Input file

        Returns:
            petl Table or None
        """
        try:
            if len(self.delimiter) == 1:
                self.sumstats = etl.fromcsv(self.filename, delimiter=self.delimiter,skipinitialspace=True)
                if self.removecomments is not None:
                    self.sumstats = etl.skipcomments(self.sumstats,self.removecomments)
            else:
                df = pd.read_csv(self.filename ,sep=self.delimiter, comment=self.removecomments)
                self.sumstats = etl.fromdataframe(df)
            
            if not self.is_table_content():
                return None
            return self.sumstats
        except (IOError, UnicodeDecodeError) as exception:
            print(exception)
            return None

    def is_table_content(self) -> bool:
        """Bool for whether table content exists

        Returns:
            Boolean
        """
        return etl.nrows(self.head_table(nrows=1)) > 0
    
    def to_file(self, outfile: Path) -> None:
        """Write table to TSV file

        Arguments:
            outfile -- Output file name
        """
        self.sumstats.totsv(str(outfile))

    def head_table(self, nrows: int = 10) -> etl.Table:
        return etl.head(self.sumstats, n=nrows)
    
    def example_table(self, nrows: int = 5) -> etl.Table:
        self.sumstats = etl.head(self.sumstats, n=nrows)
        return self

    def _get_delimiter(self, filepath: Path) -> str:
        """Get delimiter from file path

        Arguments:
            filepath -- Input file path

        Returns:
            delimiter, either ',' or '\t'
        """
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        if '.csv' in filepath.suffixes:
            return ','
        elif '.txt' in filepath.suffixes:
            return ' '
        else:
            return '\t'

    def rename_headers(self, header_map: dict) -> etl.Table:
        """Rename headers according to the header map

        Keyword Arguments:
            header_map -- dict of header mappings from old to new \
                (default: {HEADER_MAP})

        Returns:
            etl.Table
        """
        filtered_header_map = {k: v for k, v in header_map.items() if k in self.header()}
        self.sumstats = etl.rename(self.sumstats, filtered_header_map)
        return self

    def normalise_missing_values(self,na_value:str) -> etl.Table:
        self.sumstats = etl.replaceall(self.sumstats, 'NA', '#NA')
        self.sumstats = etl.replaceall(self.sumstats, None, '#NA')
        self.sumstats = etl.replaceall(self.sumstats, '', '#NA')
        
        if na_value is not None:
            self.sumstats = etl.replaceall(self.sumstats, na_value, '#NA')   
        return self
    
    def convert_neg_log10_pvalue(self) -> etl.Table:
        self.sumstats = etl.convert(self.sumstats, 'p_value', lambda x: 10**(-float(x)))
        return self

    def _get_missing_headers(self) -> set:
        """Identify and return missing headers

        Returns:
            set of missing headers
        """
        missing_headers = set(self.FIELDS_REQUIRED) - set(self.header())
        if set(self.FIELDS_EFFECT).isdisjoint(set(self.header())):
            missing_headers.add("beta")
        return missing_headers

    def _set_header_order(self) -> list:
        """Set the header order

        Returns:
            List of headers in standard order
        """
        all_headers = [h for h in self.FIELDS_REQUIRED]
        all_headers.extend([h for h in self.FIELDS_OPTIONAL])
        all_headers.extend([h for h in self.FIELDS_EFFECT])
        header_order = [h for h in self.FIELDS_REQUIRED]
        header_order.extend([h for h in self.FIELDS_OPTIONAL if h in self.header()])
        header_order.extend([h for h in self.header() if h not in all_headers])
        if 'beta' in self.header():
            header_order.insert(4, 'beta')
            for h in ('odds_ratio', 'hazard_ratio'):
                header_order.append(h) if h in self.header() else None
        elif 'beta' not in self.header() and 'odds_ratio' in self.header():
            header_order.insert(4, 'odds_ratio')
            header_order.append('hazard_ratio') if 'hazard_ratio' in self.header() else None
        elif 'odds_ratio' not in self.header() and 'hazard_ratio' in self.header():
            header_order.insert(4, 'hazard_ratio')
        else:
            pass
        return header_order

    def _add_missing_headers(self, missing_headers: set) -> etl.Table:
        """Add missing headers and fill with #NA

        Arguments:
            missing_headers -- missing headers set

        Returns:
            etl.Table
        """
        add_fields = [(h, '#NA') for h in missing_headers]
        if len(add_fields) > 1:
            self.sumstats = etl.addfields(self.sumstats, add_fields)
        else:
            field, value = add_fields[0]
            self.sumstats = etl.addfield(self.sumstats, field, value)
        return self.sumstats

    def header(self) -> tuple:
        """Get the header of the file

        Returns:
            tuple of the headers
        """
        if self.is_table_content():
            return etl.header(self.sumstats)
        return ()

    def effect_field(self) -> Union[str, None]:
        """Get the effect allele (field index 4).

        Returns:
            effect field label
        """
        field_4 = self._get_field_label_from_index(4)
        return field_4

    def p_value_field(self) -> Union[str, None]:
        """Get the p_value field (field index 7).

        Returns:
            p_value field label
        """
        field_4 = self._get_field_label_from_index(7)
        return field_4

    def _get_field_label_from_index(self, index: int) -> Union[str, None]:
        """Get the field label from specified index

        Arguments:
            index -- index of field

        Returns:
            field label or None
        """
        return self.header()[index] if len(self.header()) > index else None

    def _pval_to_mantissa_and_exponent(self, table: etl.Table) -> etl.Table:
        table_w_split_p = etl.split(self._square_up_table(table),
                                    self.p_value_field(),
                                    'e|E',
                                    newfields=['_p_value_mantissa',
                                               '_p_value_exponent'],
                                    include_original=True,
                                    maxsplit=1)
        return table_w_split_p

    def pval_to_mantissa_and_exponent(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create the mantissa and exponent columns from the pvalue field.
        First a row needs to be appended (we use index -99) with the delimiter,
        else the split cannot be done if no delimiters were found. The row is
        removed by index before returning the dataframe.

        Arguments:
            df -- dataframe

        Returns:
            dataframe
        """
        mant_and_exp = ['_p_value_mantissa', '_p_value_exponent']
        psplit_row = pd.Series({self.p_value_field(): '1000e1000'}, name=-99)
        df = pd.concat([df, psplit_row.to_frame().T], ignore_index=False)
        df[mant_and_exp] = (df[self.p_value_field()]
                            .str.split(r"e|E",
                                       regex=True,
                                       n=1,
                                       expand=True))
        df = df.drop(index=-99)
        return df

    def _prep_table_for_validation(self) -> etl.Table:
        table = etl.Table()
        if self.is_table_content():
            table = self._pval_to_mantissa_and_exponent(table=self.sumstats)
        return table

    def as_pd_df(self,
                 nrows: int = None,
                 chunksize: int = None,
                 skiprows: int = None) -> Union[pd.DataFrame, TextFileReader]:
        """Sumstats table as a Pandas dataframe or dataframe
        iterator (TextFileReader)

        Keyword Arguments:
            nrows -- Number of rows (default: {None, which means all rows})
            chunksize -- Number of rows to store in mem at once
            skiprows -- Number of rows to skip from start of file

        Returns:
            Pandas dataframe or iter
        """
        df = pd.DataFrame()
        skip = range(1, skiprows) if skiprows else None
        if self.is_table_content():
            df = pd.read_table(self.filename,
                               sep=self.delimiter,
                               chunksize=chunksize,
                               nrows=nrows,
                               na_values=["", "#NA", "NA", "N/A", "NaN", "NR"],
                               dtype=str,
                               skiprows=skip
                               )
        return df

    def _square_up_table(self, table: etl.Table, missing: str = "#NA") -> etl.Table:
        """Square up a table with missing/extra values on rows.

        Returns:
            etl.Table
        """
        return etl.cat(table, missing=missing)
    
    def split_columns_by_separator(self, field, separator: str, newfields: list,include_original:bool) -> etl.Table:
        """
        split(table, field, pattern, newfields=None, include_original=False, maxsplit=0, flags=0)
        """
        self.sumstats = etl.split(self.sumstats,field,separator,newfields,include_original=include_original)
        return self
    
    def split_capture(self, field, pattern, newfields: list,include_original:bool):
        """
        petl.sub(table, field, pattern, repl, count=0, flags=0)
        OR 
        petl.capture(table, field, pattern, newfields=None, include_original=False, flags=0)
        Convenience function to convert values under the given field using a regular expression substitution. See also re.sub().
        """
        self.sumstats = etl.capture(self.sumstats, field, pattern, newfields, include_original=include_original)
        return self
    
    def find_and_replace(self, field, find, replace) -> etl.Table:
        """
        petl.replace(table, field, a, b)
        Only applied to the colunns but not the header

        petl.sub(table, field, pattern, repl, count=0, flags=0)
        pattern can be str or regex
        """
        self.sumstats = etl.sub(self.sumstats, field, find, replace, count=0, flags=0)
        return self
    
    def extract(self, field, pattern, newfield):
        """
        capture function to extract regex pattern to original column
        """
        regexs=f"({pattern})"
        newfields=[newfield]
        self.sumstats = etl.capture(self.sumstats, field, regexs, newfields, include_original=False)
        return self

    def _covert_value (self, table: etl.Table, field, value, replace) -> etl.Table:
        """
        petl.transform.conversions.convert()
        """
        return etl.convert(table,field,'replace',value,replace)
    
    
