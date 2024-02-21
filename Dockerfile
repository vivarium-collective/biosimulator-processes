FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY . /app

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

# RUN apt-get update && apt-get install -y python3-pip

RUN apt-get -y update \
    \
    && apt-get install --no-install-recommends -y \
        xvfb \
    && mkdir /tmp/.X11-unix \
    && chmod 1777 /tmp/.X11-unix \
    \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/xvfb-startup.sh /xvfb-startup.sh

ENV XVFB_RES="1920x1080x24" \
    XVFB_ARGS=""

RUN pip install --upgrade pip \
    && pip install poetry

# Add Poetry to PATH
ENV PATH="/root/.local/bin:${PATH}"

# RUN poetry config virtualenvs.create false

RUN poetry run pip install --upgrade pip \
    && poetry run pip install python-libnuml --use-pep517 \
    && poetry run pip install jupyter \
    && poetry install

RUN jupyter trust /app/builder

ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]

