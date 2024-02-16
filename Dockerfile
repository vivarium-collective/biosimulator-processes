FROM ubuntu:latest

RUN echo "Installing system dependencies..."
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    apt-get update && sudo apt-get install -y \
    build-essential \
    libssl-dev \
    uuid-dev \
    libgpgme11-dev \
    squashfs-tools \
    libseccomp-dev \
    wget \
    pkg-config \
    git

RUN echo "Installing Go..."
RUN export VERSION=1.20 OS=linux ARCH=amd64 && \
    wget https://dl.google.com/go/go$VERSION.$OS-$ARCH.tar.gz && \
    tar -C /usr/local -xzvf go$VERSION.$OS-$ARCH.tar.gz && \
    rm go$VERSION.$OS-$ARCH.tar.gz

RUN echo "Installing singularity..."
RUN export VERSION=3.2.0 && # adjust this as necessary \
    wget https://github.com/sylabs/singularity/releases/download/v${VERSION}/singularity-${VERSION}.tar.gz && \
    tar -xzf singularity-${VERSION}.tar.gz && \
    cd singularity

WORKDIR /app

COPY . /app

RUN echo "Installing python content..."
RUN pip install --upgrade pip \
    && pip install -U "ray[default]" \
    && ./scripts/install-smoldyn-mac-silicon.sh

RUN echo "Entering..."
ENTRYPOINT ["/bin/bash"]


# ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
