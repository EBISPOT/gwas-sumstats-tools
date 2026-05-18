from js import inputFileName, config
from gwas_sumstats_tools.format import format
from datetime import datetime
from pathlib import Path
import petl as etl
import json


input_path = Path("/data") / inputFileName
config_dict = json.loads(config)
output=format(filename=input_path,test_config=True,config_dict=config_dict)
out_header=list(output.header())
out_data=etl.todataframe(output.sumstats).values.tolist()

title_list=[]
for i in out_header:
    ele={"title":i}
    title_list.append(ele)

json.dumps({"title":title_list,"data":out_data})