# use a more specific tag instead of latest for reproducibility
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# env deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10  \
    ca-certificates \
    libhdf5-dev \
    libhdf5-serial-dev \
    python3-pip  \
    python3-dev \
    build-essential  \
    libncurses5  \
    libxml2 \
    cmake  \
    make  \
    libx11-dev  \
    libc6-dev  \
    libx11-6  \
    libc6  \
    gcc  \
    libatlas-base-dev \
    swig \
    pkg-config  \
    curl  \
    tar  \
    libgl1-mesa-glx  \
    libice6  \
    libpython3.10  \
    libsm6 \
    wget  

# copy and make dirs
COPY biosimulators_processes /app/biosimulator_processes
# COPY composer-notebooks /app/notebooks

# copy files
COPY ./pyproject.toml ./poetry.lock ./README.md ./data ./scripts/trust-notebooks.sh /app/
COPY assets/scripts/enter-lab.sh /usr/local/bin/enter-lab.sh
# COPY ./scripts/xvfb-startup.sh /xvfb-startup.sh

# poetry deps
RUN python3.10 -m pip install --upgrade pip \
    && python3.10 -m pip install poetry \
    && poetry config virtualenvs.in-project true \
    && poetry env use 3.10 \
    && poetry install

# download and build Smoldyn
RUN . /app/.venv/bin/activate \
    && wget https://www.smoldyn.org/smoldyn-2.73.tgz \
    && tar -xzf smoldyn-2.73.tgz \
    && cd smoldyn-2.73 \
    && cd build \
    && cmake .. -DENABLE_PYTHON=ON -DPYTHON_EXECUTABLE=$(which python3.10) \
    && make \
    && make install \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoclean

ENV PLOTTING_ENGINE=matplotlib \
    PYTHONWARNINGS="ignore:The 'warn' parameter of use():UserWarning:tellurium.tellurium,ignore:Matplotlib is currently using agg:UserWarning:tellurium.plotting.engine_mpl"

# TODO: Use a more specific tag instead of latest for reproducibility
# FROM ubuntu:22.04
#
# ENV DEBIAN_FRONTEND=noninteractive
#     # XVFB_RES="1920x1080x24" \
#     # XVFB_ARGS="" \
#     # PATH="/app/.venv/bin:$PATH" \
#     # CONFIG_ENV_FILE="/app/config/config.env" \
#     # SECRET_ENV_FILE="/app/secret/secret.env" \
#     # STORAGE_GCS_CREDENTIALS_FILE="/app/secret/gcs_credentials.json" \
#     # STORAGE_LOCAL_CACHE_DIR="/app/scratch"
#
# WORKDIR /app
#
# # copy and make dirs
# COPY ./biosimulators_processes /app/biosimulators_processes
# COPY composer-notebooks /app/notebooks
#
# # copy files
# COPY pyproject.toml ./poetry.lock ./data ./scripts/trust-notebooks.sh /app/
# COPY ./scripts/enter-lab.sh /usr/local/bin/enter-lab.sh
# # COPY ./scripts/xvfb-startup.sh /xvfb-startup.sh
#
# VOLUME /app/data
#
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     python3.10  \
#     ca-certificates \
#     python3-pip  \
#     python3-dev \
#     build-essential  \
#     libncurses5  \
#     cmake  \
#     make  \
#     libx11-dev  \
#     libc6-dev  \
#     libx11-6  \
#     libc6  \
#     gcc  \
#     swig \
#     pkg-config  \
#     curl  \
#     tar  \
#     libgl1-mesa-glx  \
#     libice6  \
#     libpython3.10  \
#     libsm6 \
#     wget  \
#     && rm -rf /var/lib/apt/lists/* \
#     && pip install --upgrade pip && pip install poetry \
#     && poetry config virtualenvs.in-project true \
#     && poetry update \
#     && poetry install \
#     && chmod +x ./trust-composer-notebooks.sh \
#     && chmod +x /usr/local/bin/enter-lab.sh \
#     && ./trust-composer-notebooks.sh \
#     && rm ./trust-composer-notebooks.sh \
#     && apt-get clean \
#     && apt-get autoclean
#
# ENTRYPOINT ["/usr/local/bin/enter-lab.sh"]


# PLEASE NOTE: We do not need to add a USER in the Dockerfile as Singularity will handle
# such logic in conversion on the HPC.


# PLEASE NOTE: We do not need to add a USER in the Dockerfile as Singularity will handle
# such logic in conversion on the HPC.
