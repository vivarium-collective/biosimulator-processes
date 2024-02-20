# FROM ubuntu:latest
# # FROM ghcr.io/biosimulators/biosimulators:latest
#
# WORKDIR /app
#
# COPY . /app
#
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     cmake \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*
#
# RUN pip install --upgrade pip \
#     && pip install poetry
#
# RUN poetry run pip install --upgrade pip \
#     && poetry run pip install smoldyn \
#     && poetry install
#     # && pip install .

# Start with the latest Ubuntu base image
FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python 3.9, pip, Python development package, and other dependencies
RUN apt-get update && apt-get install -y \
    # software-properties-common \
    # && add-apt-repository -y ppa:deadsnakes/ppa \
    # && apt-get update \
    # && apt-get install -y \
    # python3.9 \
    # python3.9-distutils \
    # python3.9-venv \
    # python3.9-dev \
    python3 \
    python3-pip \
    build-essential \
    libncurses5 \
    cmake \
    gcc \
    swig \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Update alternatives to use Python 3.9
# RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 \
#     && update-alternatives --set python3 /usr/bin/python3.9

# Install pip for Python 3.9
RUN apt-get update && apt-get install -y python3-pip

# Install Poetry
RUN python3 -m pip install poetry

# Avoid creating virtual environments as Docker provides isolation
RUN poetry config virtualenvs.create false

RUN poetry run pip install smoldyn

# Install project dependencies using Poetry
RUN poetry install

ENV DEBIAN_FRONTEND=interactive

ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
