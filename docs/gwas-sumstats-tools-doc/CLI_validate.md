# Validation
---
The validation tool is crafted to verify if the selected summary statistics files adhere to the [gwas-ssf](https://github.com/EBISPOT/gwas-summary-statistics-standard) schema defined by the GWAS catalog. This documentation serves as a guide on utilizing the gwas-ssf validate command in your terminal environment.

## Usage
<span style="font-size:1.5em;">`gwas-ssf validate file [options]`</span>

## Options
| Options | short name | type | Default value | Description |
|:--------|:----------:|:----:|:-------------:|:------------|
|`--help`| `-h` |Boolean|False|Display help message, providing guidance on how to use the tool and its various functionalities.|
|`--errors-out`|`-e`|Boolean|False|Output errors to a CSV file, `<filename>.err.csv.gz`|
|`--p-zero`|`-z`|Boolean|False|Force p-values of zero to be allowable. Takes precedence over inferred value (-i)
|`--min-rows`|`-m`|int|100,000|Minimum rows acceptable for the file
|`--chunksize`|`-s`|int|1,000,000|Number of rows to store in memory at once. Increase this number for more speed at the cost of more memory. Decrease to save memory, at the cost of speed|
|`--infer-from-metadata`|`-i`|Boolean|False|Infer validation options from the metadata file `<filename>-meta.yaml`. E.g. fields for analysis software and negative log10 p-values affect the data validation behaviour.|


## Examples
Suppose you have a file named `GCST12345_formatted.tsv` that needs to be validated to see if it adheres to the GWAS-SSF schema.


### 1. Handling P-values of Zero
In your file, encountering a p-value of 0 can cause validation failure. However, we make exceptions for 0 p-values if the analysis software is provided in the metadata.

Option 1: Force to allow zero P-values
```bash
gwas-ssf validate GCST12345_formatted.tsv --p-zero --errors-out GCST12345_formatted.err
```
Option 2: Verify analysis software field in the metadata YAML file
```bash
gwas-ssf validate GCST12345_formatted.tsv --infer-from-metadata --errors-out GCST12345_formatted.err
```

### 2. Addressing Low Row Numbers
In your file, encountering fewer than 100,000 variants (rows) can lead to validation failure. However, we do accept data with lower row numbers under certain circumstances (please contact gwas-subs@ebi.ac.uk to request an eligibility review). To bypass the minimum row number requirement, and enable you to validate the rest of the file, utilize the --min-rows option.

```bash
gwas-ssf validate GCST12345_formatted.tsv --errors-out GCST12345_formatted.err --min-rows 50000
```
----
Copyright © EMBL-EBI 2024 | EMBL-EBI is an Outstation of the [European Molecular Biology Laboratory](https://www.embl.org/) | [Terms of use](https://www.ebi.ac.uk/about/terms-of-use) | [Data Preservation Statement](https://www.ebi.ac.uk/long-term-data-preservation)