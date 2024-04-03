import petl as etl
import json
from data_table import SumStatsTable
from typing import Union
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath('/Users/yueji/Documents/GitHub/gwas-sumstats-tools/gwas_sumstats_tools'))

from utils import (parse_accession_id, append_to_path, exit_if_no_data)

class Applyconfig:
        def __init__(self,config_in=None, data_in=None, data_out=None, config_dict=None):
            self.config_in = Path(config_in)
            self.data_in = Path(data_in)
            self.data_out = data_out
            self.config_dict = self.from_config() 
            self.delimiter=self.config_dict["fileConfig"]["fieldSeparator"]
            self.data = (
                  SumStatsTable(sumstats_file=self.data_in, delimiter=self.delimiter) if self.data_in else None
                  )
                    
        def from_config(self) -> None:
            with open(self.config_in, "r") as fh:
                  self.config_dict = json.load(fh)
            return self.config_dict
             
        def split(self, config):
              split_config=config['columnConfig']['split']
              for col in split_config:
                  if col["separator"]:
                      self.data=self.data.split_columns_by_separator(
                           field=col['field'], 
                           separator=col['separator'], 
                           newfields=col['new_field'],
                           include_original=col['include_original'] if col['include_original'] else False
                      )
                  elif col['capture']:
                       self.data=self.data.split_capture(
                           field=col['field'], 
                           pattern=col['capture'], 
                           newfields=col['new_field'],
                           include_original=col['include_original'] if col['include_original'] else False
                      )
                  else:
                       self.data=self.data
              return self.data
        
        def edit(self, config, split_table):
              edit_config=config['columnConfig']['edit']
              edit_table=split_table
              rename_dict={}
              for col in edit_config:
                   rename_dict.update({col['field']:col['rename']})
                   if col['field'] is not None:
                        if col['extract'] is not None:
                             edit_table=edit_table.extract(
                                 field=col['field'], 
                                 pattern=col['extract'],
                                 newfield=col['field']
                             )
                        if col['find'] is not None and col['replace'] is not None:
                             print(col['field'],col['find'],col['replace'])
                             edit_table=edit_table.find_and_replace(
                                 field=col['field'], 
                                 find=col['find'],
                                 replace=col['replace']
                             )
              edit_table=edit_table.rename_headers(rename_dict)       
              return edit_table
        
        def format(self):
              split_table=self.split(self.config_dict)
              edit_table=self.edit(self.config_dict,split_table)
              formatted_data=edit_table.map_header()
              return formatted_data
        
        def to_file(self) -> None:
              if self.data_out:
                   out=self.data_out
              else:
                   suffix=self.config_dict["fileConfig"]["outFileSuffix"] if self.config_dict["fileConfig"]["outFileSuffix"] else "-formatted"
                   
                   accession_id = parse_accession_id(filename=self.data_in)
                   if accession_id:
                        out = accession_id + suffix +".tsv"
                   else:
                        out = append_to_path(
                             self.data_in, suffix + ".tsv"
                             )

              self.format().to_file(out)
       





path="/Users/yueji/Downloads/pgs_test/copy.json"
file="/Users/yueji/Downloads/pgs_test/test2.tsv"
m = Applyconfig(config_in=path,data_in=file)
t=m.to_file()
#print(t.__dict__)
