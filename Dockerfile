ARG PYTHON_IMAGE=python:3.13-slim-bookworm
FROM ${PYTHON_IMAGE}

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /application

COPY . /application/

RUN --mount=type=cache,target=/root/.cache/uv \
    UV_LINK_MODE=copy uv sync --no-dev

ENTRYPOINT ["uv", "run", "gwas-ssf"]
