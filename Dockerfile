# TODO: Use a more specific tag instead of latest for reproducibility
# FROM ubuntu:22.04
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
# XVFB_RES="1920x1080x24" \
# XVFB_ARGS="" \
# PATH="/app/.venv/bin:$PATH" \
# CONFIG_ENV_FILE="/app/config/config.env" \
# SECRET_ENV_FILE="/app/secret/secret.env" \
# STORAGE_GCS_CREDENTIALS_FILE="/app/secret/gcs_credentials.json" \
# STORAGE_LOCAL_CACHE_DIR="/app/scratch"

WORKDIR /app

# copy and make dirs
COPY ./biosimulator_processes /app/biosimulator_processes
# COPY composer-notebooks /app/notebooks

# copy files
COPY pyproject.toml ./poetry.lock ./data ./scripts/trust-notebooks.sh /app/
COPY ./scripts/enter-lab.sh /usr/local/bin/enter-lab.sh
# COPY ./scripts/xvfb-startup.sh /xvfb-startup.sh

VOLUME /app/data

# env deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10  \
    ca-certificates \
    libhdf5-dev \
    libhdf5-serial-dev \
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
    libatlas-base-dev \
    swig \
    pkg-config  \
    curl  \
    tar  \
    libgl1-mesa-glx  \
    libice6  \
    libpython3.10  \
    libsm6 \
    wget  

# poetry deps
RUN python3.10 -m pip install poetry \
    && poetry config virtualenvs.in-project true \
    && poetry env use 3.10 \
    && pip wheel --no-cache-dir --use-pep517 python-libnuml \
    && poetry install

# cleanup
RUN rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoclean


# && python3.10 -m pip install poetry \
# && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 \
# && update-alternatives --set python3 /usr/bin/python3.10 \
# && pip install poetry \
# && pip install --upgrade pip  \
# && poetry update \
# && chmod +x ./trust-composer-notebooks.sh \
# && chmod +x /usr/local/bin/enter-lab.sh \
# && ./trust-composer-notebooks.sh \
# && rm ./trust-composer-notebooks.sh \

# ENTRYPOINT ["/usr/local/bin/enter-lab.sh"]


# PLEASE NOTE: We do not need to add a USER in the Dockerfile as Singularity will handle
# such logic in conversion on the HPC.
