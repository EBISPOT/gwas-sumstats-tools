# 2. Deployment Changes
Decision made date: 2026-04-16

## Status
Accepted

## Context
Previously, GitLab CI (`.gitlab-ci.yml`) was responsible for running tests, publishing to PyPI, and building/pushing Docker images to Docker Hub.

PyPI releases were made using an individual account, which requires 2FA and is not suitable for maintance. We have since applied for a GWAS Catalog organisation account on PyPI, which supports trusted publishing (OIDC) and removes the need for stored credentials.

The Docker Hub publishing use case is not fully confirmed, so Docker image builds and pushes remain in `.gitlab-ci.yml` for now.

## Decision
PyPI publishing has been moved to GitHub Actions using the `pypa/gh-action-pypi-publish` action with OIDC trusted publishing. This removes the need for API tokens or passwords.

- `.github/workflows/publish-pypi.yml` — triggered on version tags (`v*`); runs tests then publishes to PyPI
- `.gitlab-ci.yml` — continues to handle Docker image builds and pushes to Docker Hub (`ebispot/gwas-sumstats-tools`)

## Consequences
- PyPI releases no longer depend on individual account credentials or 2FA
- The `deploy` stage in `.gitlab-ci.yml` is now unused and can be removed once the Docker Hub workflow is confirmed or retired