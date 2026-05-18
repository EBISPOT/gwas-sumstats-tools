# Format
---
The Format tool is designed to facilitate the formatting of any summary statistics files into the GWAS Catalog standard format ([gwas-ssf](https://github.com/EBISPOT/gwas-summary-statistics-standard)). This documentation provides a guide on how to use the `gwas-ssf format` in terminal.

## Usage
<span style="font-size:1.5em;">`gwas-ssf format file [options]`</span>

## Options
| Options | short name | type | Default value | Description |
|:--------|:----------:|:----:|:-------------:|:------------|
|`--help`| `-h` |Boolean|False|Display help message, providing guidance on how to use the tool and its various functionalities. It's a handy feature for users who may be unfamiliar with the tool or need a quick reference on its usage.|

**Options for reading the input file**

| Options | short name | type | Default value | Description |
|:--------|:----------:|:----:|:-------------:|:------------|
|`--delimiter`|`-h` |Text|" " for .txt,"," for .csv and "\t" for .tsv|Specify the delimiter in the file, if not specified, we can automatically detect the delimiter as whitespace if your file is *.txt, comma if your file is *.csv, or tab if your file is *.tsv. Otherwise, please specify the delimiter which can help to recognise the column correctly|
|`--remove_comments`|`-r`|Text|None|Remove lines starting with the given character (e.g. “#”)|

**Options for generating configuration file**

| Options | short name | type | Default value | Description |
|:--------|:----------:|:----:|:-------------:|:------------|
|`--generate_config`|`-g` |Boolean|False|To generate the configuration file for the file that needs to be formatted|
|`--config_out`| |Path|None|Specify the configure JSON output file|

**Options for applying configuration file**

| Options | short name | type | Default value | Description |
|:--------|:----------:|:----:|:-------------:|:------------|
|`--apply_config`|`-a` |Boolean|False|Apply the given configuration file to the file|
|`--test_config`|`-t` |Boolean|False|Test the given configuration file on the first 5 rows of the file only|
|`--config_in`| |Path|None|Specify a configure JSON file to read in|
|`--ss_out`|`-o`|Path|None|Output formatted file|
|`--analysis_software`|`-f`|Text|None|Specify the analysis software used for generating the summary statistics data|
|`--minimal2standard`|`-s` |Boolean|False|Try to convert a valid, minimally formatted file to the standard format. This assumes the file at least has `p_value` combined with `rsid` in `variant_id` field or `chromosome` and `base_pair_location`. Validity of the new file is not guaranteed because mandatory data could be missing from the original file. Please use '\t' for tab, ',' for comma, and " " for whitespace|

**Options for batch applying configuration file**

| Options | short name | type | Default value | Description |
|:--------|:----------:|:----:|:-------------:|:------------|
|`--batch_apply`|`-b` |Boolean|False|Apply configuration files to a batch of summary statistics files|
|`--lsf`| |Boolean|False|Run the batch process by submitting jobs via LSF|
|`--slurm`| |Boolean|False|Run the batch process by submitting job via Slurm|


## Examples
Suppose you have a file named `gwas_sumstats.tsv` that needs to be formatted into the GWAS Summary Statistics Format(gwas-ssf) format.

### 1. To generate a configuration file:
```bash
gwas-ssf format gwas_sumstats.tsv --generate_config --config_out gwas_sumstats.json
```
If your file contains comments at the beginning, which may interfere with header recognition, you can remove them using the --remove_comments option:
```bash
gwas-ssf format gwas_sumstats.tsv --generate_config --config_out gwas_sumstats.json --remove_comments "#" 
```
Failure to recognize the correct separator can lead to header recognition issues. By default, the format assumes whitespace as the separator for files with `txt` as suffix. However, if the actual delimiter in `gwas_sumstats.tsv` is tab, you can specify it using the --delimiter option as follows:
```bash
gwas-ssf format gwas_sumstats.tsv --generate_config --config_out gwas_sumstats.json --remove_comments "#" --delimiter "\t"
```
This command ensures that the formatter identifies the correct delimiter, allowing for accurate header recognition during the formatting process. Adjust the options as needed to match the specific requirements of your input file.

### 2. Apply a configured file to a summary statistics file:
#### 2.1. Testing the configured file with the first 5 rows of your input file and previewing the result:
```bash
gwas-ssf format gwas_sumstats.tsv --test_config  --config_in gwas_sumstats.json
```
Since the --remove_comments and --delimiter options are already specified in the `gwas_sumstats.json` file, there is no need to specify them again here.
#### 2.2 Applying the configuration file to the entire file:
```bash
gwas-ssf format gwas_sumstats.tsv --apply_config  --config_in gwas_sumstats.json -o gwas_sumstats_formatted.tsv
```
These commands allow you to test and apply the configuration stored in `gwas_sumstats.json` to the summary statistics file `gwas_sumstats.tsv`, generating a formatted output file named `gwas_sumstats_formatted.tsv`. Adjust the options as needed to match your specific configuration and file requirements.

### 3. Format a summary statistics file use pre-defined configure
We provide pre-defined configuration files tailored for outputs from specific software packages. Currently, we support configurations for `REGENIE` and `BOLT-LMM`. Support for `METAL` and `SNPtest` configurations will be available soon.

To apply a pre-defined configuration for "REGENIE" to your `gwas_sumstats.tsv` file and generate a formatted output file named `gwas_sumstats_formatted.tsv`, you can use the following command:

```bash
gwas-ssf format gwas_sumstats.tsv  --apply_config --analysis_software "REGENIE" -o gwas_sumstats_formatted.tsv
```
This command ensures that the formatting process aligns with the specific output format of the "REGENIE" software, simplifying the data processing workflow. Adjust the options as needed based on the software used for generating your summary statistics file.

### 4. Apply a configuration file to a list of files 
When dealing with multiple studies in the same format within a publication, you can streamline the formatting process by generating a single configuration file and applying it to all studies.
```bash
gwas-ssf format to_format_list.tsv --apply_config --batch_apply --analysis_software "REGENIE" 
```
The `to_format_list.tsv` file is a tab-separated file containing two columns: the full path of the input file in the first column, and the full path of the corresponding output file in the second column. Here's an example format:

```tsv
path_to_GCST12341.txt path_to_GCST12341_formatted.tsv
path_to_GCST12342.txt path_to_GCST12342_formatted.tsv
path_to_GCST12343.txt path_to_GCST12343_formatted.tsv
.......
```
> [!TIP|style:callout]
> How to generate to_format_list.tsv file?
You can easily create the to_format_list.tsv file by preparing your data in a Google Sheets document. Once your data is entered, follow these steps:
>  - Go to the "File" menu and select "Download".
>  - Choose "Tab-separated values (.tsv)" from the available options.
> This will download your spreadsheet as a TSV file to your computer, ready to be used as `to_format_list.tsv`.

### 5. Batch applying a configuration file to a list of files on HPC
If your input files are large or if you have a large number of files to process, it's recommended to utilize High-Performance Computing (HPC) resources for efficient data processing. The GWAS-SSF format provides direct data submission via Slurm or LSF. If you use other job scheduling tools, please reach out to us, and we'll be happy to add support for them.

```bash
gwas-ssf format to_format_list.tsv --apply_config --batch_apply --config_in gwas_sumstats.json --slurm
```
Each input file in the list will be submitted as an independent job to run, allowing for parallel processing and efficient utilization of HPC resources. Adjust the options as needed based on your specific requirements and job scheduling system.

## Default Functions
Beyond formatting the input file according to the configuration file, the format tool also applies several default settings to every summary statistic:

1. Reorder the mandatory columns in your dataset to match the GWAS-SSF specified sequence: 
```text
chromosome, base_pair_location, effect_allele, other_allele, effect (beta/odds ratio/hazard ratio), standard_error, effect_allele_frequency, pval (or negativelog10Pvalue). 
```
Any additional columns will remain in their original input order.

2. Fill missing fields: If any mandatory column is missing from the input file, the format tool will automatically add this column and populate all its values with `#NA`.
3. Convert NA values: The tool converts any 'NA' or 'None' values to `#NA`, ensuring data consistency.

----
Copyright © EMBL-EBI 2024 | EMBL-EBI is an Outstation of the [European Molecular Biology Laboratory](https://www.embl.org/) | [Terms of use](https://www.ebi.ac.uk/about/terms-of-use) | [Data Preservation Statement](https://www.ebi.ac.uk/long-term-data-preservation)
