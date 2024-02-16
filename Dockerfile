# TODO: Make this work for Smoldyn to be platform-agnostic

FROM ubuntu:latest
# FROM ghcr.io/biosimulators/biosimulators:latest

# Implement the next two lines for use in Cloud
# RUN useradd -m simuser

# USER simuser

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    libssl-dev \
    uuid-dev \
    make \
    libgpgme11-dev \
    squashfs-tools \
    libseccomp-dev \
    wget \
    pkg-config \
    git \
    golang-go \
    && rm -rf /var/lib/apt/lists/*

# Optional: Create a symlink for python and pip if you want to use `python` and `pip` commands directly
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN pip install --upgrade pip \
    && pip install -U "ray[default]" \
    && ./scripts/install-smoldyn-mac-silicon.sh

# Install Go for ARM64
RUN wget https://go.dev/dl/go1.20.linux-arm64.tar.gz -O go.tar.gz && \
    tar -C /usr/local -xzf go.tar.gz && \
    rm go.tar.gz

# Set Go environment variables
ENV PATH="/usr/local/go/bin:${PATH}"

# Verify Go installation
RUN go version

# Clone the Singularity repository
RUN git clone https://github.com/sylabs/singularity.git && \
    cd singularity && \
    git checkout v4.1.1

WORKDIR /app/singularity

# Run mconfig
RUN ./mconfig --prefix=/opt/singularity && \
    make -C builddir && \
    make -C builddir install

WORKDIR /app

ENTRYPOINT ["/bin/bash"]





# ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
