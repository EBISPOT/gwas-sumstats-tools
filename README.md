# GWAS-SSF Tools


A basic toolkit for reading and formatting GWAS sumstats files from the GWAS Catalog.
Built with:
* [Petl](https://petl.readthedocs.io/en/stable/index.html)
* [Pydantic](https://docs.pydantic.dev/)
* [Typer](https://typer.tiangolo.com/)

There are two commands, `read` and `format`.

`read` is for:
* Previewing a data file: _no options_
* Extracting the field headers: `-h`
* Extracting all the metadata: `-M`
* Extacting specific field, value pairs from the metada: `-m <field name>` 

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


##Usage

```console
$ gwas-ssf [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `format`: Format a sumstats file and...
* `read`: Read a sumstats file

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


## TODO:
- [ ] Installation/distribution docs
- [ ] Transformation features
- [ ] update GWAS API