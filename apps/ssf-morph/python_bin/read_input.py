import json
from pathlib import Path

import petl as etl
from js import delimiter, inputFileName, removecomments

from gwas_sumstats_tools.read import read

input_path = Path("/data") / inputFileName

output = read(filename=input_path, remove_comments=removecomments, delimiter=delimiter)[
    0
]

out_header = list(output.header())
out_data = etl.todataframe(output).head(5).values.tolist()

title_list = []
for i in out_header:
    ele = {"title": i}
    title_list.append(ele)

json.dumps({"title": title_list, "data": out_data})
