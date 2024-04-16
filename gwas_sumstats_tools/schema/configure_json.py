from pydantic import BaseModel, Field
from typing import List, Optional
import json

class FileConfig (BaseModel):
    outFileSuffix: str = Field(default="formatted_")
    fieldSeparator: str = Field(default="tab")
    removeComments: str = Field(default=None)
    naValue: str = Field(default=None)
    convertNegLog10Pvalue: bool = Field(default=False)

class SplitConfig (BaseModel):
    field: Optional[str]=None
    separator: Optional[str]=None
    capture: Optional[str]=None
    new_field:Optional[List]=None
    include_original:Optional[bool]=False

class EditConfig (BaseModel):
    field: Optional[str]=None
    rename: Optional[str]=None
    find: Optional[str]=None
    replace: Optional[str]=None
    extract: Optional[str]=None

class ColumnConfig (BaseModel):
    split: List[SplitConfig]
    edit: List[EditConfig]

class Formatconfig (BaseModel):
    fileConfig: FileConfig
    columnConfig: List[ColumnConfig]

"""
#Example to show the schema structure of the json file
file_config=FileConfig()

column_config_1 = ColumnConfig(
    field="gene",
    split=SplitConfig(),
    edit=EditConfig()
)
column_config_2 = ColumnConfig(
    field="chromsome",
    split=SplitConfig(),
    edit=EditConfig()
)
format_config = Formatconfig(fileConfig=file_config,columnConfig=[column_config_1,column_config_2])

print(json.loads(format_config.json()))
example: {'fileConfig': {'outFilePrefix': 'formatted_', 'md5': False, 'convertNegLog10Pvalue': False, 'fieldSeparator': 'tab', 'removeComments': None}, 'columnConfig': [{'field': 'gene', 'split': {'leftName': None, 'rightName': None, 'separator': None}, 'edit': {'rename': None, 'find': None, 'replace': None, 'extract': None}}, {'field': 'chromsome', 'split': {'leftName': None, 'rightName': None, 'separator': None}, 'edit': {'rename': None, 'find': None, 'replace': None, 'extract': None}}]}
"""