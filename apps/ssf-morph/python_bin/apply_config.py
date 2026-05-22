from js import inputFileName, outputFileName, config
from gwas_sumstats_tools.format import format
from pathlib import Path
import json

input_path  = Path("/data") / inputFileName
output_path = Path("/data") / outputFileName
config_dict = json.loads(config)

format(filename=input_path, apply_config=True, config_dict=config_dict, data_outfile=output_path)
