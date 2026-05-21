# GWAS SumStats Tools
___

GWAS SumStats Tools is a versatile toolkit created to simplify the processing, validation, and formatting of GWAS summary statistics files intended for submission to the GWAS Catalog. This toolkit provides a variety of features designed for efficiency and ease of use.

## Features
1. Reading: Preview a GWAS summary statistics data file, extract headers, metadata, or specific field-value pairs from the metadata.
2. Formatting: Convert tabular summary statistics files to GWAS Catalog standard format (gwas-ssf), with options for splitting fields, renaming fields, reordering, converting -log (P-value) to normal P-values, handling missing values efficiently and removing comments.
3. Metadata Generation: Automatically generate metadata for a data file from a submission form or create metadata from the GWAS Catalog (for internal use).
4. Validation: Validate the integrity of a summary statistic file using a dynamically generated schema.

## Quick Start

### User-friendly Interface: SSF-morph
If you prefer a user-friendly interface for formatting or validating your data, you can use our online tool. This interface allows you to quickly format or validate individual files with a size limit of 2 GB, all without the need for command-line usage. Simply click **<span style="font-size:1.2em;">[SSF-morph](https://ebispot.github.io/gwas-sumstats-tools-ssf-morph/)</span>** to access the tool and upload your data directly from your local computer.

For instructions on how to use the SSF-morph, please visit our [UI Guide Page](UI_format).

> [!TIP]
> Please note that this interface works with **a single file only** and has a file size limitation of  <span style="font-size:1.2em;">**2GB** </span>. 



### Command Line Interface
However, if you require full access to all functions, or if you need to process larger files or multiple files simultaneously, we recommend using the command-line interface. Please follow the instructions provided here to install and use the command-line tools.

#### Local Installation with pip
Installation requirements: Python  version 3.9 to 3.11.
```bash
$ pip3 install gwas-sumstats-tools
$ gwas-ssf --help
```

If you have a different Python version installed on your local computer and encounter compatibility issues, you can create a virtual environment with Python 3.9. Please follow the instructions [here](install)

---

## Documentation Layout

This documentation site is built with [Docsify](https://docsify.js.org/) — a client-side renderer that turns Markdown files into a website with no build step. The `index.html` loads Docsify from a CDN at runtime; all content is plain `.md` files.

```
gwas-sumstats-tools-doc/
├── index.html          # Docsify entry point — loads the site and configures plugins
├── _coverpage.md       # Cover page shown before the main docs
├── _sidebar.md         # Left-hand navigation sidebar
├── _navbar.md          # Top navigation bar
│
├── README.md           # Homepage / overview (this file)
├── tutorial.md         # Step-by-step tutorial
├── install.md          # Installation instructions
│
├── CLI_read.md         # CLI: reading and previewing summary statistics files
├── CLI_format.md       # CLI: formatting files to gwas-ssf standard
├── CLI_validate.md     # CLI: validating summary statistics files
├── CLI_gen_meta.md     # CLI: metadata generation (internal users)
│
├── UI_format.md        # SSF-morph (web UI) usage guide
├── edit_config.md      # How to edit the configuration file
│
├── img/                # Images and GIFs used in the docs
│   └── gwas-demo.gif
│
└── test_data/          # Example input files referenced in the tutorial
    ├── gwas_sumstats.tsv
    ├── bolt-lmm.tsv
    ├── regenie.tsv
    ├── saige.tsv
    └── snptest.tsv
```

### Previewing locally

Because Docsify runs in the browser, you need a local HTTP server (opening `index.html` directly as a `file://` URL won't work).

**Option 1 — Docsify CLI (recommended):**
```bash
npm install -g docsify-cli
docsify serve gwas-sumstats-tools-doc
# opens at http://localhost:3000
```

**Option 2 — Python:**
```bash
cd gwas-sumstats-tools-doc
python3 -m http.server 3000
# opens at http://localhost:3000
```

### How it is deployed

The docs are served as a static site inside a Docker container alongside the [SSF-morph](https://github.com/EBISPOT/gwas-sumstats-tools) web app.

1. **`Dockerfile.docs`** (repo root) copies this folder into the nginx image:
   ```dockerfile
   COPY gwas-sumstats-tools-doc ./docs
   ```
2. **`nginx.conf`** routes requests:
   - `/apps/gwas_sumstats_tools/` → SSF-morph landing page
   - `/apps/gwas_sumstats_tools/docs/` → this Docsify site
3. The image is built and pushed by GitLab CI on pushes to `dev` or on a git tag, then deployed to Kubernetes via Helm (`deployment/helm/`).

### Adding or editing pages

1. Create a new `.md` file in this directory.
2. Add a link to it in `_sidebar.md` so it appears in the navigation.
3. Optionally link to it from `_navbar.md` if it warrants top-level navigation.

----
Copyright © EMBL-EBI 2024 | EMBL-EBI is an Outstation of the [European Molecular Biology Laboratory](https://www.embl.org/) | [Terms of use](https://www.ebi.ac.uk/about/terms-of-use) | [Data Preservation Statement](https://www.ebi.ac.uk/long-term-data-preservation)
