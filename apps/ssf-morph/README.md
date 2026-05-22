# SSF-morph

SSF-morph is a browser-based tool for formatting and validating GWAS (Genome-Wide Association Studies) summary statistics files to comply with the [GWAS Catalog standard format (gwas-ssf)](https://github.com/EBISPOT/gwas-summary-statistics-standard).

It runs entirely in the browser — no server required, no data leaves your machine — by executing Python code via [Pyodide](https://pyodide.org/) (Python compiled to WebAssembly).

> **Browser requirement**: Requires a modern browser. Google Chrome and Microsoft Edge offer the best experience (native save-file dialog via the File System Access API). Firefox works but downloads the output via the standard browser download mechanism instead.

> **File limit**: Single file only, maximum 2 GB.

> **Performance**: Apply typically takes ~4 minutes for a 0.5 GB file.

---

## How It Works

### Architecture

```
Browser
├── index.html          — UI: two-mode wizard (Format / Validate)
├── consumer.js         — Event handlers, config form builders, async orchestration
├── py-worker.js        — Async wrapper: sends Python tasks to the Web Worker
└── webworker.js        — Web Worker: runs Pyodide, mounts local filesystem, executes Python

python_bin/             — Python scripts executed inside the browser via Pyodide
├── read_input.py       — Read first 5 rows of the input file
├── generate_config.py  — Auto-generate a config template from column headers
├── test_config.py      — Apply config to first 5 rows (preview)
├── apply_config.py     — Apply config to the entire file and write output
└── validation.py       — Validate a file against the gwas-ssf schema

wheels/                 — Pre-built Python wheels loaded by Pyodide at startup
├── gwas_sumstats_tools-*.whl
├── petl-*.whl
├── frictionless-*.whl
└── stringcase-*.whl
```

### Execution Flow

1. **Startup**: When the page loads, `webworker.js` initialises Pyodide in a Web Worker, installs Python packages from `wheels/` (plus `numpy`, `pandas`, `pydantic` from PyPI), and stands by for tasks.
2. **File transfer**: The user selects an input file via the drop zone. The file is read into an `ArrayBuffer` and transferred (zero-copy) to the Web Worker, which writes it into Pyodide's in-memory filesystem (`/data`) so Python can access it by path.
3. **Python execution**: `consumer.js` calls `py-worker.js` with a script and parameters. `py-worker.js` posts a message to the Web Worker, which runs the corresponding `python_bin/*.py` script inside Pyodide and returns the result.
4. **Output streaming**: After `apply_config.py` writes the output to `/data`, the Web Worker streams it back to the main thread in 4 MiB chunks. On Chrome/Edge the chunks are written directly to a user-chosen file via `showSaveFilePicker`; on Firefox they are assembled into a Blob and downloaded normally.

### Python Back-end (via Pyodide)

All heavy lifting is delegated to the `gwas_sumstats_tools` Python library:

| Script | `gwas_sumstats_tools` call | Purpose |
|---|---|---|
| `read_input.py` | `read()` | Preview first 5 input rows |
| `generate_config.py` | `format(generate_config=True)` | Auto-generate config template |
| `test_config.py` | `format()` in-memory | Test config on 5 rows |
| `apply_config.py` | `format(apply_config=True)` | Apply config to whole file |
| `validation.py` | `validate()` | Validate against gwas-ssf schema |

---

## Deployment

SSF-morph must be served over HTTP (the File System Access API does not work from `file://`).

```bash
# Serve from the ssf-morph directory
cd ssf-morph
python -m http.server 8000
# Then open http://localhost:8000 in Chrome or Edge
```

No build step is required — all dependencies are loaded at runtime.

---

## Usage

### Format Mode (Steps 1–4)

#### Step 1 — Select input file

1. Drag and drop your summary statistics file onto the drop zone, or click it to open a file picker.
2. A confirmation message appears once the file is selected.

#### Step 2 — Prepare the configuration file

The configuration file tells SSF-morph how to map your columns to the gwas-ssf standard. There are three ways to provide it:

- **Analysis software preset**: Select `REGENIE`, `BOLT-LMM`, `SNPtest`, or `SAIGE` from the dropdown to load a pre-built config for that tool's output format.
- **Auto-generate**: Click **Generate** to create a config template derived from your file's column headers. Edit it in the text box.
- **Paste your own**: Copy an existing config JSON into the text box directly.

#### Step 3 — Tailor and test the configuration

1. Use **Show Your Input Data** and **Show Example Data** to compare your columns with the target schema.
2. Edit the config JSON in the text box (see [Configuration Format](#configuration-format) below).
3. Click **Test** to apply the config to the first 5 rows. A formatted preview appears under **Your Output** — iterate until it looks right.

#### Step 4 — Apply and download

Click **Apply** to run the config over the entire file. On Chrome/Edge a save-file dialog appears before processing starts so the output streams directly to disk. On Firefox the output is downloaded automatically when processing completes.

---

### Validate Mode (Step 5)

Validation runs independently from formatting and checks whether an existing file meets the gwas-ssf standard.

1. Click **Grant Permission** and then **Select Input File** to choose the file to validate.
2. Click **Validate the selected file**.
3. Results (pass/fail, error type, error preview) appear below.

The browser validation requires a minimum of 100,000 rows to pass (matching the CLI default). It does not support forcing acceptance of zero P-values.

---

## Configuration Format

Configuration is a JSON object with two top-level keys:

```json
{
  "fileConfig": {
    "outFileSuffix": "formatted_",
    "fieldSeparator": "\t",
    "naValue": null,
    "convertNegLog10Pvalue": false,
    "removeComments": false
  },
  "columnConfig": {
    "split": [...],
    "edit":  [...]
  }
}
```

### `fileConfig`

| Field | Description |
|---|---|
| `outFileSuffix` | Prefix added to the output filename |
| `fieldSeparator` | Delimiter for the output file (default: `\t`) |
| `naValue` | String to treat as missing (e.g. `"NA"`) |
| `convertNegLog10Pvalue` | Set `true` if the p-value column is -log10 transformed |
| `removeComments` | Set `true` to strip comment lines from the input |

### `columnConfig.split` — split one column into multiple

```json
{
  "field": "SNP",
  "separator": ":",
  "capture": null,
  "new_field": ["chromosome", "base_pair_location"],
  "include_original": null
}
```

Use this when a single column encodes multiple values (e.g. `"1:693731"` → `chromosome` + `base_pair_location`).

### `columnConfig.edit` — rename, find/replace, or extract

```json
{
  "field": "A1",
  "rename": "effect_allele",
  "find": null,
  "replace": null,
  "extract": null
}
```

Use `find`/`replace` for value substitutions, or `extract` (regex) to pull part of a value.

### Mandatory output columns

The following gwas-ssf fields must appear in the output (via `rename` or `split`):

- `chromosome`
- `base_pair_location`
- `effect_allele`
- `other_allele`
- `beta` or `odds_ratio`
- `standard_error`
- `effect_allele_frequency`
- `p_value`

---

## Dependencies

| Package | Role |
|---|---|
| [gwas-sumstats-tools](https://github.com/EBISPOT/gwas-sumstats-tools) | Core format/validate logic |
| [Pyodide](https://pyodide.org/) v0.24.1 | Python runtime in the browser (WASM) |
| [pandas](https://pandas.pydata.org/) | Chunked apply pipeline (C-speed CSV parsing and transforms) |
| [petl](https://petl.readthedocs.io/) | Used by read, generate, and test steps |
| [frictionless](https://frictionlessdata.io/) | Schema-based data validation |
| [Bootstrap 5](https://getbootstrap.com/) + EBI Visual Framework | UI components |
| [DataTables](https://datatables.net/) | Interactive data preview tables |

---

## Relationship to gwas-sumstats-tools CLI

SSF-morph is a browser front-end for the `gwas-sumstats-tools` Python package. The same `format` and `validate` commands available via the `gwas-ssf` CLI are what run inside the browser. If you prefer a command-line workflow or need to process many files, use the CLI directly:

```bash
pip install gwas-sumstats-tools
gwas-ssf --help
```
