from pathlib import Path
import petl as etl


class SumStatsTable:
    HEADER_MAP = {"variant_id": "rsid"}
    HEADERS_REQUIRED = ("chromosome", "base_pair_location", "effect_allele",
                        "other_allele", "standard_error",
                        "effect_allele_frequency", "p_value")
    HEADER_EFFECT = ("beta", "odds_ratio")
    HEADERS_OPTIONAL = ("variant_id", "rsid", "info", "ci_upper", "ci_lower", "ref_allele")
    
    def __init__(self, sumstats_file: Path, delimiter: str = None) -> None:
        self.delimiter = delimiter if delimiter else self._get_delimiter(sumstats_file)
        self.sumstats = etl.fromcsv(sumstats_file, delimiter=self.delimiter)

    def _get_delimiter(self, filepath: Path) -> str:
        return ',' if '.csv' in filepath.suffixes else '\t'

    def rename_headers(self, header_map: dict = HEADER_MAP) -> etl.Table:
        self.sumstats = etl.rename(self.sumstats, header_map)
        return self.sumstats

    def reformat_header(self) -> etl.Table:
        self.rename_headers()
        missing_headers = self._get_missing_headers()
        if missing_headers:
            self.add_missing_headers(missing_headers)
        header_order = self._get_header_order()
        self.sumstats = etl.cut(self.sumstats, *header_order)
        return self.sumstats
    
    def _get_missing_headers(self) -> set:
        missing_headers = set(self.HEADERS_REQUIRED) - set(self.get_header())
        if set(self.HEADER_EFFECT).isdisjoint(set(self.get_header())):
            missing_headers.add("beta")
        return missing_headers        
    
    def _get_header_order(self) -> list:
        all_headers = [h for h in self.HEADERS_REQUIRED].extend(
            [h for h in self.HEADERS_OPTIONAL]).extend(
                [h for h in self.HEADER_EFFECT])
        return [h for h in self.HEADERS_REQUIRED].extend(
            [h for h in self.HEADERS_OPTIONAL if h in self.get_header()]).extend(
                [h for h in self.get_header() if h not in all_headers]
            )
        
    
    def add_missing_headers(self, missing_headers) -> etl.Table:
        add_fields = [(h, '#NA') for h in missing_headers]
        if len(add_fields) > 1:
            self.sumstats = etl.addfields(self.sumstats, add_fields)
        else:
            field, value = add_fields[0]
            self.sumstats = etl.addfield(self.sumstats, field, value)
        return self.sumstats
        
    def get_header(self) -> tuple:
        return etl.header(self.sumstats)
    
