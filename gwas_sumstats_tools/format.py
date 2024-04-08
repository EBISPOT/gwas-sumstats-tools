from pathlib import Path
import petl as etl
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
import json,re,os,subprocess

from gwas_sumstats_tools.schema.headermap import header_mapper
from gwas_sumstats_tools.schema.configure_json import Formatconfig

from gwas_sumstats_tools.interfaces.data_table import SumStatsTable

from gwas_sumstats_tools.utils import (
    parse_accession_id,
    append_to_path,
    exit_if_no_data,
)


class Formatter:
    def __init__(
        self,
        data_infile: Path,
        data_outfile : Path = None,
        config_infile: Path = None,
        config_outfile: Path = None,
        config_dict: dict = {},
        format_data: bool = False,
    ) -> None:
        
        self.format_data = format_data
        self.data_infile = Path(data_infile)
        self.data_outfile = Path(data_outfile) if data_outfile else None
        self.data = (
            SumStatsTable(sumstats_file=self.data_infile) if self.data_infile else None
        )

        self.config_infile = Path(config_infile) if config_infile else None
        self.config_outfile = Path(config_outfile) if config_outfile else None
        self.config = Formatconfig.construct()
        self.config_dict = self._from_config() if self.config_infile else config_dict

        self.columns_in = list(self.data.header())
        self.delimiter=self.config_dict["fileConfig"]["fieldSeparator"] if self.config_infile else self.data.delimiter
        print ("format delimiter is:","'",self.data.delimiter,"'",)

    def generate_config(self):
        """
        Generate config file, either only print the config in json format (for weassembly to read) or save in a file
        """
        if self.config_outfile():
            return self.to_json_file()
        else:
            return self.generate_config_template()

    def apply_config (self):
        """
        Apply the configure file to a sumstats file and save the format result in a file    
        """
        return self.data_to_file()
    
    def test_config(self):
        """
        Apply the configure file to a sumstats file and save the format result in a file    
        """
        test_in=self.data.example_table()
        test_split_table=self.split(config=self.config_dict,data=test_in)
        test_edit_table=self.edit(config=self.config_dict,data=test_split_table)
        test_formatted_data=test_edit_table.map_header()
        return test_formatted_data
    
    def _set_data_outfile_name(self) -> str:
        """Set the data outfile name.
        If the data is to be formatted, the outfile name will be:
         - GCST id is available: is configured on infile name accession ID parsing.
         - append -formatted to the infile name
         - given output name

        Returns:
            data outfile name string
        """
        if self.data_outfile:
            return self.data_outfile
        else:
            accession_id = parse_accession_id(filename=self.data_infile)
            suffix=self.config_dict["fileConfig"]["outFileSuffix"] if self.config_dict["fileConfig"]["outFileSuffix"] else "-formatted"
            if accession_id:
                self.data_outfile = accession_id + suffix+ ".tsv.gz"
            else:
                self.data_outfile = append_to_path(
                    self.data_infile, suffix + ".tsv"
                )
            return self.data_outfile
        
    def _set_config_outfile_name(self) -> str:
        """Set the configure outfile name.
        The outfile name will be:
         - GCST id is available: is configured on infile name accession ID parsing.
         - append _config.json to the infile name
         - given output name

        Returns:
            data outfile name string
        """
        if self.config_outfile:
            return self.config_outfile
        else:
            accession_id = parse_accession_id(filename=self.data_infile)
            if accession_id:
                self.config_outfile = accession_id + "_config.json"
            else:
                self.config_outfile = append_to_path(
                self.data_infile, "_config.json"
                )
            return self.config_outfile

    def generate_config_template(self) -> dict:
        """
        1. map the header based on the dict from headermap.py
        2. edit the split configure and edit configure 
        """
        columns_out_config = self.suggest_header_mapping()
        col_config=self.define_columnconfig(columns_out_config)
        config_dict=self.generate_json_config(col_config)
        return config_dict
    
    def suggest_header_mapping(self) ->dict:
        """
        map the header based on the dict from headermap.py
        """
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
    
    def define_columnconfig(self, col_renames):
        """
        split configure: detect the special character in the column name and suggest it as a seperator
        edit Config: suggest the name of the column to be renamed
        """
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
        """
        append file configure, split and edit dict into json format
        """
        fileConfig={
            "outFileSuffix": None,
            "md5":False,
            "convertNegLog10Pvalue": False,
            "fieldSeparator": self.delimiter,
            "removeComments": False
        }
        format_config = {"fileConfig":fileConfig,"columnConfig":col_config}
        print(json.dumps(format_config, indent=4))
        return format_config
    
    def to_json_file(self):
        """
        this function works unless the --config-out is available. will writing the configure dict into a file
        """
        config_dict=self.generate_config_template()
        with open(self.config_outfile, "w", encoding='utf-8') as fh:
            json.dump(config_dict, fh, indent=4, ensure_ascii = False)
    
    def _from_config(self) -> None:
        """
        this function works as the first step of apply configure file if the --configure-in is available
        """
        with open(self.config_infile, "r") as fh:
                  self.config_dict = json.load(fh)
        return self.config_dict
    
    def formating(self):
        """
        formating the input sumstats by spliting the columns, rename, find and replace, as well as extract a regex pattern
        """
        split_table=self.split(config=self.config_dict,data=self.data)
        edit_table=self.edit(config=self.config_dict,data=split_table)
        formatted_data=edit_table.map_header()
        print(formatted_data.sumstats)
        return formatted_data
    
    def split(self, config, data):
        """
        all formatting are acived by in-build function from petl
        1. seperator the column based on the separator or regex pattern (regex1)(regex2)....
        2. need to give new column names after spliting in a list
        """
        split_config=config['columnConfig']['split']
        for col in split_config:
            if col["separator"]:
                data=data.split_columns_by_separator(
                     field=col['field'], 
                     separator=col['separator'], 
                     newfields=col['new_field'],
                     include_original=col['include_original'] if col['include_original'] else False
                )
            elif col['capture']:
                 data=data.split_capture(
                     field=col['field'], 
                     pattern=col['capture'], 
                     newfields=col['new_field'],
                     include_original=col['include_original'] if col['include_original'] else False
                )
            else:
                 data=data
        return data
    
    def edit(self, config, data):
        """
        all formatting are acived by in-build function from petl
        1. rename the headers
        2. find and replace anh string in the column value (not the header)
        3. extract a regex pattern
        """
        edit_config=config['columnConfig']['edit']
        edit_table=data
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
                       edit_table=edit_table.find_and_replace(
                           field=col['field'], 
                           find=col['find'],
                           replace=col['replace']
                       )
        edit_table=edit_table.rename_headers(rename_dict)
        return edit_table
    
    def data_to_file(self) -> None:
        """
        if the --ss-out is available, this function will store the output file into a file
        """
        print(self.data_outfile)
        self.formating().to_file(self.data_outfile)
