# TODO: Use a more specific tag instead of latest for reproducibility
FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive \
    XVFB_RES="1920x1080x24" \
    XVFB_ARGS="" \
    PATH="/app/.venv/bin:$PATH" \
    CONFIG_ENV_FILE="/app/config/config.env" \
    SECRET_ENV_FILE="/app/secret/secret.env" \
    STORAGE_GCS_CREDENTIALS_FILE="/app/secret/gcs_credentials.json" \
    STORAGE_LOCAL_CACHE_DIR="/app/scratch"

WORKDIR /app

# copy and make dirs
COPY ./biosimulator_processes /app/biosimulator_processes
COPY ./notebooks /app/notebooks

# copy files
COPY ./pyproject.toml ./poetry.lock ./data ./scripts/trust-notebooks.sh /app/
COPY ./scripts/xvfb-startup.sh /xvfb-startup.sh

VOLUME /app/data

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10  \
    python3-pip  \
    python3-dev \
    build-essential  \
    libncurses5  \
    cmake  \
    make  \
    libx11-dev  \
    libc6-dev  \
    libx11-6  \
    libc6  \
    gcc  \
    swig \
    pkg-config  \
    curl  \
    tar  \
    libgl1-mesa-glx  \
    libice6  \
    libpython3.10  \
    wget  \
    xvfb \
    && mkdir /tmp/.X11-unix  \
    && chmod 1777 /tmp/.X11-unix  \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip && pip install poetry \
    && poetry config virtualenvs.in-project true \
    # && poetry run pip install psutil \
    && poetry update \
    && poetry install \
    && chmod +x ./trust-notebooks.sh \
    && ./trust-notebooks.sh \
    && rm ./trust-notebooks.sh

CMD ["poetry", "run", "jupyter", "lab", "--port=8888", "--no-browser", "--allow-root"]


# PLEASE NOTE: We do not need to add a USER in the Dockerfile as Singularity will handle
# such logic in conversion on the HPC.

# type imports
# dist
# param scan demo/location
