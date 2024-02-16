FROM ubuntu:latest

RUN echo "Installing singularity..."
RUN apt-get update -y && apt-get install -y \
            build-essential \
            libseccomp-dev \
            pkg-config \
            squashfs-tools
            # cryptsetup

ENV GO_VERSION "1.20"
ENV SINGULARITY_VERSION "3.9.5"
ENV OS "linux"
ENV ARCH "amd64"

RUN echo "Installing Go..." \
RUN wget https://dl.google.com/go/go$GO_VERSION.$OS-$ARCH.tar.gz \
  && tar -C /usr/local -xzvf go$GO_VERSION.$OS-$ARCH.tar.gz \
  && rm go$GO_VERSION.$OS-$ARCH.tar.gz \
  && echo 'export PATH=/usr/local/go/bin:$PATH' >> ~/.bashrc \
  && source ~/.bashrc \
  && echo "/usr/local/go/bin" >> $GITHUB_PATH \
  && echo "Installing Singularity..." \
  && wget https://github.com/sylabs/singularity/releases/download/v${SINGULARITY_VERSION}/singularity-ce-${SINGULARITY_VERSION}.tar.gz \
  && tar -xzf singularity-ce-${SINGULARITY_VERSION}.tar.gz \
  && cd singularity-ce-${SINGULARITY_VERSION} \
  && ./mconfig \
  && make -C builddir \
  && make -C builddir install

RUN echo "Installing python system dependencies..."
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

WORKDIR /app

COPY . /app

RUN echo "Installing python content..."
RUN pip install --upgrade pip \
    && pip install -U "ray[default]" \
    && ./scripts/install-smoldyn-mac-silicon.sh

RUN echo "Entering..."
ENTRYPOINT ["/bin/bash"]


# ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
