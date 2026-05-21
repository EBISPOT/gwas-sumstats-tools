# GWAS SumStats Tools

A toolkit for processing, validating, and formatting GWAS (Genome-Wide Association Studies) summary statistics files for submission to the [GWAS Catalog](https://www.ebi.ac.uk/gwas/).

It ships as:
- **`gwas-ssf` CLI** — full-featured command-line tool (Python package on PyPI)
- **SSF-morph** — browser-based UI for formatting and validating single files (no install required)

---

## Repository Layout

```
gwas-sumstats-tools/
├── src/
│   └── gwas_sumstats_tools/    # Python package (the core library and CLI)
├── apps/
│   └── ssf-morph/              # Browser web app (Pyodide-based)
├── docs/
│   ├── gwas-sumstats-tools-doc/  # Docsify documentation site
│   └── decisions/              # Architecture decision records
├── tests/                      # Pytest test suite
├── deployment/                 # Kubernetes Helm chart
├── dist/                       # Built Python wheel and sdist archives
├── Dockerfile                  # Docker image for the CLI
├── Dockerfile.docs             # Docker image: nginx serving ssf-morph + docs
├── nginx.conf                  # nginx routing config for the Docker image
├── DEPLOYMENT.md               # End-to-end deployment guide
├── pyproject.toml              # Poetry project configuration
└── .github/                    # CI/CD pipelines
```

---

## Folder Descriptions

### `src/gwas_sumstats_tools/`
The installable Python package. Exposes a `gwas-ssf` CLI entry-point and a public Python API.

| File / Folder | Purpose |
|---|---|
| `cli.py` | Typer-based CLI — `read`, `format`, `validate`, `gen-meta` commands |
| `read.py` | Preview a summary statistics file, extract headers or metadata |
| `format.py` | Convert tabular files to gwas-ssf standard format |
| `validate.py` | Validate a file against the gwas-ssf schema |
| `gen_meta.py` | Auto-generate metadata from a submission form or the GWAS Catalog API |
| `config.py` | Load and parse the JSON configuration file used by `format` |
| `constants.py` | Shared constants (field names, defaults) |
| `utils.py` | Internal helper functions |
| `interfaces/` | Data-layer abstractions: `data_table.py` (tabular data), `metadata.py` (YAML metadata) |
| `schema/` | Pydantic/Pandera schemas for data validation and config structure |

### `apps/ssf-morph/`
A browser-only web app that runs the same Python formatting and validation logic in-browser via [Pyodide](https://pyodide.org/) (Python compiled to WebAssembly). No server or installation needed.

| File / Folder | Purpose |
|---|---|
| `index.html` | Main UI — two-mode wizard (Format / Validate) |
| `consumer.js` | Event handlers, config form builders, async orchestration |
| `py-worker.js` | Async wrapper that forwards tasks to the Web Worker |
| `webworker.js` | Web Worker: initialises Pyodide, mounts the local filesystem, runs Python scripts |
| `python_bin/` | Python scripts executed inside the browser (read, format, validate) |
| `wheels/` | Pre-built Python wheels loaded at startup by Pyodide |
| `Icons/` | UI icon assets |

> Requires a Chromium-based browser (Chrome, Edge). Single file, max 2 GB.

### `docs/gwas-sumstats-tools-doc/`
A [Docsify](https://docsify.js.org/) documentation site — plain Markdown files rendered client-side. Covers installation, CLI usage, the web UI guide, a tutorial, and the configuration format.

| File / Folder | Purpose |
|---|---|
| `index.html` | Docsify entry point |
| `README.md` | Homepage / overview |
| `install.md` | Installation instructions |
| `tutorial.md` | Step-by-step tutorial |
| `CLI_read.md` | CLI: read command reference |
| `CLI_format.md` | CLI: format command reference |
| `CLI_validate.md` | CLI: validate command reference |
| `CLI_gen_meta.md` | CLI: gen-meta command reference |
| `UI_format.md` | SSF-morph web UI guide |
| `edit_config.md` | How to write/edit the format config file |
| `img/` | Images and GIFs used in the docs |
| `test_data/` | Example input files referenced in the tutorial |

### `tests/`
Pytest test suite covering CLI, formatting, reading, validation, and utilities.

| File | Purpose |
|---|---|
| `test_cli.py` | End-to-end CLI command tests |
| `test_format.py` | Unit tests for the format module |
| `test_read.py` | Unit tests for the read module |
| `test_validate.py` | Unit tests for the validate module |
| `test_utils.py` | Unit tests for helper utilities |
| `prep_tests.py` | Test fixtures and shared setup |
| `interfaces/` | Tests for the data-layer interfaces |

### `deployment/`
Kubernetes deployment configuration using Helm.

| File | Purpose |
|---|---|
| `helm/Chart.yaml` | Helm chart metadata |
| `helm/values.yaml` | Default values (image tag, namespace, resources) |
| `helm/templates/deployment.yaml` | K8S Deployment resource |
| `helm/templates/service.yaml` | K8S Service resource |
| `helm/templates/ingress.yaml` | K8S Ingress resource |

### `docs/decisions/`
Architecture Decision Records (ADRs) — lightweight design documents explaining why key technical choices were made.

| File | Purpose |
|---|---|
| `0001-validator.md` | Decision record for the validation approach |
| `0002-deployment.md` | Decision record for the deployment architecture |

### `dist/`
Pre-built Python distribution archives (wheels and source tarballs) produced by `poetry build`. The latest wheel is also copied into `apps/ssf-morph/wheels/` for use by the browser app.

---

## Quick Start

### CLI (pip)
```bash
pip install gwas-sumstats-tools      # requires Python 3.9–3.11
gwas-ssf --help
```

### Web UI
Open [SSF-morph](https://ebispot.github.io/gwas-sumstats-tools-ssf-morph/) in Chrome or Edge — no installation required.

### Local development
```bash
# Install dependencies
poetry install

# Run tests
pytest

# Preview the docs locally
cd docs/gwas-sumstats-tools-doc
python3 -m http.server 3000
# then open http://localhost:3000
```

---

## Deployment

Two independent release flows:

| Flow | Trigger | Produces |
|---|---|---|
| **PyPI** | GitHub Release | Python package on PyPI + updated wheel in apps/ssf-morph |
| **Docs/App** | Push to `dev` or git tag via GitLab CI | Docker image → Kubernetes (EBI) |

See [DEPLOYMENT.md](DEPLOYMENT.md) for full details.

---

## Citation:
If you use the NHGRI-EBI GWAS Catalog tool in your research, please refer to the "[How to Cite the NHGRI-EBI GWAS Catalog, Data, or Diagrams](https://www.ebi.ac.uk/gwas/docs/about#:~:text=How%20to%20cite%20the%20NHGRI%2DEBI%20GWAS%20Catalog%2C%20data%20therein%20or%20diagram%3A)" section on our website for proper citation guidelines.

---

## License

Copyright © EMBL-EBI 2024. See [LICENSE](LICENSE) for details.
