FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnetcdf-dev  \
    libnetcdf-c++4-dev \
    g++  \
    cmake  \
    ninja-build  \
    git \
    && apt-get clean

RUN uv lock \
    && uv sync --frozen --extra server --extra dev --extra membrane

# --extra cobra --extra copasi

CMD ["uv", "run", "server", "up"]
