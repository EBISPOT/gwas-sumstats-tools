# GWAS SumStats Tools


A simple toolkit for reading and formatting GWAS sumstats files from the GWAS Catalog.
Built with:
* [Petl](https://petl.readthedocs.io/en/stable/index.html)
* [Pydantic](https://docs.pydantic.dev/)
* [Typer](https://typer.tiangolo.com/)

There are three commands, `validate`, `read` and `format`.


`validate` is for:
* Validating a summary statistic file using a dynamically generated schema

`read` is for:
* Previewing a data file: _no options_
* Extracting the field headers: `-h`
* Extracting all the metadata: `-M`
* Extacting specific field, value pairs from the metada: `-m <field name>`
* More functionality is to come...

`format` is for:
* Converting a minamally formatted sumstats data file to the standard format. This is not guaranteed to return a valid standard file, because manadatory data fields could be missing in the input. It simply does the following. `-s`
  * Renames `variant_id` -> `rsid`
  * Reorders the fields
  * Converts `NA` missing values to `#NA`
  * It is memory efficient and will take approx. 30s per 1 million records
* Generate metadata for a data file: `-m`
  * Read metadata in from existing file: `--meta-in <file>`
  * Create metadata from the GWAS Catalog (internal use, requires authenticated API): `-g`
  * Edit/add the values to the metadata: `-e` with `--<FIELD>=<VALUE>`

## Requirements
- python >= 3.9

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

* `-o, --ss-out PATH`: Output sumstats file
* `-s, --minimal2standard`: Try to convert a valid, minimally formatted file to the standard format.This assumes the file at least has `p_value`  combined with rsid in `variant_id` field or `chromosome` and `base_pair_location`. Validity of the new file is not guaranteed because mandatory data could be missing from the original file.  [default: False]
* `-m, --generate-metadata`: Create the metadata file  [default: False]
* `--meta-out PATH`: Specify the metadata output file
* `--meta-in PATH`: Specify a metadata file to read in
* `-e, --meta-edit`: Enable metadata edit mode. Then provide params to edit in the `--<FIELD>=<VALUE>` format e.g. `--GWASID=GCST123456` to edit/add that value  [default: False]
* `-g, --meta-gwas`: Populate metadata from GWAS Catalog  [default: False]
* `-c, --custom-header-map`: Provide a custom header mapping using the `--<FROM>:<TO>` format e.g. `--chr:chromosome`  [default: False]
* `--help`: Show this message and exit.

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
4. `poetry install`
5. `poetry run pytest`

To make a change:
branch from master -> PR to master -> poetry version -> git add pyproject.toml -> git commit -> git tag <version> -> git push origin master --tags
If all the tests pass, this will publish to pypi.
