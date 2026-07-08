"""
Pandera Schema https://pandera.readthedocs.io for defining
the summary statistics data tables. The schema is dynamically
generated because of columns that can be defined in multiple
ways e.g. the effect size column (index 4) can be a beta, an
odds ratio, a hazard ratio or a z-score - and these all have differing
validation constraints.
"""

import platform
from collections import OrderedDict

import numpy as np
from pandera import Check, Column, DataFrameSchema


class SumStatsSchema:
    """Pandera DataFrameSchema interface for
    summary statistics data.

    Note on the pvalue validator:

    Choice of standard allowing zero or
    -log10 allowing zero. The zero constraint
    is applied to the mantissa.
    The p-value float type uses numpy.longdouble where available, but even
    this is not precise enough for some
    datasets, whose very small values evaluate
    to 0, if we don't split mantissa and exp.
    """

    EFFECT_FIELD_DEFINITIONS = {
        "beta": Column(float),
        "odds_ratio": Column(
            float, [Check.ge(0, error="Must be a value greater than or equal to 0")]
        ),
        "hazard_ratio": Column(
            float, [Check.ge(0, error="Must be a value greater than or equal to 0")]
        ),
        "z-score": Column(float),
    }
    PVALUE_FIELD_DEFINITIONS = {
        # 'p_value': Column(float, [
        "p_value": Column(
            float if platform.system() == "Windows" else np.longdouble,
            [
                Check.in_range(
                    0,
                    1,
                    include_min=True,
                    error="Must be a value between 0 and 1, inclusive of 0",
                )
            ],
        ),
        "neg_log_10_p_value": Column(
            float, [Check.ge(0, error="Must be greater than or equal to 0")]
        ),
    }
    STANDARD_ERROR_DEFINITIONS = {
        "default": Column(float),
        "z-score": Column(
            object,
            [
                Check(
                    lambda series: series.isna().all(),
                    error="Must be #NA for z-score files",
                )
            ],
            nullable=True,
        ),
    }
    MANTISSA_VALIDATORS = {
        "default": Column(float, [Check.gt(0, error="Must be greater than 0")]),
        "pval_zero": Column(
            float, [Check.ge(0, error="Must be greater than or equal to 0")]
        ),
    }
    FILE_EXTENSIONS = {".tsv", ".tsv.gz"}

    def __init__(
        self,
        effect_field: str = "beta",
        pval_field: str = "p_value",
        pval_zero: bool = False,
    ) -> None:
        self.effect_field = effect_field
        self.pval_field = pval_field
        self.pval_zero = pval_zero

    def schema(self) -> DataFrameSchema:
        all_fields = OrderedDict(self.mandatory_fields(), **self.optional_fields())
        schema = DataFrameSchema(all_fields, coerce=True)
        return schema

    def mandatory_fields(self) -> dict:
        fields = OrderedDict(
            {
                "chromosome": Column(
                    int,
                    [
                        Check.in_range(1, 25, error="Must be a value between 1 and 25"),
                    ],
                ),
                "base_pair_location": Column(
                    int, [Check.ge(0, error="Must be positive integer")]
                ),
                "effect_allele": Column(
                    str,
                    [
                        Check.str_matches(
                            r"^LONG_STRING$|^[ACTGactg]+$",
                            error="Must be nucleotide sequence",
                        )
                    ],
                ),
                "other_allele": Column(
                    str,
                    [
                        Check.str_matches(
                            r"^LONG_STRING$|^[ACTGactg]+$",
                            error="Must be nucleotide sequence",
                        )
                    ],
                ),
                self.effect_field: self.EFFECT_FIELD_DEFINITIONS.get(self.effect_field),
                "standard_error": self._get_standard_error_validator(),
            }
        )
        fields.update(
            {
                "effect_allele_frequency": Column(
                    float,
                    [
                        Check.in_range(
                            0, 1, error="Must be a value between 0 and 1, inclusive"
                        )
                    ],
                ),
                self.pval_field: self.PVALUE_FIELD_DEFINITIONS.get(self.pval_field),
                "_p_value_mantissa": self._get_mantissa_validator(),
                "_p_value_exponent": Column("Int64", nullable=True),
            }
        )
        return fields

    def field_order(self) -> tuple:
        return tuple(k for k in self.mandatory_fields() if not k.startswith("_"))

    def optional_fields(self) -> dict:
        return {
            "variant_id": Column(
                str,
                [Check.str_matches(r"^[A-Za-z0-9_]+$", error="Must match pattern")],
                nullable=True,
                required=False,
            ),
            "rsid": Column(
                str,
                [Check.str_matches(r"^rs[0-9]+$", error="Must match rsID pattern")],
                nullable=True,
                required=False,
            ),
            "ref_allele": Column(
                str, [Check.isin(("OA", "EA"))], nullable=True, required=False
            ),
            "ci_upper": Column(float, nullable=True, required=False),
            "ci_lower": Column(float, nullable=True, required=False),
            "info": Column(
                float,
                [
                    Check.in_range(
                        0, 1, error="Must be a value between 0 and 1, inclusive"
                    )
                ],
                nullable=True,
                required=False,
            ),
            "n": Column(
                "Int64",
                [Check.ge(0, error="Must be greater than or equal to 0")],
                nullable=True,
                required=False,
            ),
        }

    def _get_mantissa_validator(self) -> Column:
        """Mantissa validator

        Returns:
            _description_
        """
        if self.pval_zero:
            # Constaint for zero value pvalues here
            return self.MANTISSA_VALIDATORS.get("pval_zero")
        else:
            return self.MANTISSA_VALIDATORS.get("default")

    def _get_standard_error_validator(self) -> Column:
        if self.effect_field == "z-score":
            return self.STANDARD_ERROR_DEFINITIONS.get("z-score")
        return self.STANDARD_ERROR_DEFINITIONS.get("default")
