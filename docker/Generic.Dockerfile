FROM python:3.12-slim-bookworm

ARG MODE
ENV MODE=${MODE}

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD .. /app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnetcdf-dev  \
    libnetcdf-c++4-dev \
    g++  \
    cmake  \
    ninja-build  \
    git

RUN uv lock \
    && uv sync --frozen --extra server --extra dev --extra membrane

# --extra cobra --extra copasi
RUN chmod +x /app/server/scripts/entrypoint.sh

ENTRYPOINT ["/app/server/scripts/entrypoint.sh"]
