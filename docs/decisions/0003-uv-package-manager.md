# 3. Migrate from Poetry to uv; upgrade to Python 3.13 and current dependencies
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

### Python version — CLI/Docker vs. browser runtime

The CLI and Docker images target **Python 3.13**. The browser app ([SSF-morph](../../apps/ssf-morph/)) runs inside [Pyodide](https://pyodide.org/), a WebAssembly Python runtime that bundles its own CPython build. These two runtimes are now intentionally decoupled: the CLI tracks the latest stable CPython, while the browser tracks the latest stable Pyodide release.

Pyodide bundles a specific CPython version and a fixed set of pre-compiled packages:

| Pyodide | Python | pandas |
|---|---|---|
| 0.24.1 | 3.11 | 1.5.3 |
| 0.25.x | 3.11 | 2.0.3 |
| 0.26.0 | 3.12 | 2.1.4 |
| **0.26.4 (current)** | **3.12** | **2.1.4** |

The initial migration (0.26.0) was needed to reach pandas 2.x in the browser. The subsequent bump to 0.26.4 picks up upstream bug fixes within the 3.12-based release line. Upgrading the browser to Python 3.13 requires Pyodide 0.27.x, which is tracked as a future step.

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
| Python | 3.9 | 3.13 | Latest stable CPython; CLI/Docker decoupled from Pyodide |
| `pandas` | ==1.5.3 | >=2.1,<3 | Pyodide 0.26.x bundles pandas 2.1.4 |
| `pydantic` | >=1.10.4,<2 | >=2.0,<3 | pydantic v2 required by pandera ≥0.17 |
| `pandera` | >=0.13.4,<0.14 | >=0.17,<1 | pandas 2.x support; pydantic v2 support |
| `numpy` | <2 | >=2.0,<3 | numpy 2.x required for Python 3.13 (pre-built wheels; 1.26.x has no 3.13 wheel) |
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
- `python:3.9-slim-buster` (Debian 10, EOL June 2024) → `python:3.13-slim-bookworm` (Debian 12, current LTS)

### SSF-morph browser app
- Pyodide `v0.24.1` → `v0.26.4`
- `wrapt` removed from `loadPackage` (was a pydantic v1 runtime dependency; pydantic v2 does not need it)
- `gwas_sumstats_tools` wheel rebuilt from updated source and replaced in `apps/ssf-morph/wheels/`

## Consequences

Positive

  - All flagged CVEs resolved: pandas, pydantic, and pandera are on actively maintained releases
  - Faster dependency resolution and installation (uv is 10–100x faster than pip/Poetry in benchmarks)
  - Simpler Dockerfiles — uv is copied as a single binary with no bootstrap venv required
  - Standard PEP 621 `pyproject.toml` improves interoperability with other tooling
  - CLI and Docker images are on Python 3.13 (latest stable); browser runtime (Pyodide 0.26.4) remains on Python 3.12 and is independently upgradeable
  - 85/85 existing tests pass after migration with no test changes required

Trade-offs

  - Contributors familiar with Poetry commands will need to switch to uv equivalents (`uv sync`, `uv run`, `uv add`)
  - The browser runtime (Pyodide 0.26.4) still runs Python 3.12; the CLI and browser now diverge by one minor version until Pyodide 0.27.x lands

Future Considerations

  - When Pyodide 0.27.x ships (Python 3.13), bump the CDN URL in `apps/ssf-morph/webworker.js` and rebuild the wheels in `apps/ssf-morph/wheels/` to bring the browser runtime in line with the CLI
