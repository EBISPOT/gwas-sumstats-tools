from pathlib import Path
from typing import Union
import pandas as pd
import numpy as np
import petl as etl
import gzip


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

    def __init__(self, sumstats_file: Path, delimiter: str = None) -> None:
        self.filename = str(sumstats_file)
        self.delimiter = delimiter if delimiter else self._get_delimiter(sumstats_file)
        self.sumstats = self.from_file(infile=self.filename)
        self.sumstats_df = None

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

    def from_file(self, infile: str) -> Union[etl.Table, None]:
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
            self.sumstats = etl.fromcsv(self.filename, delimiter=self.delimiter)
            if etl.nrows(self.head_table(nrows=1)) < 1:
                return None
            return self.sumstats
        except (IOError, UnicodeDecodeError) as exception:
            print(exception)
            return None

    def to_file(self, outfile: Path) -> None:
        """Write table to TSV file

        Arguments:
            outfile -- Output file name
        """
        self.sumstats.totsv(str(outfile))

    def head_table(self, nrows: int = 10) -> etl.Table:
        return etl.head(self.sumstats, n=nrows)

    def _get_delimiter(self, filepath: Path) -> str:
        """Get delimiter from file path

        Arguments:
            filepath -- Input file path

        Returns:
            delimiter, either ',' or '\t'
        """
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        return ',' if '.csv' in filepath.suffixes else '\t'

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
        return self.sumstats
    
    def normalise_missing_values(self) -> etl.Table:
        self.sumstats = etl.replaceall(self.sumstats, 'NA', '#NA')
        self.sumstats = etl.replaceall(self.sumstats, None, '#NA')
        self.sumstats = etl.replaceall(self.sumstats, '', '#NA')
        return self.sumstats

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
        if self.sumstats:
            return etl.header(self.sumstats)
        return ()

    def effect_field(self) -> Union[str, None]:
        """Get the effect allele (field index 4).

        Returns:
            effect field
        """
        field_4 = self.header()[4] if len(self.header()) > 4 else None
        return field_4

    def _pval_to_mantissa_and_exponent(self, table: etl.Table) -> etl.Table:
        table_w_split_p = etl.split(self._square_up_table(table),
                                   'p_value',
                                   'e|E',
                                   newfields=['_mantissa', '_exponent'],
                                   include_original=True,
                                   maxsplit=1)
        return table_w_split_p

    def _prep_table_for_validation(self) -> etl.Table:
        table = etl.Table()
        if self.sumstats:
            table = self._pval_to_mantissa_and_exponent(table=self.sumstats)
        return table 
        
    def as_pd_df(self, nrows: int = None) -> pd.DataFrame:
        """Sumstats table as a Pandas dataframe

        Keyword Arguments:
            nrows -- Number of rows (default: {None, which means all rows})

        Returns:
            Pandas dataframe
        """

        df = pd.DataFrame()
        if self.sumstats:
            table_to_validate = self._square_up_table(self._prep_table_for_validation())
            df = etl.todataframe(table_to_validate, nrows=nrows)
            df = df.replace([None, "", "#NA", "NA", "N/A", "NaN"], np.nan)
        return df
    
    def _square_up_table(self, table: etl.Table, missing: str="#NA") -> etl.Table:
        """Square up a table with missing/extra values on rows.

        Returns:
            etl.Table
        """
        return etl.cat(table, missing=missing)


def header_dict_from_args(args: list) -> dict:
    """Generate a dict from cli args split on ":"

    Arguments:
        args -- cli args list

    Returns:
        Dict of key, values
    """
    header_dict = {}
    for arg in args:
        if ":" not in arg:
            # skip because it's not a metadata mapping
            pass
        else:
            key, value = arg.replace("--", "").split(":")
            header_dict[key] = value
    return header_dict

