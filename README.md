# GWAS-SSF Read and Format tools

**Usage**:

```console
$ gwas-ssf [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `format`: Format a sumstats file and...
* `read`: Read a sumstats file

## `gwas-ssf format`

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
* `-m, --generate-metadata`: Do/Don't create the metadata file  [default: False]
* `--meta-out PATH`: Specify the metadata output file
* `--meta-in PATH`: Specify a metadata file to read in
* `-e, --meta-edit`: Enable metadata edit mode. Then provide params to edit in the `--<FIELD>=<VALUE>` format e.g. `--GWASID=GCST123456` to edit/add that value  [default: False]
* `-g, --meta-gwas`: Populate metadata from GWAS Catalog  [default: False]
* `-c, --custom-header-map`: Provide a custom header mapping using the `--<FROM>:<TO>` format e.g. `--chr:chromosome`  [default: False]
* `--help`: Show this message and exit.

## `gwas-ssf read`

Read a sumstats file

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
