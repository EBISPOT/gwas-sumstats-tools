"""
Pandera Schema https://pandera.readthedocs.io for defining 
the summary statistics data tables. The schema is dynamically
generated because of columns that can be defined in multiple
ways e.g. the effect size column (index 4) can be a beta, an
odds ratio or a hazard ratio - and these all have differing 
validation constraints.
"""


from pandera import Column, DataFrameSchema, Check
from pandera.dtypes import Float128


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
        'pval_zero': Column(Float128, [
            Check.in_range(0, 1,
                           include_min=True,
                           error="Must be a value between 0 and 1, inclusive of 0")
            ]),
        'pval_neg_log_zero': Column(float, [
            Check.ge(0,
                     error="Must be greater than or equal to 0")
            ])
    }
    MANTISSA_VALIDATORS = {
        'default': Column(float, [
            Check.gt(0,
                     error="Must be greater than 0")
            ]),
        'pval_zero': Column(float, [
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
                "variant_id": Column(str, [
                    Check.str_matches(r'^[A-Za-z0-9_]+$',
                                      error="Must match pattern")
                    ], nullable=True, required=False),
                "rsid": Column(str, [
                    Check.str_matches(r'^rs[0-9]+$',
                                      error="Must match rsID pattern")
                    ], nullable=True, required=False),
                "ref_allele": Column(str, [
                    Check.isin(('OA', 'EA'))
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
                    ], nullable=True, required=False),
                "_mantissa": self._get_mantissa_validator(),
                "_exponent": Column("Int64", nullable=True)           
            },
            coerce=True,
            ordered=True
        )
        return schema

    def _get_pvalue_validator(self) -> Column:
        """Get the pvalue validator.
        
        Choice of standard allowing zero or 
        -log10 allowing zero. The zero constraint
        is applied to the mantissa.
        The float type is Float128 but even
        this is not precise enough for some
        datasets, whose very small values evaluate
        to 0, if we don't split mantissa and exp.

        Returns:
            p-value validator
        """
        if self.pval_neg_log:
            return self.PVALUE_VALIDATORS.get('pval_neg_log_zero')
        else:
            return self.PVALUE_VALIDATORS.get('pval_zero')

    def _get_mantissa_validator(self) -> Column:
        """Mantissa validator

        Returns:
            _description_
        """
        if self.pval_zero:
            # Constaint for zero value pvalues here
            return self.MANTISSA_VALIDATORS.get('pval_zero')
        else:
            return self.MANTISSA_VALIDATORS.get('default')
