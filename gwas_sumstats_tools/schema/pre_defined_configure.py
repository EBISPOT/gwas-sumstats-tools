#----------------REGENIE----------------
regenie = {
    "fileConfig": {
        "outFileSuffix": "regenie_formatted",
        "fieldSeparator": " ",
        "naValue": "NA",
        "convertNegLog10Pvalue": True,
        "removeComments": None
    },
    "columnConfig": {
        "split": [
        ],
        "edit": [
            {
                "field": "CHROM",
                "rename": "chromosome",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "GENPOS",
                "rename": "base_pair_location",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "ID",
                "rename": "ID",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "ALLELE0",
                "rename": "other_allele",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "ALLELE1",
                "rename": "effect_allele",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "A1FREQ",
                "rename": "effect_allele_frequency",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "N",
                "rename": "n",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "BETA",
                "rename": "beta",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "SE",
                "rename": "standard_error",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "LOG10P",
                "rename": "p_value",
                "find": None,
                "replace": None,
                "extract": None
            }
        ]
    }
}

#----------------BOLT-LMM----------------
boltlmm = {
    "fileConfig": {
        "outFileSuffix": None,
        "fieldSeparator": None,
        "naValue": None,
        "convertNegLog10Pvalue": False,
        "removeComments": False
    },
    "columnConfig": {
        "split": [
        ],
        "edit": [
            {
                "field": "SNP",
                "rename": "variant_id",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "CHR",
                "rename": "chromosome",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "BP",
                "rename": "base_pair_location",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "GENPOS",
                "rename": "GENPOS",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "ALLELE1",
                "rename": "effect_allele",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "ALLELE0",
                "rename": "other_allele",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "A1FREQ",
                "rename": "effect_allele_frequency",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "INFO",
                "rename": "INFO",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "BETA",
                "rename": "beta",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "SE",
                "rename": "standard_error",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "P_BOLT_LMM_INF",
                "rename": "P_BOLT_LMM_INF",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "P_BOLT_LMM",
                "rename": "p_value",
                "find": None,
                "replace": None,
                "extract": None
            }
        ]
    }
}

#----------------SNPTEST----------------
snptest = {
    "fileConfig": {
        "outFileSuffix": None,
        "fieldSeparator": " ",
        "naValue": None,
        "convertNegLog10Pvalue": False,
        "removeComments": "#"
    },
    "columnConfig": {
        "split": [
        ],
        "edit": [
            {
                "field": "alternate_ids",
                "rename": "variant_id",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "rsid",
                "rename": "rsid",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "chromosome",
                "rename": "chromosome",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "position",
                "rename": "base_pair_location",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "alleleA",
                "rename": "other_allele",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "alleleB",
                "rename": "effect_allele",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "all_total",
                "rename": "n",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "frequentist_add_pvalue",
                "rename": "p_value",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "frequentist_add_beta_1",
                "rename": "beta",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "frequentist_add_se_1",
                "rename": "standard_error",
                "find": None,
                "replace": None,
                "extract": None
            }
        ]
    }
}

#----------------SAIGE------------------
saige={
    "fileConfig": {
        "outFileSuffix": None,
        "fieldSeparator": "\t",
        "naValue": None,
        "convertNegLog10Pvalue": False,
        "removeComments": None
    },
    "columnConfig": {
        "split": [
        ],
        "edit": [
            {
                "field": "CHR",
                "rename": "chromosome",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "POS",
                "rename": "base_pair_location",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "MarkerID",
                "rename": "variant_id",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "Allele1",
                "rename": "other_allele",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "Allele2",
                "rename": "effect_allele",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "AC_Allele2",
                "rename": "effect_allele_count",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "AF_Allele2",
                "rename": "effect_allele_frequency",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "MissingRate",
                "rename": "MissingRate",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "BETA",
                "rename": "beta",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "SE",
                "rename": "standard_error",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "Tstat",
                "rename": "Tstat",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "var",
                "rename": "var",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "p.value",
                "rename": "p_value",
                "find": None,
                "replace": None,
                "extract": None
            },
            {
                "field": "N",
                "rename": "n",
                "find": None,
                "replace": None,
                "extract": None
            }
        ]
    }
}
#----------------pre_defined_configure----------------
pre_defined_configure={
    "REGENIE": regenie,
    "BOLT-LMM": boltlmm,
    "SNPTEST": snptest,
    "SAIGE": saige
}