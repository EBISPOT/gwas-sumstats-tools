from pathlib import Path

from js import nrows, outputFileName, validateAll, zeropvalues

from gwas_sumstats_tools.validate import validate

# local file system is mounted in /data
input_path = Path("/data") / outputFileName
if nrows:
    minimum_rows = int(nrows)
else:
    minimum_rows = 10000

full_file = validateAll == "True"

output = validate(
    filename=input_path,
    minimum_rows=minimum_rows,
    pval_zero=eval(zeropvalues),
    full_file=full_file,
)
f"The validation result is:{output[0]}.\nReason:{output[1]}\nerror_preview:{output[2]}\nprimary_error_type:{output[3]}"
