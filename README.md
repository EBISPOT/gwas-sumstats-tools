# GWAS Summary Statistics Formatter

```
Usage: ss2ssf [OPTIONS] FILENAME  

Convert 'old' formatted sumstats to the new standard

Arguments:
 *    filename      PATH  Input sumstats file [default: None] [required]

Options:
--ss-out         -o      TEXT  Output sumstats file [default: None]
--metadata-only  -m            Only create the metadata file 
--meta-out               TEXT  Specify the metadata output file [default: None]
--meta-in                TEXT  Specify a metadata file to read in [default: None]
--meta-edit                    Enable metadata edit mode. Then provide params to edit in the `--<KEY>=<VALUE>` format e.g. `--GWASID=GCST123456` to edit/add that value
--meta-gwas                    Populate metadata from GWAS Catalog [default: True]
--help                         Show this message and exit. 
```
