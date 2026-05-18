# Metadata Generation (Internal Use)
---
The Metadata Generation tool is a utility crafted to facilitate the generation of metadata for a data file from either user form, or retrieve metadata from the GWAS Catalog through (restricted to internal use with authenticated API access). Additionally, the tool provides the flexibility to edit or add metadata values, empowering users to customize metadata.

## Usage
<span style="font-size:1.5em;">`gwas-ssf gen_meta file [options]`</span>

## Options
| Options | short name | type | Default value | Description |
|:--------|:----------:|:----:|:-------------:|:------------|
|`--help`| `-h` |Boolean|False|Display help message, providing guidance on how to use the tool and its various functionalities.|
|`--generate-metadata`|`-m`|Boolean|False|Create the metadata file|
|`--meta-out`|None|Path|None|Specify the metadata output file|
|`--meta-in`|None|Path|None|Specify a metadata file to read in|
|`--meta-edit`|`-e`|Boolean|False|Enable metadata edit mode, then specify the parameters you wish to edit using the format `--<FIELD>=<VALUE>` format e.g. `--GWASID=GCST123456` to edit/add that value|
|` --meta-gwas`|`-g`|Boolean|False|Populate metadata from GWAS Catalog (**Internal use only**)|

## Examples
### 1. Generating Metadata with GWAS Catalog API
Suppose you have a file named GCST12345.txt for which you need to generate metadata using the GWAS Catalog API. To customize the metadata with additional fields, such as setting the `file_type` to `pre-gwas-ssf`, you can use the following command:
```bash
$ gwas-ssf gen_meta GCST90278188.tsv --meta-out GCST90278188.tsv-meta.yaml --meta-gwas -e --file_type=pre-gwas-ssf
```
This command will generate metadata for the GCST12345.txt file and save it to GCST12345-meta.yaml. The metadata will be fetched from the GWAS Catalog API, and the `file_type` field will be set to pre-gwas-ssf as specified.

----
Copyright © EMBL-EBI 2024 | EMBL-EBI is an Outstation of the [European Molecular Biology Laboratory](https://www.embl.org/) | [Terms of use](https://www.ebi.ac.uk/about/terms-of-use) | [Data Preservation Statement](https://www.ebi.ac.uk/long-term-data-preservation)