# GWAS SumStats Tools

You can access comprehensive documentation for using gwas-sumstat-tools at this link: [GWAS SumStats Tools Documentation](https://ebispot.github.io/gwas-sumstats-tools-documentation/#/).

## Overview:
There are four commands, `read`, `format` `validate` and `gen_meta` (`gen_meta` function is currently only accessible to internal GWAS catalog users.)

`read` is for:
* Previewing a data file: _no options_
* Extracting the field headers: `-h`
* Extracting all the metadata: `-M`
* Extacting specific field, value pairs from the metada: `-m <field name>`

`format` is for:
* Converting sumstats data file to the standard format - [gwas-ssf](https://github.com/EBISPOT/gwas-summary-statistics-standard). **This is not guaranteed to return a valid standard file**, because manadatory data fields could be missing in the input. 
  * Generate a configuration file, which serves as a blueprint for the formatting options.
  * Test the configuration file on the first five rows of the input file.
  * Apply the configuration file to the entire input file and generate formatted output file
  > [!NOTE] 
  > It is memory efficient and will take approx. 30s per 1 million records

`gen_meta` is for:
* Generate metadata for a data file: `-m`
  * Read metadata in from existing file: `--meta-in <file>`
  * Create metadata from the GWAS Catalog (internal use, requires authenticated API): `-g`
  * Edit/add the values to the metadata: `-e` with `--<FIELD>=<VALUE>`

`validate` is for:
* Validating a summary statistic file using a dynamically generated schema

## Requirements
- python >= 3.9 and <3.12

## Installation
### Local installation with pip
```console
$ pip3 install gwas-sumstats-tools
```
### Run with Docker
The following Docker command is the equivalent to running `gwas-ssf`. 
```console
$ docker run -it -v ${PWD}:/application ebispot/gwas-sumstats-tools:latest
```
Just append any subcommands or arguments e.g.:
```console
$ docker run -it -v ${PWD}:/application ebispot/gwas-sumstats-tools:latest validate
```


## Usage

<p align="center"><img src="gwas-demo.gif"/></p>

```console
$ gwas-ssf [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `validate`: Validate a sumstats file
* `format`: Format a sumstats file
* `gen_meta`: generate meta-yaml file
* `read`: Read a sumstats file


### `gwas-ssf validate`

Validate a sumstats file


**Usage**:

```console
$ gwas-ssf validate [OPTIONS] FILENAME
```

**Arguments**:

* `FILENAME`: Input sumstats file. Must be TSV (may be gzipped) [required]

**Options**:

* `-e, --errors-out`: Output erros to a csv file, <filename>.err.csv.gz
* `-z, --p-zero`: Force p-values of zero to be allowable. Takes precedence over inferred value (-i)
* `-m, --min-rows`:  Minimum rows acceptable for the file [default: 100000]
* `-i, --infer-from-metadata`: Infer validation options from the metadata file <filename>-meta.yaml. E.g. a populated field for analysis software makes p-values of zero allowable.
* `--help`: Show this message and exit.


### `gwas-ssf read`

Read (preview) a sumstats file

**Usage**:

```console
$ gwas-ssf read [OPTIONS] FILENAME
```

**Arguments**:

* `FILENAME`: Input sumstats file  [required]

**Options**:

* `-h, --get-header`: Just return the headers of the file  [default: False]
* `--meta-in PATH`: Specify a metadata file to read in, defaulting to <filename>-meta.yaml
* `-M, --get-all-metadata`: Return all metadata  [default: False]
* `-m, --get-metadata TEXT`: Get metadata for the specified fields e.g. `-m genomeAssembly -m isHarmonised
* `--help`: Show this message and exit.



### `gwas-ssf format`

Format a sumstats file and creating a new one. Add/edit metadata.

**Usage**:

```console
$ gwas-ssf format [OPTIONS] FILENAME
```

**Arguments**:

* `FILENAME`: Input sumstats file. Must be TSV or CSV and may be gzipped  [required]

**Options**:
- Options for reading the input file
  * `-d, --delimiter Text`: Specify the delimiter in the file, if not specified, we can automatically detect the delimiter as whitespace if your file is *.txt, comma if your file is *.csv, or tab if your file is *.tsv.gz. Otherwise, please specify the delimiter which can help to recognise the column correctly
  * `-r, --remove_comments Text`: Remove the lines starts with the given character
- Options for generating configuration file
  * `-g, --generate_config Boolean`: To generate the configuration file for the file needed to be formatted
  * `--config_out Path`:Specify the configure JSON output file
- Options for applying configuration file
  * `-o, --ss-out PATH`: Output sumstats file
  * `-a, --apply_config Boolean`: Apply the given configuration file to the file
  * `-t, -test_config Boolean`: Test the given configuration file to the first 5 rows of the file
  * `--config_in Path`: Specify a configure JSON file to read in
  * `-f, --analysis_software Text`: Specify the analysis software used for generating the summary statistics data
  * `-s, --minimal2standard`: Try to convert a valid, minimally formatted file to the standard format.This assumes the file at least has `p_value`  combined with rsid in `variant_id` field or `chromosome` and `base_pair_location`. Validity of the new file is not guaranteed because mandatory data could be missing from the original file.  [default: False]
- Options for batch applying configuration file
  * `-b, --batch_apply Boolean`: Apply configuration files to a batch of summary statistics files
  * `--lsf Boolean`:Running the batch process via submitting jobs via LSF
  * `--slurm Boolean`:Running the batch process via submitting job via Slurm


### `gwas-ssf gen_meta`

Generate a meta-yaml file for the existing sumstats file OR edit the existing meta-yaml file.

**Usage**:

```console
$ gwas-ssf gen_meta [OPTIONS] FILENAME
```
**Example**:
```console
# Generate a meta-yaml file from GWAS API (-g) with customised fields (-e --file_type=pre-gwas-ssf) for GCST90278188.tsv files
$ gwas-ssf gen_meta --meta-out GCST90278188.tsv-meta.yaml -g GCST90278188.tsv -e --file_type=pre-gwas-ssf
```
**Arguments**:

* `FILENAME`: Input sumstats file. Must be TSV or CSV and may be gzipped  [required]

**Options**:
* `--meta-out PATH`: Specify the metadata output file
*  `-g, --meta-gwas`: Populate metadata from GWAS Catalog  [default: False]
* `-e, --meta-edit`: Enable metadata edit mode. Then provide params to edit in the `--<FIELD>=<VALUE>` format e.g. `--GWASID=GCST123456` to edit/add that value  [default: False]
* `--help`: Show this message and exit.

## Development
This repository uses [poetry](https://python-poetry.org/docs/) for dependency and packaging management.

To run the tests:

1. [install poetry](https://python-poetry.org/docs/#installation)
2. `git clone https://github.com/EBISPOT/gwas-sumstats-tools.git`
3. `cd gwas-sumstats-tools`
3. `python3 -m venv env`
3. `pip install poetry`
4. `poetry install`
5. `poetry run pytest -s`

To make a change:
branch from master -> PR to master -> poetry version -> git add pyproject.toml -> git commit -> git tag <version> -> git push origin master --tags
If all the tests pass, this will publish to pypi.

A simple toolkit for reading and formatting GWAS sumstats files from the GWAS Catalog.
Built with:
* [Petl](https://petl.readthedocs.io/en/stable/index.html)
* [Pydantic](https://docs.pydantic.dev/)
* [Typer](https://typer.tiangolo.com/)


## Citation:
If you use the NHGRI-EBI GWAS Catalog tool in your research, please refer to the "[How to Cite the NHGRI-EBI GWAS Catalog, Data, or Diagrams](https://www.ebi.ac.uk/gwas/docs/about#:~:text=How%20to%20cite%20the%20NHGRI%2DEBI%20GWAS%20Catalog%2C%20data%20therein%20or%20diagram%3A)" section on our website for proper citation guidelines.
