import json
from pathlib import Path

from js import config, inputFileName, outputFileName

from gwas_sumstats_tools.format import format

input_path = Path("/data") / inputFileName
output_path = Path("/data") / outputFileName
config_dict = json.loads(config)

format(
    filename=input_path,
    apply_config=True,
    config_dict=config_dict,
    data_outfile=output_path,
)
