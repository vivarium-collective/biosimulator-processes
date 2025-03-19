FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    make \
    cmake \
    ninja-build \
    libnetcdf-dev \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

ENV CC=gcc CXX=g++

RUN rm -rf /app/.venv \
    && uv lock \
    && uv sync --all-extras

CMD ["uv", "run", "server", "up"]

# uv pip install -e ."[cobra,copasi,dev,docs,membrane,quantum,vcell]"