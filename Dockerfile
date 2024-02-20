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
    gcc \
    swig \
    pkg-config \
    curl \
    tar \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y python3-pip

RUN python3 -m pip install poetry

# Avoid creating virtual environments as Docker provides isolation
RUN poetry config virtualenvs.create false

# RUN poetry run pip install smoldyn
# RUN curl -SL https://www.smoldyn.org/smoldyn-2.72.tgz -o smoldyn-2.72.tgz \
#     && tar -xzf smoldyn-2.72.tgz \
#     && rm smoldyn-2.72.tgz \
#     && mv smoldyn-2.72 smoldyn

# ENV PATH="/app/smoldyn:${PATH}"

RUN poetry add tellurium && poetry add smoldyn

RUN poetry install

ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]

