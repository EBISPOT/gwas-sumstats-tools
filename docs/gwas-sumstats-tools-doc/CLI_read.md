# Read
---
The Read tool is specifically designed to provide a comprehensive preview of GWAS summary statistics data files or metadata. It offers functionality to extract headers from GWAS summary statistics data files or extract specific fields from the metadata.

## Usage
<span style="font-size:1.5em;">`gwas-ssf read file [options]`</span>

## Options
| Options | short name | type | Default value | Description |
|:--------|:----------:|:----:|:-------------:|:------------|
|`--help`| `-h` |Boolean|False|Display help message|
|`--get_header`|`-h` |Boolean|False|Return the first five rows of the file|
|`--meta-in`| |Path|`filename-meta.yaml`|Specify a metadata file to read in,defaulting to `filename-meta.yaml`|
|`--get-all-metadata`|`-M`|Boolean|False|Return [all fields](https://github.com/EBISPOT/gwas-summary-statistics-standard/blob/master/schema/metadata-yamale-schema.yaml) in the metadata file|
|`--get-metadata`|`-m`|List| None| Get metadata for the specified fields e.g. `-m genome_assembly -m is_harmonised`|


## Examples
Suppose you download a GWAS summary statistic file `GCST90132222_buildGRCh37.tsv.gz` and its corresponding metadata YAML file `GCST90132222_buildGRCh37.tsv.gz-meta.yaml`  from the [GWAS Catalog public FTP](https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST90132001-GCST90133000/GCST90132222/) into the same folder, and you want to:

1. Preview the summary statistic (first five rows of the input file.)
```bash
gwas-ssf read GCST90132222_buildGRCh37.tsv.gz --get_header
```

<details>
<summary>output</summary>

```text
#-------- SUMSTATS DATA PREVIEW --------#
+-------------+------------+--------------------+---------------+--------------+---------+----------------+---------+------------------+---------------------------+
| variant_id  | chromosome | base_pair_location | effect_allele | other_allele | beta    | standard_error | p_value | variant_id_hg19  |base_pair_location_grch38 |
+=============+============+====================+===============+==============+=========+================+=========+==================+===========================+
| rs147324274 | 10         | 100000012          | A             | G            | 0.1719  | 0.2876         | 0.5501  | 10_100000012_G_A |98240255                  |
+-------------+------------+--------------------+---------------+--------------+---------+----------------+---------+------------------+---------------------------+
| NA          | 10         | 10000010           | T             | C            | -0.0329 | 0.0556         | 0.5536  | 10_10000010_C_T  |958047                   |
+-------------+------------+--------------------+---------------+--------------+---------+----------------+---------+------------------+---------------------------+
| rs144804129 | 10         | 100000122          | A             | T            | -0.0632 | 0.3363         | 0.8509  | 10_100000122_T_A |98240365                  |
+-------------+------------+--------------------+---------------+--------------+---------+----------------+---------+------------------+---------------------------+
| rs6602381   | 10         | 10000018           | G             | A            | -0.0088 | 0.0109         | 0.4206  | 10_10000018_A_G  |9958055                   |
+-------------+------------+--------------------+---------------+--------------+---------+----------------+---------+------------------+---------------------------+
| NA          | 10         | 10000030           | C             | A            | 0.0991  | 0.2386         | 0.6778  | 10_10000030_A_C  |9958067                   |
+-------------+------------+--------------------+---------------+--------------+---------+----------------+---------+------------------+---------------------------+
...
```
</details>

2. Previewing all fields in the metadata YAML files, `GCST90132222_buildGRCh37.tsv.gz-meta.yaml`, which is located in the same directory where your code is being executed (This function searches for the filename+"-meta.yaml" automatically):
```bash
gwas-ssf read GCST90132222_buildGRCh37.tsv.gz --get-all-metadata
```

3. Assuming you need to extract `genome_assembly` and `harmonisation status` fields from `GCST90132222_buildGRCh37.tsv.gz-meta.yaml` located in a different directory or named `your_yaml_file`.
```bash
gwas-ssf read GCST90132222_buildGRCh37.tsv.gz --meta-in path_to_yaml_file --get-metadata genome_assembly -m is_harmonised
```
output:
```bash
#-------- SUMSTATS METADATA --------#
genome_assembly: GRCh37
is_harmonised: false
```
----
Copyright © EMBL-EBI 2024 | EMBL-EBI is an Outstation of the [European Molecular Biology Laboratory](https://www.embl.org/) | [Terms of use](https://www.ebi.ac.uk/about/terms-of-use) | [Data Preservation Statement](https://www.ebi.ac.uk/long-term-data-preservation)
