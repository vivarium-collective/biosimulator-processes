# Use a more specific tag than latest for reproducibility
# FROM ubuntu:20.04
#
# ENV DEBIAN_FRONTEND=noninteractive
#
# WORKDIR /app
#
# COPY ./biosimulator_processes /app/biosimulator_processes
#
# COPY ./pyproject.toml /app
#
# COPY ./poetry.lock /app
#
# COPY ./notebooks /app/notebooks
#
# COPY ./data /app/data
#
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     python3 \
#     python3-pip \
#     build-essential \
#     libncurses5 \
#     cmake \
#     make \
#     libx11-dev \
#     libc6-dev \
#     libx11-6 \
#     libc6 \
#     gcc \
#     swig \
#     pkg-config \
#     curl \
#     tar \
#     libgl1-mesa-glx \
#     libice6 \
#     libpython3.10 \
#     wget \
#     xvfb \
#     && mkdir /tmp/.X11-unix \
#     && chmod 1777 /tmp/.X11-unix \
#     && rm -rf /var/lib/apt/lists/*
#
# COPY ./scripts/xvfb-startup.sh /xvfb-startup.sh
#
# ENV XVFB_RES="1920x1080x24" \
#     XVFB_ARGS=""
#
# RUN pip install --upgrade pip \
#     && pip install poetry
#
# RUN poetry config virtualenvs.in-project true
#
# RUN poetry run pip install --upgrade pip \
#      && poetry install
#
# # activate poetry virtualenv
# ENV PATH="/app/.venv/bin:$PATH"
# ENV CONFIG_ENV_FILE="/app/config/config.env"
# ENV SECRET_ENV_FILE="/app/secret/secret.env"
# ENV STORAGE_GCS_CREDENTIALS_FILE="/app/secret/gcs_credentials.json"
# ENV STORAGE_LOCAL_CACHE_DIR="/app/scratch"
#
# # activate the poetry virtualenv each new non-interative shell
# RUN echo "source /app/.venv/bin/activate" >> /etc/bash.bashrc
#
# # add volume mount for co-simulation data
# VOLUME /app/data
#
# # Using VOLUME allows different sim tools to share inputs and outputs
# # For example: docker volume create sim-data
# # docker run -v sim-data:/app/data --name simulator1 simulator1-image
# # docker run -v sim-data:/app/data --name simulator2 simulator2-image
#
# RUN useradd -m -s /bin/bash jupyteruser
# RUN chown -R jupyteruser:jupyteruser /app
# USER jupyteruser
#
# CMD ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]

# Use a more specific tag instead of latest for reproducibility
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive \
    XVFB_RES="1920x1080x24" \
    XVFB_ARGS="" \
    PATH="/app/.venv/bin:$PATH" \
    CONFIG_ENV_FILE="/app/config/config.env" \
    SECRET_ENV_FILE="/app/secret/secret.env" \
    STORAGE_GCS_CREDENTIALS_FILE="/app/secret/gcs_credentials.json" \
    STORAGE_LOCAL_CACHE_DIR="/app/scratch"

WORKDIR /app

COPY ./biosimulator_processes ./pyproject.toml ./poetry.lock ./notebooks ./data /app/
COPY ./scripts/xvfb-startup.sh /xvfb-startup.sh

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10  \
    python3-pip  \
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
    && poetry install

RUN useradd -m -s /bin/bash jupyteruser && chown -R jupyteruser:jupyteruser /app

USER jupyteruser

VOLUME /app/data

CMD ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
