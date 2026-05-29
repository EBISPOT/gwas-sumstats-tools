# 3. Migrate from Poetry to uv for Python dependency management
Decision made date: 2026-05-29

## Status
Accepted

## Context
The project previously used [Poetry](https://python-poetry.org/) for dependency management and packaging.

An EBI-wide vulnerability scan flagged several pinned dependencies as end-of-life or carrying known CVEs. The combination of `pandas==1.5.3`, `pandera<0.14`, and the older Poetry-pinned transitive graph made it difficult to respond to those findings incrementally — upgrading any one package risked breaking the tightly coupled resolution. This created pressure to move to a toolchain that makes dependency updates easier to manage going forward.

Beyond the security driver, uv also offers significantly faster dependency resolution and installation, a simpler Docker integration pattern, and is rapidly becoming the standard toolchain for Python projects.

Key pain points with Poetry in this project:
- Poetry required a separate virtualenv bootstrap step in Dockerfiles (creating a venv just to install Poetry itself)
- `poetry run` added overhead to every CLI invocation in Docker entrypoints
- CI pipelines installed Poetry via pip before any project dependencies could be resolved

## Decision
Replace Poetry with [uv](https://github.com/astral-sh/uv) across all environments:

- `pyproject.toml` migrated to the PEP 621 `[project]` standard with `hatchling` as the build backend
- `poetry.lock` replaced by `uv.lock`
- Dev dependencies moved to `[dependency-groups]` (uv convention)
- Dockerfiles now use `COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/` — no separate install step
- GitHub Actions workflow uses `astral-sh/setup-uv@v5` and `uv version <tag>` for version bumping at release time

Two dependency version constraints were tightened during migration to preserve existing behaviour:
- `numpy<2` — `pandas==1.5.3` is not binary-compatible with numpy 2.x
- `pandera>=0.13.4,<0.14` — Poetry's `^0.13.4` resolves to `<0.14`; pandera ≥0.14 has breaking API changes and requires pandas ≥2.1.1

## Consequences

Positive

  - Faster dependency resolution and installation (uv is 10–100x faster than pip/Poetry in benchmarks)
  - Simpler Dockerfiles — uv is copied as a single binary with no bootstrap venv required
  - Standard PEP 621 `pyproject.toml` improves interoperability with other tooling
  - `uv build` produces standard sdist and wheel artifacts compatible with PyPI publishing unchanged

Trade-offs

  - `pandera` and `pandas` remain pinned to older versions (`pandera<0.14`, `pandas==1.5.3`); upgrading either will require coordinated API migration in the schema layer
  - Contributors familiar with Poetry commands will need to switch to uv equivalents (`uv sync`, `uv run`, `uv add`)

Future Considerations

  - Upgrade `pandas` to ≥2.1.1 and `pandera` to a current release to remove the `numpy<2` workaround and unlock ongoing maintenance updates
