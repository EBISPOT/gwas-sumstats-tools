# SSF-morph
____
This guide provides instructions on how to use the GWAS summary statistics online formatting and validation tool - [SSF-morph](../../). You can use this tool to either
- **Format** (Steps 1 to 4) your summary statistics files into the GWAS Catalog standard format, as specified by the [gwas-ssf](https://github.com/EBISPOT/gwas-summary-statistics-standard) schema, or to
- **Validate** (Step 5) whether your files adhere to this standard format.

>[!NOTE|style:callout]
>This interface requires a modern browser with WebAssembly support (Google Chrome, Microsoft Edge, Firefox, or Safari 15.4+).

>[!ATTENTION|style:callout]
>Please note that this interface works with **a single file only** and has a file size limitation of **2 GB**.

From the home page, click **Start Format** to enter the formatting wizard, or **Start Validation** to validate a file directly.

## Format Steps:

### Step 1: Select the input file

Drop your input file onto the drop zone, or click it to open a file browser. Supported formats include TSV, CSV, and other delimited files (up to 2 GB). Once the file is selected you can proceed to the next step.

### Step 2: Prepare the configuration file

**2.1** Specify the delimiter used in your input file (e.g. `\t` for tab, `,` for comma) and the comment character if your file has comment lines (leave empty if not applicable).

**2.2** Select the analysis software used to generate your data (`BOLT-LMM`, `REGENIE`, `SNPtest`, `SAIGE`, or `Others`).

Click **Generate configuration** to produce a configuration template based on your input file and the selections above. Once the configuration is generated, click **Next** to continue.

Please review the configuration options described [here](edit_config?id=summary).

### Step 3: Edit and test your configuration

The configuration editor has two tabs:

- **File Config** — controls output-level settings:
  - *Output file prefix* — prepended to the output filename (e.g. `formatted_` produces `formatted_myfile.tsv`)
  - *Field separator* — delimiter for the output file
  - *Missing value text* — string used to represent null/missing values (leave blank for null)
  - *Convert -log₁₀ p-value* — tick to convert -log₁₀ p-values back to linear scale
  - *Remove comments* — specify a comment character to strip comment lines from the output

- **Column Config** — controls column-level transformations:
  - *Split* — split a single column into multiple fields using a separator or a regular expression capture group. For example, a `SNP` column containing `chr11:88249377` can be split on `:` into two new columns `chromosome` and `base_pair_location`. See [full split examples](edit_config?id=split-subsection).
  - *Edit* — rename columns, or apply find/replace/extract operations on column values. For example, rename `A1` → `effect_allele`, strip a `chr` prefix using find/replace, or extract an rsID using a regex pattern. See [full edit examples](edit_config?id=edit-subsection).

After editing, click **Update config** to apply your changes. Use **View / Copy JSON** to inspect or copy the raw configuration.

Click **Show Example data** and/or **Show Your Input data** to compare your data against the expected format, then click **Test** to apply the configuration to the first 5 rows of your file and preview the output. Adjust the configuration as needed and re-test before proceeding.

Click **Download config** to save your configuration file locally for reuse.

### Step 4: Apply configuration and download

Once you are satisfied with the test result, click **Apply & Download** to apply the configuration to the entire input file. The formatted output will be downloaded directly to your browser's download folder.


## Validate Steps:

Please note:
 - The validation function operates independently from the formatting function and can be used separately by clicking **Start Validation** from the home page.

### Step 5: Validate your file

**5.1** Drop your file onto the drop zone or click to browse and select it.

**5.2** Optionally set validation thresholds:
  - *Minimum number of variants (rows)* — defaults to 100,000 for GWAS Catalog submission; lower numbers may be acceptable in certain circumstances (contact [gwas-subs@ebi.ac.uk](mailto:gwas-subs@ebi.ac.uk) to request an eligibility review)
  - *Allow zero p-values* — set to `Yes` if your file contains zero p-values; note that the analysis software type must then be provided in the metadata template (see [GWAS Catalog submission documentation](https://www.ebi.ac.uk/gwas/docs/submission-summary-statistics-plus-metadata) for details)

**5.3** Click **Validate** to run validation. Results will be displayed below.

----
Copyright © EMBL-EBI 2024 | EMBL-EBI is an Outstation of the [European Molecular Biology Laboratory](https://www.embl.org/) | [Terms of use](https://www.ebi.ac.uk/about/terms-of-use) | [Data Preservation Statement](https://www.ebi.ac.uk/long-term-data-preservation)
