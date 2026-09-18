# 2. Deployment Changes
Decision made date: 2026-04-16

## Status
Superseded — the CLI container distribution was retired after the Pages migration.

## Context
Previously, GitLab CI (`.gitlab-ci.yml`) was responsible for running tests and publishing to PyPI.

PyPI releases were made using an individual account, which requires 2FA and is not suitable for maintance. We have since applied for a GWAS Catalog organisation account on PyPI, which supports trusted publishing (OIDC) and removes the need for stored credentials.


## Decision
PyPI publishing has been moved to GitHub Actions using the `pypa/gh-action-pypi-publish` action with OIDC trusted publishing. This removes the need for API tokens or passwords.

- `.github/workflows/publish-pypi.yml` — triggered on version tags (`v*`); runs tests then publishes to PyPI

## Consequences
- PyPI releases no longer depend on individual account credentials or 2FA
