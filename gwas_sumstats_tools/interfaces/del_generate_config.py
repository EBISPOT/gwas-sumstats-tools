import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
import re

from data_table import SumStatsTable
sys.path.insert(0, os.path.abspath('/Users/yueji/Documents/GitHub/gwas-sumstats-tools/gwas_sumstats_tools'))
from schema.headermap import header_mapper
from schema.configure_json import Formatconfig
from utils import (parse_accession_id, append_to_path, exit_if_no_data)
"""
from gwas_sumstats_tools.schema.header_map import header_mapper
from gwas_sumstats_tools.schema.configure_json import Formatconfig
"""

class Config:
    def __init__(self,
            in_file: Path=None,
            out_file: Path=None) -> None:
        
        self._infile = Path(in_file)
        self._outfile = out_file
        self.data = (
            SumStatsTable(sumstats_file=self._infile) if self._infile else None)
        self.config = Formatconfig.construct()
        self.columns_in = list(self.data.header())
        self.delimiter=self.data._get_delimiter(self._infile)

    def generate_config_template(self):
        columns_out_config = self._suggest_header_mapping()
        #missing_headers =self._get_missing_headers(columns_out_config)
        #col_renames=self._add_missing_headers(columns_out_config, missing_headers)
        col_config=self._define_columnconfig(columns_out_config)
        config_dict=self.generate_json_config(col_config)
        return config_dict
    
    def _suggest_header_mapping(self):
        columns_out = dict()
        for field in self.columns_in:
            if field.lower()  in header_mapper.keys():
                 columns_out[field] = field.lower()
            else:
                for key, value_list in header_mapper.items():
                    if field.lower() in value_list and key not in columns_out.values():
                        columns_out[field] = key
                        break
                    else:
                        columns_out[field] = field
        return columns_out
    
    def _get_missing_headers(self,columns_out: dict)->set:
        missing_headers = set(SumStatsTable.FIELDS_REQUIRED) - set(columns_out.values())
        if set(SumStatsTable.FIELDS_EFFECT).isdisjoint(set(columns_out.values())):
            missing_headers.add("beta")
        return missing_headers
    
    def _add_missing_headers(self, columns_out:dict, missing_headers: set):
        # exchange the key and values
        rev_col_dict = dict((v,k) for k,v in columns_out.items())
        if len(columns_out.keys())!=len(rev_col_dict.keys()):
            raise ValueError("Duplicate columns in the input file")
        else:
            # add the missing headers as new keys
            for header in missing_headers:
                rev_col_dict[header] = None
        return rev_col_dict
    
    def _define_columnconfig(self, col_renames):
        splitConfig=[]
        editConfig=[]
        regex=re.compile('[@!#$%^&*()<>?/|}{~:]')
        for (col,rename) in col_renames.items():
            special_char = regex.search(str(col))
            if rename not in SumStatsTable.FIELDS_REQUIRED and regex.search(col) is not None:
                split_dict={
                    'field':col,
                    'separator':special_char.group(),
                    'capture':None,
                    'new_field':[x for x in regex.split(str(col)) if x],
                    'include_original':False
                    }
            else:
                split_dict={
                    'field':col,
                    'separator':None,
                    'capture':None,
                    'new_field':None,
                    'include_original':None
                    }
            splitConfig.append(split_dict)

            edit_dict={
                'field':col,
                'rename':rename,
                'find':None,
                'replace':None,
                'extract':None
            }
            editConfig.append(edit_dict)
        columnConfig={"split":splitConfig,"edit":editConfig}
        return columnConfig

    def generate_json_config (self,col_config):
        fileConfig={
            "outFileSuffix": None,
            "md5":False,
            "convertNegLog10Pvalue": False,
            "fieldSeparator": self.delimiter,
            "removeComments": False
        }
        format_config = {"fileConfig":fileConfig,"columnConfig":col_config}
        return format_config
    
    def _set_data_outfile_name(self) -> str:
        if self._outfile:
            return self._outfile
        else:
            accession_id = parse_accession_id(filename=self._infile)
            if accession_id:
                self._outfile = accession_id + "_config.json"
            else:
                self._outfile = append_to_path(
                self._infile, "_config.json"
                )
            return self._outfile

    def to_file(self):
        config_dict=self.generate_config_template()
        with open(self._set_data_outfile_name(), "w", encoding='utf-8') as fh:
            json.dump(config_dict, fh, indent=4)
"""
file="/Users/yueji/Downloads/pgs_test/GCST90275154.tsv"
profile = Config(in_file=file,out_file="/Users/yueji/Downloads/pgs_test/del.json")
print(json.dumps(profile.generate_config_template(), indent=4))
profile.to_file()
"""