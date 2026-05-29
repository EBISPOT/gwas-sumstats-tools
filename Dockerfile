FROM python:3.9-slim-buster

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /application

COPY . /application/

RUN uv sync --no-dev

ENTRYPOINT ["uv", "run", "gwas-ssf"]
