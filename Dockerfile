FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY ./biosimulator_processes /app/biosimulator_processes

COPY ./pyproject.toml /app

COPY ./poetry.lock /app

COPY ./notebooks /app/notebooks

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    build-essential \
    libncurses5 \
    cmake \
    make \
    libx11-dev \
    libc6-dev \
    libx11-6 \
    libc6 \
    gcc \
    swig \
    pkg-config \
    curl \
    tar \
    libgl1-mesa-glx \
    libice6 \
    libpython3.10 \
    wget \
    xvfb \
    && mkdir /tmp/.X11-unix \
    && chmod 1777 /tmp/.X11-unix \
    && rm -rf /var/lib/apt/lists/*

COPY ./scripts/xvfb-startup.sh /xvfb-startup.sh

ENV XVFB_RES="1920x1080x24" \
    XVFB_ARGS=""

RUN pip install --upgrade pip \
    && pip install poetry

RUN poetry config virtualenvs.in-project true

RUN poetry run pip install --upgrade pip \
     && poetry add python-libnuml --use-pep517 \
     && poetry install

# activate poetry virtualenv
ENV PATH="/app/.venv/bin:$PATH"
ENV CONFIG_ENV_FILE="/app/config/config.env"
ENV SECRET_ENV_FILE="/app/secret/secret.env"
ENV STORAGE_GCS_CREDENTIALS_FILE="/app/secret/gcs_credentials.json"
ENV STORAGE_LOCAL_CACHE_DIR="/app/scratch"

# activate the poetry virtualenv each new non-interative shell
RUN echo "source /app/.venv/bin/activate" >> /etc/bash.bashrc

# TODO: ADD VOLUME MOUNT
# VOLUME

ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
