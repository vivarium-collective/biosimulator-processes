FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# COPY . /app

# COPY ./scripts /app

# RUN rm -r /app/composer-api

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
    && rm -rf /var/lib/apt/lists/*

RUN apt-get -y update \
    && apt-get install --no-install-recommends -y \
        xvfb \
    && mkdir /tmp/.X11-unix \
    && chmod 1777 /tmp/.X11-unix \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/xvfb-startup.sh /xvfb-startup.sh

# RUN rm -r ./scripts

ENV XVFB_RES="1920x1080x24" \
    XVFB_ARGS=""

RUN pip install --upgrade pip \
    && pip install poetry

RUN poetry config virtualenvs.in-project true

# Add Poetry to PATH
ENV PATH="/root/.local/bin:${PATH}"

RUN poetry run pip install --upgrade pip \
    && poetry run pip install python-libnuml --use-pep517 \
    && poetry install

# activate poetry virtualenv
ENV PATH="/app/.venv/bin:$PATH"
ENV CONFIG_ENV_FILE="/app/config/config.env"
ENV SECRET_ENV_FILE="/app/secret/secret.env"
ENV STORAGE_GCS_CREDENTIALS_FILE="/app/secret/gcs_credentials.json"
ENV STORAGE_LOCAL_CACHE_DIR="/app/scratch"

# activate the poetry virtualenv each new non-interative shell
RUN echo "source /app/.venv/bin/activate" >> /etc/bash.bashrc

# ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
RUN poetry add antimony>=2.12.0
RUN poetry add appdirs>=1.4.3
RUN poetry add ipykernel>=4.6.1
RUN poetry add ipython*
RUN poetry add jinja2>=3.0.0
RUN poetry add jupyter-client>=5.1.0
RUN poetry add jupyter-core>=4.3.0
RUN poetry add libroadrunner>=2.1
RUN poetry add matplotlib>=2.0.2
RUN poetry add numpy>=1.23
RUN poetry add pandas>=0.20.2
RUN poetry add phrasedml{'version': '>=1.0.9', 'markers': 'platform_machine != "arm64"'}
RUN poetry add plotly>=2.0.12
RUN poetry add pytest*
RUN poetry add python-libcombine>=0.2.2
RUN poetry add python-libnuml>=1.0.0
RUN poetry add python-libsbml>=5.18.0
RUN poetry add python-libsedml>=2.0.17
RUN poetry add requests*
RUN poetry add rrplugins{'version': '>=2.1', 'markers': 'platform_system == "Windows"'}
RUN poetry add scipy>=1.5.1
RUN poetry add matplotlib*
RUN poetry add numpy*
RUN poetry add pandas*
RUN poetry add python-copasi*
RUN poetry add PyYAML*
RUN poetry add scipy*
ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]