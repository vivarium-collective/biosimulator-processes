FROM python:3.12-slim-bookworm

ARG MODE
ENV MODE=${MODE}

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnetcdf-dev  \
    libnetcdf-c++4-dev \
    g++  \
    cmake  \
    ninja-build  \
    git

RUN uv lock \
    && uv sync --frozen --extra server --extra dev --extra cobra --extra copasi --extra membrane

RUN chmod +x /app/bsp/server/entrypoint.sh

ENTRYPOINT ["/app/bsp/server/entrypoint.sh"]

# CMD ["uv", "run", "server", "up"]
# uv pip install -e ."[cobra,copasi,dev,docs,membrane,quantum,vcell]"