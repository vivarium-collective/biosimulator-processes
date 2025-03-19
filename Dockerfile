FROM python:3.12-slim-bookworm

ARG MODE
ENV MODE=${MODE}

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
    git \
    && rm -rf /var/lib/apt/lists/*

ENV CC=gcc CXX=g++

RUN uv lock \
    && uv sync --frozen

RUN chmod +x /app/bsp/server/entrypoint.sh

ENTRYPOINT ["/app/bsp/server/entrypoint.sh"]

# CMD ["uv", "run", "server", "up"]
# uv pip install -e ."[cobra,copasi,dev,docs,membrane,quantum,vcell]"