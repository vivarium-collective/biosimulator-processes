FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN rm -rf /app/.venv \
    && uv lock \
    && uv sync --frozen --all-extras