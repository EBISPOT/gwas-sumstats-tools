"""
Pandera Schema https://pandera.readthedocs.io for defining 
the summary statistics data tables. The schema is dynamically
generated because of columns that can be defined in multiple
ways e.g. the effect size column (index 4) can be a beta, an
odds ratio or a hazard ratio - and these all have differing 
validation constraints.
"""


from pandera import Column, DataFrameSchema, Check


class SumStatsSchema:
    """Pandera DataFrameSchema interface for
    summary statistics data.
    """
    EFFECT_FIELD_DEFINITIONS = {
        "beta": Column(float),
        "odds_ratio": Column(float, [
            Check.ge(0,
                     error="Must be a value greater than or equal to 0")
            ]),
        "hazard_ratio": Column(float, [
            Check.ge(0,
                     error="Must be a value greater than or equal to 0")
            ])
        }
    PVALUE_VALIDATORS = {
        'default':  Column(float, [
            Check.in_range(0, 1,
                           include_min=False,
                           error="Must be a value > 0 and <= 1")
            ]),
        'pval_zero': Column(float, [
            Check.in_range(0, 1,
                           include_min=True,
                           error="Must be a value between 0 and 1, inclusive")
            ]),
        'pval_neg_log_default': Column(float, [
            Check.gt(0,
                     error="Must be greater than 0")
            ]),
        'pval_neg_log_zero': Column(float, [
            Check.ge(0,
                     error="Must be greater than or equal to 0")
            ])
    }
    FILE_EXTENSIONS = {
        ".tsv",
        ".tsv.gz"
    }

    def __init__(self,
                 effect_field: str = 'beta',
                 pval_zero: bool = False,
                 pval_neg_log: bool = False) -> None:
        self.effect_field = effect_field
        self.pval_zero = pval_zero
        self.pval_neg_log = pval_neg_log

    def schema(self) -> DataFrameSchema:
        schema = DataFrameSchema(
            {
                "chromosome": Column(int, [
                    Check.in_range(1, 25,
                                   error="Must be a value between 1 and 25"),
                    ]),
                "base_pair_location": Column(int, [
                    Check.ge(1,
                             error="Must be greater or equal to 1")
                    ]),

                "effect_allele": Column(str, [
                    Check.str_matches(r'^LONG_STRING$|^[ACTGactg]+$',
                                      error="Must be nucleotide sequence")
                    ]),
                "other_allele": Column(str, [
                    Check.str_matches(r'^LONG_STRING$|^[ACTGactg]+$',
                                      error="Must be nucleotide sequence")
                    ]),
                self.effect_field: self.EFFECT_FIELD_DEFINITIONS.get(self.effect_field),
                "standard_error": Column(float),
                "effect_allele_frequency": Column(float, [
                    Check.in_range(0, 1,
                                   error="Must be a value between 0 and 1, inclusive")
                    ]),
                "p_value": self._get_pvalue_validator(),
                "variant_id": Column(str, nullable=True, required=False),
                "rsid": Column(str, [
                    Check.str_matches(r'^rs\d+$',
                                      error="Must match rsID pattern")
                    ], nullable=True, required=False),
                "ref_allele": Column(str, [
                    Check.isin({'OA', 'EA'})
                    ], nullable=True, required=False),
                "ci_upper": Column(float, nullable=True, required=False),
                "ci_lower": Column(float, nullable=True, required=False),
                "info": Column(float, [
                    Check.in_range(0, 1,
                                   error="Must be a value between 0 and 1, inclusive")
                    ], nullable=True, required=False),
                "n": Column("Int64", [
                    Check.ge(0,
                             error="Must be greater than or equal to 0")
                    ], nullable=True, required=False)
            },
            coerce=True,
            ordered=True
        )
        return schema

    def _get_pvalue_validator(self) -> Column:
        if self.pval_zero and self.pval_neg_log:
            return self.PVALUE_VALIDATORS.get('pval_neg_log_zero')
        elif not self.pval_zero and self.pval_neg_log:
            return self.PVALUE_VALIDATORS.get('pval_neg_log_default')
        elif self.pval_zero and not self.pval_neg_log:
            return self.PVALUE_VALIDATORS.get('pval_zero')
        else:
            # not self.pval_zero and not self.pval_neg_log
            return self.PVALUE_VALIDATORS.get('default')