# 3. Migrate from Poetry to uv; upgrade to Python 3.12 and current dependencies
Decision made date: 2026-05-29

## Status
Accepted

## Context
The project previously used [Poetry](https://python-poetry.org/) for dependency management and packaging, pinned to Python 3.9 with `pandas==1.5.3`, `pandera<0.14`, and `pydantic<2`.

An EBI-wide vulnerability scan flagged several pinned dependencies as end-of-life or carrying known CVEs. The combination of `pandas==1.5.3`, `pandera<0.14`, and the older Poetry-pinned transitive graph made it difficult to respond to those findings incrementally — upgrading any one package risked breaking the tightly coupled resolution. This created pressure to move to a toolchain that makes dependency updates easier to manage going forward.

Beyond the security driver, uv also offers significantly faster dependency resolution and installation, a simpler Docker integration pattern, and is rapidly becoming the standard toolchain for Python projects.

Key pain points with Poetry in this project:
- Poetry required a separate virtualenv bootstrap step in Dockerfiles (creating a venv just to install Poetry itself)
- `poetry run` added overhead to every CLI invocation in Docker entrypoints
- CI pipelines installed Poetry via pip before any project dependencies could be resolved

### Python version constraint — driven by Pyodide

The target Python version (3.12) is not an arbitrary choice: it is constrained by [Pyodide](https://pyodide.org/), the WebAssembly Python runtime used by the browser app [SSF-morph](../../apps/ssf-morph/).

Pyodide bundles a specific CPython version and a fixed set of pre-compiled packages. Each Pyodide release ships one Python version and one pandas version:

| Pyodide | Python | pandas |
|---|---|---|
| 0.24.1 (previous) | 3.11 | 1.5.3 |
| 0.25.x | 3.11 | 2.0.3 |
| **0.26.0 (current)** | **3.12** | **2.1.4** |

To move from `pandas==1.5.3` to pandas 2.x in the browser we had to upgrade Pyodide. Pyodide 0.26.0 is the first release with Python 3.12. Therefore **Python 3.12 is the maximum version the browser app can target**, and we align the CLI and Docker images to the same version to eliminate drift between environments.

## Decision
Replace Poetry with [uv](https://github.com/astral-sh/uv) across all environments and upgrade all major dependencies to current releases:

### Toolchain
- `pyproject.toml` migrated to the PEP 621 `[project]` standard with `hatchling` as the build backend
- `poetry.lock` replaced by `uv.lock`
- Dev dependencies moved to `[dependency-groups]` (uv convention)
- Dockerfiles now use `COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/` — no separate install step
- GitHub Actions workflow uses `astral-sh/setup-uv@v5` and `uv version <tag>` for version bumping at release time

### Python and dependency upgrades

| Package | Before | After | Driver |
|---|---|---|---|
| Python | 3.9 | 3.12 | Pyodide 0.26.0 (see above) |
| `pandas` | ==1.5.3 | >=2.1,<3 | Pyodide 0.26.0 bundles pandas 2.1.4 |
| `pydantic` | >=1.10.4,<2 | >=2.0,<3 | pydantic v2 required by pandera ≥0.17 |
| `pandera` | >=0.13.4,<0.14 | >=0.17,<1 | pandas 2.x support; pydantic v2 support |
| `numpy` | <2 | >=1.26,<3 | pandas 2.1+ requires numpy ≥1.26 |
| `typer` | [all]>=0.7.0,<1 | >=0.9.0,<1 | `[all]` extra removed in typer 0.9+ |

### Source code changes (pydantic v1 → v2)

pydantic v2 removed several v1-only APIs. Migrated across the codebase:

| v1 API | v2 replacement |
|---|---|
| `constr(regex=...)` | `Annotated[str, StringConstraints(pattern=...)]` |
| `@validator` | `@field_validator` + `@classmethod` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `.construct()` | `.model_construct()` |
| `.parse_obj()` | `.model_validate()` |
| `.dict()` | `.model_dump()` |

### Docker base image
- `python:3.9-slim-buster` (Debian 10, EOL June 2024) → `python:3.12-slim-bookworm` (Debian 12, current LTS)

### SSF-morph browser app
- Pyodide `v0.24.1` → `v0.26.0`
- `wrapt` removed from `loadPackage` (was a pydantic v1 runtime dependency; pydantic v2 does not need it)
- `gwas_sumstats_tools` wheel rebuilt from updated source and replaced in `apps/ssf-morph/wheels/`

## Consequences

Positive

  - All flagged CVEs resolved: pandas, pydantic, and pandera are on actively maintained releases
  - Faster dependency resolution and installation (uv is 10–100x faster than pip/Poetry in benchmarks)
  - Simpler Dockerfiles — uv is copied as a single binary with no bootstrap venv required
  - Standard PEP 621 `pyproject.toml` improves interoperability with other tooling
  - Python version is now consistent across CLI, Docker images, and browser runtime
  - 85/85 existing tests pass after migration with no test changes required

Trade-offs

  - Contributors familiar with Poetry commands will need to switch to uv equivalents (`uv sync`, `uv run`, `uv add`)
  - Python version ceiling (3.12) is tied to the Pyodide release cycle; upgrading Python further requires a corresponding Pyodide upgrade and wheel rebuild

Future Considerations

  - When a new Pyodide version ships with Python 3.13+, bump `requires-python`, both Dockerfiles, and the Pyodide CDN URL in `apps/ssf-morph/webworker.js` together to keep environments in sync
