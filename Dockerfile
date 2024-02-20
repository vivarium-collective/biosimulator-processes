FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    libncurses5 \
    cmake \
    make \
    ibx11-dev \
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
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y python3-pip

RUN pip install --upgrade pip && pip install poetry

# Add Poetry to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Avoid creating virtual environments as Docker provides isolation
RUN poetry config virtualenvs.create false

# Add the script directory to PATH
#ENV PATH="/app/scripts:${PATH}"
ENV PATH="/app/smoldyn:${PATH}"

# RUN poetry run ./scripts/install-smoldyn-mac-silicon.sh

# RUN poetry add tellurium && poetry add smoldyn

RUN poetry run pip install --upgrade pip \
    && poetry run pip install python-libnuml --use-pep517 \
    && poetry install

ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]

