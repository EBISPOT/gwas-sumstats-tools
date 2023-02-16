from pathlib import Path
from typing import Union
import petl as etl


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
    FIELDS_EFFECT = ("beta", "odds_ratio")
    FIELDS_OPTIONAL = ("variant_id", "rsid", "info", "ci_upper", "ci_lower", "ref_allele")

    def __init__(self, sumstats_file: Path, delimiter: str = None) -> None:
        self.delimiter = delimiter if delimiter else self._get_delimiter(sumstats_file)
        self.sumstats = self.from_file(infile=sumstats_file)
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

    def from_file(self, infile: Path) -> Union[etl.Table, None]:
        self.sumstats = etl.fromcsv(str(infile), delimiter=self.delimiter)
        if etl.nrows(self.sumstats) < 1:
            return None
        return self.sumstats

    def to_file(self, outfile: Path) -> None:
        """Write table to TSV file

        Arguments:
            outfile -- Output file name
        """
        self.sumstats.totsv(str(outfile))

    def _get_delimiter(self, filepath: Path) -> str:
        """Get delimiter from file path

        Arguments:
            filepath -- Input file path

        Returns:
            delimiter, either ',' or '\t'
        """
        return ',' if '.csv' in filepath.suffixes else '\t'

    def rename_headers(self, header_map: dict) -> etl.Table:
        """Rename headers according to the header map

        Keyword Arguments:
            header_map -- dict of header mappings from old to new \
                (default: {HEADER_MAP})

        Returns:
            etl.Table
        """
        filtered_header_map = {k: v for k, v in header_map.items() if k in self.get_header()}
        self.sumstats = etl.rename(self.sumstats, filtered_header_map)
        return self.sumstats
    
    def normalise_missing_values(self) -> etl.Table:
        self.sumstats = etl.replaceall(self.sumstats, 'NA', '#NA')
        self.sumstats = etl.replaceall(self.sumstats, None, '#NA')
        return self.sumstats

    def _get_missing_headers(self) -> set:
        """Identify and return missing headers

        Returns:
            set of missing headers
        """
        missing_headers = set(self.FIELDS_REQUIRED) - set(self.get_header())
        if set(self.FIELDS_EFFECT).isdisjoint(set(self.get_header())):
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
        header_order.extend([h for h in self.FIELDS_OPTIONAL if h in self.get_header()])
        header_order.extend([h for h in self.get_header() if h not in all_headers])
        if 'beta' in self.get_header() and 'odds_ratio' in self.get_header():
            header_order.insert(4, 'beta')
            header_order.append('odds_ratio')
            self.effect_field = 'beta'
        elif 'beta' in self.get_header():
            header_order.insert(4, 'beta')
            self.effect_field = 'beta'
        elif 'odds_ratio' in self.get_header():
            header_order.insert(4, 'odds_ratio')
            self.effect_field = 'odds_ratio'
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

    def get_header(self) -> tuple:
        """Get the header of the file

        Returns:
            tuple of the headers
        """
        return etl.header(self.sumstats)


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

