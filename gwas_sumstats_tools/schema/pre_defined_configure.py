#------------SNPtest----------------
#snptest = {}

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
            {
                "field": "SNP",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "CHR",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "BP",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "GENPOS",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "ALLELE1",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "ALLELE0",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "A1FREQ",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "INFO",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "BETA",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "SE",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "P_BOLT_LMM_INF",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            },
            {
                "field": "P_BOLT_LMM",
                "separator": None,
                "capture": None,
                "new_field": None,
                "include_original": None
            }
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

#----------------METAL----------------
#metal = {}


#----------------pre_defined_configure----------------
pre_defined_configure={
    #"SNPtest": snptest,
    #"METAL": metal
    "REGENIE": regenie,
    "BOLT-LMM": boltlmm
}