#----------------------------out of the class----------------------------------------------

def lsf_apply_config(file_info, memory):
    """
    LSF job submission by bsub package, this function activate unless the --batch_apply=true and --lsf
    """
    sub = bsub("gwas_ssf",
               M="{}".format(str(memory)),
               R="rusage[mem={}]".format(str(memory)),
               N="")
    command = f"gwas-ssf format {file_info[0]} --apply_config --config-in {file_info[1]} -o {file_info[2]}"
    print(">>>> Submitting job to cluster, job id below")
    print(sub(command).job_id)
    print(" Formatted files, md5sums and configs will appear in "
          "the same directory as the input file.")

def slurm_apply_config(file_info, memory):
    """
    slurm job submission, this function activate unless the --batch_apply=true and --slurm
    """
    # Define output and error file paths
    output_file = "slurm-%j.out"  # %j will be replaced with the job ID
    error_file = "slurm-%j.err"  # %j will be replaced with the job ID

    # Get the current working directory
    current_dir = os.getcwd()

    # Set the SBATCH script path in the current directory
    sbatch_script_path = os.path.join(current_dir, "temp_sbatch_script.sh")

    with open(sbatch_script_path, "w") as file:
        file.write("#!/bin/bash\n")
        file.write(f"#SBATCH --mem={memory}\n")
        file.write("#SBATCH --time=01:00:00\n")
        file.write(f"#SBATCH --output={output_file}\n")
        file.write(f"#SBATCH --error={error_file}\n")
        file.write(f"gwas-ssf format {file_info[0]} --apply_config --config-in {file_info[1]} -o {file_info[2]}\n")

    # Make the script executable
    os.chmod(sbatch_script_path, 0o755)

    # SLURM job submission command
    sbatch_command = ["sbatch", sbatch_script_path]

    # Print the sbatch_command
    print("Executing command:", ' '.join(sbatch_command))

    print(">>>> Submitting job to SLURM, job id below")

    # Executing the sbatch command
    result = subprocess.run(sbatch_command, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error in submitting job: ", result.stderr)
        return

    print("Command output: ", result.stdout)

    try:
        job_id = result.stdout.strip().split()[-1]
        print("Job ID: ", job_id)
    except IndexError as e:
        print("Error parsing job ID: ", e)
        print("Full output: ", result.stdout)

    print(
        "Formatted files, md5sums and configs will appear in the same directory as the input file."
    )
# --------------------------cluster option finish---------------------------------------------------
def format(
    filename: Path,
    data_outfile: Path = None,
    minimal_to_standard: bool = False,
    generate_config: bool = False,
    config_dict: dict = None,
    config_outfile: Path = None,
    config_infile: Path = None,
    apply_config: bool = False,
    test_config: bool = False,
    batch_apply: Path = None,
    lsf: bool = False,
    slurm: bool = False,
) -> None:
    formatter = Formatter(
        data_infile=filename,
        data_outfile=data_outfile,
        config_dict=config_dict,
        config_infile=config_infile,
        config_outfile=config_outfile,
        format_data=minimal_to_standard,
    )
    if minimal_to_standard:
        exit_if_no_data(table=formatter.data.sumstats)
        print("[bold]\n-------- SUMSTATS DATA --------\n[/bold]")
        print(formatter.data.sumstats)
        if header_map:
            formatter.data.reformat_header(header_map=header_map)
        else:
            formatter.data.reformat_header()
        formatter.data.normalise_missing_values()
        print("[bold]\n-------- REFORMATTED DATA --------\n[/bold]")
        print(formatter.data.sumstats)
        print(
            f"[green]Formatting and writing sumstats data --> {str(formatter.data_outfile)}[/green]"
        )
        with Progress(
            SpinnerColumn(finished_text="Complete!"),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Processing...", total=None)
            formatter.data.to_file(outfile=formatter.data_outfile)   
    if generate_config:
        if config_outfile:
            print(f"[green]Writing config --> {str(config_outfile)}[/green]")
            formatter.to_json_file()
        else:
            print(f"[yellow]Note: No config_outfile specified. Configure file will not be saved as a file without --config-out [/yellow]")
            config=formatter.generate_config_template()
            return config
    elif apply_config:
        print("I am running at here")
        if batch_apply:
            to_format_file=etl.fromcsv(batch_apply,delimiter="\t")
            files_info=[list(row) for row in to_format_file]
            if lsf:
                for file_info in files_info:
                     lsf_apply_config(file_info, "3G")
            elif slurm:
                for file_info in files_info:
                     slurm_apply_config(file_info)
            else:
                 for file_info in files_info:
                      subprocess.run(["gwas-ssf format", file_info[0], "--apply_config", "--config-in", file_info[1], "-o", file_info[2]])      
        else:
            if not config_infile and not config_dict:
                 print("[red]Cannot format file without --config-in [file] or --config_dict string [/red]")
                 os.sys.exit(1)
            if data_outfile:
                 print(f"[green]Writing formatted data --> {str(data_outfile)}[/green]")
                 formatter.data_to_file()
            else:
                 print(f"[yellow]Note: No data_outfile specified. Data will not be saved as a file without --ss-out [/yellow]")
                 formatter.formating()
    elif test_config:
         test_out=formatter.test_config()
         return test_out
    
    if not any([minimal_to_standard, generate_config, apply_config, test_config]):
         print("Nothing to do.")